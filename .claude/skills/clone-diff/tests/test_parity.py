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


