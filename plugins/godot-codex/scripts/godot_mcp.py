from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Callable

import godot_core as core


SERVER_NAME = "godot-codex"
SERVER_VERSION = "0.1.0"
PROTOCOL_VERSION = "2025-06-18"


TOOL_DEFINITIONS = [
    {
        "name": "godot_detect",
        "title": "Detect Godot",
        "description": "Locate a Godot binary and report the detected version.",
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
        "name": "godot_project_info",
        "title": "Inspect Godot Project",
        "description": "Read project.godot and export_presets.cfg metadata without opening the editor.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_path": {"type": "string"},
                "workspace_root": {"type": "string"},
            },
            "required": ["project_path"],
        },
    },
    {
        "name": "godot_import_assets",
        "title": "Import Godot Assets",
        "description": "Run Godot headless import for a project and wait until imports complete.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_path": {"type": "string"},
                "workspace_root": {"type": "string"},
                "binary_path": {"type": "string"},
                "timeout_seconds": {"type": "integer"},
            },
            "required": ["project_path"],
        },
    },
    {
        "name": "godot_export_project",
        "title": "Export Godot Project",
        "description": "Export a Godot project using a named export preset.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_path": {"type": "string"},
                "preset": {"type": "string"},
                "output_path": {"type": "string"},
                "export_mode": {"type": "string", "enum": ["release", "debug"]},
                "workspace_root": {"type": "string"},
                "binary_path": {"type": "string"},
                "timeout_seconds": {"type": "integer"},
            },
            "required": ["project_path", "preset", "output_path"],
        },
    },
    {
        "name": "godot_run_script",
        "title": "Run Godot Script",
        "description": "Run a SceneTree/MainLoop script from a Godot project in headless mode.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_path": {"type": "string"},
                "script_path": {"type": "string"},
                "workspace_root": {"type": "string"},
                "binary_path": {"type": "string"},
                "check_only": {"type": "boolean"},
                "user_args": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "timeout_seconds": {"type": "integer"},
            },
            "required": ["project_path", "script_path"],
        },
    },
]


class GodotOperations:
    def _normalize_workspace_root(self, workspace_root: str | None) -> str:
        if workspace_root:
            return str(Path(workspace_root).resolve())
        return core.infer_workspace_root()

    def _resolve_project_path(self, project_path: str, workspace_root: str | None) -> str:
        normalized_root = self._normalize_workspace_root(workspace_root)
        return core.resolve_path(project_path, normalized_root)

    def _require_binary(self, binary_path: str | None) -> core.BinaryDetectionResult:
        detection = core.find_godot_binary(binary_path=binary_path)
        if detection.found:
            return detection

        checked = ", ".join(detection.checked_paths) if detection.checked_paths else "no candidates checked"
        raise RuntimeError(f"Could not find Godot. Checked: {checked}")

    def detect(self, **kwargs: Any) -> dict[str, Any]:
        detection = core.find_godot_binary(binary_path=kwargs.get("binary_path"))
        version = core.get_godot_version(detection.path) if detection.found and detection.path else None
        return {
            "found": detection.found,
            "path": detection.path,
            "source": detection.source,
            "version": version,
            "checked_paths": detection.checked_paths,
        }

    def project_info(
        self,
        *,
        project_path: str,
        workspace_root: str | None = None,
    ) -> dict[str, Any]:
        resolved_project = self._resolve_project_path(project_path, workspace_root)
        return core.read_project_metadata(resolved_project)

    def import_assets(
        self,
        *,
        project_path: str,
        workspace_root: str | None = None,
        binary_path: str | None = None,
        timeout_seconds: int = 300,
    ) -> dict[str, Any]:
        resolved_project = self._resolve_project_path(project_path, workspace_root)
        detection = self._require_binary(binary_path)
        command = core.build_import_command(
            binary=detection.path or "",
            project_path=resolved_project,
        )
        result = core.run_command(command, cwd=resolved_project, timeout_seconds=timeout_seconds)
        if result["returncode"] != 0:
            raise RuntimeError(core.format_command_error("import_assets", result))
        return {
            **result,
            "project_path": resolved_project,
            "binary_path": detection.path,
        }

    def export_project(
        self,
        *,
        project_path: str,
        preset: str,
        output_path: str,
        export_mode: str = "release",
        workspace_root: str | None = None,
        binary_path: str | None = None,
        timeout_seconds: int = 600,
    ) -> dict[str, Any]:
        resolved_project = self._resolve_project_path(project_path, workspace_root)
        resolved_output = (
            output_path
            if Path(output_path).is_absolute()
            else core.resolve_path(output_path, resolved_project)
        )
        detection = self._require_binary(binary_path)
        core.ensure_parent_directory(resolved_output)
        command = core.build_export_command(
            binary=detection.path or "",
            project_path=resolved_project,
            preset=preset,
            output_path=resolved_output,
            export_mode=export_mode,
        )
        result = core.run_command(command, cwd=resolved_project, timeout_seconds=timeout_seconds)
        if result["returncode"] != 0:
            raise RuntimeError(core.format_command_error("export_project", result))
        return {
            **result,
            "project_path": resolved_project,
            "output_path": resolved_output,
            "preset": preset,
            "export_mode": export_mode,
            "binary_path": detection.path,
        }

    def run_script(
        self,
        *,
        project_path: str,
        script_path: str,
        workspace_root: str | None = None,
        binary_path: str | None = None,
        check_only: bool = False,
        user_args: list[str] | None = None,
        timeout_seconds: int = 300,
    ) -> dict[str, Any]:
        resolved_project = self._resolve_project_path(project_path, workspace_root)
        resolved_script = script_path
        if not script_path.startswith("res://"):
            resolved_script = core.resolve_path(script_path, resolved_project)
        detection = self._require_binary(binary_path)
        command = core.build_run_script_command(
            binary=detection.path or "",
            project_path=resolved_project,
            script_path=resolved_script,
            check_only=check_only,
            user_args=user_args,
        )
        result = core.run_command(command, cwd=resolved_project, timeout_seconds=timeout_seconds)
        if result["returncode"] != 0:
            raise RuntimeError(core.format_command_error("run_script", result))
        return {
            **result,
            "project_path": resolved_project,
            "script_path": resolved_script,
            "check_only": check_only,
            "binary_path": detection.path,
        }


class GodotMCPServer:
    def __init__(self, operations: GodotOperations | None = None) -> None:
        self._operations = operations or GodotOperations()
        self._tool_handlers: dict[str, Callable[..., dict[str, Any]]] = {
            "godot_detect": self._operations.detect,
            "godot_project_info": self._operations.project_info,
            "godot_import_assets": self._operations.import_assets,
            "godot_export_project": self._operations.export_project,
            "godot_run_script": self._operations.run_script,
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
            except Exception as exc:  # pragma: no cover
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
    server = GodotMCPServer()
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
