import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import aseprite_core as core


class FindAsepriteBinaryTests(unittest.TestCase):
    def test_prefers_explicit_binary_path(self):
        explicit_path = "/custom/Aseprite"

        result = core.find_aseprite_binary(
            binary_path=explicit_path,
            env={},
            which_fn=lambda _: None,
            exists_fn=lambda candidate: candidate == explicit_path,
            platform_name="darwin",
        )

        self.assertTrue(result.found)
        self.assertEqual(result.path, explicit_path)
        self.assertEqual(result.source, "explicit")

    def test_uses_env_before_path_lookup(self):
        env_path = "/env/Aseprite"

        result = core.find_aseprite_binary(
            env={"ASEPRITE_BIN": env_path},
            which_fn=lambda _: "/usr/bin/aseprite",
            exists_fn=lambda candidate: candidate == env_path,
            platform_name="linux",
        )

        self.assertTrue(result.found)
        self.assertEqual(result.path, env_path)
        self.assertEqual(result.source, "env")

    def test_falls_back_to_path_lookup(self):
        path_result = "/usr/local/bin/aseprite"

        result = core.find_aseprite_binary(
            env={},
            which_fn=lambda _: path_result,
            exists_fn=lambda _: False,
            platform_name="linux",
        )

        self.assertTrue(result.found)
        self.assertEqual(result.path, path_result)
        self.assertEqual(result.source, "path")


class BuildCommandsTests(unittest.TestCase):
    def test_build_export_sprite_sheet_command_places_pre_sprite_flags_first(self):
        command = core.build_export_sprite_sheet_command(
            binary="aseprite",
            sprite_path="/tmp/hero.aseprite",
            sheet_path="/tmp/out/hero-sheet.png",
            data_path="/tmp/out/hero-sheet.json",
            sheet_type="columns",
            layer="Body Layer",
            all_layers=True,
            ignore_layers=["Guides"],
            split_layers=True,
            split_tags=True,
            tag="walk",
            ignore_empty=True,
            merge_duplicates=True,
            border_padding=2,
            shape_padding=1,
            inner_padding=3,
            trim=True,
            trim_sprite=True,
            extrude=True,
            list_layers=True,
            list_tags=True,
            list_slices=True,
            preview=True,
        )

        self.assertEqual(
            command,
            [
                "aseprite",
                "--batch",
                "--all-layers",
                "--ignore-layer",
                "Guides",
                "--layer",
                "Body Layer",
                "--split-layers",
                "--split-tags",
                "--tag",
                "walk",
                "/tmp/hero.aseprite",
                "--sheet",
                "/tmp/out/hero-sheet.png",
                "--data",
                "/tmp/out/hero-sheet.json",
                "--format",
                "json-hash",
                "--sheet-type",
                "columns",
                "--ignore-empty",
                "--merge-duplicates",
                "--border-padding",
                "2",
                "--shape-padding",
                "1",
                "--inner-padding",
                "3",
                "--trim",
                "--trim-sprite",
                "--extrude",
                "--list-layers",
                "--list-tags",
                "--list-slices",
                "--preview",
            ],
        )

    def test_build_export_frames_command_supports_split_modes(self):
        command = core.build_export_frames_command(
            binary="aseprite",
            sprite_path="/tmp/player.aseprite",
            output_path="/tmp/out/player-{tag}-{frame1}.png",
            all_layers=True,
            split_layers=True,
            split_tags=True,
            split_slices=True,
            one_frame=True,
            ignore_empty=True,
            preview=True,
        )

        self.assertEqual(
            command,
            [
                "aseprite",
                "--batch",
                "--all-layers",
                "--split-layers",
                "--split-tags",
                "--split-slices",
                "--oneframe",
                "/tmp/player.aseprite",
                "--ignore-empty",
                "--save-as",
                "/tmp/out/player-{tag}-{frame1}.png",
                "--preview",
            ],
        )

    def test_build_inspect_command_uses_json_stdout(self):
        command = core.build_inspect_command(
            binary="aseprite",
            sprite_path="/tmp/ui.aseprite",
            include_slices=True,
        )

        self.assertEqual(
            command,
            [
                "aseprite",
                "--batch",
                "--list-layers",
                "--list-tags",
                "--list-slices",
                "--data=",
                "/tmp/ui.aseprite",
            ],
        )

    def test_build_run_script_command_serializes_params(self):
        command = core.build_run_script_command(
            binary="aseprite",
            script_path="/tmp/export.lua",
            sprite_path="/tmp/ui.aseprite",
            script_params={"mode": "atlas", "scale": "2"},
            preview=True,
        )

        self.assertEqual(
            command,
            [
                "aseprite",
                "--batch",
                "--script-param",
                "mode=atlas",
                "--script-param",
                "scale=2",
                "/tmp/ui.aseprite",
                "--script",
                "/tmp/export.lua",
                "--preview",
            ],
        )


class WorkspaceRootInferenceTests(unittest.TestCase):
    def test_infers_repo_root_from_plugin_subdirectory(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_root = Path(tmp_dir) / "repo"
            plugin_dir = repo_root / "plugins" / "aseprite-codex"
            plugin_dir.mkdir(parents=True)
            (repo_root / "AGENTS.md").write_text("# repo root\n", encoding="utf-8")

            result = core.infer_workspace_root(start_dir=str(plugin_dir))

            self.assertEqual(result, str(repo_root.resolve()))


if __name__ == "__main__":
    unittest.main()
