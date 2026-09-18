#!/usr/bin/env python3
"""
detect.py — Detector determinista de defectos de UI (sin modelo, sin dependencias).

Reglas mecanicas sobre archivos de Jetpack Compose (.kt) y web (.tsx .jsx .vue
.svelte .astro .html .css .scss). Cada hallazgo cita la guia del catalogo que
incumple, para que el arreglo sea trazable con `search.py "<id>" --domain ux`.

Uso (python puede ser python3 o py segun la maquina):
  python detect.py <archivo|directorio>... [--json] [--ignore-rule <id>]...
  python detect.py --hook            # lee el payload JSON del hook por stdin (tool_input.file_path)
  python detect.py --list-rules

Supresion inline: un comentario con `design-detect: ignore` en la misma linea o
en la anterior suprime todos los hallazgos de esa linea; `design-detect: ignore <id>`
suprime solo esa regla.

Exit codes:
  0 = sin hallazgos (o --hook, que nunca falla el tool)
  1 = hallazgos
  2 = error de uso
"""

import argparse
import json
import math
import re
import sys
from pathlib import Path

COMPOSE_EXT = {".kt"}
WEB_MARKUP_EXT = {".tsx", ".jsx", ".vue", ".svelte", ".astro", ".html"}
WEB_STYLE_EXT = {".css", ".scss"}
WEB_EXT = WEB_MARKUP_EXT | WEB_STYLE_EXT
SKIP_DIRS = {"node_modules", "build", "dist", ".git", "generated", "out", ".next"}
THEME_DIR_RE = re.compile(r"(^|[\\/])(theme|tokens|design-system)([\\/]|$)", re.I)
TOKEN_FILE_RE = re.compile(r"(tokens?|theme|variables|palette|colors?)\.(css|scss)$", re.I)
IGNORE_RE = re.compile(r"design-detect:\s*ignore(?:\s+([a-z0-9-]+))?")

# (id, stack, severidad, guia, mensaje)
RULES = {
    "compose-color-literal": ("compose", "importante", "color-tokens-semanticos", "Color literal fuera del directorio de tema; usar MaterialTheme.colorScheme"),
    "compose-sp-literal": ("compose", "menor", "tipografia-material", "fontSize suelto en pantalla; usar un rol de MaterialTheme.typography"),
    "compose-dp-font": ("compose", "critico", "escala-fuente", "fontSize en dp ignora la escala de fuente del sistema; usar sp"),
    "compose-icon-button-no-description": ("compose", "critico", "a11y-nombre-accesible", "IconButton cuyo Icon lleva contentDescription = null: sin nombre accesible"),
    "compose-fixed-height-text": ("compose", "importante", "a11y-zoom-texto", "Altura fija en un contenedor con Text; con fontScale grande se recorta. Usar heightIn(min = ...)"),
    "compose-scroll-column-list": ("compose", "importante", "lazycolumn-keys", "Column con verticalScroll y forEach: lista sin reciclado; usar LazyColumn con key"),
    "compose-items-no-key": ("compose", "menor", "lazycolumn-keys", "items() sin key estable; rompe animaciones y estado al reordenar"),
    "compose-toast-error": ("compose", "menor", "estados-pantalla", "Toast para estado de error; usar estado en UiState con accion de reintento o Snackbar"),
    "compose-small-clickable": ("compose", "critico", "touch-area-minima", "clickable sobre un tamano menor a 48dp sin minimumInteractiveComponentSize"),
    "web-outline-none": ("web", "critico", "a11y-foco-visible", "outline none sin regla :focus-visible en el archivo: el foco de teclado desaparece"),
    "web-transition-all": ("web", "menor", "animar-transform", "transition: all anima propiedades de layout; listar transform y opacity"),
    "web-img-no-alt": ("web", "critico", "a11y-nombre-accesible", "<img> sin atributo alt"),
    "web-img-no-dimensions": ("web", "importante", "layout-espacio-reservado", "<img> sin width/height ni aspect-ratio: provoca layout shift"),
    "web-div-onclick": ("web", "critico", "boton-icono-nombre", "div/span con onClick como control: no es enfocable ni tiene rol; usar <button>"),
    "web-tabindex-positive": ("web", "importante", "orden-dom", "tabindex positivo rompe el orden natural de tabulacion"),
    "web-user-scalable": ("web", "critico", "a11y-zoom-texto", "viewport que bloquea el zoom (user-scalable=no / maximum-scale=1)"),
    "web-placeholder-only-label": ("web", "importante", "form-etiqueta-visible", "input con placeholder y sin id/aria-label/aria-labelledby: probable etiqueta ausente"),
    "web-hex-in-component": ("web", "importante", "color-tokens-semanticos", "Color hexadecimal en componente; consumir tokens (var(--color-*) o clase semantica)"),
    "web-gradient-text": ("web", "menor", "comp-texto-gradiente", "Texto con gradiente (background-clip: text); el enfasis va por peso o tamano"),
    "web-eyebrow-density": ("web", "importante", "comp-eyebrows-limitados", "Mas eyebrows (uppercase + tracking) que ceil(secciones / 3): ritmo de plantilla"),
    "web-icon-button-no-label": ("web", "critico", "boton-icono-nombre", "<button> con solo un svg y sin aria-label"),
    "web-reduced-motion-missing": ("web", "critico", "reduced-motion", "Animaciones definidas sin bloque prefers-reduced-motion en el archivo"),
    "web-bounce-easing": ("web", "menor", "motion-con-proposito", "Easing con rebote/overshoot (bounce, elastic, cubic-bezier con valor > 1)"),
    "web-zigzag-cap": ("web", "menor", "comp-zigzag-cap", "Tres o mas secciones consecutivas con alternancia imagen/texto (flex-row-reverse)"),
}

HEX_RE = re.compile(r"(?<![\w&])#[0-9a-fA-F]{6}\b")
IMG_TAG_RE = re.compile(r"<img\b[^>]*>", re.I | re.S)
BUTTON_TAG_RE = re.compile(r"<button\b([^>]*)>\s*<svg\b", re.I | re.S)
INPUT_TAG_RE = re.compile(r"<input\b[^>]*>", re.I | re.S)
SECTION_RE = re.compile(r"<section\b", re.I)
EYEBROW_TW_RE = re.compile(r"\buppercase\b[^\"'`\n]*\btracking-|\btracking-[^\"'`\n]*\buppercase\b")
EYEBROW_CSS_RE = re.compile(r"text-transform:\s*uppercase[^}]*letter-spacing|letter-spacing[^}]*text-transform:\s*uppercase", re.S)
BOUNCE_RE = re.compile(r"\b(bounce|elastic)\b|cubic-bezier\(\s*[-\d.]+\s*,\s*[-\d.]+\s*,\s*[-\d.]+\s*,\s*(1\.[0-9]+|[2-9])")
ROW_REVERSE_RE = re.compile(r"flex-row-reverse|flex-direction:\s*row-reverse")


class Finding(dict):
    pass


def _finding(path: Path, line: int, rule: str, evidence: str = "") -> Finding:
    stack, severity, guide, message = RULES[rule]
    return Finding(file=str(path), line=line, rule=rule, severity=severity, guide=guide,
                   message=message, evidence=evidence.strip()[:120])


def _line_of(text: str, pos: int) -> int:
    return text.count("\n", 0, pos) + 1


def _suppressed(lines: list, line_no: int, rule: str) -> bool:
    for idx in (line_no - 1, line_no - 2):
        if 0 <= idx < len(lines):
            m = IGNORE_RE.search(lines[idx])
            if m and (m.group(1) is None or m.group(1) == rule):
                return True
    return False


# ---------------- Compose ----------------

def check_compose(path: Path, text: str) -> list:
    out = []
    lines = text.splitlines()
    in_theme = bool(THEME_DIR_RE.search(str(path.parent)))
    for i, line in enumerate(lines, 1):
        if not in_theme and re.search(r"\bColor\(0x[0-9A-Fa-f]{6,8}\)", line):
            out.append(_finding(path, i, "compose-color-literal", line))
        if not in_theme and re.search(r"fontSize\s*=\s*\d+(\.\d+)?\.sp", line):
            out.append(_finding(path, i, "compose-sp-literal", line))
        if re.search(r"fontSize\s*=\s*\d+(\.\d+)?\.dp", line):
            out.append(_finding(path, i, "compose-dp-font", line))
        if "Toast.makeText" in line:
            out.append(_finding(path, i, "compose-toast-error", line))
        if re.search(r"\bitems\s*\(", line) and "key" not in line and "itemsIndexed" not in line:
            out.append(_finding(path, i, "compose-items-no-key", line))
        m = re.search(r"\.size\((\d+)\.dp\)", line)
        if m and ".clickable" in line and int(m.group(1)) < 48 and "minimumInteractiveComponentSize" not in line:
            out.append(_finding(path, i, "compose-small-clickable", line))
        if re.search(r"\.height\(\d+\.dp\)", line) and re.search(r"\b(Row|Column|Box)\s*\(", line):
            window = "\n".join(lines[i:i + 6])
            if re.search(r"\bText\s*\(", window):
                out.append(_finding(path, i, "compose-fixed-height-text", line))
    for m in re.finditer(r"IconButton\s*\(", text):
        chunk = text[m.end():m.end() + 400]
        icon = re.search(r"\bIcon\s*\(", chunk)
        if icon:
            body = chunk[icon.end():icon.end() + 250]
            if re.search(r"contentDescription\s*=\s*null", body):
                out.append(_finding(path, _line_of(text, m.start()), "compose-icon-button-no-description", chunk[:80]))
    if "verticalScroll(" in text and re.search(r"\.forEach\s*\{", text):
        pos = text.find("verticalScroll(")
        out.append(_finding(path, _line_of(text, pos), "compose-scroll-column-list", "verticalScroll + forEach"))
    return out


# ---------------- Web ----------------

def check_web(path: Path, text: str) -> list:
    out = []
    lines = text.splitlines()
    ext = path.suffix.lower()
    is_style = ext in WEB_STYLE_EXT
    is_token_file = bool(TOKEN_FILE_RE.search(path.name)) or bool(THEME_DIR_RE.search(str(path.parent)))
    has_focus_visible = ":focus-visible" in text or "focus-visible:" in text
    has_reduced_motion = "prefers-reduced-motion" in text

    for i, line in enumerate(lines, 1):
        if re.search(r"outline:\s*(none|0)\b|\boutline-none\b", line) and not has_focus_visible:
            out.append(_finding(path, i, "web-outline-none", line))
        if re.search(r"transition:\s*all\b|\btransition-all\b", line):
            out.append(_finding(path, i, "web-transition-all", line))
        if re.search(r"<(div|span)\b[^>]*\bonClick\b", line, re.I):
            out.append(_finding(path, i, "web-div-onclick", line))
        if re.search(r"tabindex\s*=\s*[\"']?[1-9]", line, re.I):
            out.append(_finding(path, i, "web-tabindex-positive", line))
        if re.search(r"user-scalable\s*=\s*no|maximum-scale\s*=\s*1(\.0)?\b", line, re.I):
            out.append(_finding(path, i, "web-user-scalable", line))
        if not is_token_file and HEX_RE.search(line) and not (is_style and re.search(r"--[\w-]+\s*:[^;]*#", line)):
            out.append(_finding(path, i, "web-hex-in-component", line))
        if re.search(r"background-clip:\s*text|\bbg-clip-text\b", line):
            out.append(_finding(path, i, "web-gradient-text", line))
        if BOUNCE_RE.search(line):
            out.append(_finding(path, i, "web-bounce-easing", line))

    for m in IMG_TAG_RE.finditer(text):
        tag = m.group(0)
        line = _line_of(text, m.start())
        if not re.search(r"\balt\s*=", tag):
            out.append(_finding(path, line, "web-img-no-alt", tag))
        if not re.search(r"\b(width|height|aspect-ratio|aspect-\[|aspect-video|aspect-square|fill)\b", tag):
            out.append(_finding(path, line, "web-img-no-dimensions", tag))
    for m in BUTTON_TAG_RE.finditer(text):
        if not re.search(r"aria-label(ledby)?\s*=", m.group(1)):
            out.append(_finding(path, _line_of(text, m.start()), "web-icon-button-no-label", m.group(0)))
    for m in INPUT_TAG_RE.finditer(text):
        tag = m.group(0)
        if re.search(r"\bplaceholder\s*=", tag) and not re.search(r"\b(id|aria-label|aria-labelledby)\s*=", tag) \
                and not re.search(r"type\s*=\s*[\"'](hidden|submit|button)", tag):
            out.append(_finding(path, _line_of(text, m.start()), "web-placeholder-only-label", tag))

    if is_style and re.search(r"@keyframes|\banimation:", text) and not has_reduced_motion:
        pos = re.search(r"@keyframes|\banimation:", text).start()
        out.append(_finding(path, _line_of(text, pos), "web-reduced-motion-missing", "@keyframes / animation sin prefers-reduced-motion"))

    if not is_style:
        sections = len(SECTION_RE.findall(text))
        eyebrows = len(EYEBROW_TW_RE.findall(text)) + len(EYEBROW_CSS_RE.findall(text))
        if sections and eyebrows > math.ceil(sections / 3):
            out.append(_finding(path, 1, "web-eyebrow-density", f"{eyebrows} eyebrows en {sections} secciones"))
        reverse_lines = [i for i, l in enumerate(lines, 1) if ROW_REVERSE_RE.search(l)]
        if len(reverse_lines) >= 2 and sections >= 3:
            # Alternancia: dos o mas secciones invertidas implican al menos tres splits consecutivos
            # cuando hay tantas secciones invertidas como la mitad de las secciones del archivo.
            if len(reverse_lines) >= math.ceil(sections / 2):
                out.append(_finding(path, reverse_lines[0], "web-zigzag-cap", f"{len(reverse_lines)} secciones invertidas en {sections}"))
    return out


def check_file(path: Path) -> list:
    ext = path.suffix.lower()
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    if ext in COMPOSE_EXT:
        if "@Composable" not in text:
            return []
        findings = check_compose(path, text)
    elif ext in WEB_EXT:
        findings = check_web(path, text)
    else:
        return []
    lines = text.splitlines()
    kept = [f for f in findings if not _suppressed(lines, f["line"], f["rule"])]
    kept.sort(key=lambda f: (f["line"], f["rule"]))
    return kept


def iter_files(targets: list):
    for target in targets:
        p = Path(target)
        if p.is_file():
            yield p
        elif p.is_dir():
            for f in p.rglob("*"):
                if f.is_file() and not any(part in SKIP_DIRS for part in f.parts):
                    yield f


def scan(targets: list, ignore_rules=()) -> list:
    findings = []
    for f in iter_files(targets):
        findings.extend(x for x in check_file(f) if x["rule"] not in ignore_rules)
    return findings


def format_text(findings: list) -> str:
    order = {"critico": 0, "importante": 1, "menor": 2}
    lines = []
    for f in sorted(findings, key=lambda f: (order[f["severity"]], f["file"], f["line"])):
        lines.append(f"[{f['severity']}] {f['file']}:{f['line']} {f['rule']} -> guia `{f['guide']}`")
        lines.append(f"    {f['message']}")
        if f["evidence"]:
            lines.append(f"    evidencia: {f['evidence']}")
    return "\n".join(lines)


def run_hook() -> int:
    """Modo hook: lee el payload por stdin y devuelve additionalContext si hay hallazgos."""
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, OSError):
        return 0
    tool_input = payload.get("tool_input") if isinstance(payload, dict) else None
    if not isinstance(tool_input, dict):
        return 0
    file_path = tool_input.get("file_path") or tool_input.get("path") or ""
    if not file_path or Path(file_path).suffix.lower() not in COMPOSE_EXT | WEB_EXT:
        return 0
    findings = check_file(Path(file_path))
    if not findings:
        return 0
    summary = format_text(findings)
    message = (
        f"design-detect: {len(findings)} hallazgo(s) de UI en {file_path}. Corregir antes de continuar; "
        f"cada regla cita la guia del catalogo (search.py \"<guia>\" --domain ux).\n{summary}"
    )
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": message}}, ensure_ascii=False))
    return 0


def main(argv=None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("targets", nargs="*")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--hook", action="store_true")
    parser.add_argument("--list-rules", action="store_true")
    parser.add_argument("--ignore-rule", action="append", default=[])
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return 0 if exc.code == 0 else 2
    if args.hook:
        return run_hook()
    if args.list_rules:
        for rule, (stack, severity, guide, message) in sorted(RULES.items()):
            print(f"{rule:40} {stack:8} {severity:10} guia={guide}")
        return 0
    if not args.targets:
        print("error: indicar archivos o directorios, --hook o --list-rules", file=sys.stderr)
        return 2
    unknown = [r for r in args.ignore_rule if r not in RULES]
    if unknown:
        print(f"error: regla desconocida: {', '.join(unknown)}", file=sys.stderr)
        return 2
    findings = scan(args.targets, set(args.ignore_rule))
    if args.json:
        print(json.dumps({"findings": findings, "count": len(findings)}, ensure_ascii=False, indent=2))
    elif findings:
        print(format_text(findings))
    else:
        print("sin hallazgos")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
