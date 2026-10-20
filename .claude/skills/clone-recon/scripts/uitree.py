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
