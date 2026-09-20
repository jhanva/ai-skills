import importlib.util
import io
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "link-user-skills.py"


def load_linker():
    spec = importlib.util.spec_from_file_location("link_user_skills", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class LinkUserSkillsTests(unittest.TestCase):
    def test_dry_run_lists_core_without_writing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "skills"
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--plugin",
                    "core",
                    "--target",
                    str(target),
                    "--dry-run",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(0, result.returncode, result.stderr)
            self.assertIn("brainstorm", result.stdout)
            self.assertFalse(target.exists())

    def test_plan_preserves_existing_unrelated_skills(self) -> None:
        linker = load_linker()
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "skills"
            target.mkdir(parents=True)
            unrelated = target / "personal"
            unrelated.mkdir()

            plan = linker.build_plan(ROOT, target, ["core"])

            self.assertTrue(unrelated.is_dir())
            self.assertIn("brainstorm", {item.name for item in plan})
            self.assertNotIn("personal", {item.name for item in plan})

    @unittest.skipIf(os.name == "nt", "La auditoria real de symlinks de Windows cubre permisos")
    def test_create_and_remove_only_managed_links(self) -> None:
        linker = load_linker()
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "skills"
            plan = linker.build_plan(ROOT, target, ["core"])
            self.assertEqual([], linker.apply_links(plan, dry_run=False))
            self.assertTrue((target / "brainstorm").is_symlink())
            self.assertEqual([], linker.remove_links(plan, dry_run=False))
            self.assertFalse((target / "brainstorm").exists())

    @unittest.skipUnless(os.name == "nt", "Las junctions solo existen en Windows")
    def test_create_and_remove_windows_junctions(self) -> None:
        linker = load_linker()
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "skills"
            plan = linker.build_plan(ROOT, target, ["core"])
            with redirect_stdout(io.StringIO()):
                errors = linker.apply_links(plan, dry_run=False, junction=True)
            self.assertEqual([], errors)
            self.assertTrue(linker.same_link(target / "brainstorm", plan[0].source))
            with redirect_stdout(io.StringIO()):
                errors = linker.remove_links(plan, dry_run=False)
            self.assertEqual([], errors)
            self.assertFalse((target / "brainstorm").exists())


if __name__ == "__main__":
    unittest.main()
