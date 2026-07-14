"""
cg_query.py — Consultas contra un grafo ya construido.

query    — BFS (contexto amplio) o DFS (trazar cadenas) desde los nodos
           que mejor matchean la pregunta. Scoring por tokens con IDF.
explain  — un nodo y todas sus conexiones.
path     — camino mas corto entre dos conceptos.
vocab    — vocabulario de tokens del grafo (para expansion de queries).

El matching tokeniza labels partiendo camelCase y snake_case, y pondera
por IDF: tokens raros en el grafo pesan mas que tokens omnipresentes.
"""

import math
import re
from collections import defaultdict, deque

_TOKEN_RE = re.compile(r"[^\W\d_]+", re.UNICODE)
_CAMEL_RE = re.compile(r"[A-Z]+(?=[A-Z][a-z])|[A-Z]?[a-z]+|[A-Z]+|\d+")

# palabras funcionales ES/EN que no discriminan en una pregunta
STOPWORDS = {
    "de", "la", "el", "los", "las", "un", "una", "unos", "unas", "que",
    "como", "para", "por", "con", "sin", "del", "en", "es", "son", "se",
    "al", "su", "sus", "esta", "este", "hay", "donde", "cual", "cuales",
    "funciona", "funcionan", "hace", "usa", "usan",
    "the", "an", "of", "to", "in", "for", "how", "does", "do", "what",
    "is", "are", "and", "or", "not", "with", "from", "where", "which",
    "works", "work", "use", "uses",
}


def tokenize(text):
    """'parseHTMLResponse_v2' -> ['parse', 'html', 'response']"""
    tokens = []
    for chunk in _TOKEN_RE.findall(text or ""):
        for part in _CAMEL_RE.findall(chunk) or [chunk]:
            t = part.lower()
            if 2 <= len(t) <= 30:
                tokens.append(t)
    return tokens


def build_index(nodes):
    """token -> set(node_id), + idf por token."""
    index = defaultdict(set)
    for n in nodes:
        for t in set(tokenize(n["label"]) + tokenize(n.get("source_file") or "")):
            index[t].add(n["id"])
    total = max(1, len(nodes))
    idf = {t: math.log(total / len(ids)) + 1.0 for t, ids in index.items()}
    return index, idf


def vocabulary(nodes):
    index, _ = build_index(nodes)
    return sorted(t for t in index if len(t) >= 3)


def match_nodes(nodes, question, top=3):
    """Devuelve [(score, node_id)] de los nodos que mejor matchean."""
    index, idf = build_index(nodes)
    q_tokens = set(tokenize(question)) - STOPWORDS
    scores = defaultdict(float)
    for t in q_tokens:
        for nid in index.get(t, ()):
            scores[nid] += idf[t]
    ranked = sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))
    return [(round(s, 2), nid) for nid, s in ranked[:top]]


def adjacency(edges):
    adj = defaultdict(list)
    for e in edges:
        adj[e["source"]].append((e["target"], e))
        adj[e["target"]].append((e["source"], e))
    return adj


def traverse(nodes, edges, seeds, mode="bfs", max_depth=None):
    """Subgrafo alcanzable desde seeds. BFS depth 3 / DFS depth 6."""
    adj = adjacency(edges)
    depth_cap = max_depth or (6 if mode == "dfs" else 3)
    visited = set(seeds)
    sub_edges = []
    if mode == "dfs":
        stack = [(s, 0) for s in reversed(seeds)]
        while stack:
            node, depth = stack.pop()
            if depth >= depth_cap:
                continue
            for nbr, e in sorted(adj[node], key=lambda x: x[0]):
                sub_edges.append(e)
                if nbr not in visited:
                    visited.add(nbr)
                    stack.append((nbr, depth + 1))
    else:
        frontier = list(seeds)
        for _ in range(depth_cap):
            nxt = []
            for node in frontier:
                for nbr, e in sorted(adj[node], key=lambda x: x[0]):
                    sub_edges.append(e)
                    if nbr not in visited:
                        visited.add(nbr)
                        nxt.append(nbr)
            frontier = nxt
            if not frontier:
                break
    # dedup edges preservando orden
    seen = set()
    deduped = []
    for e in sub_edges:
        key = (e["source"], e["target"], e["relation"])
        if key not in seen and e["source"] in visited and e["target"] in visited:
            seen.add(key)
            deduped.append(e)
    return visited, deduped


def format_subgraph(nodes, sub_nodes, sub_edges, question, seeds,
                    token_budget=2000):
    """Salida rankeada por relevancia, cortada al presupuesto de tokens."""
    by_id = {n["id"]: n for n in nodes}
    q_tokens = set(tokenize(question)) - STOPWORDS

    def relevance(nid):
        n = by_id.get(nid, {})
        return sum(1 for t in tokenize(n.get("label", "")) if t in q_tokens)

    ranked = sorted(sub_nodes, key=lambda nid: (-relevance(nid), nid))
    # seleccion por presupuesto: nodos mas relevantes primero, y solo los
    # edges entre nodos seleccionados. Evita truncar el output a ciegas.
    node_cap = max(12, min(len(ranked), token_budget // 40))
    selected = set(seeds)
    for nid in ranked:
        if len(selected) >= node_cap:
            break
        selected.add(nid)
    kept_edges = [e for e in sub_edges
                  if e["source"] in selected and e["target"] in selected]

    seed_labels = [by_id[s]["label"] for s in seeds if s in by_id]
    omitted = len(sub_nodes) - len(selected)
    lines = [f"Seeds: {seed_labels} | subgrafo: {len(sub_nodes)} nodos"
             + (f" (mostrando {len(selected)} mas relevantes, "
                f"{omitted} omitidos - sube --budget para mas)"
                if omitted > 0 else "")]
    for nid in [n for n in ranked if n in selected]:
        n = by_id.get(nid)
        if not n:
            continue
        loc = f" {n.get('source_location')}" if n.get("source_location") else ""
        src = n.get("source_file") or "externo"
        lines.append(f"  NODE {n['label']} [{n.get('kind', '?')}] "
                     f"({src}{loc})")
    for e in kept_edges:
        su = by_id.get(e["source"], {}).get("label", e["source"])
        sv = by_id.get(e["target"], {}).get("label", e["target"])
        lines.append(f"  EDGE {su} --{e['relation']} "
                     f"[{e['confidence']}]--> {sv}")
    out = "\n".join(lines)
    char_budget = token_budget * 4
    if len(out) > char_budget:
        out = out[:char_budget] + (
            f"\n... (truncado a ~{token_budget} tokens - usa --budget N "
            f"para mas)")
    return out


def shortest_path(nodes, edges, term_a, term_b):
    """BFS de camino mas corto entre los mejores matches de dos terminos."""
    ma = match_nodes(nodes, term_a, top=1)
    mb = match_nodes(nodes, term_b, top=1)
    if not ma or not mb:
        missing = term_a if not ma else term_b
        return f"No hay nodo que matchee: {missing!r}"
    src, tgt = ma[0][1], mb[0][1]
    by_id = {n["id"]: n for n in nodes}
    adj = adjacency(edges)
    prev = {src: (None, None)}
    queue = deque([src])
    while queue:
        u = queue.popleft()
        if u == tgt:
            break
        for v, e in sorted(adj[u], key=lambda x: x[0]):
            if v not in prev:
                prev[v] = (u, e)
                queue.append(v)
    if tgt not in prev:
        return (f"Sin camino entre '{by_id[src]['label']}' y "
                f"'{by_id[tgt]['label']}'")
    # reconstruir
    hops = []
    cur = tgt
    while cur is not None:
        parent, e = prev[cur]
        hops.append((cur, e))
        cur = parent
    hops.reverse()
    lines = [f"Camino mas corto ({len(hops) - 1} saltos):"]
    for i, (nid, e) in enumerate(hops):
        label = by_id.get(nid, {}).get("label", nid)
        if i == 0:
            lines.append(f"  {label}")
        else:
            lines.append(f"  --{e['relation']} [{e['confidence']}]--> "
                         f"{label}")
    return "\n".join(lines)


def explain_node(nodes, edges, term):
    matches = match_nodes(nodes, term, top=1)
    if not matches:
        return f"No hay nodo que matchee: {term!r}"
    nid = matches[0][1]
    by_id = {n["id"]: n for n in nodes}
    n = by_id[nid]
    adj = adjacency(edges)
    lines = [
        f"NODE: {n['label']}",
        f"  id: {nid}",
        f"  tipo: {n.get('kind', '?')} / {n.get('file_type', '?')}",
        f"  fuente: {n.get('source_file') or 'externo'} "
        f"{n.get('source_location') or ''}".rstrip(),
        f"  grado: {len(adj[nid])}",
        f"  comunidad: {n.get('community', '?')}",
        "",
        "CONEXIONES:",
    ]
    for nbr, e in sorted(adj[nid], key=lambda x: (x[1]["relation"], x[0])):
        other = by_id.get(nbr, {})
        direction = "-->" if e["source"] == nid else "<--"
        lines.append(f"  {direction} {other.get('label', nbr)} "
                     f"[{e['relation']}, {e['confidence']}] "
                     f"({other.get('source_file') or 'externo'})")
    return "\n".join(lines)
