# Tool Map

## When to use each tool

- `godot_detect`
  Use when the user asks whether Godot is installed, provides a custom binary path, or an automation command fails because the executable cannot be found.

- `godot_project_info`
  Use before exports or setup work when you need `project.godot` metadata, export preset names, autoloads, or input actions.

- `godot_import_assets`
  Use to refresh imports in CI or after large asset changes without opening the editor UI.

- `godot_export_project`
  Use for release or debug exports driven by `export_presets.cfg`.

- `godot_run_script`
  Use for custom automation scripts that inherit from `SceneTree` or `MainLoop`.

## Common recipes

### Read a project's export presets

- tool: `godot_project_info`
- required args:
  - `project_path`

### Refresh imports before an export

- tool: `godot_import_assets`
- required args:
  - `project_path`

### Export a release build

- tool: `godot_export_project`
- required args:
  - `project_path`
  - `preset`
  - `output_path`
- common optional args:
  - `export_mode="release"`

### Syntax-check an automation script

- tool: `godot_run_script`
- required args:
  - `project_path`
  - `script_path`
- common optional args:
  - `check_only=true`
