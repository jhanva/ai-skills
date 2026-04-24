# Tool Map

## Cuando usar cada tool

- `aseprite_detect`
  Cuando el usuario pregunta si Aseprite esta instalado, da una ruta custom al binario, o un comando falla porque no encuentra el ejecutable.

- `aseprite_inspect`
  Antes de exports que dependan de `layer`, `tag` o slices. Retorna `layers`, `tags`, `slices` y el bloque `meta` raw del JSON output de Aseprite.

- `aseprite_export_sprite_sheet`
  Para exports de atlas, JSON de metadata, tilesets, y workflows de packed sheet.

- `aseprite_export_frames`
  Para workflows de `save-as`: secuencias de frames, thumbnails de un frame, tag splits y layer splits.

- `aseprite_run_script`
  Para automatizacion custom con Lua cuando los flags del CLI no son suficientemente expresivos.

## Recetas comunes

### Packed sprite sheet con JSON

- tool: `aseprite_export_sprite_sheet`
- args requeridos:
  - `sprite_path`
  - `sheet_path`
- args opcionales comunes:
  - `data_path`
  - `sheet_type="packed"`
  - `ignore_empty=true`
  - `merge_duplicates=false`
  - `trim=true`
  - `extrude=true`

### Exportar solo un tag de animacion

- inspeccionar primero para confirmar el nombre del tag
- luego llamar `aseprite_export_frames` con:
  - `sprite_path`
  - `output_path`
  - `tag`
  - opcional `split_layers`

### Dry run antes de exportar

- pasar `preview=true`
- usar antes de exports amplios o cuando el usuario pida "muestrame el comando primero"

## Notas

- `split_layers`, `split_tags` e `ignore-layer` deben decidirse antes de abrir el sprite, por eso el MCP server siempre coloca esos flags antes del archivo de entrada.
- Para rutas de assets relativas al repo, pasar `workspace_root` para evitar resolver rutas relativas al directorio del plugin.
