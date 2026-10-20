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
