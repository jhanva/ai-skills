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
