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


def feature_score(rows):
    scored = [r for r in rows if r["prioridad"] in PRIORITY_WEIGHTS]
    total = sum(PRIORITY_WEIGHTS[r["prioridad"]] for r in scored)
    if total == 0:
        return None
    got = sum(PRIORITY_WEIGHTS[r["prioridad"]] * STATE_VALUES[r["estado"]] for r in scored)
    return int(round(100 * got / total))


def area_scores(rows):
    areas = {}
    for row in rows:
        if row["prioridad"] in PRIORITY_WEIGHTS:
            areas.setdefault(row["area"], []).append(row)
    return {area: feature_score(items) for area, items in areas.items()}


def pending_features(rows):
    by_area = area_scores(rows)
    order = {"must": 0, "should": 1, "could": 2}
    pending = [r for r in rows if r["prioridad"] in order and r["estado"] != "si"]
    pending.sort(key=lambda r: (order[r["prioridad"]], by_area[r["area"]], r["area"], r["id"]))
    return [{"id": r["id"], "feature": r["feature"], "area": r["area"],
             "prioridad": r["prioridad"], "estado": r["estado"]} for r in pending]


def verdict(must_missing, features, screen_scores):
    if must_missing:
        return "incompleto"
    if any(score < USABLE_SCREEN for score in screen_scores):
        return "incompleto"
    if (features is not None and features >= COMPLETE_FEATURES
            and all(score >= COMPLETE_SCREEN for score in screen_scores)):
        return "completo"
    return "usable"


def build_report(clone_dir):
    rows = load_features(os.path.join(clone_dir, "features.csv"))
    flows = load_flows(os.path.join(clone_dir, "flows.csv"))
    diffs = load_diffs(os.path.join(clone_dir, "diffs"))
    screens = []
    skipped = []
    for d in diffs:
        if d.get("status") == "skipped" or d.get("interactive_score") is None:
            skipped.append(d.get("screen", "?"))
        else:
            screens.append({"screen": d.get("screen", "?"), "score": d["interactive_score"],
                            "missing": len(d.get("missing", []))})
    screens.sort(key=lambda s: (s["score"], s["screen"]))
    pending = pending_features(rows)
    must_missing = [p for p in pending if p["prioridad"] == "must"]
    features = feature_score(rows)
    return {
        "verdict": verdict(must_missing, features, [s["score"] for s in screens]),
        "feature_score": features,
        "must_done": sum(1 for r in rows if r["prioridad"] == "must" and r["estado"] == "si"),
        "must_total": sum(1 for r in rows if r["prioridad"] == "must"),
        "areas": sorted(area_scores(rows).items(), key=lambda kv: (kv[1], kv[0])),
        "screens": screens,
        "screens_features_only": skipped,
        "flows": flows,
        "pending": pending,
    }


def _score(value):
    return "-" if value is None else str(value)


def render_text(report):
    lines = ["Veredicto: %s" % report["verdict"],
             "Features: %s (must %d/%d)" % (_score(report["feature_score"]),
                                            report["must_done"], report["must_total"])]
    if report["areas"]:
        lines.append("Areas: " + ", ".join("%s %s" % (a, _score(s)) for a, s in report["areas"]))
    for s in report["screens"]:
        lines.append("Pantalla %s: %d (%d faltantes)" % (s["screen"], s["score"], s["missing"]))
    if report["screens_features_only"]:
        lines.append("Solo features: " + ", ".join(report["screens_features_only"]))
    for f in report["flows"]:
        if f["clone"] is None:
            lines.append("Flujo %s: original %d pasos, clon sin medir" % (f["id"], f["original"]))
        else:
            lines.append("Flujo %s: original %d, clon %d (%+d)" % (f["id"], f["original"],
                                                                  f["clone"], f["delta"]))
    if report["pending"]:
        lines.append("Pendiente:")
        lines.extend("  %s %s [%s, %s] %s" % (p["id"], p["prioridad"], p["area"], p["estado"],
                                              p["feature"]) for p in report["pending"])
    return "\n".join(lines)


def render_markdown(report):
    out = ["# Paridad", "",
           "**Veredicto:** %s" % report["verdict"], "",
           "| metrica | valor |", "| --- | --- |",
           "| feature score | %s |" % _score(report["feature_score"]),
           "| must hechos | %d/%d |" % (report["must_done"], report["must_total"]), ""]
    if report["areas"]:
        out += ["## Areas (mas debil primero)", "", "| area | score |", "| --- | --- |"]
        out += ["| %s | %s |" % (a, _score(s)) for a, s in report["areas"]]
        out.append("")
    if report["screens"] or report["screens_features_only"]:
        out += ["## Pantallas", "", "| pantalla | score interactivo | faltantes |",
                "| --- | --- | --- |"]
        out += ["| %s | %d | %d |" % (s["screen"], s["score"], s["missing"])
                for s in report["screens"]]
        out += ["| %s | solo features | - |" % s for s in report["screens_features_only"]]
        out.append("")
    if report["flows"]:
        out += ["## Flujos", "", "| flujo | original | clon | delta |", "| --- | --- | --- | --- |"]
        for f in report["flows"]:
            clone = "-" if f["clone"] is None else str(f["clone"])
            delta = "-" if f["delta"] is None else "%+d" % f["delta"]
            out.append("| %s %s | %d | %s | %s |" % (f["id"], f["nombre"], f["original"],
                                                     clone, delta))
        out.append("")
    if report["pending"]:
        out += ["## Pendiente (orden de construccion)", ""]
        out += ["- %s **%s** %s (%s, %s)" % (p["id"], p["prioridad"], p["feature"], p["area"],
                                             p["estado"]) for p in report["pending"]]
        out.append("")
    return "\n".join(out)


def safe_stdout():
    """Evita UnicodeEncodeError en consolas cp1252: reemplaza lo no imprimible."""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="replace")


def main(argv=None):
    safe_stdout()
    ap = argparse.ArgumentParser(description="Reporte de paridad del clone pack")
    ap.add_argument("clone_dir")
    fmt = ap.add_mutually_exclusive_group()
    fmt.add_argument("--json", action="store_true")
    fmt.add_argument("--markdown", action="store_true")
    ap.add_argument("--out", help="escribe el reporte en este archivo (UTF-8)")
    args = ap.parse_args(argv)
    try:
        report = build_report(args.clone_dir)
    except InputError as exc:
        print("parity: %s" % exc, file=sys.stderr)
        return 2
    if args.json:
        output = json.dumps(report, ensure_ascii=False, indent=1)
    elif args.markdown:
        output = render_markdown(report)
    else:
        output = render_text(report)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(output + "\n")
        print("ok: %s (veredicto %s)" % (args.out, report["verdict"]))
    else:
        print(output)
    return 1 if report["verdict"] == "incompleto" else 0


if __name__ == "__main__":
    sys.exit(main())
