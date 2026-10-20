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
