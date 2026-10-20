# Plan: Clone pack

Spec: [docs/specs/clone-pack.md](../specs/clone-pack.md)
Fecha: 2026-10-20

Cada tarea de codigo sigue RED-GREEN: el test se escribe primero, se ve
fallar, se implementa, se ve pasar, commit. Los outputs esperados de este
plan salieron de ejecutar cada tarea en orden en un repo temporal: no son
estimados. Las duraciones de `Ran N tests in X.XXXs` se omiten porque varian.

Todos los comandos se corren desde la raiz del repo (`D:\Johan\repositorios\ai-skills`)
en Git Bash, salvo los bloques `powershell` de las tareas 9 y 23.

Requisitos: Python 3.10+ (`python --version`), Windows PowerShell 5.1.
Para la captura Android en un dispositivo real hace falta adb (no esta en el
PATH de esta maquina); los tests de la tarea 8 usan un adb simulado y no lo
necesitan.

## Mapa de archivos

Crear (pack nuevo en `.claude/skills/`):

- `clone-recon/scripts/uitree.py` — arbol normalizado: roles, poda, colapso, redaccion, summarize, CLI
- `clone-recon/scripts/capture_android.py` — captura via adb
- `clone-recon/scripts/capture_windows.ps1` — captura via UI Automation
- `clone-recon/tests/test_uitree.py`
- `clone-recon/tests/test_capture_android.py`
- `clone-recon/tests/fixtures/android_basic.xml`
- `clone-recon/tests/fixtures/uia_basic.json`
- `clone-recon/SKILL.md`
- `clone-recon/references/recon-template.md`
- `clone-recon/references/android-capture.md`
- `clone-recon/references/windows-capture.md`
- `clone-arch/SKILL.md`
- `clone-arch/references/stack-matrix.md`
- `clone-build/SKILL.md`
- `clone-diff/scripts/treediff.py` — diff de arboles
- `clone-diff/scripts/parity.py` — reporte de paridad
- `clone-diff/tests/test_treediff.py`
- `clone-diff/tests/test_parity.py`
- `clone-diff/SKILL.md`

Modificar:

- `CLAUDE.md` — estructura, tabla de skills, flujo "Clonar apps"
- `README.md` — seccion de skills "Clonar apps" y flujo

Sin dependencias nuevas: solo stdlib de Python y Windows PowerShell 5.1.

## Interfaces compartidas (referencia rapida)

- Arbol normalizado (`*.tree.json`): `schema`, `platform`, `screen`, `source`,
  `captured_at`, `window {w,h}`, `tree_quality (full|partial|none)`,
  `redacted`, `root`. Nodo: `role`, `name`, `text`, `id`, `bounds [x,y,w,h]`
  relativos 0-1, `enabled`, `children`.
- `uitree`: `normalize_android(xml_text, screen, source="", max_depth=25, redact=True, captured_at=None)`,
  `normalize_uia(raw, screen, max_depth=25, redact=True, captured_at=None)`,
  `empty_tree(platform, screen, source, width, height, captured_at=None)`,
  `summarize(tree, max_lines=40)`, `redact_text(text)`, `safe_stdout()`, `TreeError`.
- `capture_android`: `main(argv=None, run=default_run, sleep=time.sleep)`;
  `run(cmd) -> (code, stdout_bytes, stderr_bytes)`.
- `treediff`: `compare(orig_tree, clone_tree, use_text=True) -> dict` con
  `screen, status, interactive_score, structure_score, counts, missing, extra, text_changed, moved`.
- `parity`: `build_report(clone_dir) -> dict` con `verdict, feature_score,
  must_done, must_total, areas, screens, screens_features_only, flows, pending`.

---

## Fase 0: preparacion

### Tarea 0: rama de trabajo y docs

**Archivos:** `docs/specs/clone-pack.md`, `docs/plans/clone-pack-plan.md` (ya existen)

**Paso 1 — Crear la rama:**

```bash
git checkout -b feat/clone-pack
```

Output esperado:

```
Switched to a new branch 'feat/clone-pack'
```

**Paso 2 — Commit de spec y plan:**

```bash
git add docs/specs/clone-pack.md docs/plans/clone-pack-plan.md
git commit -m "docs(clone-pack): spec and implementation plan" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

## Fase 1: uitree.py (arbol normalizado)

### Tarea 1: uitree: constantes, roles y redaccion de texto

**Archivos:** crear `.claude/skills/clone-recon/tests/test_uitree.py`; crear `.claude/skills/clone-recon/scripts/uitree.py`

**Paso 1 — Test que falla** (Crear `test_uitree.py`):

```python
import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "scripts"))

import uitree  # noqa: E402

FIXTURES = os.path.join(HERE, "fixtures")
FIXED_TIME = "2026-10-20T00:00:00Z"


def read_fixture(name):
    with open(os.path.join(FIXTURES, name), encoding="utf-8") as fh:
        return fh.read()


def preorder(node, out=None):
    out = [] if out is None else out
    out.append((node["role"], node["id"] or node["name"] or node["text"]))
    for child in node["children"]:
        preorder(child, out)
    return out


def find(node, role, key):
    stack = [node]
    while stack:
        n = stack.pop()
        if n["role"] == role and key in (n["id"], n["name"], n["text"]):
            return n
        stack.extend(n["children"])
    return None


def uia_raw(children, truncated=False):
    return {"window": {"title": "T", "process": "app", "rect": [0, 0, 1000, 500]},
            "truncated": truncated,
            "root": {"type": "Window", "name": "T", "rect": [0, 0, 1000, 500],
                     "children": children}}


def uia_node(ctype, name="", rect=(0, 0, 100, 50), children=None, **extra):
    node = {"type": ctype, "name": name, "automationId": "", "className": "",
            "rect": list(rect), "enabled": True, "offscreen": False, "value": None,
            "toggle": None, "children": children or []}
    node.update(extra)
    return node


class RedactTextTest(unittest.TestCase):
    def test_email_is_redacted(self):
        self.assertEqual(uitree.redact_text("escribe a ana.p@mail.co hoy"), "escribe a <email> hoy")

    def test_phone_with_separators_is_redacted(self):
        self.assertEqual(uitree.redact_text("Llamar +57 300 123 4567"), "Llamar <phone>")

    def test_six_digit_number_is_redacted(self):
        self.assertEqual(uitree.redact_text("Codigo 123456"), "Codigo <num>")

    def test_dates_and_short_numbers_are_kept(self):
        self.assertEqual(uitree.redact_text("2026-10-01, 3 notas"), "2026-10-01, 3 notas")


```

**Paso 2 — Verificar que falla:**

```bash
python -m unittest discover -s .claude/skills/clone-recon/tests -p test_uitree.py
```

Output esperado (lineas clave):

```
ImportError: Failed to import test module: test_uitree
ModuleNotFoundError: No module named 'uitree'
Ran 1 test
FAILED (errors=1)
```

**Paso 3 — Implementar** (Crear `uitree.py`):

```python
#!/usr/bin/env python3
"""
uitree.py — Arbol de UI normalizado para el clone pack. Zero dependencias.

Convierte el dump crudo de una pantalla (uiautomator de Android o UI
Automation de Windows) en un arbol neutral a la plataforma: roles fijos,
bounds relativos a la ventana, datos personales redactados.

Uso:
  python uitree.py normalize --from android|uia RAW --out TREE --screen SID
                   [--source TEXTO] [--max-depth 25] [--no-redact]
  python uitree.py summarize TREE [--max-lines 40]
"""

import argparse
import datetime
import json
import re
import sys
import xml.etree.ElementTree as ET

SCHEMA = 1

ROLES = (
    "window", "group", "toolbar", "button", "link", "input", "select",
    "checkbox", "radio", "switch", "slider", "list", "listitem", "tabs", "tab",
    "menu", "menuitem", "text", "image", "unknown",
)
INTERACTIVE = frozenset({
    "button", "link", "input", "select", "checkbox", "radio", "switch",
    "slider", "tab", "menuitem", "listitem",
})
CONTENT = frozenset({"list", "tabs", "menu", "toolbar", "text", "image", "unknown"})
CONTAINERS = frozenset({"window", "group"})

ANDROID_CLASS_ROLES = {
    "Button": "button", "ImageButton": "button", "MaterialButton": "button",
    "FloatingActionButton": "button",
    "EditText": "input", "AutoCompleteTextView": "input", "TextInputEditText": "input",
    "CheckBox": "checkbox", "CheckedTextView": "checkbox",
    "Switch": "switch", "SwitchCompat": "switch", "SwitchMaterial": "switch",
    "RadioButton": "radio",
    "SeekBar": "slider", "Slider": "slider",
    "Spinner": "select",
    "RecyclerView": "list", "ListView": "list", "GridView": "list",
    "TabLayout": "tabs", "TabLayout$TabView": "tab", "TabView": "tab",
    "TextView": "text",
    "ImageView": "image",
    "WebView": "group",
}

UIA_TYPE_ROLES = {
    "Button": "button", "SplitButton": "button",
    "Hyperlink": "link",
    "Edit": "input", "Document": "input",
    "ComboBox": "select",
    "CheckBox": "checkbox",
    "RadioButton": "radio",
    "Slider": "slider", "Spinner": "slider",
    "List": "list", "DataGrid": "list", "Tree": "list", "Table": "list",
    "ListItem": "listitem", "DataItem": "listitem", "TreeItem": "listitem",
    "Tab": "tabs",
    "TabItem": "tab",
    "Menu": "menu", "MenuBar": "menu",
    "MenuItem": "menuitem",
    "ToolBar": "toolbar",
    "Text": "text",
    "Image": "image",
    "Window": "window",
}
UIA_DROP_TYPES = frozenset({"ScrollBar", "Thumb", "TitleBar"})

_BOUNDS = re.compile(r"\[(-?\d+),(-?\d+)\]\[(-?\d+),(-?\d+)\]")
_EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
_PHONE_CANDIDATE = re.compile(r"\+?\(?\d[\d \-()]*\d")
_DATE = re.compile(r"\d{1,4}[-/.]\d{1,2}[-/.]\d{1,4}")
_LONG_NUMBER = re.compile(r"\d{6,}")


class TreeError(Exception):
    """Entrada cruda invalida."""


def _now():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------- redaccion

def _phone_sub(match):
    chunk = match.group(0)
    digits = sum(ch.isdigit() for ch in chunk)
    if digits >= 7 and not _DATE.fullmatch(chunk):
        return "<phone>"
    return chunk


def redact_text(text):
    """Reemplaza emails, telefonos y numeros largos por marcadores."""
    if not text:
        return text
    text = _EMAIL.sub("<email>", text)
    text = _PHONE_CANDIDATE.sub(_phone_sub, text)
    return _LONG_NUMBER.sub("<num>", text)


```

**Paso 4 — Verificar que pasa:**

```bash
python -m unittest discover -s .claude/skills/clone-recon/tests -p test_uitree.py
```

Output esperado:

```
Ran 4 tests
OK
```

**Paso 5 — Commit:**

```bash
git add .claude/skills/clone-recon/tests/test_uitree.py .claude/skills/clone-recon/scripts/uitree.py
git commit -m "feat(clone-recon): uitree constants and text redaction" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```


### Tarea 2: uitree: pipeline comun y normalizacion Android

**Archivos:** crear `.claude/skills/clone-recon/tests/fixtures/android_basic.xml`; agregar al final de `.claude/skills/clone-recon/tests/test_uitree.py`; agregar al final de `.claude/skills/clone-recon/scripts/uitree.py`

**Paso 1 — Fixture `android_basic.xml`:**

```xml
<?xml version='1.0' encoding='UTF-8' standalone='yes' ?>
<hierarchy rotation="0">
  <node index="0" text="" resource-id="" class="android.widget.FrameLayout" content-desc="" checkable="false" clickable="false" scrollable="false" enabled="true" bounds="[0,0][1080,2400]">
    <node index="0" text="" resource-id="com.example.notes:id/content" class="android.widget.LinearLayout" content-desc="" checkable="false" clickable="false" scrollable="false" enabled="true" bounds="[0,0][1080,2400]">
      <node index="0" text="Notas" resource-id="com.example.notes:id/title" class="android.widget.TextView" content-desc="" checkable="false" clickable="false" scrollable="false" enabled="true" bounds="[40,100][540,180]" />
      <node index="1" text="" resource-id="com.example.notes:id/search" class="android.widget.EditText" content-desc="Buscar" checkable="false" clickable="true" scrollable="false" enabled="true" bounds="[40,200][1040,320]" />
      <node index="2" text="Solo favoritas" resource-id="com.example.notes:id/fav" class="android.widget.CheckBox" content-desc="" checkable="true" clickable="true" scrollable="false" enabled="true" bounds="[40,340][600,440]" />
      <node index="3" text="" resource-id="com.example.notes:id/list" class="androidx.recyclerview.widget.RecyclerView" content-desc="" checkable="false" clickable="false" scrollable="true" enabled="true" bounds="[0,460][1080,2000]">
        <node index="0" text="" resource-id="com.example.notes:id/row" class="android.widget.LinearLayout" content-desc="" checkable="false" clickable="true" scrollable="false" enabled="true" bounds="[0,460][1080,660]">
          <node index="0" text="Compras" resource-id="com.example.notes:id/row_title" class="android.widget.TextView" content-desc="" checkable="false" clickable="false" scrollable="false" enabled="true" bounds="[40,480][800,560]" />
          <node index="1" text="2026-10-01" resource-id="com.example.notes:id/row_date" class="android.widget.TextView" content-desc="" checkable="false" clickable="false" scrollable="false" enabled="true" bounds="[40,570][800,640]" />
        </node>
        <node index="1" text="" resource-id="com.example.notes:id/row" class="android.widget.LinearLayout" content-desc="" checkable="false" clickable="true" scrollable="false" enabled="true" bounds="[0,660][1080,860]">
          <node index="0" text="Ideas" resource-id="com.example.notes:id/row_title" class="android.widget.TextView" content-desc="" checkable="false" clickable="false" scrollable="false" enabled="true" bounds="[40,680][800,760]" />
          <node index="1" text="2026-10-02" resource-id="com.example.notes:id/row_date" class="android.widget.TextView" content-desc="" checkable="false" clickable="false" scrollable="false" enabled="true" bounds="[40,770][800,840]" />
        </node>
        <node index="2" text="" resource-id="com.example.notes:id/row" class="android.widget.LinearLayout" content-desc="" checkable="false" clickable="true" scrollable="false" enabled="true" bounds="[0,860][1080,1060]">
          <node index="0" text="Viaje" resource-id="com.example.notes:id/row_title" class="android.widget.TextView" content-desc="" checkable="false" clickable="false" scrollable="false" enabled="true" bounds="[40,880][800,960]" />
          <node index="1" text="2026-10-03" resource-id="com.example.notes:id/row_date" class="android.widget.TextView" content-desc="" checkable="false" clickable="false" scrollable="false" enabled="true" bounds="[40,970][800,1040]" />
        </node>
      </node>
      <node index="4" text="" resource-id="" class="android.view.View" content-desc="Nueva nota" checkable="false" clickable="true" scrollable="false" enabled="true" bounds="[880,2100][1040,2260]" />
      <node index="5" text="Guardar" resource-id="com.example.notes:id/save" class="android.widget.Button" content-desc="" checkable="false" clickable="true" scrollable="false" enabled="false" bounds="[40,2280][520,2380]" />
    </node>
  </node>
</hierarchy>
```

**Paso 2 — Test que falla** (Agregar al final de `test_uitree.py`):

```python
class AndroidNormalizeTest(unittest.TestCase):
    def setUp(self):
        self.tree = uitree.normalize_android(read_fixture("android_basic.xml"), "S01",
                                             captured_at=FIXED_TIME)

    def test_roles_follow_class_table_and_fallbacks(self):
        self.assertEqual(preorder(self.tree["root"]), [
            ("window", ""),
            ("group", "content"),
            ("text", "title"),
            ("input", "search"),
            ("checkbox", "fav"),
            ("list", "list"),
            ("listitem", "row"), ("text", "row_title"), ("text", "row_date"),
            ("listitem", "row"), ("text", "row_title"), ("text", "row_date"),
            ("listitem", "row"), ("text", "row_title"), ("text", "row_date"),
            ("button", "Nueva nota"),
            ("button", "save"),
        ])

    def test_bounds_are_relative_to_window(self):
        search = find(self.tree["root"], "input", "search")
        self.assertEqual(search["bounds"], [0.037, 0.083, 0.926, 0.05])

    def test_window_size_comes_from_top_nodes(self):
        self.assertEqual(self.tree["window"], {"w": 1080, "h": 2400})

    def test_enabled_flag_is_kept(self):
        self.assertFalse(find(self.tree["root"], "button", "save")["enabled"])

    def test_header_fields(self):
        self.assertEqual(self.tree["schema"], 1)
        self.assertEqual(self.tree["platform"], "android")
        self.assertEqual(self.tree["screen"], "S01")
        self.assertEqual(self.tree["captured_at"], FIXED_TIME)
        self.assertEqual(self.tree["tree_quality"], "full")
        self.assertTrue(self.tree["redacted"])

    def test_invalid_xml_raises_tree_error(self):
        with self.assertRaises(uitree.TreeError):
            uitree.normalize_android("<hierarchy><node", "S01")


class EmptyTreeTest(unittest.TestCase):
    def test_empty_tree_has_quality_none(self):
        tree = uitree.empty_tree("android", "S09", "com.x/.Main", 1080, 2400, FIXED_TIME)
        self.assertEqual(tree["tree_quality"], "none")
        self.assertEqual(tree["root"]["children"], [])
        self.assertEqual(tree["window"], {"w": 1080, "h": 2400})


```

**Paso 3 — Verificar que falla:**

```bash
python -m unittest discover -s .claude/skills/clone-recon/tests -p test_uitree.py
```

Output esperado (lineas clave):

```
AttributeError: module 'uitree' has no attribute 'normalize_android'
AttributeError: module 'uitree' has no attribute 'empty_tree'
Ran 11 tests
FAILED (errors=7)
```

**Paso 4 — Implementar** (Agregar al final de `uitree.py`):

```python
def _redact_node(node):
    node["name"] = redact_text(node["name"])
    if node["role"] == "input" and node["text"]:
        node["text"] = "<value>"
    else:
        node["text"] = redact_text(node["text"])
    for child in node["children"]:
        _redact_node(child)


# ----------------------------------------------------- pipeline comun (raw)
# Nodo intermedio: role, name, text, id, rect [x, y, w, h] absoluto,
# enabled, offscreen, drop, children.

def _raw(role, name="", text="", id_="", rect=(0, 0, 0, 0), enabled=True,
         offscreen=False, drop=False, children=None):
    return {"role": role, "name": name or "", "text": text or "", "id": id_ or "",
            "rect": list(rect), "enabled": bool(enabled), "offscreen": bool(offscreen),
            "drop": bool(drop), "children": children or []}


def _visible(node, win):
    x, y, w, h = node["rect"]
    wx, wy, ww, wh = win
    if w <= 0 or h <= 0:
        return False
    return x < wx + ww and y < wy + wh and x + w > wx and y + h > wy


def _prune(node, win):
    kept = []
    for child in node["children"]:
        if child["drop"] or child["offscreen"] or not _visible(child, win):
            continue
        kept.append(_prune(child, win))
    node["children"] = kept
    return node


def _collapse(node):
    node["children"] = [_collapse(c) for c in node["children"]]
    collapsed = []
    for child in node["children"]:
        while (child["role"] == "group" and not child["name"] and not child["text"]
               and not child["id"] and len(child["children"]) == 1):
            child = child["children"][0]
        collapsed.append(child)
    node["children"] = collapsed
    return node


def _limit_depth(node, max_depth, depth=0):
    """Devuelve True si se corto algun nodo."""
    if depth >= max_depth:
        cut = bool(node["children"])
        node["children"] = []
        return cut
    cut = False
    for child in node["children"]:
        cut = _limit_depth(child, max_depth, depth + 1) or cut
    return cut


def _relative(node, win):
    x, y, w, h = node["rect"]
    wx, wy, ww, wh = win
    out = {
        "role": node["role"],
        "name": node["name"],
        "text": node["text"],
        "id": node["id"],
        "bounds": [round((x - wx) / ww, 3), round((y - wy) / wh, 3),
                   round(w / ww, 3), round(h / wh, 3)],
        "enabled": node["enabled"],
        "children": [_relative(c, win) for c in node["children"]],
    }
    return out


def _has_interactive(node):
    if node["role"] in INTERACTIVE:
        return True
    return any(_has_interactive(c) for c in node["children"])


def _finish(platform, screen, source, root, win, max_depth, redact, captured_at,
            truncated=False):
    root = _prune(root, win)
    root = _collapse(root)
    truncated = _limit_depth(root, max_depth) or truncated
    rel = _relative(root, win)
    if redact:
        _redact_node(rel)
    if truncated or not _has_interactive(rel):
        quality = "partial"
    else:
        quality = "full"
    return {
        "schema": SCHEMA,
        "platform": platform,
        "screen": screen,
        "source": source,
        "captured_at": captured_at or _now(),
        "window": {"w": win[2], "h": win[3]},
        "tree_quality": quality,
        "redacted": bool(redact),
        "root": rel,
    }


def empty_tree(platform, screen, source, width, height, captured_at=None):
    """Arbol sin nodos para pantallas donde no se pudo obtener el dump."""
    return {
        "schema": SCHEMA,
        "platform": platform,
        "screen": screen,
        "source": source,
        "captured_at": captured_at or _now(),
        "window": {"w": width, "h": height},
        "tree_quality": "none",
        "redacted": True,
        "root": {"role": "window", "name": "", "text": "", "id": "",
                 "bounds": [0.0, 0.0, 1.0, 1.0], "enabled": True, "children": []},
    }


# ------------------------------------------------------------------ android

def android_role(attrs, has_children, parent_role):
    cls = attrs.get("class", "")
    short = cls.rsplit(".", 1)[-1]
    role = ANDROID_CLASS_ROLES.get(short) or ANDROID_CLASS_ROLES.get(short.split("$")[-1])
    if role is None:
        if attrs.get("checkable") == "true":
            role = "checkbox"
        elif attrs.get("clickable") == "true":
            role = "button"
        elif attrs.get("scrollable") == "true":
            role = "list"
        elif has_children:
            role = "group"
        elif attrs.get("text"):
            role = "text"
        else:
            role = "unknown"
    if parent_role == "list" and attrs.get("clickable") == "true":
        role = "listitem"
    return role


def _android_rect(bounds):
    m = _BOUNDS.fullmatch(bounds or "")
    if not m:
        return [0, 0, 0, 0]
    x1, y1, x2, y2 = (int(v) for v in m.groups())
    return [x1, y1, x2 - x1, y2 - y1]


def _android_node(el, parent_role):
    attrs = el.attrib
    kids = [k for k in el if k.tag == "node"]
    role = android_role(attrs, bool(kids), parent_role)
    rid = attrs.get("resource-id", "")
    if ":id/" in rid:
        rid = rid.split(":id/", 1)[1]
    node = _raw(role, attrs.get("content-desc", ""), attrs.get("text", ""), rid,
                _android_rect(attrs.get("bounds")), attrs.get("enabled", "true") == "true")
    node["children"] = [_android_node(k, role) for k in kids]
    return node


def normalize_android(xml_text, screen, source="", max_depth=25, redact=True,
                      captured_at=None):
    try:
        hierarchy = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        raise TreeError("XML de uiautomator invalido: %s" % exc)
    tops = [_android_node(el, "window") for el in hierarchy if el.tag == "node"]
    if not tops:
        raise TreeError("el dump de uiautomator no tiene nodos")
    width = max(n["rect"][0] + n["rect"][2] for n in tops)
    height = max(n["rect"][1] + n["rect"][3] for n in tops)
    win = [0, 0, width, height]
    root = _raw("window", rect=win, children=tops)
    return _finish("android", screen, source, root, win, max_depth, redact, captured_at)


# --------------------------------------------------------------------- uia

```

**Paso 5 — Verificar que pasa:**

```bash
python -m unittest discover -s .claude/skills/clone-recon/tests -p test_uitree.py
```

Output esperado:

```
Ran 11 tests
OK
```

**Paso 6 — Commit:**

```bash
git add .claude/skills/clone-recon/tests/fixtures/android_basic.xml .claude/skills/clone-recon/tests/test_uitree.py .claude/skills/clone-recon/scripts/uitree.py
git commit -m "feat(clone-recon): normalize uiautomator dumps" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```


### Tarea 3: uitree: normalizacion UI Automation

**Archivos:** crear `.claude/skills/clone-recon/tests/fixtures/uia_basic.json`; agregar al final de `.claude/skills/clone-recon/tests/test_uitree.py`; agregar al final de `.claude/skills/clone-recon/scripts/uitree.py`

**Paso 1 — Fixture `uia_basic.json`:**

```json
{
  "window": {"title": "Notas - Editor", "process": "notepad", "rect": [100, 50, 800, 600]},
  "truncated": false,
  "root": {
    "type": "Window", "name": "Notas - Editor", "automationId": "", "className": "Notepad",
    "rect": [100, 50, 800, 600], "enabled": true, "offscreen": false, "value": null, "toggle": null,
    "children": [
      {"type": "TitleBar", "name": "Notas - Editor", "automationId": "TitleBar", "className": "", "rect": [100, 50, 800, 30],
       "enabled": true, "offscreen": false, "value": null, "toggle": null, "children": [
        {"type": "Button", "name": "Cerrar", "automationId": "Close", "className": "", "rect": [850, 50, 50, 30],
         "enabled": true, "offscreen": false, "value": null, "toggle": null, "children": []}
      ]},
      {"type": "Pane", "name": "", "automationId": "", "className": "", "rect": [100, 80, 800, 30],
       "enabled": true, "offscreen": false, "value": null, "toggle": null, "children": [
        {"type": "MenuBar", "name": "Aplicacion", "automationId": "MenuBar", "className": "", "rect": [100, 80, 800, 30],
         "enabled": true, "offscreen": false, "value": null, "toggle": null, "children": [
          {"type": "MenuItem", "name": "Archivo", "automationId": "", "className": "", "rect": [100, 80, 60, 30],
           "enabled": true, "offscreen": false, "value": null, "toggle": null, "children": []},
          {"type": "MenuItem", "name": "Editar", "automationId": "", "className": "", "rect": [160, 80, 60, 30],
           "enabled": true, "offscreen": false, "value": null, "toggle": null, "children": []}
        ]}
      ]},
      {"type": "Edit", "name": "Editor de texto", "automationId": "15", "className": "Edit", "rect": [100, 110, 780, 400],
       "enabled": true, "offscreen": false, "value": "hola juan@correo.com", "toggle": null, "children": []},
      {"type": "ScrollBar", "name": "Vertical", "automationId": "", "className": "", "rect": [880, 110, 20, 400],
       "enabled": true, "offscreen": false, "value": null, "toggle": null, "children": []},
      {"type": "List", "name": "Recientes", "automationId": "recent", "className": "", "rect": [100, 510, 800, 100],
       "enabled": true, "offscreen": false, "value": null, "toggle": null, "children": [
        {"type": "ListItem", "name": "a.txt", "automationId": "", "className": "", "rect": [100, 510, 800, 50],
         "enabled": true, "offscreen": false, "value": null, "toggle": null, "children": []},
        {"type": "ListItem", "name": "b.txt", "automationId": "", "className": "", "rect": [100, 560, 800, 50],
         "enabled": true, "offscreen": false, "value": null, "toggle": null, "children": []}
      ]},
      {"type": "Button", "name": "Guardar", "automationId": "save", "className": "Button", "rect": [700, 620, 90, 25],
       "enabled": true, "offscreen": false, "value": null, "toggle": null, "children": []},
      {"type": "Button", "name": "Oculto", "automationId": "", "className": "Button", "rect": [0, 0, 10, 10],
       "enabled": true, "offscreen": true, "value": null, "toggle": null, "children": []},
      {"type": "Button", "name": "Ajuste automatico", "automationId": "wrap", "className": "ToggleSwitch", "rect": [100, 620, 150, 25],
       "enabled": true, "offscreen": false, "value": null, "toggle": "On", "children": []},
      {"type": "Text", "name": "Listo", "automationId": "", "className": "", "rect": [100, 640, 100, 10],
       "enabled": true, "offscreen": false, "value": null, "toggle": null, "children": []}
    ]
  }
}
```

**Paso 2 — Test que falla** (Agregar al final de `test_uitree.py`):

```python
class UiaNormalizeTest(unittest.TestCase):
    def setUp(self):
        raw = json.loads(read_fixture("uia_basic.json"))
        self.tree = uitree.normalize_uia(raw, "S02", captured_at=FIXED_TIME)

    def test_roles_follow_control_type_table(self):
        self.assertEqual(preorder(self.tree["root"]), [
            ("window", "Notas - Editor"),
            ("menu", "MenuBar"), ("menuitem", "Archivo"), ("menuitem", "Editar"),
            ("input", "15"),
            ("list", "recent"), ("listitem", "a.txt"), ("listitem", "b.txt"),
            ("button", "save"),
            ("switch", "wrap"),
            ("text", "Listo"),
        ])

    def test_scrollbar_titlebar_and_offscreen_nodes_are_dropped(self):
        self.assertIsNone(find(self.tree["root"], "slider", "Vertical"))
        self.assertIsNone(find(self.tree["root"], "button", "Close"))
        self.assertIsNone(find(self.tree["root"], "button", "Oculto"))

    def test_bounds_are_relative_to_window_origin(self):
        save = find(self.tree["root"], "button", "save")
        self.assertEqual(save["bounds"], [0.75, 0.95, 0.113, 0.042])

    def test_source_names_process_and_title(self):
        self.assertEqual(self.tree["source"], "notepad.exe: Notas - Editor")
        self.assertEqual(self.tree["platform"], "windows")

    def test_missing_window_raises_tree_error(self):
        with self.assertRaises(uitree.TreeError):
            uitree.normalize_uia({"root": {}}, "S02")


class PipelineTest(unittest.TestCase):
    def test_unnamed_single_child_group_is_collapsed(self):
        raw = uia_raw([uia_node("Pane", children=[uia_node("Button", "Ok")])])
        tree = uitree.normalize_uia(raw, "S01")
        self.assertEqual(preorder(tree["root"]), [("window", "T"), ("button", "Ok")])

    def test_named_group_is_kept(self):
        raw = uia_raw([uia_node("Pane", "Panel", children=[uia_node("Button", "Ok")])])
        tree = uitree.normalize_uia(raw, "S01")
        self.assertEqual(preorder(tree["root"]),
                         [("window", "T"), ("group", "Panel"), ("button", "Ok")])

    def test_depth_limit_marks_tree_partial(self):
        leaf = uia_node("Button", "Ok")
        for level in range(30):
            leaf = uia_node("Pane", "p%d" % level, children=[leaf])
        tree = uitree.normalize_uia(uia_raw([leaf]), "S01", max_depth=25)
        self.assertEqual(tree["tree_quality"], "partial")
        self.assertIsNone(find(tree["root"], "button", "Ok"))

    def test_raw_truncated_flag_marks_tree_partial(self):
        tree = uitree.normalize_uia(uia_raw([uia_node("Button", "Ok")], truncated=True), "S01")
        self.assertEqual(tree["tree_quality"], "partial")

    def test_tree_without_interactive_nodes_is_partial(self):
        tree = uitree.normalize_uia(uia_raw([uia_node("Text", "Hola")]), "S01")
        self.assertEqual(tree["tree_quality"], "partial")

    def test_zero_area_and_outside_window_nodes_are_dropped(self):
        raw = uia_raw([uia_node("Button", "Cero", rect=(10, 10, 0, 20)),
                       uia_node("Button", "Fuera", rect=(2000, 10, 50, 20)),
                       uia_node("Button", "Dentro", rect=(10, 10, 50, 20))])
        tree = uitree.normalize_uia(raw, "S01")
        self.assertEqual(preorder(tree["root"]), [("window", "T"), ("button", "Dentro")])


class InputRedactionTest(unittest.TestCase):
    def test_input_value_is_replaced_but_name_kept(self):
        raw = json.loads(read_fixture("uia_basic.json"))
        tree = uitree.normalize_uia(raw, "S02")
        editor = find(tree["root"], "input", "15")
        self.assertEqual(editor["text"], "<value>")
        self.assertEqual(editor["name"], "Editor de texto")

    def test_no_redact_keeps_values(self):
        raw = json.loads(read_fixture("uia_basic.json"))
        tree = uitree.normalize_uia(raw, "S02", redact=False)
        self.assertEqual(find(tree["root"], "input", "15")["text"], "hola juan@correo.com")
        self.assertFalse(tree["redacted"])


```

**Paso 3 — Verificar que falla:**

```bash
python -m unittest discover -s .claude/skills/clone-recon/tests -p test_uitree.py
```

Output esperado (lineas clave):

```
AttributeError: module 'uitree' has no attribute 'normalize_uia'
Ran 24 tests
FAILED (errors=13)
```

**Paso 4 — Implementar** (Agregar al final de `uitree.py`):

```python
def uia_role(raw_node):
    if raw_node.get("toggle") is not None and "ToggleSwitch" in (raw_node.get("className") or ""):
        return "switch"
    ctype = raw_node.get("type", "")
    return UIA_TYPE_ROLES.get(ctype, "group")


def _uia_node(raw_node):
    ctype = raw_node.get("type", "")
    node = _raw(uia_role(raw_node), raw_node.get("name"), raw_node.get("value"),
                raw_node.get("automationId"), raw_node.get("rect") or [0, 0, 0, 0],
                raw_node.get("enabled", True), raw_node.get("offscreen", False),
                drop=ctype in UIA_DROP_TYPES)
    node["children"] = [_uia_node(c) for c in raw_node.get("children", [])]
    return node


def normalize_uia(raw, screen, max_depth=25, redact=True, captured_at=None):
    try:
        window = raw["window"]
        raw_root = raw["root"]
        win = [int(v) for v in window["rect"]]
    except (KeyError, TypeError, ValueError) as exc:
        raise TreeError("JSON de UIA invalido: falta %s" % exc)
    if win[2] <= 0 or win[3] <= 0:
        raise TreeError("la ventana tiene tamano 0")
    root = _uia_node(raw_root)
    root["role"] = "window"
    root["rect"] = list(win)
    source = "%s.exe: %s" % (window.get("process", ""), window.get("title", ""))
    return _finish("windows", screen, source, root, win, max_depth, redact, captured_at,
                   truncated=bool(raw.get("truncated")))


# --------------------------------------------------------------- summarize

```

**Paso 5 — Verificar que pasa:**

```bash
python -m unittest discover -s .claude/skills/clone-recon/tests -p test_uitree.py
```

Output esperado:

```
Ran 24 tests
OK
```

**Paso 6 — Commit:**

```bash
git add .claude/skills/clone-recon/tests/fixtures/uia_basic.json .claude/skills/clone-recon/tests/test_uitree.py .claude/skills/clone-recon/scripts/uitree.py
git commit -m "feat(clone-recon): normalize UI Automation trees" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```


### Tarea 4: uitree: summarize

**Archivos:** agregar al final de `.claude/skills/clone-recon/tests/test_uitree.py`; agregar al final de `.claude/skills/clone-recon/scripts/uitree.py`

**Paso 1 — Test que falla** (Agregar al final de `test_uitree.py`):

```python
class SummarizeTest(unittest.TestCase):
    def list_tree(self, items):
        rows = [uia_node("ListItem", "item %d" % i, rect=(0, i * 10, 100, 10),
                         children=[uia_node("Text", "t", rect=(0, i * 10, 50, 10))])
                for i in range(items)]
        raw = uia_raw([uia_node("List", "Lista", rect=(0, 0, 1000, 500), children=rows)])
        return uitree.normalize_uia(raw, "S05", captured_at=FIXED_TIME)

    def test_repeated_list_items_collapse_to_one_line(self):
        text = uitree.summarize(self.list_tree(12))
        self.assertIn("listitem x12 (plantilla: text)", text)
        self.assertEqual(text.count("listitem"), 1)

    def test_header_and_lines_format(self):
        raw = uia_raw([uia_node("Button", "Ok", rect=(0, 0, 100, 50), automationId="ok")])
        tree = uitree.normalize_uia(raw, "S01")
        self.assertEqual(uitree.summarize(tree).splitlines(),
                         ["S01 windows full app.exe: T", 'button "Ok" #ok [0.05,0.05]'])

    def test_max_lines_cuts_deepest_levels_first(self):
        groups = [uia_node("Pane", "g%d" % i, children=[
            uia_node("Button", "b%d" % i, rect=(i * 10, 0, 10, 10))]) for i in range(5)]
        raw = uia_raw([uia_node("ToolBar", "Barra", rect=(0, 0, 1000, 50), children=groups)])
        tree = uitree.normalize_uia(raw, "S01")
        lines = uitree.summarize(tree, max_lines=3).splitlines()
        self.assertEqual(lines[1], 'toolbar "Barra" [0.50,0.05]')
        self.assertEqual(lines[-1], "... 5 nodos mas")
        self.assertEqual(len(lines), 3)


```

**Paso 2 — Verificar que falla:**

```bash
python -m unittest discover -s .claude/skills/clone-recon/tests -p test_uitree.py
```

Output esperado (lineas clave):

```
AttributeError: module 'uitree' has no attribute 'summarize'
Ran 27 tests
FAILED (errors=3)
```

**Paso 3 — Implementar** (Agregar al final de `uitree.py`):

```python
def signature(node):
    """Rol del nodo y roles de sus descendientes en preorden."""
    roles = []

    def walk(n):
        for c in n["children"]:
            roles.append(c["role"])
            walk(c)
    walk(node)
    return (node["role"], tuple(roles))


def _label(node):
    return node["name"] or node["text"]


def _line(node):
    parts = [node["role"]]
    label = _label(node)
    if label:
        parts.append('"%s"' % label)
    if node["id"]:
        parts.append("#" + node["id"])
    x, y, w, h = node["bounds"]
    parts.append("[%.2f,%.2f]" % (x + w / 2, y + h / 2))
    return " ".join(parts)


def _summary_lines(node, depth, out):
    if node["role"] == "list":
        groups = {}
        order = []
        for child in node["children"]:
            sig = signature(child)
            if sig not in groups:
                groups[sig] = []
                order.append(sig)
            groups[sig].append(child)
        for sig in order:
            members = groups[sig]
            if len(members) > 1:
                template = ", ".join(r for r in sig[1] if r not in CONTAINERS) or "-"
                out.append((depth, "%s x%d (plantilla: %s)" % (sig[0], len(members), template)))
            else:
                _summary_node(members[0], depth, out)
        return
    for child in node["children"]:
        _summary_node(child, depth, out)


def _summary_node(node, depth, out):
    if node["role"] in CONTAINERS:
        _summary_lines(node, depth, out)
        return
    out.append((depth, _line(node)))
    _summary_lines(node, depth + 1, out)


def summarize(tree, max_lines=40):
    header = "%s %s %s %s" % (tree["screen"], tree["platform"], tree["tree_quality"],
                              tree["source"])
    lines = []
    _summary_lines(tree["root"], 0, lines)
    kept = lines
    if len(lines) > max_lines:
        budget = max(max_lines - 1, 0)
        kept = []
        for depth_cap in range(max(d for d, _ in lines), -1, -1):
            kept = [l for l in lines if l[0] <= depth_cap]
            if len(kept) <= budget:
                break
        kept = kept[:budget]
    body = ["  " * d + text for d, text in kept]
    if len(kept) < len(lines):
        body.append("... %d nodos mas" % (len(lines) - len(kept)))
    return "\n".join([header] + body)


def count_nodes(node):
    return 1 + sum(count_nodes(c) for c in node["children"])


# --------------------------------------------------------------------- cli

```

**Paso 4 — Verificar que pasa:**

```bash
python -m unittest discover -s .claude/skills/clone-recon/tests -p test_uitree.py
```

Output esperado:

```
Ran 27 tests
OK
```

**Paso 5 — Commit:**

```bash
git add .claude/skills/clone-recon/tests/test_uitree.py .claude/skills/clone-recon/scripts/uitree.py
git commit -m "feat(clone-recon): compact tree summary" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```


### Tarea 5: uitree: CLI normalize y summarize

**Archivos:** agregar al final de `.claude/skills/clone-recon/tests/test_uitree.py`; agregar al final de `.claude/skills/clone-recon/scripts/uitree.py`

**Paso 1 — Test que falla** (Agregar al final de `test_uitree.py`):

```python
class CliTest(unittest.TestCase):
    def test_normalize_writes_tree_and_returns_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "S01.tree.json")
            buf = io.StringIO()
            with redirect_stdout(buf):
                code = uitree.main(["normalize", "--from", "android",
                                    os.path.join(FIXTURES, "android_basic.xml"),
                                    "--out", out, "--screen", "S01"])
            self.assertEqual(code, 0)
            with open(out, encoding="utf-8") as fh:
                self.assertEqual(json.load(fh)["screen"], "S01")
            self.assertIn("ok: ", buf.getvalue())

    def test_normalize_invalid_input_returns_two(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = os.path.join(tmp, "bad.xml")
            with open(bad, "w", encoding="utf-8") as fh:
                fh.write("<hierarchy><node")
            with redirect_stderr(io.StringIO()):
                code = uitree.main(["normalize", "--from", "android", bad,
                                    "--out", os.path.join(tmp, "o.json"), "--screen", "S01"])
            self.assertEqual(code, 2)

    def test_summarize_command_prints_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "t.json")
            tree = uitree.normalize_uia(uia_raw([uia_node("Button", "Ok")]), "S01")
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(tree, fh)
            buf = io.StringIO()
            with redirect_stdout(buf):
                code = uitree.main(["summarize", path])
        self.assertEqual(code, 0)
        self.assertTrue(buf.getvalue().startswith("S01 windows full"))


if __name__ == "__main__":
    unittest.main()
```

**Paso 2 — Verificar que falla:**

```bash
python -m unittest discover -s .claude/skills/clone-recon/tests -p test_uitree.py
```

Output esperado (lineas clave):

```
AttributeError: module 'uitree' has no attribute 'main'
Ran 30 tests
FAILED (errors=3)
```

**Paso 3 — Implementar** (Agregar al final de `uitree.py`):

```python
def _cmd_normalize(args):
    try:
        if args.source_format == "android":
            with open(args.raw, encoding="utf-8") as fh:
                tree = normalize_android(fh.read(), args.screen, args.source,
                                         args.max_depth, not args.no_redact)
        else:
            with open(args.raw, encoding="utf-8-sig") as fh:
                raw = json.load(fh)
            tree = normalize_uia(raw, args.screen, args.max_depth, not args.no_redact)
    except (OSError, ValueError, TreeError) as exc:
        print("uitree: %s" % exc, file=sys.stderr)
        return 2
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(tree, fh, ensure_ascii=False, indent=1)
    print("ok: %s (%d nodos, %s)" % (args.out, count_nodes(tree["root"]), tree["tree_quality"]))
    return 0


def _cmd_summarize(args):
    try:
        with open(args.tree, encoding="utf-8") as fh:
            tree = json.load(fh)
    except (OSError, ValueError) as exc:
        print("uitree: %s" % exc, file=sys.stderr)
        return 2
    print(summarize(tree, args.max_lines))
    return 0


def safe_stdout():
    """Evita UnicodeEncodeError en consolas cp1252: reemplaza lo no imprimible."""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="replace")


def main(argv=None):
    safe_stdout()
    ap = argparse.ArgumentParser(description="Arbol de UI normalizado")
    sub = ap.add_subparsers(dest="cmd", required=True)
    n = sub.add_parser("normalize")
    n.add_argument("--from", dest="source_format", choices=("android", "uia"), required=True)
    n.add_argument("raw")
    n.add_argument("--out", required=True)
    n.add_argument("--screen", required=True)
    n.add_argument("--source", default="")
    n.add_argument("--max-depth", type=int, default=25)
    n.add_argument("--no-redact", action="store_true")
    s = sub.add_parser("summarize")
    s.add_argument("tree")
    s.add_argument("--max-lines", type=int, default=40)
    args = ap.parse_args(argv)
    if args.cmd == "normalize":
        return _cmd_normalize(args)
    return _cmd_summarize(args)


if __name__ == "__main__":
    sys.exit(main())
```

**Paso 4 — Verificar que pasa:**

```bash
python -m unittest discover -s .claude/skills/clone-recon/tests -p test_uitree.py
```

Output esperado:

```
Ran 30 tests
OK
```

**Paso 5 — Commit:**

```bash
git add .claude/skills/clone-recon/tests/test_uitree.py .claude/skills/clone-recon/scripts/uitree.py
git commit -m "feat(clone-recon): uitree command line" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```


---

## Fase 2: capture_android.py

### Tarea 6: capture_android: localizar adb y elegir dispositivo

**Archivos:** crear `.claude/skills/clone-recon/tests/test_capture_android.py`; crear `.claude/skills/clone-recon/scripts/capture_android.py`

**Paso 1 — Test que falla** (Crear `test_capture_android.py`):

```python
import io
import json
import os
import struct
import sys
import tempfile
import unittest
import zlib
from contextlib import redirect_stderr, redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "scripts"))

import capture_android  # noqa: E402

FIXTURES = os.path.join(HERE, "fixtures")
ACTIVITY_LINE = (b"  topResumedActivity=ActivityRecord{1a2b3c u0 "
                 b"com.example.notes/.MainActivity t42}\n")


def raw_screencap(width, height, pixel=b"\x10\x20\x30\xff", varied=True, header=16):
    pixels = bytearray(pixel * (width * height))
    if varied:
        pixels[0:4] = b"\xff\xff\xff\xff"
    head = struct.pack("<III", width, height, 1)
    if header == 16:
        head += struct.pack("<I", 0)
    return head + bytes(pixels)


class FakeAdb:
    """Responde a los comandos de adb segun el escenario."""

    def __init__(self, devices=("emulator-5554",), dump_failures=0, screen=None):
        with open(os.path.join(FIXTURES, "android_basic.xml"), "rb") as fh:
            self.xml = fh.read()
        self.devices = devices
        self.dump_failures = dump_failures
        self.screen = screen if screen is not None else raw_screencap(4, 2)
        self.calls = []

    def __call__(self, cmd):
        self.calls.append(cmd)
        args = cmd[1:]
        if args == ["devices"]:
            body = "List of devices attached\n" + "".join(
                "%s\tdevice\n" % d for d in self.devices)
            return 0, body.encode(), b""
        if "uiautomator" in args:
            if self.dump_failures > 0:
                self.dump_failures -= 1
                return 1, b"", b"ERROR: could not get idle state.\n"
            return 0, b"UI hierchary dumped to: /sdcard/clone_dump.xml\n", b""
        if args[-2:] == ["cat", capture_android.DUMP_PATH]:
            return 0, self.xml, b""
        if args[-1] == "screencap":
            return 0, self.screen, b""
        if "dumpsys" in args:
            return 0, ACTIVITY_LINE, b""
        return 1, b"", b"comando inesperado"


def run_main(fake, out_dir, *extra):
    argv = ["--id", "S01", "--out", out_dir, "--adb", "adb"] + list(extra)
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = capture_android.main(argv, run=fake, sleep=lambda s: None)
    return code, out.getvalue(), err.getvalue()


class FindAdbTest(unittest.TestCase):
    def test_explicit_path_wins(self):
        self.assertEqual(capture_android.find_adb("C:/sdk/adb.exe", env={}), "C:/sdk/adb.exe")

    def test_android_home_is_searched(self):
        home = os.path.join("X", "sdk")
        expected = os.path.join(home, "platform-tools", "adb.exe" if os.name == "nt" else "adb")
        found = capture_android.find_adb(env={"ANDROID_HOME": home}, which=lambda n: None,
                                         isfile=lambda p: p == expected)
        self.assertEqual(found, expected)

    def test_missing_adb_returns_none(self):
        self.assertIsNone(capture_android.find_adb(env={}, which=lambda n: None,
                                                   isfile=lambda p: False))


class DeviceTest(unittest.TestCase):
    def test_list_devices_keeps_only_ready_devices(self):
        listing = b"List of devices attached\nemulator-5554\tdevice\nR58M\tunauthorized\n"
        devices = capture_android.list_devices("adb", lambda cmd: (0, listing, b""))
        self.assertEqual(devices, ["emulator-5554"])

    def test_single_device_is_picked_without_serial(self):
        self.assertEqual(capture_android.pick_serial(["emulator-5554"]), "emulator-5554")

    def test_two_devices_without_serial_raise(self):
        with self.assertRaisesRegex(capture_android.CaptureError, "Usa --serial"):
            capture_android.pick_serial(["aaa", "bbb"])

    def test_unknown_serial_raises(self):
        with self.assertRaisesRegex(capture_android.CaptureError, "no esta conectado"):
            capture_android.pick_serial(["aaa"], "zzz")


```

**Paso 2 — Verificar que falla:**

```bash
python -m unittest discover -s .claude/skills/clone-recon/tests -p test_capture_android.py
```

Output esperado (lineas clave):

```
ImportError: Failed to import test module: test_capture_android
ModuleNotFoundError: No module named 'capture_android'
Ran 1 test
FAILED (errors=1)
```

**Paso 3 — Implementar** (Crear `capture_android.py`):

```python
#!/usr/bin/env python3
"""
capture_android.py — Captura una pantalla de una app Android via adb. Zero dependencias.

Guarda screenshot, dump crudo de uiautomator y arbol normalizado:
  <out>/<SID>.png  <out>/<SID>.raw.xml  <out>/<SID>.tree.json
y muestra por stdout el resumen del arbol.

Uso:
  python capture_android.py --id S03@vacio --out clone/captures/original
         [--serial SERIAL] [--adb RUTA] [--max-depth 25] [--no-redact] [--retries 3]

Exit: 0 ok, 1 captura parcial (sin arbol o pantalla negra), 2 error de entorno.
"""

import argparse
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import time
import zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import uitree  # noqa: E402

DUMP_PATH = "/sdcard/clone_dump.xml"
_ACTIVITY = re.compile(
    r"(?:topResumedActivity|mResumedActivity)[=:]\s*ActivityRecord\{\S+ \S+ (\S+)")


class CaptureError(Exception):
    """Error de entorno: adb, dispositivo o captura imposible."""


def default_run(cmd):
    proc = subprocess.run(cmd, capture_output=True)
    return proc.returncode, proc.stdout, proc.stderr


def find_adb(explicit=None, env=None, which=shutil.which, isfile=os.path.isfile):
    if explicit:
        return explicit
    env = os.environ if env is None else env
    found = which("adb")
    if found:
        return found
    exe = "adb.exe" if os.name == "nt" else "adb"
    candidates = []
    if env.get("ANDROID_HOME"):
        candidates.append(os.path.join(env["ANDROID_HOME"], "platform-tools", exe))
    if env.get("LOCALAPPDATA"):
        candidates.append(os.path.join(env["LOCALAPPDATA"], "Android", "Sdk",
                                       "platform-tools", exe))
    if env.get("HOME"):
        candidates.append(os.path.join(env["HOME"], "Android", "Sdk", "platform-tools", exe))
    for path in candidates:
        if isfile(path):
            return path
    return None


def list_devices(adb, run):
    code, out, err = run([adb, "devices"])
    if code != 0:
        raise CaptureError("adb devices fallo: %s" % err.decode("utf-8", "replace").strip())
    serials = []
    for line in out.decode("utf-8", "replace").splitlines()[1:]:
        parts = line.split()
        if len(parts) >= 2 and parts[1] == "device":
            serials.append(parts[0])
    return serials


def pick_serial(devices, serial=None):
    if serial:
        if serial not in devices:
            raise CaptureError("el dispositivo %s no esta conectado. Conectados: %s"
                               % (serial, ", ".join(devices) or "ninguno"))
        return serial
    if not devices:
        raise CaptureError("no hay dispositivos. Conecta uno con depuracion USB activa "
                           "y acepta la huella RSA en el telefono.")
    if len(devices) > 1:
        raise CaptureError("hay %d dispositivos: %s. Usa --serial."
                           % (len(devices), ", ".join(devices)))
    return devices[0]


```

**Paso 4 — Verificar que pasa:**

```bash
python -m unittest discover -s .claude/skills/clone-recon/tests -p test_capture_android.py
```

Output esperado:

```
Ran 7 tests
OK
```

**Paso 5 — Commit:**

```bash
git add .claude/skills/clone-recon/tests/test_capture_android.py .claude/skills/clone-recon/scripts/capture_android.py
git commit -m "feat(clone-recon): adb discovery and device selection" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```


### Tarea 7: capture_android: screencap crudo a PNG

**Archivos:** agregar al final de `.claude/skills/clone-recon/tests/test_capture_android.py`; agregar al final de `.claude/skills/clone-recon/scripts/capture_android.py`

**Paso 1 — Test que falla** (Agregar al final de `test_capture_android.py`):

```python
class ScreencapTest(unittest.TestCase):
    def test_parses_12_and_16_byte_headers(self):
        for header in (12, 16):
            w, h, pixels = capture_android.parse_raw_screencap(raw_screencap(4, 2, header=header))
            self.assertEqual((w, h, len(pixels)), (4, 2, 32))

    def test_unsupported_format_raises(self):
        data = struct.pack("<III", 2, 1, 4) + b"\x00" * 4
        with self.assertRaises(capture_android.CaptureError):
            capture_android.parse_raw_screencap(data)

    def test_encoded_png_roundtrips_pixels(self):
        pixels = bytes(range(32))
        png = capture_android.encode_png(4, 2, pixels)
        self.assertTrue(png.startswith(b"\x89PNG\r\n\x1a\n"))
        idat_len = struct.unpack(">I", png[33:37])[0]
        raw = zlib.decompress(png[41:41 + idat_len])
        self.assertEqual(raw, b"\x00" + pixels[:16] + b"\x00" + pixels[16:])


```

**Paso 2 — Verificar que falla:**

```bash
python -m unittest discover -s .claude/skills/clone-recon/tests -p test_capture_android.py
```

Output esperado (lineas clave):

```
AttributeError: module 'capture_android' has no attribute 'encode_png'
AttributeError: module 'capture_android' has no attribute 'parse_raw_screencap'
Ran 10 tests
FAILED (errors=3)
```

**Paso 3 — Implementar** (Agregar al final de `capture_android.py`):

```python
def parse_raw_screencap(data):
    """Header de screencap crudo (12 o 16 bytes) + RGBA. Devuelve (w, h, pixels)."""
    if len(data) < 12:
        raise CaptureError("screencap devolvio %d bytes" % len(data))
    width, height, fmt = struct.unpack_from("<III", data, 0)
    header = len(data) - width * height * 4
    if fmt not in (1, 2) or header not in (12, 16):
        raise CaptureError("formato de screencap no soportado (formato %d)" % fmt)
    return width, height, data[header:]


def is_uniform(pixels):
    first = pixels[:4]
    return pixels == first * (len(pixels) // 4)


def encode_png(width, height, pixels):
    stride = width * 4
    raw = b"".join(b"\x00" + pixels[y * stride:(y + 1) * stride] for y in range(height))

    def chunk(kind, body):
        return (struct.pack(">I", len(body)) + kind + body
                + struct.pack(">I", zlib.crc32(kind + body) & 0xFFFFFFFF))

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(raw, 6)) + chunk(b"IEND", b""))


```

**Paso 4 — Verificar que pasa:**

```bash
python -m unittest discover -s .claude/skills/clone-recon/tests -p test_capture_android.py
```

Output esperado:

```
Ran 10 tests
OK
```

**Paso 5 — Commit:**

```bash
git add .claude/skills/clone-recon/tests/test_capture_android.py .claude/skills/clone-recon/scripts/capture_android.py
git commit -m "feat(clone-recon): raw screencap decoding and png encoding" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```


### Tarea 8: capture_android: captura completa y CLI

**Archivos:** agregar al final de `.claude/skills/clone-recon/tests/test_capture_android.py`; agregar al final de `.claude/skills/clone-recon/scripts/capture_android.py`

**Paso 1 — Test que falla** (Agregar al final de `test_capture_android.py`):

```python
class SerialTest(unittest.TestCase):
    def test_two_devices_without_serial_exits_two(self):
        fake = FakeAdb(devices=("aaa", "bbb"))
        with tempfile.TemporaryDirectory() as tmp:
            code, _, err = run_main(fake, tmp)
        self.assertEqual(code, 2)
        self.assertIn("aaa, bbb", err)

    def test_serial_selects_device(self):
        fake = FakeAdb(devices=("aaa", "bbb"))
        with tempfile.TemporaryDirectory() as tmp:
            code, _, _ = run_main(fake, tmp, "--serial", "bbb")
        self.assertEqual(code, 0)
        self.assertIn(["adb", "-s", "bbb", "exec-out", "screencap"], fake.calls)

    def test_no_devices_exits_two(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, _, err = run_main(FakeAdb(devices=()), tmp)
        self.assertEqual(code, 2)
        self.assertIn("no hay dispositivos", err)


class CaptureTest(unittest.TestCase):
    def test_happy_path_writes_three_files_and_exits_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, out, _ = run_main(FakeAdb(), tmp)
            self.assertEqual(code, 0)
            self.assertEqual(sorted(os.listdir(tmp)), ["S01.png", "S01.raw.xml", "S01.tree.json"])
            with open(os.path.join(tmp, "S01.tree.json"), encoding="utf-8") as fh:
                tree = json.load(fh)
        self.assertEqual(tree["source"], "com.example.notes/.MainActivity")
        self.assertEqual(tree["tree_quality"], "full")
        self.assertTrue(out.startswith("S01 android full com.example.notes/.MainActivity"))

    def test_dump_failing_every_retry_gives_quality_none_and_exit_one(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, _, err = run_main(FakeAdb(dump_failures=3), tmp)
            with open(os.path.join(tmp, "S01.tree.json"), encoding="utf-8") as fh:
                tree = json.load(fh)
            self.assertFalse(os.path.exists(os.path.join(tmp, "S01.raw.xml")))
        self.assertEqual(code, 1)
        self.assertEqual(tree["tree_quality"], "none")
        self.assertIn("uiautomator dump fallo 3 veces", err)

    def test_dump_recovers_on_second_try(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, _, _ = run_main(FakeAdb(dump_failures=1), tmp)
        self.assertEqual(code, 0)

    def test_uniform_screenshot_warns_and_exits_one(self):
        fake = FakeAdb(screen=raw_screencap(4, 2, b"\x00\x00\x00\xff", varied=False))
        with tempfile.TemporaryDirectory() as tmp:
            code, _, err = run_main(fake, tmp)
        self.assertEqual(code, 1)
        self.assertIn("un solo color", err)


if __name__ == "__main__":
    unittest.main()
```

**Paso 2 — Verificar que falla:**

```bash
python -m unittest discover -s .claude/skills/clone-recon/tests -p test_capture_android.py
```

Output esperado (lineas clave):

```
AttributeError: module 'capture_android' has no attribute 'main'
Ran 17 tests
FAILED (errors=7)
```

**Paso 3 — Implementar** (Agregar al final de `capture_android.py`):

```python
def dump_ui(adb, serial, run, retries=3, sleep=time.sleep):
    """Devuelve el XML de uiautomator, o None si fallo todas las veces."""
    for attempt in range(retries):
        code, out, err = run([adb, "-s", serial, "shell", "uiautomator", "dump", DUMP_PATH])
        if code == 0 and b"ERROR" not in out + err:
            code, out, _ = run([adb, "-s", serial, "exec-out", "cat", DUMP_PATH])
            if code == 0 and b"<hierarchy" in out:
                return out.decode("utf-8", "replace")
        if attempt < retries - 1:
            sleep(1)
    return None


def screencap(adb, serial, run):
    """Devuelve (png_bytes, width, height, uniform)."""
    code, out, err = run([adb, "-s", serial, "exec-out", "screencap"])
    if code != 0:
        raise CaptureError("screencap fallo: %s" % err.decode("utf-8", "replace").strip())
    width, height, pixels = parse_raw_screencap(out)
    return encode_png(width, height, pixels), width, height, is_uniform(pixels)


def current_activity(adb, serial, run):
    code, out, _ = run([adb, "-s", serial, "shell", "dumpsys", "activity", "activities"])
    if code != 0:
        return ""
    match = _ACTIVITY.search(out.decode("utf-8", "replace"))
    return match.group(1) if match else ""


def capture(args, run=default_run, sleep=time.sleep):
    adb = find_adb(args.adb)
    if not adb:
        raise CaptureError("no encuentro adb. Instala Android SDK Platform-Tools o pasa --adb RUTA.")
    serial = pick_serial(list_devices(adb, run), args.serial)
    os.makedirs(args.out, exist_ok=True)
    base = os.path.join(args.out, args.id)

    xml_text = dump_ui(adb, serial, run, args.retries, sleep)
    png, width, height, uniform = screencap(adb, serial, run)
    source = current_activity(adb, serial, run)
    with open(base + ".png", "wb") as fh:
        fh.write(png)

    partial = False
    if xml_text is not None:
        with open(base + ".raw.xml", "w", encoding="utf-8") as fh:
            fh.write(xml_text)
        tree = uitree.normalize_android(xml_text, args.id, source, args.max_depth,
                                        not args.no_redact)
    else:
        print("aviso: uiautomator dump fallo %d veces; solo screenshot." % args.retries,
              file=sys.stderr)
        tree = uitree.empty_tree("android", args.id, source, width, height)
        partial = True
    if uniform:
        print("aviso: el screenshot es de un solo color (FLAG_SECURE o pantalla apagada).",
              file=sys.stderr)
        partial = True

    with open(base + ".tree.json", "w", encoding="utf-8") as fh:
        json.dump(tree, fh, ensure_ascii=False, indent=1)
    print(uitree.summarize(tree))
    return 1 if partial else 0


def main(argv=None, run=default_run, sleep=time.sleep):
    uitree.safe_stdout()
    ap = argparse.ArgumentParser(description="Captura de pantalla Android para el clone pack")
    ap.add_argument("--id", required=True, help="id de pantalla, ej. S03@vacio")
    ap.add_argument("--out", required=True)
    ap.add_argument("--serial")
    ap.add_argument("--adb")
    ap.add_argument("--max-depth", type=int, default=25)
    ap.add_argument("--no-redact", action="store_true")
    ap.add_argument("--retries", type=int, default=3)
    args = ap.parse_args(argv)
    try:
        return capture(args, run, sleep)
    except (CaptureError, uitree.TreeError) as exc:
        print("capture_android: %s" % exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
```

**Paso 4 — Verificar que pasa:**

```bash
python -m unittest discover -s .claude/skills/clone-recon/tests -p test_capture_android.py
```

Output esperado:

```
Ran 17 tests
OK
```

**Paso 5 — Commit:**

```bash
git add .claude/skills/clone-recon/tests/test_capture_android.py .claude/skills/clone-recon/scripts/capture_android.py
git commit -m "feat(clone-recon): android capture command" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```


---

## Fase 3: capture_windows.ps1

### Tarea 9: captura via UI Automation

Sin test automatizado: depende de ventanas reales. Se verifica contra el Bloc
de notas y la Calculadora de Windows (criterios 2 y 3 de la spec). Requiere
que `uitree.py` (Fase 1) exista.

**Archivos:** crear `.claude/skills/clone-recon/scripts/capture_windows.ps1`

**Paso 1 — Verificar que falla** (en PowerShell):

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .claude/skills/clone-recon/scripts/capture_windows.ps1 -Id N01 -Out "$env:TEMP\clonecap" -Process notepad
```

Output esperado (primera linea):

```
El argumento '.claude/skills/clone-recon/scripts/capture_windows.ps1' para el parámetro -File no existe. Proporcione la ruta de acceso a un archivo '.ps1' existente como argumento para el parámetro -File.
```

**Paso 2 — Crear `.claude/skills/clone-recon/scripts/capture_windows.ps1`:**

```powershell
<#
capture_windows.ps1 - Captura una ventana de Windows via UI Automation. Sin instalar nada.

Guarda <Out>\<Id>.raw.json (arbol UIA crudo) y <Out>\<Id>.png (la ventana).
Normalizar despues con:
  python uitree.py normalize --from uia <Out>\<Id>.raw.json --out <Out>\<Id>.tree.json --screen <Id>

Uso:
  powershell -NoProfile -ExecutionPolicy Bypass -File capture_windows.ps1 -Id S03 -Out clone\captures\original -Process notepad
  powershell -NoProfile -ExecutionPolicy Bypass -File capture_windows.ps1 -Id S03 -Out clone\captures\original -Title "Calculadora"

Exit: 0 ok, 2 ventana no encontrada o acceso denegado.
#>
param(
    [Parameter(Mandatory = $true)][string]$Id,
    [Parameter(Mandatory = $true)][string]$Out,
    [string]$Process = "",
    [string]$Title = "",
    [int]$MaxDepth = 25
)

$ErrorActionPreference = "Stop"
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
Add-Type -AssemblyName System.Drawing
Add-Type -AssemblyName System.Windows.Forms

$script:Truncated = $false

function Fail([string]$Message) {
    [Console]::Error.WriteLine("capture_windows: $Message")
    exit 2
}

function Find-Window {
    if (-not $Process -and -not $Title) { Fail "indica -Process o -Title." }
    $root = [System.Windows.Automation.AutomationElement]::RootElement
    $condition = [System.Windows.Automation.Condition]::TrueCondition
    $windows = $root.FindAll([System.Windows.Automation.TreeScope]::Children, $condition)
    $found = @()
    foreach ($w in $windows) {
        $info = $w.Current
        if ($Title -and $info.Name -notlike "*$Title*") { continue }
        if ($Process) {
            try { $procName = (Get-Process -Id $info.ProcessId).ProcessName } catch { continue }
            if ($procName -ne $Process) { continue }
        }
        $found += $w
    }
    if ($found.Count -eq 0) {
        $hint = ""
        if ($Process) { $hint = " Si es una app de la Tienda (UWP/WinUI) vive dentro de ApplicationFrameHost: usa -Title." }
        Fail "ventana no encontrada.$hint"
    }
    $focused = [System.Windows.Automation.AutomationElement]::FocusedElement
    foreach ($w in $found) {
        if ($focused -and $focused.Current.ProcessId -eq $w.Current.ProcessId) { return $w }
    }
    if ($found.Count -gt 1) {
        [Console]::Error.WriteLine("capture_windows: $($found.Count) ventanas coinciden; uso '$($found[0].Current.Name)'.")
    }
    return $found[0]
}

function Get-Rect($element) {
    $r = $element.Current.BoundingRectangle
    if ($r.IsEmpty) { return @(0, 0, 0, 0) }
    return @([int]$r.X, [int]$r.Y, [int]$r.Width, [int]$r.Height)
}

function Get-PatternValue($element) {
    $pattern = $null
    if ($element.TryGetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern, [ref]$pattern)) {
        return $pattern.Current.Value
    }
    return $null
}

function Get-ToggleState($element) {
    $pattern = $null
    if ($element.TryGetCurrentPattern([System.Windows.Automation.TogglePattern]::Pattern, [ref]$pattern)) {
        return [string]$pattern.Current.ToggleState
    }
    return $null
}

function Convert-Node($element, [int]$depth) {
    $info = $element.Current
    $node = [ordered]@{
        type         = $info.ControlType.ProgrammaticName -replace '^ControlType\.', ''
        name         = $info.Name
        automationId = $info.AutomationId
        className    = $info.ClassName
        rect         = Get-Rect $element
        enabled      = $info.IsEnabled
        offscreen    = $info.IsOffscreen
        value        = Get-PatternValue $element
        toggle       = Get-ToggleState $element
        children     = @()
    }
    $walker = [System.Windows.Automation.TreeWalker]::ControlViewWalker
    $child = $walker.GetFirstChild($element)
    if ($child -and $depth -ge $MaxDepth) {
        $script:Truncated = $true
        return $node
    }
    $kids = New-Object System.Collections.ArrayList
    while ($child) {
        [void]$kids.Add((Convert-Node $child ($depth + 1)))
        $child = $walker.GetNextSibling($child)
    }
    $node.children = $kids.ToArray()
    return $node
}

$window = Find-Window
try {
    $tree = Convert-Node $window 0
} catch [System.UnauthorizedAccessException] {
    Fail "acceso denegado. La app corre como administrador: ejecuta la terminal como administrador o captura solo screenshot."
} catch [System.Windows.Automation.ElementNotAvailableException] {
    Fail "la ventana se cerro durante la captura."
}

$rect = Get-Rect $window
$procName = (Get-Process -Id $window.Current.ProcessId).ProcessName
$raw = [ordered]@{
    window    = [ordered]@{ title = $window.Current.Name; process = $procName; rect = $rect }
    truncated = $script:Truncated
    root      = $tree
}

New-Item -ItemType Directory -Force -Path $Out | Out-Null
$base = Join-Path $Out $Id
$json = $raw | ConvertTo-Json -Depth 100 -Compress
[System.IO.File]::WriteAllText("$base.raw.json", $json, (New-Object System.Text.UTF8Encoding($false)))

if ($rect[2] -gt 0 -and $rect[3] -gt 0) {
    $bitmap = New-Object System.Drawing.Bitmap($rect[2], $rect[3])
    $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
    $graphics.CopyFromScreen($rect[0], $rect[1], 0, 0, $bitmap.Size)
    $bitmap.Save("$base.png", [System.Drawing.Imaging.ImageFormat]::Png)
    $graphics.Dispose()
    $bitmap.Dispose()
}

Write-Output "ok: $base.raw.json ($procName, '$($window.Current.Name)', truncated=$($script:Truncated))"
exit 0
```

Nota: no usar `$matches` como nombre de variable: es automatica en PowerShell.

**Paso 3 — Verificar con el Bloc de notas** (en PowerShell; abre y cierra Notepad):

```powershell
$cap = "$env:TEMP\clonecap"
$p = Start-Process notepad -PassThru; Start-Sleep -Seconds 2
powershell -NoProfile -ExecutionPolicy Bypass -File .claude/skills/clone-recon/scripts/capture_windows.ps1 -Id N01 -Out $cap -Process notepad
Stop-Process -Id $p.Id
python .claude/skills/clone-recon/scripts/uitree.py normalize --from uia "$cap\N01.raw.json" --out "$cap\N01.tree.json" --screen N01
python -c "import json,sys;t=json.load(open(sys.argv[1],encoding='utf-8'));c={};st=[t['root']];[(c.__setitem__(n['role'],c.get(n['role'],0)+1),st.extend(n['children'])) for n in iter(lambda:st.pop() if st else None,None)];print(t['tree_quality'],'input=%d'%c.get('input',0),'button=%d'%c.get('button',0))" "$cap\N01.tree.json"
```

Output esperado (rutas segun `%TEMP%`; Windows en espanol):

```
ok: C:\Users\Usuario\AppData\Local\Temp\clonecap\N01.raw.json (notepad, 'Sin título: Bloc de notas', truncated=False)
ok: C:\Users\Usuario\AppData\Local\Temp\clonecap\N01.tree.json (15 nodos, full)
full input=6 button=0
```

Criterio 2 cumplido: al menos 1 `input` y `tree_quality=full`. Los botones
Minimizar/Maximizar/Cerrar no aparecen porque la barra de titulo se descarta.

**Paso 4 — Verificar con la Calculadora** (en PowerShell; abre y cierra la Calculadora):

```powershell
$cap = "$env:TEMP\clonecap"
Start-Process calc; Start-Sleep -Seconds 4
powershell -NoProfile -ExecutionPolicy Bypass -File .claude/skills/clone-recon/scripts/capture_windows.ps1 -Id C01 -Out $cap -Process CalculatorApp
"exit=$LASTEXITCODE"
powershell -NoProfile -ExecutionPolicy Bypass -File .claude/skills/clone-recon/scripts/capture_windows.ps1 -Id C01 -Out $cap -Title "Calculadora"
Get-Process CalculatorApp -ErrorAction SilentlyContinue | Stop-Process
python .claude/skills/clone-recon/scripts/uitree.py normalize --from uia "$cap\C01.raw.json" --out "$cap\C01.tree.json" --screen C01
python -c "import json,sys;t=json.load(open(sys.argv[1],encoding='utf-8'));c={};st=[t['root']];[(c.__setitem__(n['role'],c.get(n['role'],0)+1),st.extend(n['children'])) for n in iter(lambda:st.pop() if st else None,None)];print(t['tree_quality'],'input=%d'%c.get('input',0),'button=%d'%c.get('button',0))" "$cap\C01.tree.json"
```

Output esperado:

```
capture_windows: ventana no encontrada. Si es una app de la Tienda (UWP/WinUI) vive dentro de ApplicationFrameHost: usa -Title.
exit=2
ok: C:\Users\Usuario\AppData\Local\Temp\clonecap\C01.raw.json (ApplicationFrameHost, 'Calculadora', truncated=False)
ok: C:\Users\Usuario\AppData\Local\Temp\clonecap\C01.tree.json (50 nodos, full)
full input=0 button=36
```

Criterio 3 cumplido: 36 botones (10 o mas). Por proceso falla con el mensaje
que sugiere `-Title`. Si Windows esta en ingles, el titulo es "Calculator".

**Paso 5 — Commit:**

```bash
git add .claude/skills/clone-recon/scripts/capture_windows.ps1
git commit -m "feat(clone-recon): windows capture via ui automation" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

## Fase 4: treediff.py

### Tarea 10: treediff: carga y aplanado de arboles

**Archivos:** crear `.claude/skills/clone-diff/tests/test_treediff.py`; crear `.claude/skills/clone-diff/scripts/treediff.py`

**Paso 1 — Test que falla** (Crear `test_treediff.py`):

```python
import copy
import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "scripts"))

import treediff  # noqa: E402


def node(role, label="", id_="", bounds=(0.0, 0.0, 0.1, 0.1), children=None):
    return {"role": role, "name": label, "text": "", "id": id_, "bounds": list(bounds),
            "enabled": True, "children": children or []}


def tree(children, screen="S01", quality="full"):
    return {"schema": 1, "platform": "android", "screen": screen, "source": "",
            "captured_at": "2026-10-20T00:00:00Z", "window": {"w": 1080, "h": 2400},
            "tree_quality": quality, "redacted": True,
            "root": node("window", bounds=(0, 0, 1, 1), children=children)}


def form_screen():
    return tree([
        node("text", "Ajustes", bounds=(0.05, 0.02, 0.5, 0.05)),
        node("button", "Guardar", "save", (0.05, 0.90, 0.4, 0.05)),
        node("button", "Cancelar", "cancel", (0.55, 0.90, 0.4, 0.05)),
        node("button", "Ayuda", "", (0.80, 0.02, 0.1, 0.05)),
        node("button", "", "", (0.05, 0.50, 0.1, 0.05)),
    ])


def list_screen(items):
    rows = [node("listitem", "nota %d" % i, "row", (0.0, 0.1 + i * 0.04, 1.0, 0.04),
                 [node("text", "nota %d" % i, "row_title", (0.05, 0.1 + i * 0.04, 0.5, 0.02))])
            for i in range(items)]
    return tree([node("list", "", "notes", (0.0, 0.1, 1.0, 0.8), rows)])


class FlattenTest(unittest.TestCase):
    def test_containers_are_not_scored(self):
        flat = treediff.flatten(tree([node("group", children=[node("button", "Ok")])]))
        self.assertEqual([(n["role"], n["parent_role"]) for n in flat], [("button", "root")])

    def test_parent_role_is_nearest_non_container(self):
        bar = node("toolbar", "Barra", children=[node("group", children=[node("button", "Ok")])])
        flat = treediff.flatten(tree([bar]))
        self.assertEqual([(n["role"], n["parent_role"]) for n in flat],
                         [("toolbar", "root"), ("button", "toolbar")])

    def test_list_children_become_one_template_with_count(self):
        flat = treediff.flatten(list_screen(5))
        self.assertEqual([(n["role"], n["count"]) for n in flat], [("list", 1), ("listitem", 5)])

    def test_labels_are_normalized(self):
        self.assertEqual(treediff.normalize_label("  Edición   Rápida "), "edicion rapida")

    def test_load_tree_rejects_other_schema(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "t.json")
            with open(path, "w", encoding="utf-8") as fh:
                json.dump({"schema": 2}, fh)
            with self.assertRaises(treediff.DiffError):
                treediff.load_tree(path)


```

**Paso 2 — Verificar que falla:**

```bash
python -m unittest discover -s .claude/skills/clone-diff/tests -p test_treediff.py
```

Output esperado (lineas clave):

```
ImportError: Failed to import test module: test_treediff
ModuleNotFoundError: No module named 'treediff'
Ran 1 test
FAILED (errors=1)
```

**Paso 3 — Implementar** (Crear `treediff.py`):

```python
#!/usr/bin/env python3
"""
treediff.py — Compara el arbol de UI normalizado del original contra el del clon.
Zero dependencias.

Uso:
  python treediff.py ORIGINAL.tree.json CLON.tree.json [--json] [--ignore-text] [--out DIFF.json]

Empareja nodos del mismo rol en pasadas (lista por firma, id, etiqueta,
posicion) y reporta interactive_score, structure_score, faltantes, extras,
textos cambiados y nodos movidos. Exit 0 si pudo leer ambos arboles, 2 si no.
"""

import argparse
import json
import math
import sys
import unicodedata

INTERACTIVE = frozenset({
    "button", "link", "input", "select", "checkbox", "radio", "switch",
    "slider", "tab", "menuitem", "listitem",
})
CONTENT = frozenset({"list", "tabs", "menu", "toolbar", "text", "image", "unknown"})
CONTAINERS = frozenset({"window", "group"})
WEIGHTS = dict([(r, 3) for r in INTERACTIVE] + [(r, 1) for r in CONTENT])

POSITION_MATCH = 0.08
MOVED = 0.15


class DiffError(Exception):
    """Archivo ausente o con schema distinto de 1."""


def load_tree(path):
    try:
        with open(path, encoding="utf-8") as fh:
            tree = json.load(fh)
    except (OSError, ValueError) as exc:
        raise DiffError("no puedo leer %s: %s" % (path, exc))
    if not isinstance(tree, dict) or tree.get("schema") != 1:
        raise DiffError("%s no es un arbol schema 1" % path)
    return tree


def normalize_label(text):
    text = unicodedata.normalize("NFKD", text or "")
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return " ".join(text.lower().split())


def signature(node):
    roles = []

    def walk(n):
        for c in n["children"]:
            roles.append(c["role"])
            walk(c)
    walk(node)
    return (node["role"], tuple(roles))


def _center(bounds):
    x, y, w, h = bounds
    return (x + w / 2, y + h / 2)


def _flat(node, parent_role, item_sig, count):
    return {
        "role": node["role"],
        "id": node["id"],
        "label": normalize_label(node["name"] or node["text"]),
        "raw_label": node["name"] or node["text"],
        "bounds": node["bounds"],
        "center": _center(node["bounds"]),
        "parent_role": parent_role,
        "item_sig": item_sig,
        "count": count,
    }


def flatten(tree):
    """Nodos puntuables (sin contenedores). Los hijos de un list se reducen
    a una plantilla por firma, sin descender en ella."""
    out = []

    def walk(node, parent_role):
        if node["role"] == "list":
            out.append(_flat(node, parent_role, None, 1))
            groups = {}
            order = []
            for child in node["children"]:
                sig = signature(child)
                if sig not in groups:
                    groups[sig] = []
                    order.append(sig)
                groups[sig].append(child)
            for sig in order:
                first = groups[sig][0]
                if first["role"] not in CONTAINERS:
                    out.append(_flat(first, "list", sig, len(groups[sig])))
            return
        next_parent = parent_role
        if node["role"] not in CONTAINERS:
            out.append(_flat(node, parent_role, None, 1))
            next_parent = node["role"]
        for child in node["children"]:
            walk(child, next_parent)

    walk(tree["root"], "root")
    return out


```

**Paso 4 — Verificar que pasa:**

```bash
python -m unittest discover -s .claude/skills/clone-diff/tests -p test_treediff.py
```

Output esperado:

```
Ran 5 tests
OK
```

**Paso 5 — Commit:**

```bash
git add .claude/skills/clone-diff/tests/test_treediff.py .claude/skills/clone-diff/scripts/treediff.py
git commit -m "feat(clone-diff): load and flatten ui trees" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```


### Tarea 11: treediff: emparejamiento y scores

**Archivos:** agregar al final de `.claude/skills/clone-diff/tests/test_treediff.py`; agregar al final de `.claude/skills/clone-diff/scripts/treediff.py`

**Paso 1 — Test que falla** (Agregar al final de `test_treediff.py`):

```python
class CompareTest(unittest.TestCase):
    def test_identical_trees_score_100(self):
        result = treediff.compare(form_screen(), form_screen())
        self.assertEqual((result["interactive_score"], result["structure_score"]), (100, 100))
        self.assertEqual(result["missing"], [])

    def test_missing_button_is_reported_and_lowers_score(self):
        clone = form_screen()
        del clone["root"]["children"][2]
        result = treediff.compare(form_screen(), clone)
        self.assertEqual([m["label"] for m in result["missing"]], ["Cancelar"])
        self.assertEqual(result["interactive_score"], 75)
        self.assertEqual(result["structure_score"], 77)

    def test_reordered_siblings_still_match(self):
        clone = form_screen()
        kids = clone["root"]["children"]
        kids[1]["bounds"], kids[2]["bounds"] = kids[2]["bounds"], kids[1]["bounds"]
        kids[1], kids[2] = kids[2], kids[1]
        result = treediff.compare(form_screen(), clone)
        self.assertEqual(result["interactive_score"], 100)

    def test_list_size_difference_is_not_missing(self):
        result = treediff.compare(list_screen(3), list_screen(20))
        self.assertEqual(result["missing"], [])
        self.assertEqual(result["interactive_score"], 100)

    def test_changed_label_with_same_id_is_text_changed(self):
        clone = form_screen()
        clone["root"]["children"][1]["name"] = "Aplicar"
        result = treediff.compare(form_screen(), clone)
        self.assertEqual(result["interactive_score"], 100)
        self.assertEqual(result["text_changed"],
                         [{"role": "button", "original": "Guardar", "clone": "Aplicar"}])

    def test_label_match_ignores_case_and_accents(self):
        orig = tree([node("button", "Edición", bounds=(0.1, 0.1, 0.1, 0.1))])
        clone = tree([node("button", "edicion", bounds=(0.8, 0.8, 0.1, 0.1))])
        self.assertEqual(treediff.compare(orig, clone)["interactive_score"], 100)

    def test_ignore_text_disables_label_pass(self):
        orig = tree([node("button", "Ayuda", bounds=(0.1, 0.1, 0.1, 0.1))])
        clone = tree([node("button", "Ayuda", bounds=(0.8, 0.8, 0.1, 0.1))])
        self.assertEqual(treediff.compare(orig, clone, use_text=False)["interactive_score"], 0)
        self.assertEqual(treediff.compare(orig, clone, use_text=True)["interactive_score"], 100)

    def test_far_match_is_reported_as_moved(self):
        orig = tree([node("button", "Ayuda", bounds=(0.1, 0.1, 0.1, 0.1))])
        clone = tree([node("button", "Ayuda", bounds=(0.8, 0.8, 0.1, 0.1))])
        moved = treediff.compare(orig, clone)["moved"]
        self.assertEqual(moved, [{"role": "button", "label": "Ayuda", "distance": 0.99}])

    def test_quality_none_is_skipped(self):
        result = treediff.compare(form_screen(), tree([], quality="none"))
        self.assertEqual(result["status"], "skipped")
        self.assertIsNone(result["interactive_score"])

    def test_screen_without_interactive_has_null_interactive_score(self):
        only_text = tree([node("text", "Hola")])
        result = treediff.compare(only_text, copy.deepcopy(only_text))
        self.assertIsNone(result["interactive_score"])
        self.assertEqual(result["structure_score"], 100)

    def test_extra_clone_nodes_do_not_penalize(self):
        clone = form_screen()
        clone["root"]["children"].append(node("button", "Nuevo", bounds=(0.4, 0.4, 0.1, 0.1)))
        result = treediff.compare(form_screen(), clone)
        self.assertEqual(result["interactive_score"], 100)
        self.assertEqual([e["label"] for e in result["extra"]], ["Nuevo"])


```

**Paso 2 — Verificar que falla:**

```bash
python -m unittest discover -s .claude/skills/clone-diff/tests -p test_treediff.py
```

Output esperado (lineas clave):

```
AttributeError: module 'treediff' has no attribute 'compare'
Ran 16 tests
FAILED (errors=11)
```

**Paso 3 — Implementar** (Agregar al final de `treediff.py`):

```python
def _distance(a, b):
    return math.hypot(a["center"][0] - b["center"][0], a["center"][1] - b["center"][1])


def match(orig, clone, use_text=True):
    """Devuelve {indice_original: (indice_clon, pasada)}."""

    def same_item(o, c):
        return o["item_sig"] is not None and o["item_sig"] == c["item_sig"]

    def same_id(o, c):
        return bool(o["id"]) and o["id"] == c["id"]

    def same_label(o, c):
        return use_text and bool(o["label"]) and o["label"] == c["label"]

    def near(o, c):
        return _distance(o, c) < POSITION_MATCH and o["parent_role"] == c["parent_role"]

    pairs = {}
    used = set()
    for name, test in (("item", same_item), ("id", same_id), ("label", same_label),
                       ("position", near)):
        candidates = []
        for i, o in enumerate(orig):
            if i in pairs:
                continue
            for j, c in enumerate(clone):
                if j in used or c["role"] != o["role"]:
                    continue
                if test(o, c):
                    candidates.append((_distance(o, c), i, j))
        candidates.sort()
        for _, i, j in candidates:
            if i not in pairs and j not in used:
                pairs[i] = (j, name)
                used.add(j)
    return pairs


def _score(nodes, matched_idx, roles):
    total = sum(WEIGHTS[n["role"]] for n in nodes if n["role"] in roles)
    if total == 0:
        return None
    got = sum(WEIGHTS[nodes[i]["role"]] for i in matched_idx if nodes[i]["role"] in roles)
    return int(round(100 * got / total))


def _describe(node):
    return {"role": node["role"], "label": node["raw_label"], "id": node["id"],
            "bounds": node["bounds"]}


def compare(orig_tree, clone_tree, use_text=True):
    screen = orig_tree.get("screen", "")
    for which, tree in (("original", orig_tree), ("clon", clone_tree)):
        if tree.get("tree_quality") == "none":
            return {"screen": screen, "status": "skipped",
                    "reason": "tree_quality none en %s" % which,
                    "interactive_score": None, "structure_score": None,
                    "counts": {}, "missing": [], "extra": [], "text_changed": [], "moved": []}
    orig = flatten(orig_tree)
    clone = flatten(clone_tree)
    pairs = match(orig, clone, use_text)
    matched_clone = {j for j, _ in pairs.values()}

    missing = [_describe(n) for i, n in enumerate(orig) if i not in pairs]
    missing.sort(key=lambda d: (d["role"] not in INTERACTIVE, d["bounds"][1], d["bounds"][0]))
    extra = [_describe(n) for j, n in enumerate(clone) if j not in matched_clone]
    text_changed = []
    moved = []
    for i, (j, how) in sorted(pairs.items()):
        o, c = orig[i], clone[j]
        if how in ("id", "position") and o["label"] != c["label"]:
            text_changed.append({"role": o["role"], "original": o["raw_label"],
                                 "clone": c["raw_label"]})
        dist = _distance(o, c)
        if dist > MOVED:
            moved.append({"role": o["role"], "label": o["raw_label"],
                          "distance": round(dist, 2)})

    return {
        "screen": screen,
        "status": "ok",
        "interactive_score": _score(orig, pairs, INTERACTIVE),
        "structure_score": _score(orig, pairs, INTERACTIVE | CONTENT),
        "counts": {"original": len(orig), "clone": len(clone), "matched": len(pairs)},
        "missing": missing,
        "extra": extra,
        "text_changed": text_changed,
        "moved": moved,
    }


```

**Paso 4 — Verificar que pasa:**

```bash
python -m unittest discover -s .claude/skills/clone-diff/tests -p test_treediff.py
```

Output esperado:

```
Ran 16 tests
OK
```

**Paso 5 — Commit:**

```bash
git add .claude/skills/clone-diff/tests/test_treediff.py .claude/skills/clone-diff/scripts/treediff.py
git commit -m "feat(clone-diff): match nodes and score screens" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```


### Tarea 12: treediff: salida de texto y CLI

**Archivos:** agregar al final de `.claude/skills/clone-diff/tests/test_treediff.py`; agregar al final de `.claude/skills/clone-diff/scripts/treediff.py`

**Paso 1 — Test que falla** (Agregar al final de `test_treediff.py`):

```python
class CliTest(unittest.TestCase):
    def write(self, tmp, name, data):
        path = os.path.join(tmp, name)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(data, fh)
        return path

    def test_json_output_has_scores(self):
        with tempfile.TemporaryDirectory() as tmp:
            a = self.write(tmp, "a.json", form_screen())
            buf = io.StringIO()
            with redirect_stdout(buf):
                code = treediff.main([a, a, "--json"])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(buf.getvalue())["interactive_score"], 100)

    def test_text_output_first_line(self):
        clone = form_screen()
        del clone["root"]["children"][2]
        with tempfile.TemporaryDirectory() as tmp:
            a = self.write(tmp, "a.json", form_screen())
            b = self.write(tmp, "b.json", clone)
            buf = io.StringIO()
            with redirect_stdout(buf):
                treediff.main([a, b])
        lines = buf.getvalue().splitlines()
        self.assertEqual(lines[0], "S01: interactivo 75, estructura 77 "
                                   "(original 5 nodos, clon 4, emparejados 4)")
        self.assertEqual(lines[1:3], ["Faltan (1):", '  button "Cancelar" #cancel [0.75,0.93]'])

    def test_out_writes_utf8_json_and_prints_text(self):
        orig = tree([node("menuitem", "Edición", bounds=(0.1, 0.1, 0.1, 0.1))])
        with tempfile.TemporaryDirectory() as tmp:
            a = self.write(tmp, "a.json", orig)
            out_path = os.path.join(tmp, "diff.json")
            buf = io.StringIO()
            with redirect_stdout(buf):
                code = treediff.main([a, a, "--out", out_path])
            with open(out_path, encoding="utf-8") as fh:
                written = json.load(fh)
        self.assertEqual(code, 0)
        self.assertEqual(written["interactive_score"], 100)
        self.assertTrue(buf.getvalue().startswith("S01: interactivo 100"))

    def test_wrong_schema_exits_two(self):
        with tempfile.TemporaryDirectory() as tmp:
            a = self.write(tmp, "a.json", form_screen())
            b = self.write(tmp, "b.json", {"schema": 2})
            with redirect_stderr(io.StringIO()):
                self.assertEqual(treediff.main([a, b]), 2)

    def test_missing_file_exits_two(self):
        with redirect_stderr(io.StringIO()):
            self.assertEqual(treediff.main(["no-existe.json", "tampoco.json"]), 2)


if __name__ == "__main__":
    unittest.main()
```

**Paso 2 — Verificar que falla:**

```bash
python -m unittest discover -s .claude/skills/clone-diff/tests -p test_treediff.py
```

Output esperado (lineas clave):

```
AttributeError: module 'treediff' has no attribute 'main'
Ran 21 tests
FAILED (errors=5)
```

**Paso 3 — Implementar** (Agregar al final de `treediff.py`):

```python
def _fmt_score(value):
    return "-" if value is None else str(value)


def render_text(result):
    if result["status"] == "skipped":
        return "%s: omitida (%s). Se evalua solo por features." % (result["screen"],
                                                                   result["reason"])
    c = result["counts"]
    lines = ["%s: interactivo %s, estructura %s (original %d nodos, clon %d, emparejados %d)"
             % (result["screen"], _fmt_score(result["interactive_score"]),
                _fmt_score(result["structure_score"]), c["original"], c["clone"], c["matched"])]

    def section(title, items, fmt):
        if items:
            lines.append("%s (%d):" % (title, len(items)))
            lines.extend("  " + fmt(item) for item in items)

    def node_fmt(d):
        x, y, w, h = d["bounds"]
        label = ' "%s"' % d["label"] if d["label"] else ""
        ident = " #%s" % d["id"] if d["id"] else ""
        return "%s%s%s [%.2f,%.2f]" % (d["role"], label, ident, x + w / 2, y + h / 2)

    section("Faltan", result["missing"], node_fmt)
    section("Extra en el clon", result["extra"], node_fmt)
    section("Texto distinto", result["text_changed"],
            lambda d: '%s "%s" -> "%s"' % (d["role"], d["original"], d["clone"]))
    section("Movidos", result["moved"],
            lambda d: '%s "%s" (%.2f)' % (d["role"], d["label"], d["distance"]))
    return "\n".join(lines)


def safe_stdout():
    """Evita UnicodeEncodeError en consolas cp1252: reemplaza lo no imprimible."""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="replace")


def main(argv=None):
    safe_stdout()
    ap = argparse.ArgumentParser(description="Diff de arboles de UI normalizados")
    ap.add_argument("original")
    ap.add_argument("clone")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--ignore-text", action="store_true")
    ap.add_argument("--out", help="escribe el resultado JSON en este archivo (UTF-8)")
    args = ap.parse_args(argv)
    try:
        orig = load_tree(args.original)
        clone = load_tree(args.clone)
    except DiffError as exc:
        print("treediff: %s" % exc, file=sys.stderr)
        return 2
    result = compare(orig, clone, use_text=not args.ignore_text)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump(result, fh, ensure_ascii=False, indent=1)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=1))
    else:
        print(render_text(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

**Paso 4 — Verificar que pasa:**

```bash
python -m unittest discover -s .claude/skills/clone-diff/tests -p test_treediff.py
```

Output esperado:

```
Ran 21 tests
OK
```

**Paso 5 — Commit:**

```bash
git add .claude/skills/clone-diff/tests/test_treediff.py .claude/skills/clone-diff/scripts/treediff.py
git commit -m "feat(clone-diff): treediff command line" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```


---

## Fase 5: parity.py

### Tarea 13: parity: carga y validacion de CSV y diffs

**Archivos:** crear `.claude/skills/clone-diff/tests/test_parity.py`; crear `.claude/skills/clone-diff/scripts/parity.py`

**Paso 1 — Test que falla** (Crear `test_parity.py`):

```python
import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "scripts"))

import parity  # noqa: E402

HEADER = "id,feature,area,prioridad,pantallas,estado,notas\n"
MIXED = (HEADER +
         "K01,Crear nota,notas,must,S01,si,\n"
         "K02,Buscar,notas,must,S01,parcial,falta filtro\n"
         "K03,Etiquetas,organizar,should,S02,si,\n"
         "K04,Exportar,datos,should,S03,no,\n"
         "K05,Temas,ajustes,could,S04,parcial,\n"
         "K06,Sincronizar con su nube,datos,skip,,no,red del original\n"
         "K07,Atajos de teclado,notas,extra,,si,\n")
ALL_MUST_DONE = (HEADER +
                 "K01,Crear nota,notas,must,S01,si,\n"
                 "K02,Buscar,notas,must,S01,si,\n"
                 "K03,Etiquetas,organizar,should,S02,%s,\n")


class Workspace:
    def __init__(self, features, diffs=(), flows=None):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = self.tmp.name
        with open(os.path.join(self.path, "features.csv"), "w", encoding="utf-8") as fh:
            fh.write(features)
        os.makedirs(os.path.join(self.path, "diffs"))
        for d in diffs:
            with open(os.path.join(self.path, "diffs", d["screen"] + ".json"), "w",
                      encoding="utf-8") as fh:
                json.dump(d, fh)
        if flows is not None:
            with open(os.path.join(self.path, "flows.csv"), "w", encoding="utf-8") as fh:
                fh.write("id,nombre,pantallas,pasos_original,pasos_clon\n" + flows)

    def __enter__(self):
        return self.path

    def __exit__(self, *exc):
        self.tmp.cleanup()


def diff(screen, score, missing=0):
    return {"screen": screen, "status": "ok", "interactive_score": score,
            "missing": [{}] * missing}


def run(args):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = parity.main(args)
    return code, out.getvalue(), err.getvalue()


class LoadTest(unittest.TestCase):
    def test_invalid_priority_raises_naming_row(self):
        with Workspace(HEADER + "K01,Crear,notas,urgente,S01,si,\n") as ws:
            with self.assertRaisesRegex(parity.InputError, "fila 2: prioridad 'urgente' invalida"):
                parity.load_features(os.path.join(ws, "features.csv"))

    def test_invalid_state_raises(self):
        with Workspace(HEADER + "K01,Crear,notas,must,S01,hecho,\n") as ws:
            with self.assertRaisesRegex(parity.InputError, "estado 'hecho' invalido"):
                parity.load_features(os.path.join(ws, "features.csv"))

    def test_missing_column_raises(self):
        with Workspace("id,feature,area\nK01,Crear,notas\n") as ws:
            with self.assertRaisesRegex(parity.InputError, "faltan columnas"):
                parity.load_features(os.path.join(ws, "features.csv"))

    def test_flow_delta_and_unmeasured(self):
        flows = "F01,Crear nota,S01>S02,5,4\nF02,Buscar,S01>S03,3,\n"
        with Workspace(ALL_MUST_DONE % "si", flows=flows) as ws:
            loaded = parity.load_flows(os.path.join(ws, "flows.csv"))
        self.assertEqual([(f["id"], f["delta"]) for f in loaded], [("F01", -1), ("F02", None)])

    def test_non_numeric_steps_raise(self):
        with Workspace(ALL_MUST_DONE % "si", flows="F01,Crear,S01,cinco,\n") as ws:
            with self.assertRaisesRegex(parity.InputError, "flows.csv fila 2"):
                parity.load_flows(os.path.join(ws, "flows.csv"))

    def test_missing_flows_file_is_empty(self):
        self.assertEqual(parity.load_flows(os.path.join("no", "existe.csv")), [])

    def test_diffs_are_loaded_in_name_order(self):
        with Workspace(ALL_MUST_DONE % "si", [diff("S02", 90), diff("S01", 80)]) as ws:
            loaded = parity.load_diffs(os.path.join(ws, "diffs"))
        self.assertEqual([d["screen"] for d in loaded], ["S01", "S02"])


```

**Paso 2 — Verificar que falla:**

```bash
python -m unittest discover -s .claude/skills/clone-diff/tests -p test_parity.py
```

Output esperado (lineas clave):

```
ImportError: Failed to import test module: test_parity
ModuleNotFoundError: No module named 'parity'
Ran 1 test
FAILED (errors=1)
```

**Paso 3 — Implementar** (Crear `parity.py`):

```python
#!/usr/bin/env python3
"""
parity.py — Reporte de paridad del clon contra el original. Zero dependencias.

Lee clone/features.csv, clone/flows.csv (opcional) y clone/diffs/*.json
(salidas de treediff.py --json) y calcula feature score, score por pantalla,
deltas de pasos por flujo y un veredicto: incompleto, usable o completo.

Uso:
  python parity.py clone/ [--json | --markdown] [--out ARCHIVO]

Exit: 0 usable o completo, 1 incompleto, 2 error de entrada.
"""

import argparse
import csv
import glob
import json
import os
import sys

PRIORITY_WEIGHTS = {"must": 3, "should": 2, "could": 1}
PRIORITIES = set(PRIORITY_WEIGHTS) | {"skip", "extra"}
STATE_VALUES = {"si": 1.0, "parcial": 0.5, "no": 0.0}
FEATURE_COLUMNS = ["id", "feature", "area", "prioridad", "pantallas", "estado", "notas"]
FLOW_COLUMNS = ["id", "nombre", "pantallas", "pasos_original", "pasos_clon"]

USABLE_SCREEN = 70
COMPLETE_SCREEN = 85
COMPLETE_FEATURES = 90


class InputError(Exception):
    """Archivo de entrada ausente o mal formado."""


def _read_csv(path, columns):
    with open(path, newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        missing = [c for c in columns if c not in (reader.fieldnames or [])]
        if missing:
            raise InputError("%s: faltan columnas %s" % (path, ", ".join(missing)))
        return list(reader)


def load_features(path):
    if not os.path.isfile(path):
        raise InputError("no existe %s" % path)
    rows = _read_csv(path, FEATURE_COLUMNS)
    for line, row in enumerate(rows, start=2):
        row["prioridad"] = row["prioridad"].strip().lower()
        row["estado"] = row["estado"].strip().lower()
        if row["prioridad"] not in PRIORITIES:
            raise InputError("features.csv fila %d: prioridad '%s' invalida" % (line, row["prioridad"]))
        if row["prioridad"] in PRIORITY_WEIGHTS and row["estado"] not in STATE_VALUES:
            raise InputError("features.csv fila %d: estado '%s' invalido" % (line, row["estado"]))
    return rows


def load_flows(path):
    if not os.path.isfile(path):
        return []
    flows = []
    for line, row in enumerate(_read_csv(path, FLOW_COLUMNS), start=2):
        try:
            original = int(row["pasos_original"])
            clone = int(row["pasos_clon"]) if row["pasos_clon"].strip() else None
        except ValueError:
            raise InputError("flows.csv fila %d: pasos no numericos" % line)
        flows.append({"id": row["id"], "nombre": row["nombre"], "original": original,
                      "clone": clone, "delta": None if clone is None else clone - original})
    return flows


def load_diffs(directory):
    diffs = []
    for path in sorted(glob.glob(os.path.join(directory, "*.json"))):
        try:
            with open(path, encoding="utf-8") as fh:
                diffs.append(json.load(fh))
        except (OSError, ValueError) as exc:
            raise InputError("no puedo leer %s: %s" % (path, exc))
    return diffs


```

**Paso 4 — Verificar que pasa:**

```bash
python -m unittest discover -s .claude/skills/clone-diff/tests -p test_parity.py
```

Output esperado:

```
Ran 7 tests
OK
```

**Paso 5 — Commit:**

```bash
git add .claude/skills/clone-diff/tests/test_parity.py .claude/skills/clone-diff/scripts/parity.py
git commit -m "feat(clone-diff): load and validate parity inputs" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```


### Tarea 14: parity: scores, pendientes y veredicto

**Archivos:** agregar al final de `.claude/skills/clone-diff/tests/test_parity.py`; agregar al final de `.claude/skills/clone-diff/scripts/parity.py`

**Paso 1 — Test que falla** (Agregar al final de `test_parity.py`):

```python
class ScoreTest(unittest.TestCase):
    def test_weighted_score_counts_partial_as_half_and_skips_skip_and_extra(self):
        with Workspace(MIXED) as ws:
            report = parity.build_report(ws)
        self.assertEqual(report["feature_score"], 64)
        self.assertEqual((report["must_done"], report["must_total"]), (1, 2))

    def test_pending_is_ordered_must_should_could(self):
        with Workspace(MIXED) as ws:
            report = parity.build_report(ws)
        self.assertEqual([p["id"] for p in report["pending"]], ["K02", "K04", "K05"])

    def test_areas_weakest_first(self):
        with Workspace(MIXED) as ws:
            report = parity.build_report(ws)
        self.assertEqual(report["areas"][0], ("datos", 0))


class VerdictTest(unittest.TestCase):
    def test_missing_must_is_incompleto(self):
        with Workspace(MIXED) as ws:
            self.assertEqual(parity.build_report(ws)["verdict"], "incompleto")

    def test_screen_below_70_is_incompleto(self):
        with Workspace(ALL_MUST_DONE % "si", [diff("S01", 69)]) as ws:
            self.assertEqual(parity.build_report(ws)["verdict"], "incompleto")

    def test_usable_at_threshold_70(self):
        with Workspace(ALL_MUST_DONE % "si", [diff("S01", 70)]) as ws:
            self.assertEqual(parity.build_report(ws)["verdict"], "usable")

    def test_completo_needs_features_90_and_screens_85(self):
        with Workspace(ALL_MUST_DONE % "si", [diff("S01", 85), diff("S02", 100)]) as ws:
            self.assertEqual(parity.build_report(ws)["verdict"], "completo")

    def test_features_below_90_is_only_usable(self):
        with Workspace(ALL_MUST_DONE % "no", [diff("S01", 100)]) as ws:
            report = parity.build_report(ws)
        self.assertEqual(report["feature_score"], 75)
        self.assertEqual(report["verdict"], "usable")

    def test_skipped_screens_are_listed_as_features_only(self):
        skipped = {"screen": "S09", "status": "skipped", "interactive_score": None}
        with Workspace(ALL_MUST_DONE % "si", [skipped]) as ws:
            report = parity.build_report(ws)
        self.assertEqual(report["screens_features_only"], ["S09"])
        self.assertEqual(report["verdict"], "completo")


```

**Paso 2 — Verificar que falla:**

```bash
python -m unittest discover -s .claude/skills/clone-diff/tests -p test_parity.py
```

Output esperado (lineas clave):

```
AttributeError: module 'parity' has no attribute 'build_report'
Ran 16 tests
FAILED (errors=9)
```

**Paso 3 — Implementar** (Agregar al final de `parity.py`):

```python
def feature_score(rows):
    scored = [r for r in rows if r["prioridad"] in PRIORITY_WEIGHTS]
    total = sum(PRIORITY_WEIGHTS[r["prioridad"]] for r in scored)
    if total == 0:
        return None
    got = sum(PRIORITY_WEIGHTS[r["prioridad"]] * STATE_VALUES[r["estado"]] for r in scored)
    return int(round(100 * got / total))


def area_scores(rows):
    areas = {}
    for row in rows:
        if row["prioridad"] in PRIORITY_WEIGHTS:
            areas.setdefault(row["area"], []).append(row)
    return {area: feature_score(items) for area, items in areas.items()}


def pending_features(rows):
    by_area = area_scores(rows)
    order = {"must": 0, "should": 1, "could": 2}
    pending = [r for r in rows if r["prioridad"] in order and r["estado"] != "si"]
    pending.sort(key=lambda r: (order[r["prioridad"]], by_area[r["area"]], r["area"], r["id"]))
    return [{"id": r["id"], "feature": r["feature"], "area": r["area"],
             "prioridad": r["prioridad"], "estado": r["estado"]} for r in pending]


def verdict(must_missing, features, screen_scores):
    if must_missing:
        return "incompleto"
    if any(score < USABLE_SCREEN for score in screen_scores):
        return "incompleto"
    if (features is not None and features >= COMPLETE_FEATURES
            and all(score >= COMPLETE_SCREEN for score in screen_scores)):
        return "completo"
    return "usable"


def build_report(clone_dir):
    rows = load_features(os.path.join(clone_dir, "features.csv"))
    flows = load_flows(os.path.join(clone_dir, "flows.csv"))
    diffs = load_diffs(os.path.join(clone_dir, "diffs"))
    screens = []
    skipped = []
    for d in diffs:
        if d.get("status") == "skipped" or d.get("interactive_score") is None:
            skipped.append(d.get("screen", "?"))
        else:
            screens.append({"screen": d.get("screen", "?"), "score": d["interactive_score"],
                            "missing": len(d.get("missing", []))})
    screens.sort(key=lambda s: (s["score"], s["screen"]))
    pending = pending_features(rows)
    must_missing = [p for p in pending if p["prioridad"] == "must"]
    features = feature_score(rows)
    return {
        "verdict": verdict(must_missing, features, [s["score"] for s in screens]),
        "feature_score": features,
        "must_done": sum(1 for r in rows if r["prioridad"] == "must" and r["estado"] == "si"),
        "must_total": sum(1 for r in rows if r["prioridad"] == "must"),
        "areas": sorted(area_scores(rows).items(), key=lambda kv: (kv[1], kv[0])),
        "screens": screens,
        "screens_features_only": skipped,
        "flows": flows,
        "pending": pending,
    }


```

**Paso 4 — Verificar que pasa:**

```bash
python -m unittest discover -s .claude/skills/clone-diff/tests -p test_parity.py
```

Output esperado:

```
Ran 16 tests
OK
```

**Paso 5 — Commit:**

```bash
git add .claude/skills/clone-diff/tests/test_parity.py .claude/skills/clone-diff/scripts/parity.py
git commit -m "feat(clone-diff): parity scores and verdict" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```


### Tarea 15: parity: reportes y CLI

**Archivos:** agregar al final de `.claude/skills/clone-diff/tests/test_parity.py`; agregar al final de `.claude/skills/clone-diff/scripts/parity.py`

**Paso 1 — Test que falla** (Agregar al final de `test_parity.py`):

```python
class CliTest(unittest.TestCase):
    def test_incompleto_exits_one_with_text_report(self):
        with Workspace(MIXED) as ws:
            code, out, _ = run([ws])
        self.assertEqual(code, 1)
        self.assertEqual(out.splitlines()[:2], ["Veredicto: incompleto", "Features: 64 (must 1/2)"])

    def test_usable_exits_zero(self):
        with Workspace(ALL_MUST_DONE % "si", [diff("S01", 70)]) as ws:
            code, out, _ = run([ws])
        self.assertEqual(code, 0)
        self.assertTrue(out.startswith("Veredicto: usable"))

    def test_invalid_input_exits_two_with_message(self):
        with Workspace(HEADER + "K01,Crear,notas,urgente,S01,si,\n") as ws:
            code, _, err = run([ws])
        self.assertEqual(code, 2)
        self.assertIn("fila 2: prioridad 'urgente' invalida", err)

    def test_missing_features_file_exits_two(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, _, err = run([tmp])
        self.assertEqual(code, 2)
        self.assertIn("no existe", err)

    def test_markdown_output_has_verdict_and_screens(self):
        with Workspace(ALL_MUST_DONE % "si", [diff("S01", 90)]) as ws:
            code, out, _ = run([ws, "--markdown"])
        self.assertEqual(code, 0)
        self.assertIn("**Veredicto:** completo", out)
        self.assertIn("| S01 | 90 | 0 |", out)

    def test_out_writes_report_to_utf8_file(self):
        features = HEADER + "K01,Edición rápida,notas,must,S01,si,\n"
        with Workspace(features) as ws:
            target = os.path.join(ws, "parity.md")
            code, out, _ = run([ws, "--markdown", "--out", target])
            with open(target, encoding="utf-8") as fh:
                text = fh.read()
        self.assertEqual(code, 0)
        self.assertIn("**Veredicto:** completo", text)
        self.assertEqual(out.strip(), "ok: %s (veredicto completo)" % target)

    def test_json_output_is_parseable(self):
        with Workspace(ALL_MUST_DONE % "si") as ws:
            code, out, _ = run([ws, "--json"])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)["verdict"], "completo")


if __name__ == "__main__":
    unittest.main()
```

**Paso 2 — Verificar que falla:**

```bash
python -m unittest discover -s .claude/skills/clone-diff/tests -p test_parity.py
```

Output esperado (lineas clave):

```
AttributeError: module 'parity' has no attribute 'main'
Ran 23 tests
FAILED (errors=7)
```

**Paso 3 — Implementar** (Agregar al final de `parity.py`):

```python
def _score(value):
    return "-" if value is None else str(value)


def render_text(report):
    lines = ["Veredicto: %s" % report["verdict"],
             "Features: %s (must %d/%d)" % (_score(report["feature_score"]),
                                            report["must_done"], report["must_total"])]
    if report["areas"]:
        lines.append("Areas: " + ", ".join("%s %s" % (a, _score(s)) for a, s in report["areas"]))
    for s in report["screens"]:
        lines.append("Pantalla %s: %d (%d faltantes)" % (s["screen"], s["score"], s["missing"]))
    if report["screens_features_only"]:
        lines.append("Solo features: " + ", ".join(report["screens_features_only"]))
    for f in report["flows"]:
        if f["clone"] is None:
            lines.append("Flujo %s: original %d pasos, clon sin medir" % (f["id"], f["original"]))
        else:
            lines.append("Flujo %s: original %d, clon %d (%+d)" % (f["id"], f["original"],
                                                                  f["clone"], f["delta"]))
    if report["pending"]:
        lines.append("Pendiente:")
        lines.extend("  %s %s [%s, %s] %s" % (p["id"], p["prioridad"], p["area"], p["estado"],
                                              p["feature"]) for p in report["pending"])
    return "\n".join(lines)


def render_markdown(report):
    out = ["# Paridad", "",
           "**Veredicto:** %s" % report["verdict"], "",
           "| metrica | valor |", "| --- | --- |",
           "| feature score | %s |" % _score(report["feature_score"]),
           "| must hechos | %d/%d |" % (report["must_done"], report["must_total"]), ""]
    if report["areas"]:
        out += ["## Areas (mas debil primero)", "", "| area | score |", "| --- | --- |"]
        out += ["| %s | %s |" % (a, _score(s)) for a, s in report["areas"]]
        out.append("")
    if report["screens"] or report["screens_features_only"]:
        out += ["## Pantallas", "", "| pantalla | score interactivo | faltantes |",
                "| --- | --- | --- |"]
        out += ["| %s | %d | %d |" % (s["screen"], s["score"], s["missing"])
                for s in report["screens"]]
        out += ["| %s | solo features | - |" % s for s in report["screens_features_only"]]
        out.append("")
    if report["flows"]:
        out += ["## Flujos", "", "| flujo | original | clon | delta |", "| --- | --- | --- | --- |"]
        for f in report["flows"]:
            clone = "-" if f["clone"] is None else str(f["clone"])
            delta = "-" if f["delta"] is None else "%+d" % f["delta"]
            out.append("| %s %s | %d | %s | %s |" % (f["id"], f["nombre"], f["original"],
                                                     clone, delta))
        out.append("")
    if report["pending"]:
        out += ["## Pendiente (orden de construccion)", ""]
        out += ["- %s **%s** %s (%s, %s)" % (p["id"], p["prioridad"], p["feature"], p["area"],
                                             p["estado"]) for p in report["pending"]]
        out.append("")
    return "\n".join(out)


def safe_stdout():
    """Evita UnicodeEncodeError en consolas cp1252: reemplaza lo no imprimible."""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="replace")


def main(argv=None):
    safe_stdout()
    ap = argparse.ArgumentParser(description="Reporte de paridad del clone pack")
    ap.add_argument("clone_dir")
    fmt = ap.add_mutually_exclusive_group()
    fmt.add_argument("--json", action="store_true")
    fmt.add_argument("--markdown", action="store_true")
    ap.add_argument("--out", help="escribe el reporte en este archivo (UTF-8)")
    args = ap.parse_args(argv)
    try:
        report = build_report(args.clone_dir)
    except InputError as exc:
        print("parity: %s" % exc, file=sys.stderr)
        return 2
    if args.json:
        output = json.dumps(report, ensure_ascii=False, indent=1)
    elif args.markdown:
        output = render_markdown(report)
    else:
        output = render_text(report)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(output + "\n")
        print("ok: %s (veredicto %s)" % (args.out, report["verdict"]))
    else:
        print(output)
    return 1 if report["verdict"] == "incompleto" else 0


if __name__ == "__main__":
    sys.exit(main())
```

**Paso 4 — Verificar que pasa:**

```bash
python -m unittest discover -s .claude/skills/clone-diff/tests -p test_parity.py
```

Output esperado:

```
Ran 23 tests
OK
```

**Paso 5 — Commit:**

```bash
git add .claude/skills/clone-diff/tests/test_parity.py .claude/skills/clone-diff/scripts/parity.py
git commit -m "feat(clone-diff): parity reports and command line" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```


---

## Fase 6: skills y referencias

Cada SKILL.md se valida con este chequeo de frontmatter (se usa en las
tareas 16, 19, 20 y 21):

```bash
python -c "import sys;t=open(sys.argv[1],encoding='utf-8').read();fm=t.split('---')[1];req=['name:','description:','when_to_use:','argument-hint:','disable-model-invocation: true','allowed-tools:'];miss=[r for r in req if r not in fm];print('falta: '+', '.join(miss) if miss else 'frontmatter ok');sys.exit(1 if miss else 0)" <ruta al SKILL.md>
```

### Tarea 16: SKILL.md de clone-recon

**Archivos:** crear `.claude/skills/clone-recon/SKILL.md`

**Paso 1 — Verificacion que falla** (el archivo aun no existe):

```bash
python -c "import sys;t=open(sys.argv[1],encoding='utf-8').read();fm=t.split('---')[1];req=['name:','description:','when_to_use:','argument-hint:','disable-model-invocation: true','allowed-tools:'];miss=[r for r in req if r not in fm];print('falta: '+', '.join(miss) if miss else 'frontmatter ok');sys.exit(1 if miss else 0)" .claude/skills/clone-recon/SKILL.md
```

Output esperado (ultima linea):

```
FileNotFoundError: [Errno 2] No such file or directory: '.claude/skills/clone-recon/SKILL.md'
```

**Paso 2 — Crear `.claude/skills/clone-recon/SKILL.md`:**

````markdown
---
name: clone-recon
description: >
  Desarma una app Android o de escritorio Windows instalada por el usuario en
  pantallas, estados, flujos, componentes, modelo de datos inferido y matriz
  de features, capturando screenshot + arbol de UI normalizado de cada
  pantalla mientras el usuario navega. Primer paso del clone pack.
when_to_use: >
  Cuando el usuario dice "clone-recon", "quiero clonar esta app", "desarma
  esta app", "mapea las pantallas de X", "quiero mi propia version de X".
argument-hint: "[app] [android|windows] [paquete, proceso o titulo de ventana]"
disable-model-invocation: true
allowed-tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Bash(python *)
  - Bash(powershell *)
  - Bash(adb *)
---

# Clone Recon — Desarmar la app original

Todo el pack construye sobre lo que esta skill escribe. Un recon pobre da un
clon pobre: aqui se invierte el tiempo.

Scripts (en Windows usar `python`, en macOS/Linux `python3`):

```
${CLAUDE_SKILL_DIR}/scripts/capture_android.py   captura via adb
${CLAUDE_SKILL_DIR}/scripts/capture_windows.ps1  captura via UI Automation
${CLAUDE_SKILL_DIR}/scripts/uitree.py            normalize | summarize
```

## Reglas

- **Solo observar la UI.** La app instalada por el usuario en su dispositivo
  y fuentes publicas. Nunca descompilar APK/EXE, nunca extraer recursos del
  paquete (iconos, imagenes, fuentes, strings), nunca interceptar trafico de
  red, nunca usar APIs privadas del original.
- **El usuario navega y hace login.** Nunca pedir ni escribir contrasenas.
- **Leer el resumen, no el raw.** Despues de cada captura se lee la salida de
  `summarize` (unas 40 lineas). Nunca cargar `*.raw.xml` o `*.raw.json`.
- **Las capturas son referencia.** No se copian al clon.
- **Los numeros salen de los scripts.** No estimar conteos.

## Salida (en el proyecto del clon)

```
clone/recon.md        plantilla: references/recon-template.md
clone/screens.csv     id,nombre,como_llegar,estados,proposito,estado_clon
clone/flows.csv       id,nombre,pantallas,pasos_original,pasos_clon
clone/features.csv    id,feature,area,prioridad,pantallas,estado,notas
clone/captures/original/<SID>.png|.raw.*|.tree.json
```

`<SID>` es `S03` o `S03@estado`. Ids estables: S01.. pantallas, F01.. flujos,
K01.. features. Prioridad: `must | should | could | skip | extra`. Estado de
feature: `no | parcial | si`. Estado de pantalla: `no | parcial | hecho`.

## Paso 1: alcance

Preguntar una cosa a la vez, o proponer y pedir un si:

1. App y plataforma (android | windows) y como identificarla: paquete
   Android, nombre de proceso, o titulo de ventana.
2. El corte: por defecto el flujo principal que hace util a la app. "Toda la
   app" no es un alcance.
3. Para quien es el clon (el usuario, su equipo).

## Paso 2: entorno

- **Android:** `python ${CLAUDE_SKILL_DIR}/scripts/capture_android.py --help`
  y luego una captura de prueba. Si falla, seguir `references/android-capture.md`.
- **Windows:** captura de prueba con `-Process` o `-Title`. Si falla, seguir
  `references/windows-capture.md`.

Sugerir agregar `clone/captures/` al `.gitignore` del proyecto: las capturas
pueden tener datos personales aunque se redacten.

## Paso 3: fuentes publicas

Tabla en `recon.md` con URL por fila: ficha de Play Store o web oficial,
centro de ayuda, changelog. El centro de ayuda es la lista de features mas
completa que existe; el changelog dice que considera importante el equipo.

## Paso 4: bucle de captura

Por cada pantalla y estado dentro del alcance:

1. Pedir: "Navega a <pantalla> en estado <estado> y dime listo."
2. Capturar:
   - Android:
     `python ${CLAUDE_SKILL_DIR}/scripts/capture_android.py --id S03@vacio --out clone/captures/original`
   - Windows:
     `powershell -NoProfile -ExecutionPolicy Bypass -File ${CLAUDE_SKILL_DIR}/scripts/capture_windows.ps1 -Id S03@vacio -Out clone/captures/original -Process <proceso>`
     y luego
     `python ${CLAUDE_SKILL_DIR}/scripts/uitree.py normalize --from uia clone/captures/original/S03@vacio.raw.json --out clone/captures/original/S03@vacio.tree.json --screen S03@vacio`
     y `python ${CLAUDE_SKILL_DIR}/scripts/uitree.py summarize clone/captures/original/S03@vacio.tree.json`
3. Leer el resumen y el PNG. Registrar la fila en `screens.csv`.
4. Exit 1 de captura (sin arbol o pantalla negra): anotar en la fila que la
   pantalla sera "solo features" y seguir.

Estados minimos a pedir por pantalla: vacio, con datos, error si aplica. Un
estado que no se capturo es un estado que no se construye.

## Paso 5: flujos

Por cada objetivo del usuario dentro del alcance, en `flows.csv`: la
secuencia de pantallas (`S01>S04>S05`) y los pasos del camino feliz (taps,
clicks, teclas de envio). En `recon.md`, los casos edge de cada flujo.

## Paso 6: componentes

Partes de UI repetidas (botones, campos, listas, dialogos, menus): nombre,
variantes, estados, pantallas donde aparecen. Seccion en `recon.md`.

## Paso 7: modelo de datos inferido

Entidades, campos y relaciones, cada uno con evidencia (SIDs, articulos de
ayuda) y confianza: `alta | media | supuesto`. Lo que se adivina se marca
como supuesto.

## Paso 8: features

`features.csv`, una fila por feature con prioridad y SIDs. Lo que no se puede
reconstruir va como `skip` con la razon en `notas`: contenido licenciado, la
red de usuarios, datos del servidor del original, hardware, integraciones
privadas. `estado` empieza en `no`.

## Paso 9: tamano

Pantallas, flujos, entidades y las 3 partes mas dificiles (sincronizacion,
tiempo real, integraciones, offline, multimedia). Tamano: S (un fin de
semana), M (unas semanas), L (un trimestre), XL (re-acotar el corte).

## Cierre

Resumen de 5 lineas: el flujo principal, conteo de pantallas y flujos, las 3
partes dificiles, lo que queda fuera, y siguiente paso: `/clone-arch`.
````

**Paso 3 — Verificar:**

```bash
python -c "import sys;t=open(sys.argv[1],encoding='utf-8').read();fm=t.split('---')[1];req=['name:','description:','when_to_use:','argument-hint:','disable-model-invocation: true','allowed-tools:'];miss=[r for r in req if r not in fm];print('falta: '+', '.join(miss) if miss else 'frontmatter ok');sys.exit(1 if miss else 0)" .claude/skills/clone-recon/SKILL.md
```

Output esperado:

```
frontmatter ok
```

**Paso 4 — Commit:**

```bash
git add .claude/skills/clone-recon/SKILL.md
git commit -m "feat(clone-recon): add skill instructions" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```


### Tarea 17: Plantilla del recon

**Archivos:** crear `.claude/skills/clone-recon/references/recon-template.md`

**Paso 1 — Verificacion que falla** (el archivo aun no existe):

```bash
python -c "import sys;t=open(sys.argv[1],encoding='utf-8').read();miss=[n for n in ['## Pantallas','## Modelo de datos inferido','## Tamano'] if n not in t];print('falta: '+', '.join(miss) if miss else 'contenido ok');sys.exit(1 if miss else 0)" .claude/skills/clone-recon/references/recon-template.md
```

Output esperado (ultima linea):

```
FileNotFoundError: [Errno 2] No such file or directory: '.claude/skills/clone-recon/references/recon-template.md'
```

**Paso 2 — Crear `.claude/skills/clone-recon/references/recon-template.md`:**

````markdown
# Recon: <app> (<android | windows>)

Corte: <lo que se reconstruye>
Para: <quien usa el clon>
Fecha: <AAAA-MM-DD>
Identificador: <paquete | proceso | titulo de ventana>

## Fuentes

| # | fuente | URL | notas |
| --- | --- | --- | --- |
| 1 | app instalada | - | capturas en clone/captures/original/ |

## Flujo principal

<una frase: lo que hace util a la app>

## Pantallas

Ver `screens.csv`. Total: <n> pantallas, <n> estados capturados, <n> solo features.

## Flujos

Ver `flows.csv`. Casos edge por flujo:

- F01 <nombre>: <casos edge>

## Componentes

| componente | variantes | estados | pantallas |
| --- | --- | --- | --- |
| Boton | primario, secundario, icono | normal, deshabilitado, cargando | S01, S03 |

## Modelo de datos inferido

```
<Entidad>  <campos>
           evidencia: <SIDs, articulos de ayuda>
           confianza: alta | media | supuesto
```

Relaciones: <Usuario 1-n Nota, Nota n-n Etiqueta, ...>

## Features

Ver `features.csv`. must: <n>, should: <n>, could: <n>, skip: <n>.

## Fuera de alcance

- <contenido licenciado, red de usuarios, datos del servidor, hardware, ...>

## Tamano

Pantallas <n>, flujos <n>, entidades <n>. Partes dificiles: <3>. Tamano: <S | M | L | XL>.
````

**Paso 3 — Verificar:**

```bash
python -c "import sys;t=open(sys.argv[1],encoding='utf-8').read();miss=[n for n in ['## Pantallas','## Modelo de datos inferido','## Tamano'] if n not in t];print('falta: '+', '.join(miss) if miss else 'contenido ok');sys.exit(1 if miss else 0)" .claude/skills/clone-recon/references/recon-template.md
```

Output esperado:

```
contenido ok
```

**Paso 4 — Commit:**

```bash
git add .claude/skills/clone-recon/references/recon-template.md
git commit -m "docs(clone-recon): recon map template" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```


### Tarea 18: Referencias de captura Android y Windows

**Archivos:** crear `.claude/skills/clone-recon/references/android-capture.md`; crear `.claude/skills/clone-recon/references/windows-capture.md`

**Paso 1 — Verificacion que falla** (el archivo aun no existe):

```bash
python -c "import sys;t=open(sys.argv[1],encoding='utf-8').read();miss=[n for n in ['## Problemas conocidos','FLAG_SECURE'] if n not in t];print('falta: '+', '.join(miss) if miss else 'contenido ok');sys.exit(1 if miss else 0)" .claude/skills/clone-recon/references/android-capture.md
```

Output esperado (ultima linea):

```
FileNotFoundError: [Errno 2] No such file or directory: '.claude/skills/clone-recon/references/android-capture.md'
```

```bash
python -c "import sys;t=open(sys.argv[1],encoding='utf-8').read();miss=[n for n in ['## Problemas conocidos','ApplicationFrameHost'] if n not in t];print('falta: '+', '.join(miss) if miss else 'contenido ok');sys.exit(1 if miss else 0)" .claude/skills/clone-recon/references/windows-capture.md
```

Output esperado (ultima linea):

```
FileNotFoundError: [Errno 2] No such file or directory: '.claude/skills/clone-recon/references/windows-capture.md'
```

**Paso 2 — Crear `.claude/skills/clone-recon/references/android-capture.md`:**

````markdown
# Captura Android

## Requisitos

1. **adb** (Android SDK Platform-Tools). El script lo busca en este orden:
   `--adb`, PATH, `%ANDROID_HOME%\platform-tools`,
   `%LOCALAPPDATA%\Android\Sdk\platform-tools` (donde lo deja Android
   Studio), `~/Android/Sdk/platform-tools`. Si no hay Android Studio, bajar
   Platform-Tools desde developer.android.com/tools/releases/platform-tools y
   pasar la ruta con `--adb`.
2. **Dispositivo con depuracion USB.** Ajustes > Acerca del telefono > tocar 7
   veces "Numero de compilacion". Luego Opciones de desarrollador > Depuracion
   USB. Al conectar, aceptar la huella RSA en el telefono.
3. Verificar: `adb devices` debe listar el dispositivo como `device` (no
   `unauthorized` ni `offline`).

Un emulador de Android Studio sirve igual si la app esta instalada en el.

## Uso

```
python capture_android.py --id S03@vacio --out clone/captures/original [--serial SERIAL]
```

Escribe `S03@vacio.png`, `S03@vacio.raw.xml`, `S03@vacio.tree.json` e imprime
el resumen. Exit 0 ok, 1 captura parcial, 2 error de entorno.

## Problemas conocidos

| sintoma | causa | que hacer |
| --- | --- | --- |
| exit 2 "no encuentro adb" | Platform-Tools no instalado o fuera de las rutas conocidas | instalar o pasar `--adb` |
| exit 2 "hay N dispositivos" | emulador y telefono a la vez | `--serial` con el que corresponda |
| exit 2 "no hay dispositivos" | cable solo de carga, depuracion apagada, RSA sin aceptar | revisar los 3 |
| exit 1 "uiautomator dump fallo" | animacion, video o carga continua en pantalla | pausar el video o esperar a que termine la animacion y repetir |
| exit 1 "un solo color" | la app usa FLAG_SECURE (bancos, pagos) o la pantalla esta apagada | el arbol suele salir bien; la pantalla queda sin screenshot util |
| arbol con pocos nodos | juego, Unity, Flutter sin semantica, canvas propio | `tree_quality` partial o none: la pantalla se evalua solo por features |
| exit 2 "formato de screencap no soportado" | dispositivo con formato de pixel distinto de RGBA_8888 | tomar screenshot manual y guardarlo como `<SID>.png` |

## Que guarda y que no

- Guarda la jerarquia de vistas que Android expone a accesibilidad: clases,
  textos visibles, content-desc, resource-id, bounds y flags.
- No lee memoria, archivos ni red de la app.
- Con `--no-redact` se conservan emails, telefonos y valores de campos. Solo
  usarlo con datos de prueba.
````

**Paso 3 — Crear `.claude/skills/clone-recon/references/windows-capture.md`:**

````markdown
# Captura Windows

## Requisitos

Ninguno extra: Windows PowerShell 5.1 trae UI Automation y System.Drawing.
La ventana debe estar abierta, visible y no minimizada.

## Uso

```
powershell -NoProfile -ExecutionPolicy Bypass -File capture_windows.ps1 -Id S03 -Out clone/captures/original -Process notepad
powershell -NoProfile -ExecutionPolicy Bypass -File capture_windows.ps1 -Id S03 -Out clone/captures/original -Title "Calculadora"
python uitree.py normalize --from uia clone/captures/original/S03.raw.json --out clone/captures/original/S03.tree.json --screen S03
python uitree.py summarize clone/captures/original/S03.tree.json
```

`-Process` es el nombre del proceso sin `.exe` (ver el Administrador de
tareas, pestana Detalles). `-Title` busca ventanas cuyo titulo contenga el
texto. `-MaxDepth` (25 por defecto) limita la profundidad del recorrido.

## Problemas conocidos

| sintoma | causa | que hacer |
| --- | --- | --- |
| "ventana no encontrada" con `-Process` en una app de la Tienda | las apps UWP/WinUI viven dentro de `ApplicationFrameHost.exe` | usar `-Title` |
| "N ventanas coinciden" | varias instancias o titulos parecidos | se usa la que tiene foco; dar foco a la correcta antes de capturar |
| "acceso denegado" | la app corre como administrador | abrir la terminal como administrador o capturar solo screenshot |
| arbol casi vacio | juego DirectX/OpenGL, app Java/Swing sin Java Access Bridge, UI dibujada a mano | `tree_quality` partial o none: la pantalla se evalua solo por features |
| arbol enorme (Electron, navegadores) | cada div expone un nodo | normal: `uitree` descarta lo fuera de pantalla y colapsa grupos vacios |
| screenshot con otra ventana encima | `CopyFromScreen` copia lo que se ve | traer la ventana al frente y repetir |

## Clones web

Un clon web abierto en una pestana normal del navegador incluye en el arbol
la UI del navegador (pestanas, barra de direcciones). Para capturarlo limpio,
abrirlo como ventana de app: `chrome --app=http://localhost:3000` o
`msedge --app=http://localhost:3000`, y capturar por `-Title`. Un clon Tauri
o cualquier app con WebView2 expone su contenido por UI Automation sin pasos
extra.

## Que se descarta al normalizar

Barras de titulo (`TitleBar`), barras de desplazamiento (`ScrollBar`,
`Thumb`), nodos fuera de pantalla, nodos de area 0 y grupos sin nombre con un
solo hijo. Los botones Minimizar/Maximizar/Cerrar de apps con barra de titulo
propia (UWP) se conservan: aparecen igual en original y clon si ambos son
apps de Windows.
````

**Paso 4 — Verificar:**

```bash
python -c "import sys;t=open(sys.argv[1],encoding='utf-8').read();miss=[n for n in ['## Problemas conocidos','FLAG_SECURE'] if n not in t];print('falta: '+', '.join(miss) if miss else 'contenido ok');sys.exit(1 if miss else 0)" .claude/skills/clone-recon/references/android-capture.md
```

Output esperado:

```
contenido ok
```

```bash
python -c "import sys;t=open(sys.argv[1],encoding='utf-8').read();miss=[n for n in ['## Problemas conocidos','ApplicationFrameHost'] if n not in t];print('falta: '+', '.join(miss) if miss else 'contenido ok');sys.exit(1 if miss else 0)" .claude/skills/clone-recon/references/windows-capture.md
```

Output esperado:

```
contenido ok
```

**Paso 5 — Commit:**

```bash
git add .claude/skills/clone-recon/references/android-capture.md .claude/skills/clone-recon/references/windows-capture.md
git commit -m "docs(clone-recon): capture setup and troubleshooting" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```


### Tarea 19: Skill clone-arch y matriz de stack

**Archivos:** crear `.claude/skills/clone-arch/SKILL.md`; crear `.claude/skills/clone-arch/references/stack-matrix.md`

**Paso 1 — Verificacion que falla** (el archivo aun no existe):

```bash
python -c "import sys;t=open(sys.argv[1],encoding='utf-8').read();fm=t.split('---')[1];req=['name:','description:','when_to_use:','argument-hint:','disable-model-invocation: true','allowed-tools:'];miss=[r for r in req if r not in fm];print('falta: '+', '.join(miss) if miss else 'frontmatter ok');sys.exit(1 if miss else 0)" .claude/skills/clone-arch/SKILL.md
```

Output esperado (ultima linea):

```
FileNotFoundError: [Errno 2] No such file or directory: '.claude/skills/clone-arch/SKILL.md'
```

```bash
python -c "import sys;t=open(sys.argv[1],encoding='utf-8').read();miss=[n for n in ['## Criterios','capturabilidad','## Ejemplo'] if n not in t];print('falta: '+', '.join(miss) if miss else 'contenido ok');sys.exit(1 if miss else 0)" .claude/skills/clone-arch/references/stack-matrix.md
```

Output esperado (ultima linea):

```
FileNotFoundError: [Errno 2] No such file or directory: '.claude/skills/clone-arch/references/stack-matrix.md'
```

**Paso 2 — Crear `.claude/skills/clone-arch/SKILL.md`:**

```markdown
---
name: clone-arch
description: >
  Elige el stack del clon con una matriz de decision ponderada, convierte el
  modelo de datos inferido del recon en un esquema real, define modulos y
  capas, y fija el orden de construccion empezando por un corte vertical del
  flujo principal. Segundo paso del clone pack.
when_to_use: >
  Cuando el usuario dice "clone-arch", "que stack uso para el clon",
  "disena la arquitectura del clon", o despues de /clone-recon.
argument-hint: "[ruta al proyecto del clon]"
disable-model-invocation: true
allowed-tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
---

# Clone Arch — Stack, datos y orden de construccion

Lee `clone/recon.md`, `clone/screens.csv`, `clone/flows.csv` y
`clone/features.csv`. Escribe `clone/architecture.md`.

Si no existe `clone/recon.md`: detenerse y pedir `/clone-recon`. Planear un
clon de memoria es como se pierde la mitad de la app.

## Paso 1: stack

Puntuar los candidatos con `references/stack-matrix.md` y mostrar la tabla
completa. Recomendar el de mayor total con una linea de por que. Si el usuario
ya tiene un stack decidido, usarlo y solo marcar los riesgos que la matriz
detecta.

Si el elegido tiene capturabilidad 2 o menos, avisar: las pantallas del clon
quedaran como "solo features" en `/clone-diff` y la paridad de UI no se podra
medir.

## Paso 2: modelo de datos

Del modelo inferido en `recon.md` a un esquema real para el stack elegido
(Room en Android, SQLite/EF Core en .NET, SQLite en Tauri o web local):

- clave primaria por tabla, y `created_at`/`updated_at` si el original
  muestra fechas
- claves foraneas con regla de borrado decidida, no por defecto
- indices en cada clave foranea y en cada columna por la que se filtra u
  ordena en alguna pantalla
- estados como enum o restriccion check
- fechas en UTC, mostradas en la zona del usuario
- los campos con confianza `supuesto` se marcan en el esquema con un comentario
- migracion inicial escrita

## Paso 3: modulos y capas

Clean Architecture: `domain` (entidades y casos de uso, sin framework),
`data` (repositorios, base de datos), `ui` (pantallas y ViewModels). Un modulo
o paquete de feature por area de `features.csv` cuando hay mas de 3 areas.
En Android, cuando exista codigo, validar con `/android-arch`.

## Paso 4: partes delicadas

Una linea por cada una que aplique: sincronizacion, offline, notificaciones,
tareas en segundo plano, archivos grandes, busqueda, integraciones con el
sistema (bandeja, inicio automatico, atajos globales), permisos de Android.

## Paso 5: orden de construccion

1. **Hito 1, corte vertical:** el flujo F01 de punta a punta, feo pero
   funcionando. Prueba el stack.
2. **Must** de `features.csv`, agrupados por area.
3. **Should**, luego **could**.

Cada hito lista sus SIDs, tablas y K-IDs, en el orden en que `/clone-build`
los va a construir.

## Salida

`clone/architecture.md` con: tabla de la matriz y stack elegido, esquema,
modulos, partes delicadas y orden de construccion. Resumen: stack en una
linea, numero de tablas, numero de hitos, las 3 partes mas riesgosas, y
siguiente paso: `/clone-build`.
```

**Paso 3 — Crear `.claude/skills/clone-arch/references/stack-matrix.md`:**

```markdown
# Matriz de stack

Cada candidato se puntua de 1 a 5 por criterio. Total = suma de
(puntaje x peso). Mostrar siempre la tabla completa, no solo el ganador.

## Criterios

| criterio | peso | que mide |
| --- | --- | --- |
| plataforma | 3 | encaja con donde corre el original y donde se va a usar el clon |
| integracion con el sistema | 2 | notificaciones, archivos, bandeja, servicios en segundo plano, atajos |
| offline y sincronizacion | 2 | facilidad para datos locales y sincronizar entre dispositivos |
| experiencia del usuario | 2 | cuanto conoce el usuario el stack (Kotlin/Android pesa a favor) |
| Android y PC a la vez | 2 | un solo codigo para ambas plataformas |
| capturabilidad | 1 | expone arbol de UI que `capture_*` puede leer para el diff |

## Candidatos y puntajes base

Puntajes de partida; ajustar con lo que dice el recon y explicar cada ajuste.

| candidato | plataforma | integracion | offline | experiencia | ambas | capturabilidad |
| --- | --- | --- | --- | --- | --- | --- |
| Kotlin + Jetpack Compose (Android) | 5 si el original es Android, 1 si es de escritorio | 5 | 5 | 5 | 1 | 5 |
| Kotlin Multiplatform + Compose Multiplatform | 4 | 3 | 4 | 4 | 5 | 2 |
| C# + WinUI 3 | 5 si el original es de Windows, 1 si es Android | 5 | 4 | 2 | 1 | 5 |
| C# + WPF | 4 si el original es de Windows, 1 si es Android | 4 | 4 | 2 | 1 | 5 |
| Tauri + web (TypeScript) | 4 en escritorio, 1 en Android | 3 | 3 | 3 | 2 | 4 |
| App web local (navegador) | 3 | 1 | 2 | 3 | 3 | 3 |

Notas de capturabilidad:
- Compose (Android): el arbol de semantica sale por uiautomator. Poner
  `contentDescription` y `testTag` en los elementos interactivos mejora el diff.
- Compose Multiplatform en escritorio: la accesibilidad en Windows depende de
  Java Access Bridge y suele exponer pocos nodos. De ahi el 2.
- WinUI 3 y WPF: UI Automation nativa. Poner `AutomationProperties.AutomationId`.
- Tauri: WebView2 expone el DOM accesible por UI Automation.
- Web local: capturable abierta como ventana de app (`--app=URL`). En una
  pestana normal se mezcla la UI del navegador.

## Ejemplo

Original: app de notas Android. El usuario la quiere en el telefono y en el PC.

| candidato | plataforma x3 | integracion x2 | offline x2 | experiencia x2 | ambas x2 | captura x1 | total |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Kotlin + Compose (Android) | 15 | 10 | 10 | 10 | 2 | 5 | 52 |
| Kotlin Multiplatform | 12 | 6 | 8 | 8 | 10 | 2 | 46 |
| Tauri + web | 3 | 6 | 6 | 6 | 4 | 4 | 29 |

Recomendacion: Kotlin + Compose para Android y empezar ahi; si el PC es un
requisito duro, Kotlin Multiplatform, sabiendo que en escritorio la paridad
de UI no se podra medir con el diff de arbol.
```

**Paso 4 — Verificar:**

```bash
python -c "import sys;t=open(sys.argv[1],encoding='utf-8').read();fm=t.split('---')[1];req=['name:','description:','when_to_use:','argument-hint:','disable-model-invocation: true','allowed-tools:'];miss=[r for r in req if r not in fm];print('falta: '+', '.join(miss) if miss else 'frontmatter ok');sys.exit(1 if miss else 0)" .claude/skills/clone-arch/SKILL.md
```

Output esperado:

```
frontmatter ok
```

```bash
python -c "import sys;t=open(sys.argv[1],encoding='utf-8').read();miss=[n for n in ['## Criterios','capturabilidad','## Ejemplo'] if n not in t];print('falta: '+', '.join(miss) if miss else 'contenido ok');sys.exit(1 if miss else 0)" .claude/skills/clone-arch/references/stack-matrix.md
```

Output esperado:

```
contenido ok
```

**Paso 5 — Commit:**

```bash
git add .claude/skills/clone-arch/SKILL.md .claude/skills/clone-arch/references/stack-matrix.md
git commit -m "feat(clone-arch): add skill and stack matrix" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```


### Tarea 20: Skill clone-build

**Archivos:** crear `.claude/skills/clone-build/SKILL.md`

**Paso 1 — Verificacion que falla** (el archivo aun no existe):

```bash
python -c "import sys;t=open(sys.argv[1],encoding='utf-8').read();fm=t.split('---')[1];req=['name:','description:','when_to_use:','argument-hint:','disable-model-invocation: true','allowed-tools:'];miss=[r for r in req if r not in fm];print('falta: '+', '.join(miss) if miss else 'frontmatter ok');sys.exit(1 if miss else 0)" .claude/skills/clone-build/SKILL.md
```

Output esperado (ultima linea):

```
FileNotFoundError: [Errno 2] No such file or directory: '.claude/skills/clone-build/SKILL.md'
```

**Paso 2 — Crear `.claude/skills/clone-build/SKILL.md`:**

````markdown
---
name: clone-build
description: >
  Construye el clon pantalla por pantalla en el orden de clone/architecture.md:
  logica con /tdd, UI con todos los estados del recon, captura del clon con el
  mismo script que el original y diff de arbol de UI contra el original como
  definicion de terminado. Tercer paso del clone pack.
when_to_use: >
  Cuando el usuario dice "clone-build", "construye el clon", "construye la
  pantalla S03", "siguiente hito del clon", o despues de /clone-arch.
argument-hint: "[hito | SID]"
disable-model-invocation: true
allowed-tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Bash
---

# Clone Build — Pantalla por pantalla contra el original

Lee `clone/architecture.md`, `clone/recon.md`, `clone/screens.csv`,
`clone/features.csv` y los resumenes de `clone/captures/original/`. Actualiza
`screens.csv`, `features.csv` y `clone/build-log.md`.

Scripts del pack:

```
${CLAUDE_SKILL_DIR}/../clone-recon/scripts/capture_android.py
${CLAUDE_SKILL_DIR}/../clone-recon/scripts/capture_windows.ps1
${CLAUDE_SKILL_DIR}/../clone-recon/scripts/uitree.py
${CLAUDE_SKILL_DIR}/../clone-diff/scripts/treediff.py
```

Sin `clone/architecture.md`: detenerse y pedir `/clone-arch`.

## Reglas

- **Codigo propio.** Todo se escribe aqui a partir del recon. Nunca copiar
  recursos, codigo ni assets del original.
- **Logica con `/tdd`.** ViewModels, casos de uso y repositorios: test que
  falla primero.
- **Leer resumenes, no raws.** `uitree.py summarize` sobre la captura original.
- **Un commit por pantalla:** `build(clone): S03 ajustes`.

## Ciclo por pantalla

Argumento: un hito (`hito 2`) o un SID (`S03`). Sin argumento: la siguiente
pantalla con `estado_clon` distinto de `hecho` en el orden de
`architecture.md`.

1. **Contexto.** Fila de `screens.csv`, resumen de cada estado capturado
   (`uitree.py summarize clone/captures/original/<SID>.tree.json`), flujos de
   `flows.csv` que pasan por ella, features (K-IDs) que la mencionan.
2. **Logica** con `/tdd`.
3. **UI** con todos los estados del recon. En el stack, dar ids estables a los
   elementos interactivos (`testTag`/`contentDescription` en Compose,
   `AutomationProperties.AutomationId` en WinUI/WPF, `id`/`aria-label` en web):
   el diff los usa para emparejar.
4. **Correr el clon** y llevarlo a la pantalla y estado. Pedir al usuario que
   navegue si hace falta.
5. **Capturar el clon** con el mismo script que el original, a
   `clone/captures/clone/` y con el mismo SID.
6. **Diff:**
   `python ${CLAUDE_SKILL_DIR}/../clone-diff/scripts/treediff.py clone/captures/original/<SID>.tree.json clone/captures/clone/<SID>.tree.json --out clone/diffs/<SID>.json`
   Escribe el JSON (UTF-8) para `/clone-diff` e imprime la version de texto
   con los faltantes. No redirigir con `>`: en Windows rompe los acentos.
7. **Definicion de terminado:**
   - [ ] todos los estados de la pantalla capturados en el clon
   - [ ] `interactive_score >= 85`, o cada faltante justificado en `build-log.md`
   - [ ] tests de la logica pasan
   - [ ] `features.csv` (estado `si` o `parcial` con nota) y `screens.csv`
         (`estado_clon`) actualizados
   - [ ] captura del clon guardada
8. **Log y commit.** Una linea en `build-log.md`:
   `S03 | 2026-10-20 | hecho | interactivo 92 | falta: atajo de teclado`.
   Luego el commit de la pantalla.

Un diff `skipped` (arbol `none` en original o clon) no bloquea: la pantalla
se cierra solo por features y se anota en el log.

## Cuando una pantalla es mas grande de lo estimado

Decirlo en el chat y en el log antes de seguir. No entregar media pantalla en
silencio. Proponer partirla: lo que entra en este hito y lo que pasa al
siguiente.

## Cuando no se entiende como funciona algo del original

Volver al original como usuario: centro de ayuda, el changelog, o pedir al
usuario que lo repita en su dispositivo y capturar el estado que falta. Nunca
descompilar ni mirar su trafico.

## Salida

Por pantalla: score y faltantes. Al cerrar un hito: pantallas hechas /
total, must hechos / total, y siguiente hito. Cuando no quedan pantallas:
siguiente paso `/clone-diff`.
````

**Paso 3 — Verificar:**

```bash
python -c "import sys;t=open(sys.argv[1],encoding='utf-8').read();fm=t.split('---')[1];req=['name:','description:','when_to_use:','argument-hint:','disable-model-invocation: true','allowed-tools:'];miss=[r for r in req if r not in fm];print('falta: '+', '.join(miss) if miss else 'frontmatter ok');sys.exit(1 if miss else 0)" .claude/skills/clone-build/SKILL.md
```

Output esperado:

```
frontmatter ok
```

**Paso 4 — Commit:**

```bash
git add .claude/skills/clone-build/SKILL.md
git commit -m "feat(clone-build): add skill instructions" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```


### Tarea 21: Skill clone-diff

**Archivos:** crear `.claude/skills/clone-diff/SKILL.md`

**Paso 1 — Verificacion que falla** (el archivo aun no existe):

```bash
python -c "import sys;t=open(sys.argv[1],encoding='utf-8').read();fm=t.split('---')[1];req=['name:','description:','when_to_use:','argument-hint:','disable-model-invocation: true','allowed-tools:'];miss=[r for r in req if r not in fm];print('falta: '+', '.join(miss) if miss else 'frontmatter ok');sys.exit(1 if miss else 0)" .claude/skills/clone-diff/SKILL.md
```

Output esperado (ultima linea):

```
FileNotFoundError: [Errno 2] No such file or directory: '.claude/skills/clone-diff/SKILL.md'
```

**Paso 2 — Crear `.claude/skills/clone-diff/SKILL.md`:**

````markdown
---
name: clone-diff
description: >
  Mide cuanto alcanzo el clon al original: feature score ponderado (must,
  should, could), score de arbol de UI por pantalla, pasos por flujo y un
  veredicto (incompleto, usable, completo) con la lista de lo que falta en
  orden de construccion. Ultimo paso del clone pack.
when_to_use: >
  Cuando el usuario dice "clone-diff", "cuanto le falta al clon", "compara
  con el original", "paridad", "esta listo el clon", o despues de /clone-build.
argument-hint: "[ruta a clone/]"
disable-model-invocation: true
allowed-tools:
  - Read
  - Write
  - Glob
  - Grep
  - Bash(python *)
  - Bash(python3 *)
---

# Clone Diff — Paridad con evidencia

Scripts (en Windows usar `python`, en macOS/Linux `python3`):

```
${CLAUDE_SKILL_DIR}/scripts/treediff.py   ORIGINAL.tree.json CLON.tree.json [--json] [--ignore-text] [--out DIFF.json]
${CLAUDE_SKILL_DIR}/scripts/parity.py     clone/ [--json | --markdown] [--out ARCHIVO]
```

Para escribir archivos usar siempre `--out` (UTF-8), nunca `>`: en Windows la
redireccion usa la codificacion de la consola y rompe los acentos.

## Que significa paridad aqui

El clon hace el mismo trabajo, no se ve igual. El **feature score** es el
numero principal: si el usuario puede hacer todo lo que hacia en el original.
El **score de arbol** mide si cada pantalla tiene los mismos controles en la
misma estructura. Los textos distintos y los controles extra no penalizan:
son decisiones del clon.

## Paso 1: diffs al dia

Para cada fila de `clone/screens.csv` con `estado_clon` `hecho` o `parcial` y
cada estado capturado, verificar que existe `clone/diffs/<SID>.json` y que es
mas nuevo que las dos capturas. Si falta o esta viejo:

```
python ${CLAUDE_SKILL_DIR}/scripts/treediff.py clone/captures/original/<SID>.tree.json clone/captures/clone/<SID>.tree.json --out clone/diffs/<SID>.json
```

Si falta la captura del clon, pedir que se capture (ver `/clone-build` paso 5).

## Paso 2: pasos por flujo

Para cada fila de `clone/flows.csv` sin `pasos_clon`: pedir al usuario que
recorra el flujo en el clon y cuente taps/clicks/teclas de envio del camino
feliz. Anotarlo en la columna.

## Paso 3: reporte

```
python ${CLAUDE_SKILL_DIR}/scripts/parity.py clone/ --markdown --out clone/parity.md
python ${CLAUDE_SKILL_DIR}/scripts/parity.py clone/
```

Exit 1 significa veredicto `incompleto` (no es un error). Exit 2 es un
problema en `features.csv` o `flows.csv`: el mensaje dice fila y valor.

Pesos y umbrales:

- features: must 3, should 2, could 1; `si` 1, `parcial` 0.5, `no` 0;
  `skip` y `extra` no cuentan
- **incompleto:** algun must no esta en `si`, o alguna pantalla bajo 70
- **usable:** todos los must en `si` y todas las pantallas en 70 o mas
- **completo:** usable, feature score 90 o mas y todas las pantallas en 85 o mas
- pantallas `skipped` (sin arbol): se listan como "solo features"

## Paso 4: revision a mano

Para las 3 pantallas con menor score, leer la version de texto del diff:

```
python ${CLAUDE_SKILL_DIR}/scripts/treediff.py clone/captures/original/<SID>.tree.json clone/captures/clone/<SID>.tree.json
```

Clasificar cada faltante: falta de verdad (va a la lista), existe con otro
rol o en otra pantalla (anotar, no es falta), o fue descartado a proposito
(anotar en `build-log.md`). Si un falso faltante se repite porque el clon no
tiene ids estables, recomendarlos (ver `/clone-build` paso 3).

## Salida

Presentar con los numeros de `parity.py`, sin redondear ni estimar:

1. Veredicto, feature score y must hechos / total.
2. Score por pantalla, de menor a mayor, y las pantallas "solo features".
3. Flujos con delta de pasos (negativo es mejor que el original).
4. Las 5 cosas que mas suben el score: primero must pendientes, luego
   faltantes interactivos de las pantallas mas bajas.
5. Siguiente paso: `/clone-build <SID o hito>` para los huecos, o terminado
   si el veredicto es `completo`.
````

**Paso 3 — Verificar:**

```bash
python -c "import sys;t=open(sys.argv[1],encoding='utf-8').read();fm=t.split('---')[1];req=['name:','description:','when_to_use:','argument-hint:','disable-model-invocation: true','allowed-tools:'];miss=[r for r in req if r not in fm];print('falta: '+', '.join(miss) if miss else 'frontmatter ok');sys.exit(1 if miss else 0)" .claude/skills/clone-diff/SKILL.md
```

Output esperado:

```
frontmatter ok
```

**Paso 4 — Commit:**

```bash
git add .claude/skills/clone-diff/SKILL.md
git commit -m "feat(clone-diff): add skill instructions" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```


---

## Fase 7: documentacion del repo y verificacion final

### Tarea 22: CLAUDE.md y README.md

**Archivos:** modificar `CLAUDE.md`, `README.md`

**Paso 1 — Verificacion que falla:**

```bash
python -c "t=open('CLAUDE.md',encoding='utf-8').read();r=open('README.md',encoding='utf-8').read();n=[s for s in ['clone-recon','clone-arch','clone-build','clone-diff'] if t.count('/'+s)<2 or r.count(s+'/SKILL.md')<1];print('faltan: '+', '.join(n) if n else 'docs ok');exit(1 if n else 0)"
```

Output esperado:

```
faltan: clone-recon, clone-arch, clone-build, clone-diff
```

**Paso 2 — `CLAUDE.md`, estructura.** Reemplazar:

```
  git-identity/references/setup.md — Referencia para modo setup
```

por:

```
  git-identity/references/setup.md — Referencia para modo setup
  clone-recon/SKILL.md             — Desarmar app Android/Windows (pantallas, flujos, features)
  clone-recon/references/recon-template.md   — Plantilla de clone/recon.md
  clone-recon/references/android-capture.md  — Setup y problemas de captura con adb
  clone-recon/references/windows-capture.md  — Setup y problemas de captura con UI Automation
  clone-recon/scripts/capture_android.py     — Captura via adb (screenshot + arbol de UI)
  clone-recon/scripts/capture_windows.ps1    — Captura via UI Automation (PowerShell 5.1)
  clone-recon/scripts/uitree.py              — Arbol de UI normalizado (normalize, summarize)
  clone-arch/SKILL.md              — Stack, esquema y orden de construccion del clon
  clone-arch/references/stack-matrix.md      — Matriz de decision de stack
  clone-build/SKILL.md             — Construccion pantalla por pantalla contra el original
  clone-diff/SKILL.md              — Paridad: features + arbol de UI + veredicto
  clone-diff/scripts/treediff.py             — Diff de arboles de UI normalizados
  clone-diff/scripts/parity.py               — Reporte de paridad y veredicto
```

**Paso 3 — `CLAUDE.md`, tabla de skills.** Reemplazar:

```
| `/git-identity` | Solo usuario | Identidades Git separadas: audit y setup de 4 capas |
```

por:

```
| `/git-identity` | Solo usuario | Identidades Git separadas: audit y setup de 4 capas |
| `/clone-recon` | Solo usuario | Desarmar app Android/Windows: capturas, flujos, features |
| `/clone-arch` | Solo usuario | Stack (matriz), esquema y orden de construccion del clon |
| `/clone-build` | Solo usuario | Construir pantalla por pantalla con diff contra el original |
| `/clone-diff` | Solo usuario | Paridad: feature score, score de UI por pantalla, veredicto |
```

**Paso 4 — `CLAUDE.md`, flujo.** Reemplazar (inicio de la seccion Infraestructura):

````
### Infraestructura
```
/git-identity 
````

por:

````
### Clonar apps (uso propio)
```
/clone-recon  -->  /clone-arch  -->  /clone-build (usa /tdd)  -->  /clone-diff
 capturas,         stack,            pantalla por pantalla,        veredicto:
 flujos,           esquema,          diff de arbol de UI           incompleto,
 features          hitos             contra el original            usable, completo
```

### Infraestructura
```
/git-identity 
````

**Paso 5 — `README.md`, seccion de skills.** Reemplazar (final del parrafo de codegraph y el titulo siguiente):

```
El directorio `codegraph-out/` es committeable: el equipo comparte un solo grafo.

### Game development
```

por:

```
El directorio `codegraph-out/` es committeable: el equipo comparte un solo grafo.

### Clonar apps

| Skill | Activacion | Proposito |
|---|---|---|
| [`clone-recon`](./.claude/skills/clone-recon/SKILL.md) | Explicita | Desarma una app Android o de escritorio Windows instalada: captura screenshot + arbol de UI de cada pantalla mientras el usuario navega, y arma pantallas, flujos, modelo de datos y matriz de features |
| [`clone-arch`](./.claude/skills/clone-arch/SKILL.md) | Explicita | Elige el stack del clon con una matriz ponderada, convierte el modelo inferido en esquema real y fija el orden de construccion |
| [`clone-build`](./.claude/skills/clone-build/SKILL.md) | Explicita | Construye pantalla por pantalla con `/tdd`, captura el clon con el mismo script y lo compara contra el original como definicion de terminado |
| [`clone-diff`](./.claude/skills/clone-diff/SKILL.md) | Explicita | Feature score ponderado, score de arbol de UI por pantalla, pasos por flujo y veredicto (incompleto, usable, completo) |

Solo en Claude Code por ahora. Para uso propio: reconstruye funcionalidad observando la UI, nunca descompila ni extrae recursos. Scripts zero-deps (stdlib de Python 3.10+ y Windows PowerShell 5.1): `capture_android.py` (adb), `capture_windows.ps1` (UI Automation), `uitree.py` (arbol normalizado neutral a la plataforma, con redaccion de datos personales), `treediff.py` y `parity.py`.

### Game development
```

**Paso 6 — `README.md`, flujo.** Reemplazar:

```
### Multiples problemas independientes
```

por:

````
### Clonar apps

```
clone-recon  -->  clone-arch  -->  clone-build (usa tdd)  -->  clone-diff
```

### Multiples problemas independientes
````

**Paso 7 — Verificar:**

```bash
python -c "t=open('CLAUDE.md',encoding='utf-8').read();r=open('README.md',encoding='utf-8').read();n=[s for s in ['clone-recon','clone-arch','clone-build','clone-diff'] if t.count('/'+s)<2 or r.count(s+'/SKILL.md')<1];print('faltan: '+', '.join(n) if n else 'docs ok');exit(1 if n else 0)"
```

Output esperado:

```
docs ok
```

**Paso 8 — Commit:**

```bash
git add CLAUDE.md README.md
git commit -m "docs: document clone pack skills" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

### Tarea 23: verificacion final (criterios de la spec)

Aplicar `/verify`. Cada comando se corre fresco y se lee su output completo.

**Paso 1 — Criterio 1, suites completas:**

```bash
python -m unittest discover -s .claude/skills/clone-recon/tests
python -m unittest discover -s .claude/skills/clone-diff/tests
```

Output esperado (en ese orden):

```
Ran 47 tests
OK
```

```
Ran 44 tests
OK
```

**Paso 2 — Criterios 2 y 3:** repetir los pasos 3 y 4 de la tarea 9. Mismos outputs.

**Paso 3 — Criterio 4, diff de una captura contra si misma** (en PowerShell, despues del paso 2):

```powershell
python .claude/skills/clone-diff/scripts/treediff.py "$env:TEMP\clonecap\N01.tree.json" "$env:TEMP\clonecap\N01.tree.json"
```

Output esperado:

```
N01: interactivo 100, estructura 100 (original 12 nodos, clon 12, emparejados 12)
```

**Paso 4 — Criterio 5, frontmatter de las cuatro skills:**

```bash
for s in clone-recon clone-arch clone-build clone-diff; do python -c "import sys;t=open(sys.argv[1],encoding='utf-8').read();fm=t.split('---')[1];req=['name:','description:','when_to_use:','argument-hint:','disable-model-invocation: true','allowed-tools:'];miss=[r for r in req if r not in fm];print('falta: '+', '.join(miss) if miss else 'frontmatter ok');sys.exit(1 if miss else 0)" .claude/skills/$s/SKILL.md; done
```

Output esperado:

```
frontmatter ok
frontmatter ok
frontmatter ok
frontmatter ok
```

**Paso 5 — Criterio 6:** el chequeo de la tarea 22 da `docs ok`.

**Paso 6 — Criterio 7, sin emojis ni referencias externas:**

```bash
python -c "import glob;bad=[f for f in glob.glob('.claude/skills/clone-*/**/*',recursive=True) if f.endswith(('.md','.py','.ps1','.json','.xml')) and any(0x1F300<=ord(c)<=0x1FAFF or 0x2600<=ord(c)<=0x27BF for c in open(f,encoding='utf-8').read())];print(bad or 'sin emojis')"
```

Output esperado:

```
sin emojis
```

```bash
python -c "import glob,re;bad=[f for f in glob.glob('.claude/skills/clone-*/**/*',recursive=True) if f.endswith(('.md','.py','.ps1')) and re.search(r'github\.com|inspirad|basado en|port de',open(f,encoding='utf-8').read(),re.I)];print(bad or 'sin referencias externas')"
```

Output esperado:

```
sin referencias externas
```

**Paso 7 — Criterio 8, solo stdlib:**

```bash
python -c "import ast,sys,glob;own={'uitree','capture_android','treediff','parity'};bad=sorted({(f,m) for f in glob.glob('.claude/skills/clone-*/**/*.py',recursive=True) for n in ast.walk(ast.parse(open(f,encoding='utf-8').read())) if isinstance(n,(ast.Import,ast.ImportFrom)) for m in ([a.name for a in n.names] if isinstance(n,ast.Import) else [n.module or '']) if m.split('.')[0] not in sys.stdlib_module_names|own});print(bad or 'solo stdlib')"
```

Output esperado:

```
solo stdlib
```

**Paso 8 — Limpieza:**

```powershell
Remove-Item -Recurse -Force "$env:TEMP\clonecap"
```

Sin commit: esta tarea no cambia archivos. Si algun output difiere del
esperado, no se reporta como terminado: se aplica `/debug`.
