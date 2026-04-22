from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Callable

import aseprite_core as core


SERVER_NAME = "aseprite-codex"
SERVER_VERSION = "0.1.0"
PROTOCOL_VERSION = "2025-06-18"


TOOL_DEFINITIONS = [
    {
        "name": "aseprite_detect",
        "title": "Detect Aseprite",
        "description": "Locate the Aseprite binary and report where it was found.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "binary_path": {
                    "type": "string",
                    "description": "Optional absolute path or command name to check first.",
                }
            },
        },
    },
    {
        "name": "aseprite_inspect",
        "title": "Inspect Aseprite Sprite",
        "description": "Read layer, tag, and slice metadata from an .aseprite file.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "sprite_path": {"type": "string"},
                "workspace_root": {"type": "string"},
                "binary_path": {"type": "string"},
                "include_slices": {"type": "boolean"},
            },
            "required": ["sprite_path"],
        },
    },
    {
        "name": "aseprite_export_sprite_sheet",
        "title": "Export Sprite Sheet",
        "description": "Export a sprite sheet and optional JSON metadata from Aseprite.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "sprite_path": {"type": "string"},
                "sheet_path": {"type": "string"},
                "data_path": {"type": "string"},
                "workspace_root": {"type": "string"},
                "binary_path": {"type": "string"},
                "data_format": {"type": "string", "enum": ["json-hash", "json-array"]},
                "sheet_type": {
                    "type": "string",
                    "enum": ["horizontal", "vertical", "rows", "columns", "packed"],
                },
                "sheet_width": {"type": "integer"},
                "sheet_height": {"type": "integer"},
                "layer": {"type": "string"},
                "ignore_layers": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "all_layers": {"type": "boolean"},
                "split_layers": {"type": "boolean"},
                "split_tags": {"type": "boolean"},
                "split_slices": {"type": "boolean"},
                "split_grid": {"type": "boolean"},
                "export_tileset": {"type": "boolean"},
                "tag": {"type": "string"},
                "frame_tag": {"type": "string"},
                "frame_range": {"type": "string"},
                "ignore_empty": {"type": "boolean"},
                "merge_duplicates": {"type": "boolean"},
                "border_padding": {"type": "integer"},
                "shape_padding": {"type": "integer"},
                "inner_padding": {"type": "integer"},
                "trim": {"type": "boolean"},
                "trim_sprite": {"type": "boolean"},
                "extrude": {"type": "boolean"},
                "list_layers": {"type": "boolean"},
                "list_tags": {"type": "boolean"},
                "list_slices": {"type": "boolean"},
                "preview": {"type": "boolean"},
            },
            "required": ["sprite_path", "sheet_path"],
        },
    },
    {
        "name": "aseprite_export_frames",
        "title": "Export Frames",
        "description": "Export frames or tagged animations from Aseprite to individual files.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "sprite_path": {"type": "string"},
                "output_path": {"type": "string"},
                "workspace_root": {"type": "string"},
                "binary_path": {"type": "string"},
                "layer": {"type": "string"},
                "ignore_layers": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "all_layers": {"type": "boolean"},
                "split_layers": {"type": "boolean"},
                "split_tags": {"type": "boolean"},
                "split_slices": {"type": "boolean"},
                "tag": {"type": "string"},
                "frame_tag": {"type": "string"},
                "frame_range": {"type": "string"},
                "one_frame": {"type": "boolean"},
                "ignore_empty": {"type": "boolean"},
                "preview": {"type": "boolean"},
            },
            "required": ["sprite_path", "output_path"],
        },
    },
    {
        "name": "aseprite_run_script",
        "title": "Run Aseprite Script",
        "description": "Execute a Lua script through the Aseprite CLI.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "script_path": {"type": "string"},
                "sprite_path": {"type": "string"},
                "workspace_root": {"type": "string"},
                "binary_path": {"type": "string"},
                "script_params": {
                    "type": "object",
                    "additionalProperties": {"type": "string"},
                },
                "preview": {"type": "boolean"},
            },
            "required": ["script_path"],
        },
    },
]


class AsepriteOperations:
    def _normalize_workspace_root(self, workspace_root: str | None) -> str | None:
        if workspace_root:
            return str(Path(workspace_root).resolve())
        return core.infer_workspace_root()

    def _require_binary(self, binary_path: str | None) -> core.BinaryDetectionResult:
        detection = core.find_aseprite_binary(binary_path=binary_path)
        if detection.found:
            return detection

        checked = ", ".join(detection.checked_paths) if detection.checked_paths else "no candidates checked"
        raise RuntimeError(f"Could not find Aseprite. Checked: {checked}")

    def detect(self, **kwargs: Any) -> dict[str, Any]:
        detection = core.find_aseprite_binary(binary_path=kwargs.get("binary_path"))
        version = core.get_aseprite_version(detection.path) if detection.found and detection.path else None
        return {
            "found": detection.found,
            "path": detection.path,
            "source": detection.source,
            "version": version,
            "checked_paths": detection.checked_paths,
        }

    def inspect(
        self,
        *,
        sprite_path: str,
        workspace_root: str | None = None,
        binary_path: str | None = None,
        include_slices: bool = True,
    ) -> dict[str, Any]:
        normalized_root = self._normalize_workspace_root(workspace_root)
        detection = self._require_binary(binary_path)
        resolved_sprite = core.resolve_path(sprite_path, normalized_root)

        command = core.build_inspect_command(
            binary=detection.path or "",
            sprite_path=resolved_sprite,
            include_slices=include_slices,
        )
        result = core.run_command(command, cwd=normalized_root)
        if result["returncode"] != 0:
            raise RuntimeError(core.format_command_error("inspect", result))

        try:
            parsed = json.loads(str(result["stdout"]) or "{}")
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"inspect returned invalid JSON: {exc}") from exc

        meta = parsed.get("meta", {})
        return {
            "sprite_path": resolved_sprite,
            "layers": [layer.get("name") for layer in meta.get("layers", []) if layer.get("name")],
            "tags": [tag.get("name") for tag in meta.get("frameTags", []) if tag.get("name")],
            "slices": [slice_info.get("name") for slice_info in meta.get("slices", []) if slice_info.get("name")],
            "meta": meta,
            "command": command,
        }

    def export_sprite_sheet(self, **kwargs: Any) -> dict[str, Any]:
        normalized_root = self._normalize_workspace_root(kwargs.get("workspace_root"))
        detection = self._require_binary(kwargs.get("binary_path"))
        resolved_sprite = core.resolve_path(kwargs["sprite_path"], normalized_root)
        resolved_sheet = core.resolve_path(kwargs["sheet_path"], normalized_root)
        resolved_data = (
            core.resolve_path(kwargs["data_path"], normalized_root)
            if kwargs.get("data_path")
            else None
        )
        if not kwargs.get("preview", False):
            core.ensure_parent_directory(resolved_sheet)
            if resolved_data:
                core.ensure_parent_directory(resolved_data)

        command = core.build_export_sprite_sheet_command(
            binary=detection.path or "",
            sprite_path=resolved_sprite,
            sheet_path=resolved_sheet,
            data_path=resolved_data,
            data_format=kwargs.get("data_format", "json-hash"),
            sheet_type=kwargs.get("sheet_type", "packed"),
            sheet_width=kwargs.get("sheet_width"),
            sheet_height=kwargs.get("sheet_height"),
            layer=kwargs.get("layer"),
            ignore_layers=kwargs.get("ignore_layers"),
            all_layers=kwargs.get("all_layers", False),
            split_layers=kwargs.get("split_layers", False),
            split_tags=kwargs.get("split_tags", False),
            split_slices=kwargs.get("split_slices", False),
            split_grid=kwargs.get("split_grid", False),
            export_tileset=kwargs.get("export_tileset", False),
            tag=kwargs.get("tag"),
            frame_tag=kwargs.get("frame_tag"),
            frame_range=kwargs.get("frame_range"),
            ignore_empty=kwargs.get("ignore_empty", False),
            merge_duplicates=kwargs.get("merge_duplicates", False),
            border_padding=kwargs.get("border_padding"),
            shape_padding=kwargs.get("shape_padding"),
            inner_padding=kwargs.get("inner_padding"),
            trim=kwargs.get("trim", False),
            trim_sprite=kwargs.get("trim_sprite", False),
            extrude=kwargs.get("extrude", False),
            list_layers=kwargs.get("list_layers", False),
            list_tags=kwargs.get("list_tags", False),
            list_slices=kwargs.get("list_slices", False),
            preview=kwargs.get("preview", False),
        )
        result = core.run_command(command, cwd=normalized_root)
        if result["returncode"] != 0:
            raise RuntimeError(core.format_command_error("export sprite sheet", result))

        return {
            "sprite_path": resolved_sprite,
            "sheet_path": resolved_sheet,
            "data_path": resolved_data,
            "preview": kwargs.get("preview", False),
            "command": command,
            "returncode": result["returncode"],
            "stdout": result["stdout"],
            "stderr": result["stderr"],
        }

    def export_frames(self, **kwargs: Any) -> dict[str, Any]:
        normalized_root = self._normalize_workspace_root(kwargs.get("workspace_root"))
        detection = self._require_binary(kwargs.get("binary_path"))
        resolved_sprite = core.resolve_path(kwargs["sprite_path"], normalized_root)
        resolved_output = core.resolve_path(kwargs["output_path"], normalized_root)
        if not kwargs.get("preview", False):
            core.ensure_parent_directory(resolved_output)

        command = core.build_export_frames_command(
            binary=detection.path or "",
            sprite_path=resolved_sprite,
            output_path=resolved_output,
            layer=kwargs.get("layer"),
            ignore_layers=kwargs.get("ignore_layers"),
            all_layers=kwargs.get("all_layers", False),
            split_layers=kwargs.get("split_layers", False),
            split_tags=kwargs.get("split_tags", False),
            split_slices=kwargs.get("split_slices", False),
            tag=kwargs.get("tag"),
            frame_tag=kwargs.get("frame_tag"),
            frame_range=kwargs.get("frame_range"),
            one_frame=kwargs.get("one_frame", False),
            ignore_empty=kwargs.get("ignore_empty", False),
            preview=kwargs.get("preview", False),
        )
        result = core.run_command(command, cwd=normalized_root)
        if result["returncode"] != 0:
            raise RuntimeError(core.format_command_error("export frames", result))

        return {
            "sprite_path": resolved_sprite,
            "output_path": resolved_output,
            "preview": kwargs.get("preview", False),
            "command": command,
            "returncode": result["returncode"],
            "stdout": result["stdout"],
            "stderr": result["stderr"],
        }

    def run_script(self, **kwargs: Any) -> dict[str, Any]:
        normalized_root = self._normalize_workspace_root(kwargs.get("workspace_root"))
        detection = self._require_binary(kwargs.get("binary_path"))
        resolved_script = core.resolve_path(kwargs["script_path"], normalized_root)
        resolved_sprite = (
            core.resolve_path(kwargs["sprite_path"], normalized_root)
            if kwargs.get("sprite_path")
            else None
        )

        command = core.build_run_script_command(
            binary=detection.path or "",
            script_path=resolved_script,
            sprite_path=resolved_sprite,
            script_params=kwargs.get("script_params"),
            preview=kwargs.get("preview", False),
        )
        result = core.run_command(command, cwd=normalized_root)
        if result["returncode"] != 0:
            raise RuntimeError(core.format_command_error("run script", result))

        return {
            "script_path": resolved_script,
            "sprite_path": resolved_sprite,
            "preview": kwargs.get("preview", False),
            "command": command,
            "returncode": result["returncode"],
            "stdout": result["stdout"],
            "stderr": result["stderr"],
        }


class AsepriteMCPServer:
    def __init__(self, operations: AsepriteOperations | Any | None = None) -> None:
        self.operations = operations or AsepriteOperations()
        self._tool_handlers: dict[str, Callable[..., dict[str, Any]]] = {
            "aseprite_detect": self.operations.detect,
            "aseprite_inspect": self.operations.inspect,
            "aseprite_export_sprite_sheet": self.operations.export_sprite_sheet,
            "aseprite_export_frames": self.operations.export_frames,
            "aseprite_run_script": self.operations.run_script,
        }

    def _response(self, message_id: Any, result: dict[str, Any]) -> dict[str, Any]:
        return {"jsonrpc": "2.0", "id": message_id, "result": result}

    def _error(self, message_id: Any, code: int, message: str) -> dict[str, Any]:
        return {
            "jsonrpc": "2.0",
            "id": message_id,
            "error": {"code": code, "message": message},
        }

    def _tool_result(self, payload: dict[str, Any], *, is_error: bool = False) -> dict[str, Any]:
        text = core.dump_json_text(payload) if not is_error else str(payload["message"])
        result: dict[str, Any] = {
            "content": [{"type": "text", "text": text}],
            "isError": is_error,
        }
        if not is_error:
            result["structuredContent"] = payload
        return result

    def handle_message(self, message: dict[str, Any]) -> dict[str, Any] | None:
        method = message.get("method")
        message_id = message.get("id")

        if method == "initialize":
            return self._response(
                message_id,
                {
                    "protocolVersion": PROTOCOL_VERSION,
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
                },
            )

        if method == "notifications/initialized":
            return None

        if method == "tools/list":
            return self._response(message_id, {"tools": TOOL_DEFINITIONS})

        if method == "tools/call":
            params = message.get("params", {})
            tool_name = params.get("name")
            arguments = params.get("arguments", {}) or {}
            handler = self._tool_handlers.get(tool_name)
            if handler is None:
                return self._error(message_id, -32601, f"Unknown tool: {tool_name}")
            try:
                payload = handler(**arguments)
                return self._response(message_id, self._tool_result(payload))
            except Exception as exc:  # pragma: no cover - exercised via tests
                return self._response(
                    message_id,
                    self._tool_result({"message": str(exc)}, is_error=True),
                )

        if message_id is None:
            return None

        return self._error(message_id, -32601, f"Unsupported method: {method}")


def _write_response(response: dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(response, separators=(",", ":")) + "\n")
    sys.stdout.flush()


def main() -> int:
    server = AsepriteMCPServer()
    for raw_line in sys.stdin:
        line = raw_line.strip()
        if not line:
            continue
        try:
            message = json.loads(line)
        except json.JSONDecodeError as exc:
            print(f"Invalid JSON-RPC message: {exc}", file=sys.stderr)
            continue

        response = server.handle_message(message)
        if response is not None:
            _write_response(response)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
