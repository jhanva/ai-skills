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
