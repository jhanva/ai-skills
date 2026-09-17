import json
import subprocess
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOOK_SCRIPT = ROOT / ".codex" / "hooks" / "codex_hooks.py"
SECRET_SCANNER = ROOT / "plugins" / "core" / "skills" / "secure" / "scripts" / "scan-secrets.py"


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def run_hook(action: str, payload: dict) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(HOOK_SCRIPT), action],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        cwd=ROOT,
        check=False,
    )


class CodexConfigTests(unittest.TestCase):
    def test_project_config_contains_only_real_agent_settings(self) -> None:
        config = tomllib.loads(read(".codex/config.toml"))

        self.assertEqual({"max_threads", "max_depth"}, set(config["agents"]))
        self.assertTrue(config["features"]["hooks"])

    def test_custom_agents_have_required_codex_fields(self) -> None:
        for path in sorted((ROOT / ".codex" / "agents").glob("*.toml")):
            with self.subTest(path=path.name):
                agent = tomllib.loads(path.read_text(encoding="utf-8"))
                self.assertTrue(agent.get("name"))
                self.assertTrue(agent.get("description"))
                self.assertTrue(agent.get("developer_instructions"))

    def test_hooks_are_registered_with_cross_platform_commands(self) -> None:
        hooks = json.loads(read(".codex/hooks.json"))["hooks"]

        self.assertIn("SessionStart", hooks)
        self.assertIn("PreToolUse", hooks)
        handlers = [
            handler
            for groups in hooks.values()
            for group in groups
            for handler in group["hooks"]
        ]
        self.assertTrue(all("command" in handler for handler in handlers))
        self.assertTrue(all("commandWindows" in handler for handler in handlers))

    def test_model_bump_helper_only_updates_standalone_agent_files(self) -> None:
        helper = read("scripts/bump-codex-model.sh")

        self.assertNotIn("[agents.models]", helper)
        self.assertNotIn("Update .codex/config.toml", helper)
        self.assertIn("python", helper)


class CodexHookTests(unittest.TestCase):
    def test_pre_tool_policy_blocks_env_but_allows_template(self) -> None:
        blocked = run_hook(
            "pre-tool-policy",
            {"tool_name": "Bash", "tool_input": {"command": "Get-Content .env"}},
        )
        allowed = run_hook(
            "pre-tool-policy",
            {"tool_name": "Bash", "tool_input": {"command": "Get-Content .env.example"}},
        )

        self.assertEqual(0, blocked.returncode, blocked.stderr)
        decision = json.loads(blocked.stdout)["hookSpecificOutput"]
        self.assertEqual("deny", decision["permissionDecision"])
        self.assertEqual("", allowed.stdout)

    def test_pre_tool_policy_blocks_destructive_git_command(self) -> None:
        result = run_hook(
            "pre-tool-policy",
            {"tool_name": "Bash", "tool_input": {"command": "git reset --hard"}},
        )

        self.assertEqual("deny", json.loads(result.stdout)["hookSpecificOutput"]["permissionDecision"])

class SkillRegressionTests(unittest.TestCase):
    def test_secure_scanner_is_native_and_has_fixed_classification(self) -> None:
        self.assertTrue(SECRET_SCANNER.is_file())
        scanner = SECRET_SCANNER.read_text(encoding="utf-8")
        secure = read("plugins/core/skills/secure/SKILL.md")

        self.assertNotIn(".claude/skills", scanner)
        self.assertNotIn(".agents/skills", scanner)
        self.assertIn('"Stripe Publishable Key", r"pk_live_', scanner)
        self.assertIn('"low"', scanner)
        self.assertIn("OWASP A03:2021", secure)
        self.assertIn("${CLAUDE_PLUGIN_ROOT}/skills/secure/scripts/scan-secrets.py", secure)

    def test_secure_scanner_detects_a_token_and_help_is_successful(self) -> None:
        help_result = subprocess.run(
            [sys.executable, str(SECRET_SCANNER), "--help"],
            text=True,
            capture_output=True,
            check=False,
        )
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            (target / "config.py").write_text(
                'token = "ghp_' + "a" * 36 + '"\n', encoding="utf-8"
            )
            scan_result = subprocess.run(
                [sys.executable, str(SECRET_SCANNER), str(target)],
                text=True,
                capture_output=True,
                check=False,
            )

        self.assertEqual(0, help_result.returncode, help_result.stderr)
        self.assertEqual(1, scan_result.returncode, scan_result.stderr)
        report = json.loads(scan_result.stdout)
        # Un token especifico no se duplica como "Generic Secret" en la misma linea.
        self.assertEqual(1, report["findings_count"])
        self.assertEqual("GitHub Token (classic)", report["findings"][0]["type"])

    def test_readme_points_to_plugin_skills_and_codex_hooks(self) -> None:
        readme = read("README.md")

        self.assertIn("./plugins/repo-ops/skills/browser-control/SKILL.md", readme)
        self.assertIn(".codex/hooks.json", readme)
        self.assertIn("/plugin marketplace add jhanva/ai-skills", readme)
        self.assertNotIn("./.agents/skills/", readme)
        self.assertNotIn("./.claude/skills/", readme)

    def test_browser_helpers_include_cross_platform_fixes(self) -> None:
        skill = read("plugins/repo-ops/skills/browser-control/SKILL.md")
        helper = read("plugins/repo-ops/skills/browser-control/references/cdp_helpers.py")

        self.assertIn("tempfile", helper)
        self.assertIn("ord(key.upper()[0])", helper)
        self.assertIn("def screenshot(path=None", helper)
        self.assertNotIn('screenshot(path="/tmp/', skill)
        self.assertIn("UI Automation/PowerShell", skill)


if __name__ == "__main__":
    unittest.main()
