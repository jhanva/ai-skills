# Tool Map

## Cuando usar cada tool

- `godot_detect`
  Cuando el usuario pregunta si Godot esta instalado, da una ruta custom al binario, o un comando de automatizacion falla porque no encuentra el ejecutable.

- `godot_project_info`
  Antes de exports o trabajo de setup cuando necesitas metadata de `project.godot`, nombres de export presets, autoloads o input actions.

- `godot_import_assets`
  Para refrescar imports en CI o despues de cambios grandes de assets sin abrir el editor UI.

- `godot_export_project`
  Para exports release o debug manejados por `export_presets.cfg`.

- `godot_run_script`
  Para scripts de automatizacion custom que heredan de `SceneTree` o `MainLoop`.

## Recetas comunes

### Leer export presets de un proyecto

- tool: `godot_project_info`
- args requeridos:
  - `project_path`

### Refrescar imports antes de un export

- tool: `godot_import_assets`
- args requeridos:
  - `project_path`

### Exportar un release build

- tool: `godot_export_project`
- args requeridos:
  - `project_path`
  - `preset`
  - `output_path`
- args opcionales comunes:
  - `export_mode="release"`

### Validar sintaxis de un script de automatizacion

- tool: `godot_run_script`
- args requeridos:
  - `project_path`
  - `script_path`
- args opcionales comunes:
  - `check_only=true`
