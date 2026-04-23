---
name: godot-workflows
description: Use this skill when the user wants to inspect a Godot 4 project, run headless imports, export builds, or execute automation scripts from Codex without opening the editor manually.
---

# Godot Workflows

Use this skill for repeatable `Godot 4` automation from Codex.

## First move

1. If the Godot binary path is unknown, call `godot_detect`.
2. If the task is about project setup, presets, autoloads, or input map, call `godot_project_info` first.
3. Choose the narrowest execution tool:
   - `godot_import_assets` for import cache refreshes and CI-style imports
   - `godot_export_project` for release or debug exports
   - `godot_run_script` for `SceneTree` or `MainLoop` automation scripts

## Path rules

- Prefer absolute paths.
- If the prompt uses repo-relative paths, pass `workspace_root`.
- For script automation, keep `script_path` as `res://...` when the script lives inside the project.

## Guardrails

- Prefer MCP tools over raw shell commands for repeatable Godot tasks.
- Inspect the project before exporting when the preset name is uncertain.
- Use `godot_run_script` with `check_only=true` when you only need syntax validation.

## Load on demand

- Read `references/tool-map.md` for common command recipes and argument choices.
