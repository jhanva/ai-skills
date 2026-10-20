import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "plugins", "clone", "skills", "clone-recon", "scripts"))

import uitree  # noqa: E402

FIXTURES = os.path.join(HERE, "fixtures", "clone")
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
