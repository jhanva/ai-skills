#!/usr/bin/env python3
"""
search.py — Consulta el catalogo UI/UX del plugin design.

Uso (python puede ser python3 o py segun la maquina):
  python search.py "<consulta>" --domain <style|palette|typography|ux|motion> [-n N] [--json]
  python search.py "<consulta>" --stack <compose|web> [-n N] [--json]
  python search.py "<consulta>" --design-system -p "Nombre" --stack <compose|web> [--mode <modo>] [--json]
  python search.py "<consulta>" --design-system -p "Nombre" --stack <stack> --persist --output-dir <raiz> [--page <nombre>] [--force]
  python search.py "<consulta>" --design-system ... --persist --audience "..." --context "..." [--voice "..."] [--constraints "..."]

Modos por superficie (--mode; si se omite se infiere de la consulta y se marca como no verificado):
  persuadir   el visitante decide y actua: landing, marketing, pricing
  operar      el visitante completa tareas: app, dashboard, formularios, admin
  leer        el visitante entiende algo: docs, articulos, ayuda
  experimentar el visitante esta dentro de la obra: portfolio, galeria, showcase

Exit codes:
  0 = resultados encontrados / archivo escrito / --help
  1 = sin resultados que superen el umbral de relevancia
  2 = error de uso (dominio o stack invalido, argumentos incompletos)
  3 = se nego a sobreescribir un archivo existente (usar --force con autorizacion del usuario)
  4 = error inesperado
"""

import argparse
import json
import re
import sys
import unicodedata
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import catalog  # noqa: E402

SPACING = {
    "baja": ("24, 32, 48, 64, 96", "Espaciosa: marketing, lectura, onboarding"),
    "media": ("8, 16, 24, 32, 48, 64", "Estandar: apps de producto"),
    "alta": ("4, 8, 12, 16, 24, 32", "Densa: dashboards, tablas, herramientas internas"),
}
FALLBACK = {"style": "minimalismo-editorial", "palette": "neutral-producto", "typography": "sistema-neutral"}

MODES = {
    "persuadir": (
        "El visitante decide y actua; el diseno es el producto.",
        "Gana la expresion: una idea por seccion, imagen real, CTA visible en el primer viewport. Las reglas de composicion (comp-*) aplican completas.",
        ("landing", "marketing", "campana", "pricing", "precio", "portada", "home", "venta", "conversion", "promocion", "lanzamiento", "waitlist", "sitio"),
    ),
    "operar": (
        "El visitante completa una tarea.",
        "Gana la escaneabilidad: consistencia, expectativas nativas, densidad segun el uso real. La marca vive en los detalles, no en el layout.",
        ("app", "dashboard", "panel", "admin", "formulario", "herramienta", "configuracion", "editor", "consola", "tarea", "gestion", "checkout", "onboarding", "chat", "mapa", "pantalla"),
    ),
    "leer": (
        "El visitante entiende algo.",
        "Gana la comprension: estructura navegable, medida de 60-75 caracteres, jerarquia de encabezados; la expresion va despues.",
        ("documentacion", "docs", "articulo", "blog", "ayuda", "guia", "changelog", "legal", "terminos", "manual", "lectura", "noticias"),
    ),
    "experimentar": (
        "El visitante esta dentro de la obra.",
        "Gana el artefacto: la interfaz retrocede, el contenido manda desde el primer viewport; motion con proposito, nunca decorativo.",
        ("portfolio", "galeria", "showcase", "exposicion", "inmersivo", "obra", "museo", "fotografia", "arte", "evento"),
    ),
}


def infer_mode(query: str):
    """Modo por superficie a partir de la consulta; None si ninguna palabra clave aparece."""
    # Palabras normalizadas sin filtrar stopwords: "app" es stopword en el catalogo
    # pero aqui es la senal principal de "operar".
    words = set(re.findall(r"[a-z0-9]+", catalog.normalize(query)))
    best, best_hits = None, 0
    for mode, (_, _, keywords) in MODES.items():
        hits = sum(1 for k in keywords if k in words or k + "s" in words or k + "es" in words)
        if hits > best_hits:
            best, best_hits = mode, hits
    return best


def pick_style(query: str, mode: str):
    """Estilo restringido al modo; si nada del modo hace match, busca sin restriccion."""
    hits = [h for h in catalog.search(query, "style", limit=10) if mode in h.get("modo", "").split("|")]
    if hits:
        return hits[0], True
    return pick(query, "style")


def slugify(name: str) -> str:
    text = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-") or "proyecto"


def pick(query: str, domain: str):
    hits = catalog.search(query, domain, limit=1)
    if hits:
        return hits[0], True
    rows = catalog.load_rows(catalog.catalog_path(domain))
    return next(r for r in rows if r["id"] == FALLBACK[domain]), False


def build_design_system(query: str, project: str, stack: str, mode=None) -> dict:
    mode_verified = mode is not None
    mode = mode or infer_mode(query)
    mode_inferred = mode is not None
    mode = mode or "operar"
    style, style_hit = pick_style(query, mode)
    palette, palette_hit = pick(query, "palette")
    typography, typo_hit = pick(query, "typography")
    ux_rows = catalog.load_rows(catalog.catalog_path("ux"))
    a11y = [r for r in ux_rows if r["prioridad"] == "critica"]
    a11y += catalog.search(query, "ux", limit=4)
    seen, checklist = set(), []
    for row in a11y:
        if row["id"] not in seen:
            seen.add(row["id"])
            checklist.append(row)
    motion_rows = catalog.load_rows(catalog.catalog_path("motion"))
    motion = catalog.search(query, "motion", limit=2) or [r for r in motion_rows if r["id"] == "micro-feedback"]
    motion += [r for r in motion_rows if r["id"] == "reduced-motion" and r["id"] not in {m["id"] for m in motion}]
    stack_rows = catalog.load_rows(catalog.catalog_path("stack", stack))
    base = [r for r in stack_rows if r["tema"] == "tokens"]
    extra = [r for r in catalog.search(query, "stack", stack=stack, limit=4) if r["tema"] != "tokens"]
    return {
        "project": project,
        "slug": slugify(project),
        "query": query,
        "stack": stack,
        "mode": mode,
        "mode_source": "explicito" if mode_verified else ("inferido" if mode_inferred else "por defecto"),
        "style": style, "palette": palette, "typography": typography,
        "verified": {"style": style_hit, "palette": palette_hit, "typography": typo_hit},
        "spacing": SPACING[style.get("densidad", "media")],
        "checklist": checklist,
        "motion": motion,
        "stack_rules": base + extra,
    }


def render_master(ds: dict, page=None) -> str:
    s, p, t = ds["style"], ds["palette"], ds["typography"]
    scale, scale_note = ds["spacing"]
    title = f"# Sistema de diseno — {ds['project']}"
    if page:
        title = f"# Override de pantalla — {ds['project']} / {page}"
    lines = [
        title, "",
        f"Generado: {date.today().isoformat()} | Consulta: \"{ds['query']}\" | Stack: {ds['stack']}", "",
    ]
    if page:
        lines += ["Lo que no aparece aqui hereda de `MASTER.md`. Cada seccion sustituye a la de MASTER, no la complementa.", ""]
    unverified = [k for k, v in ds["verified"].items() if not v]
    if unverified:
        lines += [f"> Sin match verificado para: {', '.join(unverified)}. Se uso el valor neutral por defecto; revisar antes de aplicar.", ""]
    if ds["mode_source"] == "por defecto":
        lines += ["> Modo no inferido de la consulta: se asumio `operar`. Confirmar con el usuario o pasar --mode.", ""]
    if not page:
        lines += ["Verdad durable del producto (audiencia, contexto de uso, voz, restricciones): ver `PRODUCT.md` en esta carpeta. Este archivo decide el look; aquel decide para quien y por que.", ""]
    what, rule, _ = MODES[ds["mode"]]
    lines += [
        "## Modo", "",
        f"**{ds['mode']}** ({ds['mode_source']}) — {what}", "",
        f"Regla de desempate: {rule}", "",
        "## Estilo", "",
        f"**{s['nombre']}** (`{s['id']}`) — {s['resumen']}", "",
        f"- Usar cuando: {s['cuando_usar']}",
        f"- Evitar cuando: {s['cuando_evitar']}",
        f"- Efectos: {s['efectos']}",
        f"- Riesgos de accesibilidad: {s['riesgos_a11y']}", "",
        "## Color", "",
        f"Paleta `{p['id']}` — {p['dominio']}, mood {p['mood']}.", "",
        "| Token | Claro | Oscuro |", "|---|---|---|",
        f"| primario | {p['primario']} | {p['primario']} |",
        f"| secundario | {p['secundario']} | {p['secundario']} |",
        f"| acento | {p['acento']} | {p['acento']} |",
        f"| fondo | {p['fondo_claro']} | {p['fondo_oscuro']} |",
        f"| texto | {p['texto_claro']} | {p['texto_oscuro']} |",
        f"| exito / aviso / error | {p['exito']} / {p['aviso']} / {p['error']} | idem |", "",
        f"Contraste: {p['notas_contraste']}", "",
        "## Tipografia", "",
        f"`{t['id']}` — titulos **{t['titulos']}**, cuerpo **{t['cuerpo']}**. Base {t['base_px']}px, line-height {t['line_height']}.", "",
        f"- Cuando usar: {t['cuando_usar']}",
        f"- Notas: {t['notas']}", "",
        "## Espaciado", "",
        f"Escala (px/dp): {scale}. {scale_note}.", "",
        "## Motion", "",
    ]
    for m in ds["motion"]:
        lines.append(f"- **{m['nombre']}** (`{m['id']}`): {m['duracion_ms']} ms, easing {m['easing']}. {m['uso']} Reduced motion: {m['reduced_motion']}")
    lines += ["", "## Accesibilidad", "", "Checklist obligatorio antes de dar una pantalla por terminada:", ""]
    for r in ds["checklist"]:
        lines.append(f"- [ ] `{r['id']}` ({r['prioridad']}, WCAG {r['wcag']}): {r['criterio']}")
    lines += ["", "## Anti-patrones", ""]
    for r in ds["checklist"]:
        lines.append(f"- {r['anti_patron']}")
    lines += ["", f"## Stack: {ds['stack']}", ""]
    for r in ds["stack_rules"]:
        lines.append(f"- **{r['tema']}** — {r['regla']} Implementacion: {r['implementacion']}")
    lines.append("")
    return "\n".join(lines)


def render_product(ds: dict, audience: str, context: str, voice: str, constraints: str) -> str:
    return "\n".join([
        f"# Producto — {ds['project']}", "",
        f"Generado: {date.today().isoformat()}. Verdad durable del producto; cambia mucho menos que el look (`MASTER.md`).", "",
        "## Audiencia", "", audience, "",
        "## Contexto de uso", "", context, "",
        "## Voz", "", voice or "Por definir con el usuario.", "",
        "## Restricciones", "", constraints or "Ninguna declarada.", "",
        "## Superficies y modos", "",
        f"- {ds['query']}: `{ds['mode']}` ({ds['mode_source']})", "",
    ])


def persist_product(ds: dict, output_dir: Path, audience: str, context: str, voice: str, constraints: str):
    base = output_dir / "design-system" / ds["slug"]
    target = base / "PRODUCT.md"
    if target.exists():
        return None
    base.mkdir(parents=True, exist_ok=True)
    target.write_text(render_product(ds, audience, context, voice, constraints), encoding="utf-8", newline="\n")
    return target


def persist(ds: dict, output_dir: Path, page, force: bool) -> Path:
    base = output_dir / "design-system" / ds["slug"]
    if page:
        target = base / "pages" / f"{slugify(page)}.md"
    else:
        target = base / "MASTER.md"
    if target.exists() and not force:
        raise FileExistsError(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    if page:
        (base / "pages").mkdir(exist_ok=True)
    target.write_text(render_master(ds, page=page), encoding="utf-8", newline="\n")
    return target


def print_hits(domain: str, hits: list) -> None:
    for hit in hits:
        print(f"[{hit['id']}] (score {hit['_score']}, cobertura {hit['_coverage']})")
        for key, value in hit.items():
            if key.startswith("_") or key in ("id", "keywords"):
                continue
            print(f"  {key}: {value}")
        print()


def main(argv=None) -> int:
    for stream in (sys.stdout, sys.stderr):
        # Windows abre los pipes en cp1252; el catalogo y el markdown son UTF-8.
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("query")
    parser.add_argument("--domain", choices=[d for d in catalog.DOMAINS if d != "stack"])
    parser.add_argument("--stack", choices=list(catalog.STACKS))
    parser.add_argument("--design-system", action="store_true")
    parser.add_argument("-p", "--project", default="Proyecto")
    parser.add_argument("-n", "--limit", type=int, default=5)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--persist", action="store_true")
    parser.add_argument("--output-dir")
    parser.add_argument("--page")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--mode", choices=list(MODES))
    parser.add_argument("--audience")
    parser.add_argument("--context")
    parser.add_argument("--voice", default="")
    parser.add_argument("--constraints", default="")
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return 0 if exc.code == 0 else 2

    if args.design_system:
        if not args.stack:
            print("error: --design-system requiere --stack (compose|web)", file=sys.stderr)
            return 2
        ds = build_design_system(args.query, args.project, args.stack, args.mode)
        if args.persist:
            if not args.output_dir:
                print("error: --persist requiere --output-dir apuntando a la raiz del proyecto", file=sys.stderr)
                return 2
            if bool(args.audience) != bool(args.context):
                print("error: --audience y --context van juntos", file=sys.stderr)
                return 2
            try:
                target = persist(ds, Path(args.output_dir), args.page, args.force)
            except FileExistsError as exc:
                print(f"existe {exc}; no se sobreescribe sin --force (requiere autorizacion del usuario)", file=sys.stderr)
                return 3
            print(f"escrito {target}")
            if args.audience:
                product = persist_product(ds, Path(args.output_dir), args.audience, args.context, args.voice, args.constraints)
                print(f"escrito {product}" if product else "PRODUCT.md ya existe; no se toca (editarlo a mano si cambio la verdad del producto)")
            elif not args.page and not (Path(args.output_dir) / "design-system" / ds["slug"] / "PRODUCT.md").exists():
                print("aviso: no existe PRODUCT.md; pasar --audience y --context para crearlo", file=sys.stderr)
            return 0
        if args.json:
            print(json.dumps(ds, ensure_ascii=False, indent=2))
        else:
            print(render_master(ds, page=args.page))
        return 0

    if args.stack and args.domain:
        print("error: usar --domain o --stack, no ambos", file=sys.stderr)
        return 2
    if not (args.stack or args.domain):
        print("error: falta --domain o --stack", file=sys.stderr)
        return 2
    domain = "stack" if args.stack else args.domain
    hits = catalog.search(args.query, domain, stack=args.stack, limit=args.limit)
    suggestion = [] if hits else catalog.suggest(args.query, domain, stack=args.stack)
    if args.json:
        payload = {"domain": domain, "stack": args.stack, "query": args.query, "results": hits}
        if not hits:
            payload["sugerencia"] = suggestion
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    elif hits:
        print_hits(domain, hits)
    else:
        hint = f" Terminos cercanos: {', '.join(suggestion)}" if suggestion else ""
        print(f"Sin resultados verificados para \"{args.query}\" en {domain}.{hint}")
    return 0 if hits else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # noqa: BLE001
        print(f"error inesperado: {exc}", file=sys.stderr)
        sys.exit(4)
