---
name: pixellab-workflows
description: >
  Genera assets pixel art con el MCP oficial de PixelLab: personajes con
  direcciones, animaciones, tilesets top-down y sidescroller, tiles isometricos
  y objetos de mapa. Workflow asincrono: crear, capturar ID, poll, descargar.
disable-model-invocation: true
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash
---

# PixelLab Workflows

Usa esta skill cuando los MCP tools de PixelLab esten instalados en Claude Code.

## Primer movimiento

1. Si tools de PixelLab como `create_character` o `create_topdown_tileset` son visibles, usalos directamente.
2. Si los tools no son visibles, informa al usuario que el MCP de PixelLab no esta configurado o autenticado.
3. Prefiere la operacion de asset mas especifica:
   - `create_character` y luego `animate_character` para personajes direccionales
   - `create_topdown_tileset` o `create_sidescroller_tileset` para kits de terreno
   - `create_isometric_tile` para assets isometricos individuales
   - `create_map_object` para props de mapa

## Patron de workflow

- Los tools de creacion de PixelLab son asincronos: retornan IDs primero, luego se hace poll con el tool `get_*` correspondiente.
- Encolar jobs de seguimiento inmediatamente cuando la API lo soporte, luego inspeccionar estado despues.
- Mantener download URLs e IDs generados en la conversacion cuando importen para el siguiente paso.

## Guardrails

- No intentar simular PixelLab con `curl` manual si los MCP tools ya estan disponibles.
- Si Claude Code no tiene los MCP tools de PixelLab cargados, explicar que el plugin o el API token necesita setup.
- Preferir restricciones explicitas de tamano, direcciones y estilo sobre prompts vagos para outputs game-ready.

## Carga just-in-time

- Lee `references/tool-map.md` para un mapa compacto de los tools oficiales del MCP.
