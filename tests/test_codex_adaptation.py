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

        self.assertEqual(
            {
                "enabled",
                "max_concurrent_threads_per_session",
                "default_subagent_model",
                "default_subagent_reasoning_effort",
                "interrupt_message",
            },
            set(config["agents"]),
        )
        self.assertEqual("gpt-5.6-terra", config["agents"]["default_subagent_model"])
        self.assertTrue(config["features"]["hooks"])

    def test_custom_agents_have_required_codex_fields(self) -> None:
        for path in sorted((ROOT / ".codex" / "agents").glob("*.toml")):
            with self.subTest(path=path.name):
                agent = tomllib.loads(path.read_text(encoding="utf-8"))
                self.assertTrue(agent.get("name"))
                self.assertTrue(agent.get("description"))
                self.assertTrue(agent.get("developer_instructions"))

    def test_custom_agents_use_supported_role_pins_without_repo_dependencies(self) -> None:
        expected = {
            "harness-explorer.toml": "gpt-5.6-luna",
            "harness-implementer.toml": "gpt-5.6-terra",
            "harness-reviewer.toml": "gpt-5.6-terra",
            "prompt-artist.toml": "gpt-6-astra",
            "reviewer.toml": "gpt-6-astra",
            "security-auditor.toml": "gpt-6-astra",
            "ui-reviewer.toml": "gpt-6-astra",
            "task-implementer.toml": "gpt-5.6-sol",
        }
        for name, model in expected.items():
            agent = tomllib.loads(read(f".codex/agents/{name}"))
            self.assertEqual(model, agent["model"], name)
            if name != "prompt-artist.toml":
                self.assertNotIn("plugins/", agent["developer_instructions"], name)

    def test_harness_assets_are_domain_neutral(self) -> None:
        expected_agents = {
            "harness-explorer.toml",
            "harness-implementer.toml",
            "harness-reviewer.toml",
        }
        agent_paths = ROOT / ".codex" / "agents"

        self.assertTrue(expected_agents.issubset({path.name for path in agent_paths.glob("*.toml")}))

        harness_paths = [
            *(agent_paths / name for name in expected_agents),
            ROOT / "plugins" / "core" / "evals" / "orchestrate-manager-worker" / "prompt.md",
        ]
        for path in harness_paths:
            with self.subTest(path=path.name):
                content = path.read_text(encoding="utf-8").lower()
                self.assertNotRegex(content, r"\berp\b|erp_|erp-")

    def test_prompt_artist_uses_one_canonical_reference_set(self) -> None:
        agent = tomllib.loads(read(".codex/agents/prompt-artist.toml"))
        instructions = agent["developer_instructions"]
        reference_root = "plugins/core/references/prompt-artist"

        for name in ("domains.md", "techniques.md", "platforms.md", "text-safety.md"):
            self.assertIn(f"{reference_root}/{name}", instructions)
            self.assertTrue((ROOT / reference_root / name).is_file())

        duplicate_root = ROOT / ".codex" / "agents" / "prompt-artist"
        self.assertFalse(any(duplicate_root.glob("*.md")))

    def test_hooks_are_registered_with_cross_platform_commands(self) -> None:
        hooks = json.loads(read(".codex/hooks.json"))["hooks"]

        self.assertIn("SessionStart", hooks)
        self.assertIn("PreToolUse", hooks)
        self.assertIn("SubagentStop", hooks)
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

    def test_subagent_stop_requires_result_envelope_for_harness_agents(self) -> None:
        result = run_hook(
            "subagent-stop",
            {
                "agent_type": "harness_implementer",
                "last_assistant_message": "Termine la implementacion.",
            },
        )

        self.assertEqual(0, result.returncode, result.stderr)
        response = json.loads(result.stdout)
        self.assertEqual("block", response["decision"])
        self.assertIn("RESULT_ENVELOPE", response["reason"])

    def test_subagent_stop_rejects_invalid_result_envelope(self) -> None:
        result = run_hook(
            "subagent-stop",
            {
                "agent_type": "harness_implementer",
                "cwd": str(ROOT),
                "last_assistant_message": 'RESULT_ENVELOPE: {"status":"passed"}',
            },
        )

        self.assertEqual(0, result.returncode, result.stderr)
        response = json.loads(result.stdout)
        self.assertEqual("block", response["decision"])
        self.assertIn("task_id", response["reason"])

    def test_subagent_stop_accepts_valid_result_envelope(self) -> None:
        envelope = {
            "task_id": "billing-create-invoice",
            "status": "passed",
            "summary": "Implementado y verificado.",
            "changed_files": ["src/billing/create-invoice.ts"],
            "checks": [{"command": "pnpm test --filter billing", "result": "passed"}],
            "assumptions": [],
            "risks": [],
            "out_of_scope": [],
        }
        result = run_hook(
            "subagent-stop",
            {
                "agent_type": "harness_implementer",
                "cwd": str(ROOT / "tests"),
                "last_assistant_message": "RESULT_ENVELOPE: " + json.dumps(envelope),
            },
        )

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("", result.stdout)

class SkillRegressionTests(unittest.TestCase):
    def test_claude_project_context_stays_small_and_defers_to_canonical_docs(self) -> None:
        claude = read("CLAUDE.md")

        self.assertLessEqual(len(claude.splitlines()), 30)
        self.assertTrue(claude.startswith("@AGENTS.md"))
        self.assertIn("README.md", claude)
        self.assertNotIn("## Skills disponibles", claude)

    def test_secure_scanner_is_native_and_has_fixed_classification(self) -> None:
        self.assertTrue(SECRET_SCANNER.is_file())
        scanner = SECRET_SCANNER.read_text(encoding="utf-8")
        secure = read("plugins/core/skills/secure/SKILL.md")

        self.assertNotIn(".claude/skills", scanner)
        self.assertNotIn(".agents/skills", scanner)
        self.assertIn('"Stripe Publishable Key", r"pk_live_', scanner)
        self.assertIn('"low"', scanner)
        self.assertIn("OWASP", secure)
        self.assertIn("[scan-secrets.py](scripts/scan-secrets.py)", secure)

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
