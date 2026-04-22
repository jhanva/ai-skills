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
        return ["/Applications/Aseprite.app/Contents/MacOS/aseprite"]
    if platform_name.startswith("win"):
        return [
            r"C:\Program Files\Aseprite\Aseprite.exe",
            r"C:\Program Files (x86)\Aseprite\Aseprite.exe",
        ]
    return ["/usr/local/bin/aseprite", "/usr/bin/aseprite", "/snap/bin/aseprite"]


def find_aseprite_binary(
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

    env_path = env.get("ASEPRITE_BIN")
    if env_path:
        candidates.append((env_path, "env", False))

    path_candidate = which_fn("aseprite")
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


def resolve_path(path_value: str, workspace_root: str | None = None) -> str:
    path = Path(path_value)
    if path.is_absolute():
        return str(path)
    base = Path(workspace_root).resolve() if workspace_root else Path(infer_workspace_root()).resolve()
    return str((base / path).resolve())


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


def ensure_parent_directory(path_value: str) -> None:
    Path(path_value).parent.mkdir(parents=True, exist_ok=True)


def _append_flag(command: list[str], flag: str, enabled: bool) -> None:
    if enabled:
        command.append(flag)


def _append_value(command: list[str], flag: str, value: str | int | None) -> None:
    if value is None:
        return
    command.extend([flag, str(value)])


def _append_repeated(command: list[str], flag: str, values: Sequence[str] | None) -> None:
    for value in values or []:
        command.extend([flag, value])


def build_export_sprite_sheet_command(
    *,
    binary: str,
    sprite_path: str,
    sheet_path: str,
    data_path: str | None = None,
    data_format: str = "json-hash",
    sheet_type: str = "packed",
    sheet_width: int | None = None,
    sheet_height: int | None = None,
    layer: str | None = None,
    ignore_layers: Sequence[str] | None = None,
    all_layers: bool = False,
    split_layers: bool = False,
    split_tags: bool = False,
    split_slices: bool = False,
    split_grid: bool = False,
    export_tileset: bool = False,
    tag: str | None = None,
    frame_tag: str | None = None,
    frame_range: str | None = None,
    ignore_empty: bool = False,
    merge_duplicates: bool = False,
    border_padding: int | None = None,
    shape_padding: int | None = None,
    inner_padding: int | None = None,
    trim: bool = False,
    trim_sprite: bool = False,
    extrude: bool = False,
    list_layers: bool = False,
    list_tags: bool = False,
    list_slices: bool = False,
    preview: bool = False,
) -> list[str]:
    command = [binary, "--batch"]
    _append_flag(command, "--all-layers", all_layers)
    _append_repeated(command, "--ignore-layer", ignore_layers)
    _append_value(command, "--layer", layer)
    _append_flag(command, "--split-layers", split_layers)
    _append_flag(command, "--split-tags", split_tags)
    _append_flag(command, "--split-slices", split_slices)
    _append_flag(command, "--split-grid", split_grid)
    _append_flag(command, "--export-tileset", export_tileset)
    _append_value(command, "--tag", tag)
    _append_value(command, "--frame-tag", frame_tag)
    _append_value(command, "--frame-range", frame_range)
    command.append(sprite_path)
    command.extend(["--sheet", sheet_path])
    if data_path:
        command.extend(["--data", data_path, "--format", data_format])
    _append_value(command, "--sheet-type", sheet_type)
    _append_value(command, "--sheet-width", sheet_width)
    _append_value(command, "--sheet-height", sheet_height)
    _append_flag(command, "--ignore-empty", ignore_empty)
    _append_flag(command, "--merge-duplicates", merge_duplicates)
    _append_value(command, "--border-padding", border_padding)
    _append_value(command, "--shape-padding", shape_padding)
    _append_value(command, "--inner-padding", inner_padding)
    _append_flag(command, "--trim", trim)
    _append_flag(command, "--trim-sprite", trim_sprite)
    _append_flag(command, "--extrude", extrude)
    _append_flag(command, "--list-layers", list_layers)
    _append_flag(command, "--list-tags", list_tags)
    _append_flag(command, "--list-slices", list_slices)
    _append_flag(command, "--preview", preview)
    return command


def build_export_frames_command(
    *,
    binary: str,
    sprite_path: str,
    output_path: str,
    layer: str | None = None,
    ignore_layers: Sequence[str] | None = None,
    all_layers: bool = False,
    split_layers: bool = False,
    split_tags: bool = False,
    split_slices: bool = False,
    tag: str | None = None,
    frame_tag: str | None = None,
    frame_range: str | None = None,
    one_frame: bool = False,
    ignore_empty: bool = False,
    preview: bool = False,
) -> list[str]:
    command = [binary, "--batch"]
    _append_flag(command, "--all-layers", all_layers)
    _append_repeated(command, "--ignore-layer", ignore_layers)
    _append_value(command, "--layer", layer)
    _append_flag(command, "--split-layers", split_layers)
    _append_flag(command, "--split-tags", split_tags)
    _append_flag(command, "--split-slices", split_slices)
    _append_flag(command, "--oneframe", one_frame)
    _append_value(command, "--tag", tag)
    _append_value(command, "--frame-tag", frame_tag)
    _append_value(command, "--frame-range", frame_range)
    command.append(sprite_path)
    _append_flag(command, "--ignore-empty", ignore_empty)
    command.extend(["--save-as", output_path])
    _append_flag(command, "--preview", preview)
    return command


def build_inspect_command(
    *,
    binary: str,
    sprite_path: str,
    include_slices: bool = True,
) -> list[str]:
    command = [binary, "--batch", "--list-layers", "--list-tags"]
    if include_slices:
        command.append("--list-slices")
    command.extend(["--data=", sprite_path])
    return command


def build_run_script_command(
    *,
    binary: str,
    script_path: str,
    sprite_path: str | None = None,
    script_params: Mapping[str, str] | None = None,
    preview: bool = False,
) -> list[str]:
    command = [binary, "--batch"]
    for key, value in (script_params or {}).items():
        command.extend(["--script-param", f"{key}={value}"])
    if sprite_path:
        command.append(sprite_path)
    command.extend(["--script", script_path])
    _append_flag(command, "--preview", preview)
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


def get_aseprite_version(binary_path: str) -> str | None:
    result = run_command([binary_path, "--version"], timeout_seconds=30)
    if result["returncode"] != 0:
        return None
    output = f"{result['stdout']}\n{result['stderr']}".strip()
    return output.splitlines()[0] if output else None


def format_command_error(action: str, result: Mapping[str, object]) -> str:
    stdout = str(result.get("stdout", "")).strip()
    stderr = str(result.get("stderr", "")).strip()
    details = stderr or stdout or "Aseprite returned no error details."
    return f"{action} failed with exit code {result.get('returncode')}: {details}"


def dump_json_text(payload: Mapping[str, object]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True)
