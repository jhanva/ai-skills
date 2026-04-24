---
name: aseprite-workflows
description: >
  Inspecciona archivos .aseprite, exporta sprite sheets o frame sequences, y
  automatiza Aseprite con scripts Lua usando los MCP tools del servidor local.
  Prefiere los tools estructurados sobre automatizacion de GUI.
disable-model-invocation: true
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash
---

# Aseprite Workflows

Usa esta skill para tareas repetibles de Aseprite desde Claude Code.

## Primer movimiento

1. Si no se conoce la ruta del binario, llama `aseprite_detect`.
2. Si la tarea menciona layers, tags, slices, o "que tiene este sprite", llama `aseprite_inspect`.
3. Elige el tool de export mas especifico:
   - `aseprite_export_sprite_sheet` para atlas + JSON
   - `aseprite_export_frames` para secuencias de frames, tags o layer splits
   - `aseprite_run_script` solo cuando los flags de export no son suficientes

## Reglas de rutas

- Preferir rutas absolutas.
- Si el prompt usa rutas relativas al repo, pasar `workspace_root` para que el MCP server las resuelva correctamente.
- Usar `preview=true` para validar un comando antes de exports grandes.

## Guardrails

- Preferir MCP tools estructurados sobre comandos shell manuales para cualquier tarea repetible.
- Mantener los outputs cerca del asset fuente a menos que el usuario pida otro destino.
- Cuando un workflow necesita tags/layers y el archivo no ha sido inspeccionado, inspeccionar primero en vez de adivinar nombres.

## Carga just-in-time

- Lee `references/tool-map.md` para recetas comunes y mapeo de argumentos.
