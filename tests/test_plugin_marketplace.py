import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLUGINS_DIR = ROOT / "plugins"
KEBAB = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    assert match, f"{path} sin frontmatter"
    fields = {}
    for line in match.group(1).splitlines():
        if line and not line.startswith(" ") and ":" in line:
            key, _, value = line.partition(":")
            fields[key.strip()] = value.strip()
    return fields


def plugin_dirs() -> list[Path]:
    return sorted(p for p in PLUGINS_DIR.iterdir() if p.is_dir())


def skill_dirs(plugin: Path) -> list[Path]:
    return sorted(p for p in (plugin / "skills").iterdir() if p.is_dir())


class MarketplaceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.claude = load_json(ROOT / ".claude-plugin" / "marketplace.json")
        self.codex = load_json(ROOT / ".agents" / "plugins" / "marketplace.json")

    def test_claude_marketplace_lists_every_plugin_with_relative_source(self) -> None:
        self.assertEqual("ai-skills", self.claude["name"])
        self.assertTrue(self.claude["owner"]["name"])
        entries = {e["name"]: e for e in self.claude["plugins"]}
        self.assertEqual({p.name for p in plugin_dirs()}, set(entries))
        for name, entry in entries.items():
            self.assertEqual(f"./plugins/{name}", entry["source"])

    def test_codex_marketplace_mirrors_claude_marketplace(self) -> None:
        self.assertEqual(self.claude["name"], self.codex["name"])
        codex_entries = {e["name"]: e["source"] for e in self.codex["plugins"]}
        self.assertEqual({e["name"] for e in self.claude["plugins"]}, set(codex_entries))
        for name, source in codex_entries.items():
            self.assertEqual({"source": "local", "path": f"./plugins/{name}"}, source)

    def test_marketplace_versions_match_plugin_manifests(self) -> None:
        for entry in self.claude["plugins"]:
            manifest = load_json(PLUGINS_DIR / entry["name"] / ".claude-plugin" / "plugin.json")
            self.assertEqual(manifest["version"], entry["version"], entry["name"])


class PluginManifestTests(unittest.TestCase):
    def test_each_plugin_has_claude_and_portable_manifests_in_sync(self) -> None:
        for plugin in plugin_dirs():
            with self.subTest(plugin=plugin.name):
                claude = load_json(plugin / ".claude-plugin" / "plugin.json")
                portable = load_json(plugin / "plugin.json")
                self.assertEqual(plugin.name, claude["name"])
                self.assertRegex(claude["name"], KEBAB)
                for key in ("name", "version", "description"):
                    self.assertEqual(claude[key], portable[key], key)
                self.assertIn("agent-plugins.org", portable["$schema"])

    def test_component_directories_live_at_plugin_root(self) -> None:
        for plugin in plugin_dirs():
            with self.subTest(plugin=plugin.name):
                manifest_dir_entries = [p.name for p in (plugin / ".claude-plugin").iterdir()]
                self.assertEqual(["plugin.json"], manifest_dir_entries)
                self.assertTrue(skill_dirs(plugin))

    def test_agents_directory_contains_only_agent_definitions(self) -> None:
        # Claude Code carga todo .md bajo agents/ como agente: los anexos van a references/.
        for plugin in plugin_dirs():
            agents = plugin / "agents"
            if not agents.is_dir():
                continue
            with self.subTest(plugin=plugin.name):
                for entry in agents.iterdir():
                    self.assertTrue(entry.is_file() and entry.suffix == ".md", entry)
                    self.assertTrue(frontmatter(entry).get("name"), entry)

    def test_plugin_hooks_reference_scripts_through_plugin_root(self) -> None:
        for plugin in plugin_dirs():
            hooks_file = plugin / "hooks" / "hooks.json"
            if not hooks_file.is_file():
                continue
            with self.subTest(plugin=plugin.name):
                hooks = load_json(hooks_file)["hooks"]
                handlers = [h for groups in hooks.values() for g in groups for h in g["hooks"]]
                self.assertTrue(handlers)
                for handler in handlers:
                    command = handler["command"]
                    script = re.search(r'\$\{CLAUDE_PLUGIN_ROOT\}"?/([^\s"]+)', command)
                    self.assertIsNotNone(script, command)
                    self.assertTrue((plugin / script.group(1)).is_file(), script.group(1))


class SkillLayoutTests(unittest.TestCase):
    def setUp(self) -> None:
        self.skills = [s for p in plugin_dirs() for s in skill_dirs(p)]
        self.assertGreaterEqual(len(self.skills), 21)

    def test_skill_names_are_unique_and_match_directory(self) -> None:
        names = [frontmatter(s / "SKILL.md")["name"] for s in self.skills]
        self.assertEqual(len(names), len(set(names)))
        for skill, name in zip(self.skills, names):
            self.assertEqual(skill.name, name)

    def test_each_skill_declares_codex_invocation_policy(self) -> None:
        for skill in self.skills:
            with self.subTest(skill=skill.name):
                policy = (skill / "agents" / "openai.yaml").read_text(encoding="utf-8")
                self.assertIn("allow_implicit_invocation:", policy)
                explicit_only = "disable-model-invocation: true" in (skill / "SKILL.md").read_text(
                    encoding="utf-8"
                )
                self.assertEqual(explicit_only, "allow_implicit_invocation: false" in policy)

    def test_skill_files_stay_under_500_lines_and_avoid_layer_paths(self) -> None:
        for skill in self.skills:
            with self.subTest(skill=skill.name):
                text = (skill / "SKILL.md").read_text(encoding="utf-8")
                self.assertLess(len(text.splitlines()), 500)
                self.assertNotIn(".claude/skills/", text)
                self.assertNotIn(".agents/skills/", text)


if __name__ == "__main__":
    unittest.main()
