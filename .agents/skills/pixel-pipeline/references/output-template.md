# Pixel Pipeline Output Template

Lee este archivo solo cuando vayas a producir la spec final del pipeline o cuando necesites las validaciones completas.

## Entregable sugerido

1. Convenciones base: resolucion, grid, paleta, render resolution
2. Sprite list: entities, animaciones, frame counts
3. Tileset plan: autotile rules, layers, variantes
4. Atlas strategy: agrupacion por contexto y budget
5. Animation data format: schema o estructura
6. Palette system: base + variants + shader approach
7. Workflow de export: Aseprite, naming, batch export
8. Integration: carga en engine y snippets minimos

## Checklist de validacion

- Paleta consistente
- Tile size consistente
- No hay resoluciones mezcladas
- Filtering nearest en todas las texturas
- Integer scaling
- TextureAtlas definido
- Padding suficiente
- Camera snapping

## Anti-patrones a revisar

- Texturas sueltas en produccion
- Linear filtering
- Rotaciones arbitrarias en pixel art
- Animaciones hardcodeadas
- No camera snap

## Cierre sugerido

- Recomendar `$plan` para convertir el pipeline en tareas
