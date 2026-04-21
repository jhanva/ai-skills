---
name: tileset-spec
description: >-
  Define tileset specifications para zonas o biomes (forest, dungeon, town). Lee art-bible,
  determina tile types con variantes, autotile configuration, layer structure, y formato de
  export. Output: design/tilesets/{zone}-spec.md con tiles catalog y reglas de construccion
  de niveles.
---

# Tileset Specification

## Uso en Codex

- Esta skill esta pensada para invocacion explicita con `$tileset-spec`.
- Trabaja con lecturas puntuales: `rg -n` para buscar, `rg --files` o `find` para listar, y `sed -n` para leer solo el fragmento necesario.
- Si falta contexto menor, propone un catalogo base razonable y dejalo explicito; pregunta solo por decisiones que cambian biome, collision o autotile.
- Delega solo si el usuario pidio paralelismo o delegacion.

Specs para tilesets de zonas/biomes: tile types, autotile, layers, variantes, y export. Output: `design/tilesets/{zone}-spec.md`.

## FASE 1: Leer art-bible y level context

Leer `design/art-bible.md` para: tile size, paleta, grid alignment, perspective. Buscar referencias de la zona en `design/levels/` o `design/world-map.md`.

Si no hay tile size definido: ERROR. Si la zona no aparece en level docs: ADVERTIR.

## FASE 2: Clasificar biome

Definir tema visual: palette dominante, mood, y elementos visuales unicos del biome.

Biomes comunes: Forest (verde, organico), Dungeon (gris, claustrofobico), Town (marron, civilizado), Desert (amarillo, arido), Cave (marron oscuro, subterraneo), Snow (blanco, frio).

## FASE 3: Tile types con variantes

Catalogo completo. Tabla: `type → variants → autotile → collision → notes`.

Categorias:
- **Terrain** (base layer): 1x1, autotile si conecta con otros terrains
- **Walls** (collision): 1x1 con autotile para corners, siempre solid
- **Decorations** (objects): 1x1 sin collision, multiple variantes para diversity
- **Large props** (objects): multi-tile (trees 2x3, boulders 2x2), collision parcial
- **Interactables** (events): chests, doors, switches — trigger collision

Specs: minimo 10 tile types, maximo 50, cada uno con 1-5 variantes.

## FASE 4: Autotile configuration

**4-bit (16 tiles)**: detecta 4 direcciones. Usar para: caminos, transiciones simples.

**8-bit (47 tiles)**: detecta 8 direcciones (cardinal + diagonales). Usar para: walls, cliffs, plataformas que necesitan inner/outer corners.

Decision matrix: tabla `tile type → sistema → razon`.

## FASE 5: Layer structure

| Layer | Z-Index | Purpose | Collision | Contenido |
|-------|---------|---------|-----------|-----------|
| Ground | 0 | Base terrain | No | Grass, dirt, stone floor |
| Ground Deco | 1 | Detalles terrain | No | Cracks, puddles, tufts |
| Objects | 2 | Props y obstaculos | Yes (Y-sort) | Rocks, bushes, tree trunks |
| Above | 3 | Sobre el player | No | Tree foliage, roof overhangs |

Regla: Objects layer con Y-sort enabled para depth effect.

## FASE 6: Variantes y visual diversity

- **Terrain**: 3-4 variantes (random selection, se ve natural)
- **Decorations**: 5-7 variantes (flowers con colores diferentes)
- **Walls**: 1 base (autotile genera diversity) + opcionales (cracked, mossy)

## FASE 7: Export format y atlas layout

**Tileset atlas** (recomendado): grid del tile size, organizacion logica (terrain arriba, walls medio, props abajo), margin/spacing 0px.

Naming: `{zone}_tileset.png` o separar en `{zone}_{category}.png`.

Metadata: TileSet resource (.tres) con atlas, autotile configs, collision shapes, custom data.

## FASE 8: Generar spec document

Escribir `design/tilesets/{zone}-spec.md` con: biome, tile size, palette, visual theme, tile types tabla, autotile config, layers, atlas layout, variant counts, export checklist, Godot integration notes.

## FASE 9: Validaciones finales

- Tile count total <= 256 (cabe en atlas 16x16)
- Autotile configs correctas (4-bit=16, 8-bit=47)
- Todos los tiles tienen layer asignado
- Variant counts razonables
- Collision definida para tiles solid
