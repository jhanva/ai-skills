import sys
import unittest
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import godot_mcp as mcp


class FakeOperations:
    def detect(self, **_kwargs):
        return {
            "found": True,
            "path": "/usr/local/bin/godot",
            "source": "path",
            "version": "4.4.1.stable",
        }

    def project_info(self, **kwargs):
        return {
            "project_path": kwargs["project_path"],
            "project_name": "Star Garden",
            "export_presets": ["Windows Desktop"],
        }

    def import_assets(self, **kwargs):
        return {
            "command": ["godot", "--headless", "--path", kwargs["project_path"], "--import"],
            "returncode": 0,
        }

    def export_project(self, **kwargs):
        return {
            "command": ["godot", "--headless"],
            "returncode": 0,
            "output_path": kwargs["output_path"],
        }

    def run_script(self, **kwargs):
        return {
            "command": ["godot", "--script", kwargs["script_path"]],
            "returncode": 0,
            "script_path": kwargs["script_path"],
        }


class ErrorOperations(FakeOperations):
    def project_info(self, **_kwargs):
        raise RuntimeError("broken project info")


class GodotMCPServerTests(unittest.TestCase):
    def test_tools_list_returns_godot_tools(self):
        server = mcp.GodotMCPServer(FakeOperations())

        response = server.handle_message(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/list",
                "params": {},
            }
        )

        tool_names = [tool["name"] for tool in response["result"]["tools"]]
        self.assertEqual(
            tool_names,
            [
                "godot_detect",
                "godot_project_info",
                "godot_import_assets",
                "godot_export_project",
                "godot_run_script",
            ],
        )

    def test_tool_calls_return_structured_content(self):
        server = mcp.GodotMCPServer(FakeOperations())

        response = server.handle_message(
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "godot_project_info",
                    "arguments": {"project_path": "/workspace/game"},
                },
            }
        )

        self.assertFalse(response["result"].get("isError", False))
        self.assertEqual(
            response["result"]["structuredContent"]["project_name"],
            "Star Garden",
        )

    def test_tool_failures_are_reported_as_tool_results(self):
        server = mcp.GodotMCPServer(ErrorOperations())

        response = server.handle_message(
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "godot_project_info",
                    "arguments": {"project_path": "/workspace/game"},
                },
            }
        )

        self.assertTrue(response["result"]["isError"])
        self.assertIn("broken project info", response["result"]["content"][0]["text"])


if __name__ == "__main__":
    unittest.main()
