from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Mapping, Sequence


ExistsFn = Callable[[str], bool]
WhichFn = Callable[[str], str | None]
WORKSPACE_MARKERS = (".git", "AGENTS.md")


@dataclass(frozen=True)
class BinaryDetectionResult:
    found: bool
    path: str | None
    source: str | None
    checked_paths: list[str]


def _default_exists(candidate: str) -> bool:
    return Path(candidate).exists()


def _platform_candidates(platform_name: str) -> list[str]:
    if platform_name.startswith("darwin"):
        return [
            "/Applications/Godot.app/Contents/MacOS/Godot",
            "/Applications/Godot_mono.app/Contents/MacOS/Godot",
        ]
    if platform_name.startswith("win"):
        return [
            r"C:\Program Files\Godot\Godot.exe",
            r"C:\Program Files\Godot_v4\Godot_v4.exe",
            r"C:\Program Files\Godot\Godot_v4.4-stable_win64.exe",
        ]
    return ["/usr/local/bin/godot", "/usr/bin/godot", "/snap/bin/godot"]


def find_godot_binary(
    binary_path: str | None = None,
    env: Mapping[str, str] | None = None,
    which_fn: WhichFn = shutil.which,
    exists_fn: ExistsFn = _default_exists,
    platform_name: str | None = None,
) -> BinaryDetectionResult:
    env = env or os.environ
    platform_name = platform_name or sys.platform
    checked_paths: list[str] = []
    candidates: list[tuple[str, str, bool]] = []

    if binary_path:
        candidates.append((binary_path, "explicit", False))
        resolved_explicit = which_fn(binary_path)
        if resolved_explicit and resolved_explicit != binary_path:
            candidates.append((resolved_explicit, "explicit", True))

    env_path = env.get("GODOT_BIN")
    if env_path:
        candidates.append((env_path, "env", False))

    for command_name in ("godot", "godot4", "godot-mono", "godot4-mono"):
        path_candidate = which_fn(command_name)
        if path_candidate:
            candidates.append((path_candidate, "path", True))

    for candidate in _platform_candidates(platform_name):
        candidates.append((candidate, "platform-default", False))

    seen: set[str] = set()
    for candidate, source, trusted in candidates:
        if candidate in seen:
            continue
        seen.add(candidate)
        checked_paths.append(candidate)
        if trusted or exists_fn(candidate):
            return BinaryDetectionResult(
                found=True,
                path=candidate,
                source=source,
                checked_paths=checked_paths,
            )

    return BinaryDetectionResult(
        found=False,
        path=None,
        source=None,
        checked_paths=checked_paths,
    )


def infer_workspace_root(
    start_dir: str | None = None,
    markers: Sequence[str] = WORKSPACE_MARKERS,
) -> str:
    current = Path(start_dir).resolve() if start_dir else Path.cwd().resolve()
    candidates = (current, *current.parents)
    for candidate in candidates:
        for marker in markers:
            if (candidate / marker).exists():
                return str(candidate)
    return str(current)


def resolve_path(path_value: str, workspace_root: str | None = None) -> str:
    path = Path(path_value)
    if path.is_absolute():
        return str(path)
    base = Path(workspace_root).resolve() if workspace_root else Path(infer_workspace_root()).resolve()
    return str((base / path).resolve())


def ensure_parent_directory(path_value: str) -> None:
    Path(path_value).parent.mkdir(parents=True, exist_ok=True)


def build_import_command(*, binary: str, project_path: str) -> list[str]:
    return [
        binary,
        "--headless",
        "--path",
        project_path,
        "--import",
    ]


def build_export_command(
    *,
    binary: str,
    project_path: str,
    preset: str,
    output_path: str,
    export_mode: str = "release",
) -> list[str]:
    export_flag = "--export-release" if export_mode == "release" else "--export-debug"
    return [
        binary,
        "--headless",
        "--path",
        project_path,
        export_flag,
        preset,
        output_path,
    ]


def build_run_script_command(
    *,
    binary: str,
    project_path: str,
    script_path: str,
    check_only: bool = False,
    user_args: Sequence[str] | None = None,
) -> list[str]:
    command = [
        binary,
        "--headless",
        "--path",
        project_path,
        "--script",
        script_path,
    ]
    if check_only:
        command.append("--check-only")
    if user_args:
        command.append("--")
        command.extend(user_args)
    return command


def run_command(
    command: Sequence[str],
    *,
    cwd: str | None = None,
    timeout_seconds: int = 300,
) -> dict[str, object]:
    completed = subprocess.run(
        list(command),
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
        check=False,
    )
    return {
        "command": list(command),
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def get_godot_version(binary_path: str) -> str | None:
    result = run_command([binary_path, "--version"], timeout_seconds=30)
    if result["returncode"] != 0:
        return None
    output = f"{result['stdout']}\n{result['stderr']}".strip()
    return output.splitlines()[0] if output else None


def _parse_ini_sections(path: Path) -> dict[str, dict[str, str]]:
    sections: dict[str, dict[str, str]] = {}
    current_section: str | None = None

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith(";"):
            continue
        if line.startswith("[") and line.endswith("]"):
            current_section = line[1:-1]
            sections.setdefault(current_section, {})
            continue
        if "=" not in line or current_section is None:
            continue
        key, value = line.split("=", 1)
        sections[current_section][key.strip()] = value.strip()

    return sections


def _unquote(value: str | None) -> str | None:
    if value is None:
        return None
    if len(value) >= 2 and value[0] == '"' and value[-1] == '"':
        return value[1:-1]
    return value


def read_project_metadata(project_path: str) -> dict[str, object]:
    root = Path(project_path).resolve()
    project_file = root / "project.godot"
    if not project_file.exists():
        raise FileNotFoundError(f"Could not find project.godot in {root}")

    project_sections = _parse_ini_sections(project_file)
    export_file = root / "export_presets.cfg"
    export_sections = _parse_ini_sections(export_file) if export_file.exists() else {}

    application = project_sections.get("application", {})
    autoloads = sorted(project_sections.get("autoload", {}).keys())
    input_actions = sorted(project_sections.get("input", {}).keys())
    export_presets: list[str] = []
    for section_name, values in export_sections.items():
        if not section_name.startswith("preset."):
            continue
        preset_name = _unquote(values.get("name"))
        if preset_name:
            export_presets.append(preset_name)

    return {
        "project_path": str(root),
        "project_name": _unquote(application.get("config/name")),
        "main_scene": _unquote(application.get("run/main_scene")),
        "autoloads": autoloads,
        "input_actions": input_actions,
        "export_presets": export_presets,
        "files": {
            "project_godot": str(project_file),
            "export_presets_cfg": str(export_file) if export_file.exists() else None,
        },
    }


def format_command_error(action: str, result: Mapping[str, object]) -> str:
    stdout = str(result.get("stdout", "")).strip()
    stderr = str(result.get("stderr", "")).strip()
    details = stderr or stdout or "Godot returned no error details."
    return f"{action} failed with exit code {result.get('returncode')}: {details}"


def dump_json_text(payload: Mapping[str, object]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True)
