import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "plugins", "clone", "skills", "clone-diff", "scripts"))

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
