#!/usr/bin/env python3
"""Hooks de proyecto para Codex.

Codex entrega un objeto JSON por stdin. Este modulo mantiene la traduccion de
los hooks de Claude sin depender de bash, jq ni campos que Codex no emite.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


SAFE_ENV_RE = re.compile(
    r"(?i)(?<![A-Za-z0-9_.])\.env\.(?:example|sample|template)(?![A-Za-z0-9_.])"
)
ENV_RE = re.compile(r"(?i)(?<![A-Za-z0-9_.])\.env(?:\.[A-Za-z0-9_-]+)?(?![A-Za-z0-9_.])")
ENV_FILE_COMMAND_RE = re.compile(
    r"(?ix)(?:[<>]|\b(?:cat|less|more|bat|head|tail|grep|rg|sed|awk|tee|source|cp|mv|type|"
    r"get-content|set-content|add-content|out-file|select-string|copy-item|move-item|remove-item)\b)"
)
DESTRUCTIVE_COMMANDS = (
    (re.compile(r"(?i)(?:^|[;&|]\s*)rm\s+-(?:rf|fr)\b"), "recursive forced deletion"),
    (re.compile(r"(?i)\bgit\s+push\b[^\r\n]*(?:--force(?:-with-lease)?|-f)\b"), "forced git push"),
    (re.compile(r"(?i)\bgit\s+reset\s+--hard\b"), "git reset --hard"),
    (re.compile(r"(?i)\bgit\s+clean\b[^\r\n]*\s-[A-Za-z]*[fd][A-Za-z]*\b"), "destructive git clean"),
    (re.compile(r"(?i)(?:^|[;&|]\s*)sudo\b"), "sudo command"),
    (re.compile(r"(?i)\bchmod\b[^\r\n]*\b777\b"), "world-writable permissions"),
)
PATCH_PATH_RE = re.compile(r"^\*\*\* (?:Add|Update|Delete) File:\s*(.+?)\s*$", re.MULTILINE)
PATCH_MOVE_RE = re.compile(r"^\*\*\* Move to:\s*(.+?)\s*$", re.MULTILINE)
HARDCODED_RE = re.compile(
    r"(?i)(damage|health|speed|rate|chance|cost|duration|mana|stamina)\s*[:=]\s*\d"
)
MOTION_RE = re.compile(r"(?i)(position|velocity|rotation)\s*(?:[+*/-]=|=[^=])")
UI_IMPORT_RE = re.compile(r"(?i)(?:from|import|preload|load).*?['\"].*?ui[/\\]")


def load_payload() -> dict[str, Any]:
    try:
        value = json.load(sys.stdin)
    except (json.JSONDecodeError, OSError):
        return {}
    return value if isinstance(value, dict) else {}


def emit(value: dict[str, Any]) -> None:
    print(json.dumps(value, ensure_ascii=False))


def deny(reason: str) -> None:
    emit(
        {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": reason,
            }
        }
    )


def additional_context(event: str, message: str) -> None:
    emit(
        {
            "hookSpecificOutput": {
                "hookEventName": event,
                "additionalContext": message,
            }
        }
    )


def tool_command(payload: dict[str, Any]) -> str:
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return ""
    command = tool_input.get("command")
    return command if isinstance(command, str) else ""


def patch_paths(patch: str) -> list[str]:
    paths = PATCH_PATH_RE.findall(patch) + PATCH_MOVE_RE.findall(patch)
    for line in patch.splitlines():
        if line.startswith("diff --git a/"):
            parts = line.split()
            if len(parts) >= 4:
                paths.extend((parts[2][2:], parts[3][2:]))
        elif line.startswith(("+++ b/", "--- a/")):
            paths.append(line[6:].strip())
    cleaned: list[str] = []
    for raw in paths:
        path = raw.strip().strip('"\'')
        if path and path != "/dev/null" and path not in cleaned:
            cleaned.append(path.replace("\\", "/"))
    return cleaned


def is_protected_env_path(path: str) -> bool:
    name = Path(path).name.lower()
    if name in {".env.example", ".env.sample", ".env.template"}:
        return False
    return name == ".env" or name.startswith(".env.")


def pre_tool_policy(payload: dict[str, Any]) -> None:
    command = tool_command(payload)
    tool_name = payload.get("tool_name", "")
    if not command:
        return

    if tool_name == "apply_patch":
        protected = [path for path in patch_paths(command) if is_protected_env_path(path)]
        if protected:
            deny(f"Protected .env file cannot be edited: {protected[0]}")
        return

    for pattern, reason in DESTRUCTIVE_COMMANDS:
        if pattern.search(command):
            deny(f"Repository policy blocked {reason}.")
            return

    without_safe_names = SAFE_ENV_RE.sub("SAFE_ENV_TEMPLATE", command)
    if ENV_RE.search(without_safe_names) and ENV_FILE_COMMAND_RE.search(without_safe_names):
        deny("Direct access to .env files is blocked; use .env.example, .env.sample or .env.template.")


def run_git(cwd: Path, *args: str) -> str:
    try:
        completed = subprocess.run(
            ["git", *args], cwd=cwd, text=True, capture_output=True, check=False, timeout=8
        )
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return completed.stdout.strip() if completed.returncode == 0 else ""


def validate_gameplay_code(payload: dict[str, Any]) -> None:
    command = tool_command(payload)
    if not re.search(r"(?i)(?:^|&&|;|\|)\s*git(?:\s+-C\s+\S+)?\s+commit\b", command):
        return
    cwd = Path(str(payload.get("cwd") or ".")).resolve()
    staged = run_git(cwd, "diff", "--cached", "--name-only").splitlines()
    warnings: list[str] = []
    for relative in staged:
        normalized = relative.replace("\\", "/")
        path = cwd / relative
        if not path.is_file() or path.suffix.lower() not in {".gd", ".cs"}:
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if normalized.startswith("src/gameplay/"):
            if HARDCODED_RE.search(content):
                warnings.append(f"HARDCODED: {normalized} has gameplay values that should be data-driven.")
            if UI_IMPORT_RE.search(content):
                warnings.append(f"LAYER: {normalized} imports UI directly; prefer signals.")
        if MOTION_RE.search(content) and "delta" not in content:
            warnings.append(f"DELTA: {normalized} changes motion without an explicit delta strategy.")
    if warnings:
        additional_context("PreToolUse", "Gameplay code warnings before commit:\n- " + "\n- ".join(warnings))


def resolve_edited_path(cwd: Path, raw: str) -> Path | None:
    candidate = Path(raw)
    if not candidate.is_absolute():
        candidate = cwd / candidate
    try:
        resolved = candidate.resolve()
        resolved.relative_to(cwd)
    except (OSError, ValueError):
        return None
    return resolved


def post_edit_checks(payload: dict[str, Any]) -> None:
    if payload.get("tool_name") != "apply_patch":
        return
    cwd = Path(str(payload.get("cwd") or ".")).resolve()
    warnings: list[str] = []
    for relative in patch_paths(tool_command(payload)):
        normalized = relative.replace("\\", "/").lstrip("./")
        path = resolve_edited_path(cwd, normalized)
        if path is None:
            continue
        if normalized.startswith("assets/"):
            if re.search(r"[A-Z\s-]", path.name):
                warnings.append(f"NAMING: {normalized} must use lowercase_snake_case.")
            if normalized.startswith("assets/data/") and path.suffix.lower() == ".json" and path.is_file():
                try:
                    json.loads(path.read_text(encoding="utf-8"))
                except (OSError, UnicodeDecodeError, json.JSONDecodeError):
                    warnings.append(f"JSON: {normalized} is not valid JSON.")
        match = re.match(r"src/gameplay/([^/]+)/", normalized)
        if match:
            system = match.group(1)
            direct = cwd / "design" / "gdd" / f"{system}.md"
            alternate = cwd / "design" / "gdd" / f"{system}-system.md"
            if not direct.is_file() and not alternate.is_file():
                warnings.append(
                    f"DESIGN: {normalized} has no design/gdd/{system}.md. "
                    f"Use $design-system {system} to define it."
                )
    if warnings:
        additional_context("PostToolUse", "Edited-file warnings:\n- " + "\n- ".join(warnings))


def session_context(payload: dict[str, Any]) -> None:
    cwd = Path(str(payload.get("cwd") or ".")).resolve()
    lines = ["Game dev project context:"]
    branch = run_git(cwd, "rev-parse", "--abbrev-ref", "HEAD")
    if branch:
        lines.append(f"Branch: {branch}")
    log = run_git(cwd, "log", "--oneline", "-5")
    if log:
        lines.append("Recent commits:\n" + log)
    sprint_dir = cwd / "production" / "sprints"
    sprints = sorted(sprint_dir.glob("sprint-*.md"), key=lambda path: path.stat().st_mtime, reverse=True)
    if sprints:
        lines.append(f"Active sprint: {sprints[0].stem}")
    modified = run_git(cwd, "diff", "--name-only")
    staged = run_git(cwd, "diff", "--cached", "--name-only")
    if staged:
        lines.append("Staged files:\n" + staged)
    if modified:
        lines.append("Modified files:\n" + modified)
    print("\n".join(lines))


ACTIONS = {
    "pre-tool-policy": pre_tool_policy,
    "validate-gameplay-code": validate_gameplay_code,
    "post-edit-checks": post_edit_checks,
    "session-context": session_context,
}


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] not in ACTIONS:
        print(f"Usage: {Path(sys.argv[0]).name} <{'|'.join(ACTIONS)}>", file=sys.stderr)
        return 2
    ACTIONS[sys.argv[1]](load_payload())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
