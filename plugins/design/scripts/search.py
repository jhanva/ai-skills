#!/usr/bin/env python3
"""
search.py — Consulta el catalogo UI/UX del plugin design.

Uso (python puede ser python3 o py segun la maquina):
  python search.py "<consulta>" --domain <style|palette|typography|ux|motion> [-n N] [--json]
  python search.py "<consulta>" --stack <compose|web> [-n N] [--json]
  python search.py "<consulta>" --design-system -p "Nombre" --stack <compose|web> [--json]
  python search.py "<consulta>" --design-system -p "Nombre" --stack <stack> --persist --output-dir <raiz> [--page <nombre>] [--force]

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


def slugify(name: str) -> str:
    text = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-") or "proyecto"


def pick(query: str, domain: str):
    hits = catalog.search(query, domain, limit=1)
    if hits:
        return hits[0], True
    rows = catalog.load_rows(catalog.catalog_path(domain))
    return next(r for r in rows if r["id"] == FALLBACK[domain]), False


def build_design_system(query: str, project: str, stack: str) -> dict:
    style, style_hit = pick(query, "style")
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
    lines += [
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
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return 0 if exc.code == 0 else 2

    if args.design_system:
        if not args.stack:
            print("error: --design-system requiere --stack (compose|web)", file=sys.stderr)
            return 2
        ds = build_design_system(args.query, args.project, args.stack)
        if args.persist:
            if not args.output_dir:
                print("error: --persist requiere --output-dir apuntando a la raiz del proyecto", file=sys.stderr)
                return 2
            try:
                target = persist(ds, Path(args.output_dir), args.page, args.force)
            except FileExistsError as exc:
                print(f"existe {exc}; no se sobreescribe sin --force (requiere autorizacion del usuario)", file=sys.stderr)
                return 3
            print(f"escrito {target}")
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
