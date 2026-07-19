# Game Arch — Persistencia y rendering en Godot 4

Lee este archivo solo cuando definas persistencia o rendering.

## Save system

Usa un formato versionado y datos primitivos. Baseline:

- `FileAccess` para leer/escribir
- `JSON` si el save debe ser inspeccionable
- `store_var()`/`get_var()` si prima simplicidad binaria
- `ConfigFile` para settings, no para world state grande
- `ResourceSaver` solo para recursos propios controlados; no deserializar
  Resources arbitrarios de una fuente no confiable

Guarda IDs y paths estables, no referencias a nodos vivos. No serialices estado
derivado que pueda recalcularse. Incluye `save_version` y una migracion por
version.

Para escritura segura, escribe primero a un temporal, valida y reemplaza el save
anterior. Conserva backup antes de migrar; si una migracion falla, no destruyas
el ultimo save valido.

## Lifecycle

- `preload()`: recursos pequenos conocidos al parsear
- `load()`: carga condicional
- `ResourceLoader.load_threaded_request()`: escenas o recursos pesados
- `queue_free()`: nodos al final del frame
- Resources: refcount; nodos: lifecycle del scene tree

Busca `remove_child()` sin `queue_free()` y conexiones persistentes a autoloads.
Ambos pueden dejar nodos huerfanos o callbacks muertos.

## Rendering 2D

Checklist:

- `z_index`/`y_sort_enabled` definidos por capa
- nearest filtering e integer scaling para pixel art
- atlas o `SpriteFrames` por contexto, no un atlas global gigante
- no crear `ImageTexture`, materiales o shaders cada frame
- camera snapping y physics interpolation coherentes
- CanvasLayers separados para world, effects y UI

Godot ya agrupa draw calls cuando materiales y texturas lo permiten. No apliques
consejos de `SpriteBatch.begin()/end()` o `dispose()` de LibGDX: no corresponden
al lifecycle de Godot.
