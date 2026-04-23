import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import godot_core as core


class FindGodotBinaryTests(unittest.TestCase):
    def test_prefers_explicit_binary_path(self):
        explicit_path = "/custom/Godot"

        result = core.find_godot_binary(
            binary_path=explicit_path,
            env={},
            which_fn=lambda _: None,
            exists_fn=lambda candidate: candidate == explicit_path,
            platform_name="linux",
        )

        self.assertTrue(result.found)
        self.assertEqual(result.path, explicit_path)
        self.assertEqual(result.source, "explicit")

    def test_uses_env_before_path_lookup(self):
        env_path = "/env/Godot"

        result = core.find_godot_binary(
            env={"GODOT_BIN": env_path},
            which_fn=lambda _: "/usr/bin/godot",
            exists_fn=lambda candidate: candidate == env_path,
            platform_name="linux",
        )

        self.assertTrue(result.found)
        self.assertEqual(result.path, env_path)
        self.assertEqual(result.source, "env")


class BuildCommandsTests(unittest.TestCase):
    def test_build_import_command_uses_headless_project_path(self):
        command = core.build_import_command(
            binary="godot",
            project_path="/workspace/game",
        )

        self.assertEqual(
            command,
            [
                "godot",
                "--headless",
                "--path",
                "/workspace/game",
                "--import",
            ],
        )

    def test_build_export_command_supports_release_export(self):
        command = core.build_export_command(
            binary="godot",
            project_path="/workspace/game",
            preset="Windows Desktop",
            output_path="/workspace/builds/game.exe",
            export_mode="release",
        )

        self.assertEqual(
            command,
            [
                "godot",
                "--headless",
                "--path",
                "/workspace/game",
                "--export-release",
                "Windows Desktop",
                "/workspace/builds/game.exe",
            ],
        )

    def test_build_run_script_command_supports_check_only_and_user_args(self):
        command = core.build_run_script_command(
            binary="godot",
            project_path="/workspace/game",
            script_path="res://tools/check.gd",
            check_only=True,
            user_args=["--target", "player"],
        )

        self.assertEqual(
            command,
            [
                "godot",
                "--headless",
                "--path",
                "/workspace/game",
                "--script",
                "res://tools/check.gd",
                "--check-only",
                "--",
                "--target",
                "player",
            ],
        )


class ProjectParsingTests(unittest.TestCase):
    def test_read_project_metadata_extracts_core_settings(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            project_root = Path(tmp_dir)
            (project_root / "project.godot").write_text(
                """
; Engine configuration file.
[application]
config/name="Star Garden"
run/main_scene="res://scenes/main.tscn"

[autoload]
GameState="*res://autoload/game_state.gd"

[input]
move_left={"deadzone": 0.5, "events": []}
move_right={"deadzone": 0.5, "events": []}
""".strip(),
                encoding="utf-8",
            )
            (project_root / "export_presets.cfg").write_text(
                """
[preset.0]
name="Windows Desktop"
platform="Windows Desktop"

[preset.1]
name="Web"
platform="Web"
""".strip(),
                encoding="utf-8",
            )

            metadata = core.read_project_metadata(str(project_root))

        self.assertEqual(metadata["project_name"], "Star Garden")
        self.assertEqual(metadata["main_scene"], "res://scenes/main.tscn")
        self.assertEqual(metadata["autoloads"], ["GameState"])
        self.assertEqual(metadata["input_actions"], ["move_left", "move_right"])
        self.assertEqual(metadata["export_presets"], ["Windows Desktop", "Web"])


if __name__ == "__main__":
    unittest.main()
