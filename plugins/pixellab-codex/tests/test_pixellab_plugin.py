import json
import unittest
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]


class PixelLabPluginFilesTests(unittest.TestCase):
    def test_plugin_manifest_exposes_mcp_and_skills(self):
        manifest = json.loads((PLUGIN_ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))

        self.assertEqual(manifest["name"], "pixellab-codex")
        self.assertEqual(manifest["skills"], "./skills/")
        self.assertEqual(manifest["mcpServers"], "./.mcp.json")
        self.assertIn("PixelLab", manifest["interface"]["displayName"])

    def test_mcp_config_points_to_official_pixellab_server(self):
        config = json.loads((PLUGIN_ROOT / ".mcp.json").read_text(encoding="utf-8"))
        server = config["mcpServers"]["pixellab-codex"]

        self.assertEqual(server["url"], "https://api.pixellab.ai/mcp")
        self.assertEqual(server["transport"], "http")
        self.assertIn("Authorization", server["headers"])


if __name__ == "__main__":
    unittest.main()
