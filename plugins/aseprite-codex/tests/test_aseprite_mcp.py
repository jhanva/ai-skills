import sys
import unittest
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import aseprite_mcp as mcp


class FakeOperations:
    def detect(self, **_kwargs):
        return {
            "found": True,
            "path": "/Applications/Aseprite.app/Contents/MacOS/aseprite",
            "source": "path",
            "version": "Aseprite 1.3.0",
        }

    def inspect(self, **kwargs):
        return {
            "sprite_path": kwargs["sprite_path"],
            "layers": ["Base", "Shadow"],
            "tags": ["idle", "walk"],
            "slices": ["cursor"],
        }

    def export_sprite_sheet(self, **kwargs):
        return {
            "command": ["aseprite", "--batch", kwargs["sprite_path"]],
            "returncode": 0,
            "sheet_path": kwargs["sheet_path"],
        }

    def export_frames(self, **kwargs):
        return {
            "command": ["aseprite", "--batch", kwargs["sprite_path"]],
            "returncode": 0,
            "output_path": kwargs["output_path"],
        }

    def run_script(self, **kwargs):
        return {
            "command": ["aseprite", "--script", kwargs["script_path"]],
            "returncode": 0,
            "script_path": kwargs["script_path"],
        }


class ErrorOperations(FakeOperations):
    def inspect(self, **_kwargs):
        raise RuntimeError("broken inspect")


class AsepriteMCPServerTests(unittest.TestCase):
    def test_initialize_returns_tools_capability(self):
        server = mcp.AsepriteMCPServer(FakeOperations())

        response = server.handle_message(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {},
                    "clientInfo": {"name": "tests", "version": "1.0"},
                },
            }
        )

        self.assertEqual(response["result"]["serverInfo"]["name"], "aseprite-codex")
        self.assertIn("tools", response["result"]["capabilities"])

    def test_tools_list_returns_aseprite_tools(self):
        server = mcp.AsepriteMCPServer(FakeOperations())

        response = server.handle_message(
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list",
                "params": {},
            }
        )

        tool_names = [tool["name"] for tool in response["result"]["tools"]]
        self.assertEqual(
            tool_names,
            [
                "aseprite_detect",
                "aseprite_inspect",
                "aseprite_export_sprite_sheet",
                "aseprite_export_frames",
                "aseprite_run_script",
            ],
        )

    def test_tools_call_returns_structured_content(self):
        server = mcp.AsepriteMCPServer(FakeOperations())

        response = server.handle_message(
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "aseprite_inspect",
                    "arguments": {"sprite_path": "/tmp/ui.aseprite"},
                },
            }
        )

        self.assertFalse(response["result"].get("isError", False))
        self.assertEqual(
            response["result"]["structuredContent"]["layers"],
            ["Base", "Shadow"],
        )

    def test_tool_failures_are_reported_as_tool_results(self):
        server = mcp.AsepriteMCPServer(ErrorOperations())

        response = server.handle_message(
            {
                "jsonrpc": "2.0",
                "id": 4,
                "method": "tools/call",
                "params": {
                    "name": "aseprite_inspect",
                    "arguments": {"sprite_path": "/tmp/ui.aseprite"},
                },
            }
        )

        self.assertTrue(response["result"]["isError"])
        self.assertIn("broken inspect", response["result"]["content"][0]["text"])


class AsepriteOperationsWorkspaceTests(unittest.TestCase):
    def test_inspect_uses_inferred_workspace_root_for_relative_paths(self):
        server = mcp.AsepriteOperations()
        original_find_binary = mcp.core.find_aseprite_binary
        original_infer_workspace_root = mcp.core.infer_workspace_root
        original_run_command = mcp.core.run_command
        captured: dict[str, object] = {}

        try:
            mcp.core.find_aseprite_binary = lambda **_kwargs: mcp.core.BinaryDetectionResult(
                found=True,
                path="/usr/local/bin/aseprite",
                source="path",
                checked_paths=["/usr/local/bin/aseprite"],
            )
            mcp.core.infer_workspace_root = lambda start_dir=None: "/workspace"

            def fake_run_command(command, *, cwd=None, timeout_seconds=300):
                captured["command"] = command
                captured["cwd"] = cwd
                return {"returncode": 0, "stdout": "{\"meta\": {}}", "stderr": ""}

            mcp.core.run_command = fake_run_command

            result = server.inspect(sprite_path="assets/player.aseprite")

            self.assertEqual(captured["cwd"], "/workspace")
            self.assertEqual(
                captured["command"],
                [
                    "/usr/local/bin/aseprite",
                    "--batch",
                    "--list-layers",
                    "--list-tags",
                    "--list-slices",
                    "--data=",
                    "/workspace/assets/player.aseprite",
                ],
            )
            self.assertEqual(result["sprite_path"], "/workspace/assets/player.aseprite")
        finally:
            mcp.core.find_aseprite_binary = original_find_binary
            mcp.core.infer_workspace_root = original_infer_workspace_root
            mcp.core.run_command = original_run_command


if __name__ == "__main__":
    unittest.main()
