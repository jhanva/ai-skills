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
