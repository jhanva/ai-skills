import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLUGINS = ROOT / "plugins"
SHARED_SKILL_PATTERNS = {
    "slash skill invocation": re.compile(
        r"(?<![$\w])/(?:brainstorm|plan|tdd|review|secure|verify|debug|execute|parallel|"
        r"codegraph|humanize|design-system|ui-review|ui-tokens|image-algo|image-pipeline)\b"
    ),
    "Claude Agent tool": re.compile(r"\bAgent tool\b", re.IGNORECASE),
    "Claude subagent type": re.compile(r"\bsubagent_type\b"),
    "Claude argument macro": re.compile(r"\$ARGUMENTS\b"),
    "Claude plugin root macro": re.compile(r"\$\{CLAUDE_PLUGIN_ROOT\}"),
    "Claude skill root macro": re.compile(r"\$\{CLAUDE_SKILL_DIR\}"),
    "runtime tool name": re.compile(r"\b(?:Read|Write|Edit|Glob|Grep|Bash) tool\b"),
}


def skill_files() -> list[Path]:
    return sorted(PLUGINS.glob("*/skills/*/SKILL.md"))


def shared_instruction_files() -> list[Path]:
    return sorted(PLUGINS.glob("*/skills/**/*.md"))


def description(path: Path) -> str:
    lines = path.read_text(encoding="utf-8").splitlines()
    try:
        start = lines.index("description: >") + 1
    except ValueError as exc:
        raise AssertionError(f"{path} no usa description: >") from exc

    parts = []
    for line in lines[start:]:
        if not line.startswith("  "):
            break
        parts.append(line[2:].strip())
    return " ".join(parts).strip()


class SharedSkillPortabilityTests(unittest.TestCase):
    def test_shared_skill_instructions_do_not_depend_on_one_runtime(self) -> None:
        violations = []
        for path in shared_instruction_files():
            text = path.read_text(encoding="utf-8")
            for label, pattern in SHARED_SKILL_PATTERNS.items():
                for match in pattern.finditer(text):
                    line = text.count("\n", 0, match.start()) + 1
                    violations.append(f"{path.relative_to(ROOT)}:{line}: {label}")

        self.assertEqual([], violations, "\n".join(violations))

    def test_skill_descriptions_fit_initial_context_budget(self) -> None:
        descriptions = {path.parent.name: description(path) for path in skill_files()}
        oversized = {name: len(text) for name, text in descriptions.items() if len(text) > 300}

        self.assertEqual({}, oversized)
        self.assertLessEqual(sum(map(len, descriptions.values())), 5_000)

    def test_agents_file_stays_focused(self) -> None:
        agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        self.assertLessEqual(len(agents), 10_000)

    def test_critical_skills_have_a_no_subagent_fallback(self) -> None:
        for name in ("execute", "review", "secure"):
            with self.subTest(skill=name):
                text = (PLUGINS / "core" / "skills" / name / "SKILL.md").read_text(
                    encoding="utf-8"
                )
                self.assertIn("Fallback sin subagente", text)


if __name__ == "__main__":
    unittest.main()
