---
name: godot-workflows
description: >
  Inspecciona proyectos Godot 4, corre imports headless, exporta builds y
  ejecuta scripts de automatizacion sin abrir el editor manualmente.
  Usa los MCP tools del servidor local.
disable-model-invocation: true
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash
---

# Godot Workflows

Usa esta skill para automatizacion repetible de Godot 4 desde Claude Code.

## Primer movimiento

1. Si no se conoce la ruta del binario de Godot, llama `godot_detect`.
2. Si la tarea es sobre setup del proyecto, presets, autoloads o input map, llama `godot_project_info` primero.
3. Elige el tool de ejecucion mas especifico:
   - `godot_import_assets` para refrescar import cache y CI-style imports
   - `godot_export_project` para exports release o debug
   - `godot_run_script` para scripts de automatizacion `SceneTree` o `MainLoop`

## Reglas de rutas

- Preferir rutas absolutas.
- Si el prompt usa rutas relativas al repo, pasar `workspace_root`.
- Para automatizacion de scripts, mantener `script_path` como `res://...` cuando el script vive dentro del proyecto.

## Guardrails

- Preferir MCP tools sobre comandos shell manuales para tareas repetibles de Godot.
- Inspeccionar el proyecto antes de exportar cuando el nombre del preset no es seguro.
- Usar `godot_run_script` con `check_only=true` cuando solo se necesita validacion de sintaxis.

## Carga just-in-time

- Lee `references/tool-map.md` para recetas comunes y opciones de argumentos.
