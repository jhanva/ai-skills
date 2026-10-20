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

