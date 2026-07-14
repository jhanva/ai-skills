#!/usr/bin/env python3
"""
codegraph.py — Knowledge graph de un proyecto de codigo. Zero dependencias.

Convierte una carpeta (codigo, SQL, docs, configs) en un grafo consultable:
nodos = archivos/clases/funciones/tablas/conceptos, edges = imports/calls/
herencia/referencias, con tag de confianza (EXTRACTED/INFERRED/AMBIGUOUS).

Uso:
  python codegraph.py build <ruta> [--force] [--no-html] [--directed]
  python codegraph.py label <ruta> --file labels.json
  python codegraph.py query <ruta> "pregunta" [--dfs] [--budget N]
  python codegraph.py path <ruta> "ConceptoA" "ConceptoB"
  python codegraph.py explain <ruta> "Concepto"
  python codegraph.py vocab <ruta>
  python codegraph.py merge-fragments <ruta> [--dir DIR]
  python codegraph.py save-answer <ruta> --question Q --answer A [--nodes N...]
  python codegraph.py stats <ruta>

Outputs en <ruta>/codegraph-out/:
  graph.json       — grafo completo (node-link, compatible d3)
  GRAPH_REPORT.md  — reporte legible con god nodes, comunidades, preguntas
  graph.html       — visualizacion interactiva autocontenida
  cache/           — extracciones por archivo (hash de contenido)
  labels.json      — nombres de comunidades (los pone el agente)
  semantic.json    — fragmentos semanticos LLM + respuestas guardadas

`build` es incremental por defecto: los archivos sin cambios se leen del
cache. `--force` re-extrae todo.

Exit codes: 0 ok · 1 error de datos (grafo vacio, sin graph.json) · 2 uso.
"""

import argparse
import hashlib
import json
import sys
import time
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import cg_analyze
import cg_extract
import cg_html
import cg_query

OUT_DIR_NAME = "codegraph-out"
MAX_FILE_BYTES = 1_500_000

SKIP_DIRS = {
    ".git", ".svn", ".hg", "node_modules", "__pycache__", ".venv", "venv",
    "env", ".tox", ".mypy_cache", ".pytest_cache", ".ruff_cache", "dist",
    "build", "target", "out", "bin", "obj", ".gradle", ".idea", ".vscode",
    "vendor", "Pods", ".dart_tool", ".next", ".nuxt", "coverage",
    OUT_DIR_NAME, "graphify-out", ".godot",
}
SKIP_FILE_PREFIXES = (".env",)
SKIP_FILE_SUFFIXES = (".pem", ".key", ".pfx", ".p12", ".keystore", ".jks",
                      ".lock", ".min.js", ".min.css", ".map")
SKIP_FILE_NAMES = {"package-lock.json", "yarn.lock", "uv.lock", "Cargo.lock",
                   "poetry.lock", "composer.lock", "Gemfile.lock"}

FILE_CATEGORIES = {
    "python": "code", "javascript": "code", "typescript": "code",
    "kotlin": "code", "java": "code", "csharp": "code", "go": "code",
    "rust": "code", "gdscript": "code", "shell": "code",
    "powershell": "code", "php": "code", "ruby": "code", "swift": "code",
    "c": "code", "cpp": "code",
    "sql": "sql", "markdown": "docs", "config": "config",
}


def eprint(*args):
    print(*args, file=sys.stderr)


def out_dir(root):
    return root / OUT_DIR_NAME


# ---------------------------------------------------------------------------
# Scan
# ---------------------------------------------------------------------------

def scan(root):
    """Recorre root y devuelve (files, skipped_sensitive). files es lista
    de rutas relativas (posix) de archivos soportados."""
    files = []
    skipped_sensitive = 0
    root = root.resolve()
    stack = [root]
    while stack:
        d = stack.pop()
        try:
            entries = sorted(d.iterdir(), key=lambda p: p.name)
        except (PermissionError, OSError):
            continue
        for p in entries:
            name = p.name
            if p.is_dir():
                if name not in SKIP_DIRS and not name.startswith(".git"):
                    stack.append(p)
                continue
            if name in SKIP_FILE_NAMES:
                continue
            if name.startswith(SKIP_FILE_PREFIXES):
                skipped_sensitive += 1
                continue
            if name.lower().endswith(SKIP_FILE_SUFFIXES):
                continue
            if cg_extract.language_of(name) is None:
                continue
            try:
                if p.stat().st_size > MAX_FILE_BYTES:
                    continue
            except OSError:
                continue
            files.append(p.relative_to(root).as_posix())
    return sorted(files), skipped_sensitive


def read_text(path):
    try:
        raw = path.read_bytes()
    except OSError:
        return None
    if b"\x00" in raw[:4096]:
        return None  # binario
    for enc in ("utf-8", "latin-1"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return None


# ---------------------------------------------------------------------------
# Cache de extraccion por archivo
# ---------------------------------------------------------------------------

def _cache_path(od, digest):
    return od / "cache" / f"{digest}.json"


def extract_with_cache(root, files, od, force=False):
    """Extrae cada archivo, usando cache por hash de contenido."""
    extractions = []
    hits = 0
    manifest = {}
    (od / "cache").mkdir(parents=True, exist_ok=True)
    live_digests = set()
    for rel in files:
        text = read_text(root / rel)
        if text is None:
            continue
        digest = hashlib.sha256(
            (rel + "\x00" + text).encode("utf-8", "replace")).hexdigest()
        manifest[rel] = digest
        live_digests.add(digest)
        cpath = _cache_path(od, digest)
        if not force and cpath.exists():
            try:
                extractions.append(
                    json.loads(cpath.read_text(encoding="utf-8")))
                hits += 1
                continue
            except (json.JSONDecodeError, OSError):
                pass
        result = cg_extract.extract_file(rel, text)
        if result is None:
            continue
        cpath.write_text(
            json.dumps(result, ensure_ascii=False), encoding="utf-8")
        extractions.append(result)
    # limpiar cache huerfano
    for stale in (od / "cache").glob("*.json"):
        if stale.stem not in live_digests:
            stale.unlink(missing_ok=True)
    (od / "manifest.json").write_text(
        json.dumps(manifest, indent=1, ensure_ascii=False), encoding="utf-8")
    return extractions, hits


# ---------------------------------------------------------------------------
# Fragmentos semanticos (subagentes LLM) y respuestas guardadas
# ---------------------------------------------------------------------------

def load_semantic(od):
    p = od / "semantic.json"
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            eprint("ADVERTENCIA: semantic.json corrupto, se ignora")
    return {"nodes": [], "edges": []}


def save_semantic(od, data):
    (od / "semantic.json").write_text(
        json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")


def merge_fragments(od, frag_dir):
    """Valida y fusiona fragmentos JSON de subagentes en semantic.json."""
    sem = load_semantic(od)
    seen = {n["id"] for n in sem["nodes"]}
    added_n = added_e = bad = 0
    for f in sorted(Path(frag_dir).glob("*.json")):
        try:
            frag = json.loads(f.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            eprint(f"  fragmento invalido (JSON): {f.name}")
            bad += 1
            continue
        for n in frag.get("nodes", []):
            if not isinstance(n, dict) or "id" not in n or "label" not in n:
                continue
            if n["id"] in seen:
                continue
            seen.add(n["id"])
            sem["nodes"].append({
                "id": cg_extract.norm_id(str(n["id"])),
                "label": str(n["label"])[:120],
                "kind": n.get("kind", "concept"),
                "file_type": n.get("file_type", "concept"),
                "source_file": n.get("source_file"),
                "source_location": n.get("source_location"),
            })
            added_n += 1
        for e in frag.get("edges", []):
            if not isinstance(e, dict) or "source" not in e \
                    or "target" not in e:
                continue
            conf = e.get("confidence", "INFERRED")
            if conf not in ("EXTRACTED", "INFERRED", "AMBIGUOUS"):
                conf = "INFERRED"
            sem["edges"].append({
                "source": cg_extract.norm_id(str(e["source"])),
                "target": cg_extract.norm_id(str(e["target"])),
                "relation": str(e.get("relation", "references"))[:60],
                "confidence": conf,
                "confidence_score": float(e.get("confidence_score", 0.75)),
                "source_file": e.get("source_file"),
                "source_location": e.get("source_location"),
            })
            added_e += 1
    save_semantic(od, sem)
    print(f"Fragmentos fusionados: +{added_n} nodos, +{added_e} edges"
          + (f", {bad} invalidos" if bad else ""))
    print("Ejecuta 'build' para integrarlos al grafo.")


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------

def _node_degrees(edges):
    deg = defaultdict(int)
    for e in edges:
        deg[e["source"]] += 1
        deg[e["target"]] += 1
    return deg


def _community_reps(nodes, edges, communities):
    """Nodo representativo por comunidad: el de mayor grado (empate ->
    id lexicografico menor). Es el ancla estable de los labels."""
    deg = _node_degrees(edges)
    best = {}
    for n in nodes:
        c = communities.get(n["id"])
        if c is None:
            continue
        cand = (-deg.get(n["id"], 0), n["id"])
        if c not in best or cand < best[c]:
            best[c] = cand
    return {c: nid for c, (_, nid) in best.items()}


def load_labels(od, nodes=None, edges=None, communities=None):
    """Labels anclados a nodos representativos, no a ids numericos.

    Los ids de comunidad cambian entre rebuilds cuando el corpus cambia;
    el ancla por nodo sobrevive. Devuelve {community_id: nombre} para el
    build actual. Un miembro anclado le da nombre a su comunidad (gana el
    de mayor grado si hay varios)."""
    p = od / "labels.json"
    if not p.exists():
        return {}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    anchors = data.get("anchors", {})
    if not anchors or nodes is None:
        return {}
    deg = _node_degrees(edges or [])
    result = {}
    strength = {}
    for n in nodes:
        nid = n["id"]
        if nid not in anchors:
            continue
        c = communities.get(nid)
        if c is None:
            continue
        d = deg.get(nid, 0)
        if c not in result or d > strength[c]:
            result[c] = anchors[nid]
            strength[c] = d
    return result


def cmd_build(args):
    root = Path(args.ruta).resolve()
    if not root.is_dir():
        eprint(f"ERROR: no es un directorio: {root}")
        return 2
    od = out_dir(root)
    od.mkdir(parents=True, exist_ok=True)
    t0 = time.time()

    files, skipped = scan(root)
    if not files:
        eprint("ERROR: no hay archivos soportados en la ruta.")
        return 1
    by_cat = defaultdict(int)
    for rel in files:
        by_cat[FILE_CATEGORIES.get(cg_extract.language_of(rel), "otros")] += 1

    extractions, cache_hits = extract_with_cache(
        root, files, od, force=args.force)
    resolved = cg_extract.resolve(extractions, files)
    nodes, edges = resolved["nodes"], resolved["edges"]

    # fusionar capa semantica (fragmentos LLM + respuestas guardadas)
    sem = load_semantic(od)
    known = {n["id"] for n in nodes}
    for n in sem["nodes"]:
        if n["id"] not in known:
            known.add(n["id"])
            nodes.append(n)
    dangling = 0
    for e in sem["edges"]:
        if e["source"] in known and e["target"] in known:
            edges.append(e)
        else:
            dangling += 1

    if not nodes:
        eprint("ERROR: el grafo quedo vacio - la extraccion no produjo nodos.")
        return 1

    # proteccion anti-encogimiento: no pisar un grafo bueno con uno menor
    gpath = od / "graph.json"
    if gpath.exists() and not args.force:
        try:
            prev = json.loads(gpath.read_text(encoding="utf-8"))
            if len(nodes) < len(prev.get("nodes", [])) * 0.5:
                eprint(f"ERROR: el nuevo grafo ({len(nodes)} nodos) es menos "
                       f"de la mitad del existente "
                       f"({len(prev['nodes'])} nodos).")
                eprint("Si es intencional (borraste archivos), usa --force.")
                return 1
        except (json.JSONDecodeError, OSError):
            pass

    communities = cg_analyze.louvain(nodes, edges)
    for n in nodes:
        n["community"] = communities.get(n["id"], 0)
    cohesion = cg_analyze.cohesion_scores(nodes, edges, communities)
    comm_labels = load_labels(od, nodes, edges, communities)
    gods = cg_analyze.god_nodes(nodes, edges)
    surprises = cg_analyze.surprising_connections(nodes, edges, communities)
    questions = cg_analyze.suggest_questions(
        nodes, edges, communities, comm_labels)

    meta = {
        # solo el nombre de la carpeta: graph.json es committeable y no debe
        # llevar rutas absolutas de la maquina local
        "root": root.name,
        "date": time.strftime("%Y-%m-%d"),
        "total_files": len(files),
        "skipped": skipped,
        "by_category": dict(by_cat),
    }
    health = {
        "dropped_ambiguous": resolved["dropped_ambiguous"],
        "dangling": dangling,
    }

    graph_doc = {
        "directed": True,
        "multigraph": False,
        "graph": {**meta, "tool": "codegraph", "version": 1},
        "nodes": nodes,
        "links": edges,
    }
    gpath.write_text(
        json.dumps(graph_doc, indent=1, ensure_ascii=False),
        encoding="utf-8")

    report = cg_analyze.render_report(
        meta, nodes, edges, communities, comm_labels, cohesion,
        gods, surprises, questions, health)
    (od / "GRAPH_REPORT.md").write_text(report, encoding="utf-8")

    comm_sizes = defaultdict(int)
    for c in communities.values():
        comm_sizes[c] += 1
    ranked = sorted(comm_sizes, key=lambda c: (-comm_sizes[c], c))
    comm_list = [{"id": c, "label": comm_labels.get(c, f"Comunidad {c}"),
                  "size": comm_sizes[c]} for c in ranked[:24]]

    if not args.no_html:
        html = cg_html.render_html(
            root.name, f"{len(nodes)} nodos - {len(edges)} edges - "
            f"{len(comm_list)} comunidades", nodes, edges, comm_list)
        (od / "graph.html").write_text(html, encoding="utf-8")

    elapsed = time.time() - t0
    print(f"Corpus: {len(files)} archivos "
          f"({', '.join(f'{v} {k}' for k, v in sorted(by_cat.items()))})"
          + (f" - {skipped} sensibles omitidos" if skipped else ""))
    print(f"Grafo: {len(nodes)} nodos, {len(edges)} edges, "
          f"{len(comm_list)} comunidades "
          f"[cache: {cache_hits}/{len(files)} hits]")
    if health["dropped_ambiguous"]:
        print(f"Salud: {health['dropped_ambiguous']} llamadas ambiguas "
              f"descartadas (no se inventan edges)")
    if dangling:
        print(f"Salud: {dangling} edges semanticos con extremos "
              f"desconocidos, omitidos")
    unlabeled = [c for c in ranked[:20] if c not in comm_labels]
    if unlabeled:
        print(f"Pendiente: {len(unlabeled)} comunidades principales sin "
              f"nombre (ids: {unlabeled}) - revisa GRAPH_REPORT.md y "
              f"ejecuta 'label'")
    print(f"Outputs en {od} ({elapsed:.1f}s)")
    return 0


def cmd_label(args):
    root = Path(args.ruta).resolve()
    od = out_dir(root)
    if args.file:
        try:
            labels = json.loads(Path(args.file).read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as e:
            eprint(f"ERROR leyendo labels: {e}")
            return 2
    else:
        try:
            labels = json.loads(args.labels or "{}")
        except json.JSONDecodeError as e:
            eprint(f"ERROR en JSON de labels: {e}")
            return 2
    if not labels:
        eprint("ERROR: no se recibieron labels.")
        return 2
    # convertir {community_id: nombre} del build actual en anclas estables
    # {nodo_representativo: nombre} que sobreviven renumeraciones futuras
    nodes, edges = load_graph(args.ruta)
    communities = {n["id"]: n.get("community") for n in nodes
                   if n.get("community") is not None}
    reps = _community_reps(nodes, edges, communities)
    p = od / "labels.json"
    existing = {}
    if p.exists():
        try:
            existing = json.loads(
                p.read_text(encoding="utf-8")).get("anchors", {})
        except json.JSONDecodeError:
            pass
    missing = []
    for k, v in labels.items():
        rep = reps.get(int(k))
        if rep is None:
            missing.append(k)
            continue
        existing[rep] = str(v)
    p.write_text(json.dumps({"anchors": existing}, indent=1,
                            ensure_ascii=False), encoding="utf-8")
    if missing:
        eprint(f"ADVERTENCIA: comunidades inexistentes ignoradas: {missing}")
    print(f"Labels guardados: {len(existing)} anclas. Regenerando...")
    args.force = False
    args.no_html = False
    return cmd_build(args)


# ---------------------------------------------------------------------------
# Consultas
# ---------------------------------------------------------------------------

def load_graph(root):
    gpath = out_dir(Path(root).resolve()) / "graph.json"
    if not gpath.exists():
        eprint("ERROR: no existe codegraph-out/graph.json - "
               "ejecuta primero: codegraph.py build <ruta>")
        sys.exit(1)
    doc = json.loads(gpath.read_text(encoding="utf-8"))
    return doc["nodes"], doc["links"]


def cmd_query(args):
    nodes, edges = load_graph(args.ruta)
    matches = cg_query.match_nodes(nodes, args.pregunta, top=3)
    if not matches:
        print("Sin nodos que matcheen la pregunta. "
              "Usa 'vocab' para ver el vocabulario del grafo.")
        return 0
    seeds = [nid for _, nid in matches]
    mode = "dfs" if args.dfs else "bfs"
    sub_nodes, sub_edges = cg_query.traverse(nodes, edges, seeds, mode)
    print(f"Modo: {mode.upper()}")
    print(cg_query.format_subgraph(
        nodes, sub_nodes, sub_edges, args.pregunta, seeds,
        token_budget=args.budget))
    return 0


def cmd_path(args):
    nodes, edges = load_graph(args.ruta)
    print(cg_query.shortest_path(nodes, edges, args.a, args.b))
    return 0


def cmd_explain(args):
    nodes, edges = load_graph(args.ruta)
    print(cg_query.explain_node(nodes, edges, args.concepto))
    return 0


def cmd_vocab(args):
    nodes, _ = load_graph(args.ruta)
    vocab = cg_query.vocabulary(nodes)
    print("\n".join(vocab))
    eprint(f"({len(vocab)} tokens)")
    return 0


def cmd_stats(args):
    nodes, edges = load_graph(args.ruta)
    by_conf = defaultdict(int)
    by_rel = defaultdict(int)
    for e in edges:
        by_conf[e["confidence"]] += 1
        by_rel[e["relation"]] += 1
    by_kind = defaultdict(int)
    for n in nodes:
        by_kind[n.get("kind", "?")] += 1
    print(f"Nodos: {len(nodes)}")
    for k, v in sorted(by_kind.items(), key=lambda kv: -kv[1]):
        print(f"  {k}: {v}")
    print(f"Edges: {len(edges)}")
    for k, v in sorted(by_rel.items(), key=lambda kv: -kv[1]):
        print(f"  {k}: {v}")
    print("Confianza:")
    for k, v in sorted(by_conf.items()):
        print(f"  {k}: {v}")
    return 0


def cmd_save_answer(args):
    root = Path(args.ruta).resolve()
    od = out_dir(root)
    nodes, _ = load_graph(args.ruta)
    sem = load_semantic(od)
    aid = "answer_" + hashlib.sha256(
        args.question.encode("utf-8")).hexdigest()[:12]
    if any(n["id"] == aid for n in sem["nodes"]):
        print("Esta pregunta ya estaba guardada.")
        return 0
    sem["nodes"].append({
        "id": aid,
        "label": "Q: " + args.question[:90],
        "kind": "answer",
        "file_type": "answer",
        "source_file": None,
        "source_location": None,
        "answer": args.answer[:2000],
        "outcome": args.outcome,
    })
    cited = 0
    for term in args.nodes or []:
        m = cg_query.match_nodes(nodes, term, top=1)
        if m:
            sem["edges"].append({
                "source": aid, "target": m[0][1], "relation": "cites",
                "confidence": "EXTRACTED", "confidence_score": 1.0,
                "source_file": None, "source_location": None,
            })
            cited += 1
    save_semantic(od, sem)
    print(f"Respuesta guardada ({cited} nodos citados). "
          f"Se integra al grafo en el proximo build.")
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    ap = argparse.ArgumentParser(prog="codegraph", add_help=True)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("build", help="construir/actualizar el grafo")
    p.add_argument("ruta")
    p.add_argument("--force", action="store_true",
                   help="ignorar cache y proteccion anti-encogimiento")
    p.add_argument("--no-html", action="store_true")
    p.set_defaults(fn=cmd_build)

    p = sub.add_parser("label", help="nombrar comunidades y regenerar")
    p.add_argument("ruta")
    p.add_argument("--file", help="archivo JSON {\"0\": \"nombre\", ...}")
    p.add_argument("--labels", help="JSON inline")
    p.set_defaults(fn=cmd_label)

    p = sub.add_parser("query", help="consultar el grafo")
    p.add_argument("ruta")
    p.add_argument("pregunta")
    p.add_argument("--dfs", action="store_true",
                   help="trazado en profundidad (cadenas)")
    p.add_argument("--budget", type=int, default=2000,
                   help="presupuesto de tokens del output")
    p.set_defaults(fn=cmd_query)

    p = sub.add_parser("path", help="camino mas corto entre dos conceptos")
    p.add_argument("ruta")
    p.add_argument("a")
    p.add_argument("b")
    p.set_defaults(fn=cmd_path)

    p = sub.add_parser("explain", help="explicar un nodo y sus conexiones")
    p.add_argument("ruta")
    p.add_argument("concepto")
    p.set_defaults(fn=cmd_explain)

    p = sub.add_parser("vocab", help="vocabulario de tokens del grafo")
    p.add_argument("ruta")
    p.set_defaults(fn=cmd_vocab)

    p = sub.add_parser("merge-fragments",
                       help="fusionar fragmentos semanticos de subagentes")
    p.add_argument("ruta")
    p.add_argument("--dir", default=None,
                   help="carpeta de fragmentos (default: "
                        "codegraph-out/fragments)")
    p.set_defaults(fn=lambda a: merge_fragments(
        out_dir(Path(a.ruta).resolve()),
        a.dir or out_dir(Path(a.ruta).resolve()) / "fragments") or 0)

    p = sub.add_parser("save-answer",
                       help="guardar una respuesta en el grafo")
    p.add_argument("ruta")
    p.add_argument("--question", required=True)
    p.add_argument("--answer", required=True)
    p.add_argument("--nodes", nargs="*")
    p.add_argument("--outcome", choices=["useful", "dead_end", "corrected"],
                   default="useful")
    p.set_defaults(fn=cmd_save_answer)

    p = sub.add_parser("stats", help="estadisticas del grafo")
    p.add_argument("ruta")
    p.set_defaults(fn=cmd_stats)

    args = ap.parse_args(argv)
    try:
        return args.fn(args) or 0
    except BrokenPipeError:
        return 0
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    sys.exit(main())
