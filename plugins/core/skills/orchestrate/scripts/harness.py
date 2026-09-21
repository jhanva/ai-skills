#!/usr/bin/env python3
"""Contratos y routing determinista para workflows manager-worker."""

from __future__ import annotations

import argparse
from fnmatch import fnmatchcase
import json
import re
import sys
from pathlib import Path
from pathlib import PurePosixPath
from typing import Any


RISK_DIMENSIONS = (
    "ambiguity",
    "coupling",
    "blast_radius",
    "verifiability",
    "sensitivity",
    "reversibility",
)


def _non_empty_strings(value: Any) -> bool:
    return isinstance(value, list) and bool(value) and all(
        isinstance(item, str) and bool(item.strip()) for item in value
    )


def _string_list(value: Any) -> bool:
    return isinstance(value, list) and all(isinstance(item, str) for item in value)


def _repository_relative_path(value: str) -> bool:
    path = value.replace("\\", "/")
    return bool(path) and not path.startswith("/") and not re.match(r"^[A-Za-z]:/", path) and (
        ".." not in PurePosixPath(path).parts
    )


def validate_task(task: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    task_id = task.get("task_id")
    if not isinstance(task_id, str) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", task_id):
        errors.append("task_id must use lowercase letters, digits, and hyphens")
    objective = task.get("objective")
    if not isinstance(objective, str) or not objective.strip():
        errors.append("objective must be a non-empty string")
    if task.get("mode") not in {"read", "write", "review"}:
        errors.append("mode must be read, write, or review")
    allowed_paths = task.get("allowed_paths")
    if not _non_empty_strings(allowed_paths):
        errors.append("allowed_paths must be a non-empty list of strings")
    elif not all(_repository_relative_path(path) for path in allowed_paths):
        errors.append("allowed_paths entries must be repository-relative patterns")
    forbidden_paths = task.get("forbidden_paths")
    if not _string_list(forbidden_paths):
        errors.append("forbidden_paths must be a list of strings")
    elif not all(_repository_relative_path(path) for path in forbidden_paths):
        errors.append("forbidden_paths entries must be repository-relative patterns")
    if not _non_empty_strings(task.get("acceptance")):
        errors.append("acceptance must be a non-empty list of strings")
    commands = task.get("commands")
    if not _string_list(commands):
        errors.append("commands must be a list of strings")
    elif task.get("mode") == "write" and not commands:
        errors.append("write tasks must define at least one verification command")
    dimensions = task.get("risk_dimensions")
    if not isinstance(dimensions, dict) or set(dimensions) != set(RISK_DIMENSIONS):
        errors.append(
            "risk_dimensions must contain exactly: " + ", ".join(sorted(RISK_DIMENSIONS))
        )
    if isinstance(dimensions, dict):
        for name in RISK_DIMENSIONS:
            if name in dimensions and (
                isinstance(dimensions[name], bool) or dimensions[name] not in {0, 1, 2}
            ):
                errors.append(f"risk_dimensions.{name} must be 0, 1, or 2")
    attempts = task.get("max_attempts")
    if isinstance(attempts, bool) or attempts not in {1, 2}:
        errors.append("max_attempts must be 1 or 2")
    if task.get("expected_result") != "result-envelope-v1":
        errors.append("expected_result must be result-envelope-v1")
    return errors


def validate_result_envelope(result: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    task_id = result.get("task_id")
    if not isinstance(task_id, str) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", task_id):
        errors.append("task_id must use lowercase letters, digits, and hyphens")
    status = result.get("status")
    if status not in {"passed", "failed", "blocked", "partial"}:
        errors.append("status must be passed, failed, blocked, or partial")
    summary = result.get("summary")
    if not isinstance(summary, str) or not summary.strip():
        errors.append("summary must be a non-empty string")
    changed_files = result.get("changed_files")
    if not _string_list(changed_files):
        errors.append("changed_files must be a list of strings")
        changed_files = []
    checks = result.get("checks")
    valid_checks = isinstance(checks, list) and all(
        isinstance(check, dict)
        and isinstance(check.get("command"), str)
        and bool(check["command"].strip())
        and check.get("result") in {"passed", "failed", "skipped"}
        for check in (checks or [])
    )
    if not valid_checks:
        errors.append("checks must contain command/result objects")
    for field in ("assumptions", "risks", "out_of_scope"):
        if not _string_list(result.get(field)):
            errors.append(f"{field} must be a list of strings")
    if status == "passed" and (
        not checks or not valid_checks or any(check["result"] != "passed" for check in checks)
    ):
        errors.append("passed results require at least one check and every check must pass")
    return errors


def validate_result(task: dict[str, Any], result: dict[str, Any]) -> list[str]:
    errors = validate_result_envelope(result)
    if result.get("task_id") != task.get("task_id"):
        errors.append("result task_id must match contract task_id")
    changed_files = result.get("changed_files")
    if not _string_list(changed_files):
        changed_files = []
    if task.get("mode") in {"read", "review"} and changed_files:
        errors.append("read and review tasks cannot report changed_files")
    allowed = task.get("allowed_paths", [])
    forbidden = task.get("forbidden_paths", [])
    for raw_path in changed_files:
        path = str(raw_path).replace("\\", "/")
        if not _repository_relative_path(path):
            errors.append(f"changed file must be a repository-relative path: {path}")
            continue
        if not any(fnmatchcase(path, pattern.replace("\\", "/")) for pattern in allowed):
            errors.append(f"changed file is outside allowed_paths: {path}")
        if any(fnmatchcase(path, pattern.replace("\\", "/")) for pattern in forbidden):
            errors.append(f"changed file matches forbidden_paths: {path}")
    return errors


def route_task(task: dict[str, Any]) -> dict[str, Any]:
    dimensions = task["risk_dimensions"]
    score = sum(int(dimensions[name]) for name in RISK_DIMENSIONS)
    if dimensions["sensitivity"] == 2:
        return {"role": "orchestrator", "score": score, "reason": "sensitive task override"}
    if task.get("mode") == "read" and score <= 3:
        return {"role": "explorer", "score": score, "reason": "low-risk read-only task"}
    if score <= 7:
        return {"role": "implementer", "score": score, "reason": "bounded implementation task"}
    return {"role": "orchestrator", "score": score, "reason": "high-risk task"}


def load_json(path: str) -> dict[str, Any]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def write_json(value: dict[str, Any]) -> None:
    print(json.dumps(value, ensure_ascii=False, sort_keys=True))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="action", required=True)
    validate_task_parser = subparsers.add_parser("validate-task")
    validate_task_parser.add_argument("task")
    route_parser = subparsers.add_parser("route")
    route_parser.add_argument("task")
    validate_result_parser = subparsers.add_parser("validate-result")
    validate_result_parser.add_argument("task")
    validate_result_parser.add_argument("result")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        task = load_json(args.task)
        if args.action == "validate-task":
            errors = validate_task(task)
            write_json({"ok": not errors, "errors": errors})
            return 0 if not errors else 1
        if args.action == "route":
            errors = validate_task(task)
            if errors:
                write_json({"ok": False, "errors": errors})
                return 1
            write_json(route_task(task))
            return 0
        result = load_json(args.result)
        errors = validate_result(task, result)
        write_json({"ok": not errors, "errors": errors})
        return 0 if not errors else 1
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        write_json({"ok": False, "errors": [str(exc)]})
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
