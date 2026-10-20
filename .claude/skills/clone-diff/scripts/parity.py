#!/usr/bin/env python3
"""
parity.py — Reporte de paridad del clon contra el original. Zero dependencias.

Lee clone/features.csv, clone/flows.csv (opcional) y clone/diffs/*.json
(salidas de treediff.py --json) y calcula feature score, score por pantalla,
deltas de pasos por flujo y un veredicto: incompleto, usable o completo.

Uso:
  python parity.py clone/ [--json | --markdown] [--out ARCHIVO]

Exit: 0 usable o completo, 1 incompleto, 2 error de entrada.
"""

import argparse
import csv
import glob
import json
import os
import sys

PRIORITY_WEIGHTS = {"must": 3, "should": 2, "could": 1}
PRIORITIES = set(PRIORITY_WEIGHTS) | {"skip", "extra"}
STATE_VALUES = {"si": 1.0, "parcial": 0.5, "no": 0.0}
FEATURE_COLUMNS = ["id", "feature", "area", "prioridad", "pantallas", "estado", "notas"]
FLOW_COLUMNS = ["id", "nombre", "pantallas", "pasos_original", "pasos_clon"]

USABLE_SCREEN = 70
COMPLETE_SCREEN = 85
COMPLETE_FEATURES = 90


class InputError(Exception):
    """Archivo de entrada ausente o mal formado."""


def _read_csv(path, columns):
    with open(path, newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        missing = [c for c in columns if c not in (reader.fieldnames or [])]
        if missing:
            raise InputError("%s: faltan columnas %s" % (path, ", ".join(missing)))
        return list(reader)


def load_features(path):
    if not os.path.isfile(path):
        raise InputError("no existe %s" % path)
    rows = _read_csv(path, FEATURE_COLUMNS)
    for line, row in enumerate(rows, start=2):
        row["prioridad"] = row["prioridad"].strip().lower()
        row["estado"] = row["estado"].strip().lower()
        if row["prioridad"] not in PRIORITIES:
            raise InputError("features.csv fila %d: prioridad '%s' invalida" % (line, row["prioridad"]))
        if row["prioridad"] in PRIORITY_WEIGHTS and row["estado"] not in STATE_VALUES:
            raise InputError("features.csv fila %d: estado '%s' invalido" % (line, row["estado"]))
    return rows


def load_flows(path):
    if not os.path.isfile(path):
        return []
    flows = []
    for line, row in enumerate(_read_csv(path, FLOW_COLUMNS), start=2):
        try:
            original = int(row["pasos_original"])
            clone = int(row["pasos_clon"]) if row["pasos_clon"].strip() else None
        except ValueError:
            raise InputError("flows.csv fila %d: pasos no numericos" % line)
        flows.append({"id": row["id"], "nombre": row["nombre"], "original": original,
                      "clone": clone, "delta": None if clone is None else clone - original})
    return flows


def load_diffs(directory):
    diffs = []
    for path in sorted(glob.glob(os.path.join(directory, "*.json"))):
        try:
            with open(path, encoding="utf-8") as fh:
                diffs.append(json.load(fh))
        except (OSError, ValueError) as exc:
            raise InputError("no puedo leer %s: %s" % (path, exc))
    return diffs
