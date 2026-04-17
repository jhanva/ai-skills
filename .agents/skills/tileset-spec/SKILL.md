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
- Cuando aqui se indique buscar patrones, usa `rg -n`; para listar archivos, usa `rg --files` o `find`; para leer fragmentos concretos, usa `sed -n`.
- Cuando aqui se hable de subagentes, usa los agentes integrados de Codex o los definidos en `.codex/agents/`, y solo delega si el usuario lo pidio explicitamente.
- Las referencias a `Read/Write/Edit/Grep/Glob/Bash` se traducen segun `AGENTS.md` del repo.

Define specs completas para tilesets de zonas/biomes: tile types, autotile configuration, layers, variantes, y export. Genera catalogo tecnico para producir niveles cohesivos.

## FASE 1: Leer Art-Bible y Level Design Context

**Objetivo**: Cargar restricciones tecnicas y tematica de la zona.

1. Buscar y leer `design/art-bible.md`
2. Extraer datos criticos:
   - Tile size base (ej: 16x16, 32x32)
   - Paleta de colores para este biome
   - Grid alignment (pixel snap, tile snap)
   - Perspective (top-down, side-view, isometric)
3. Buscar referencias de la zona en `design/levels/` o `design/world-map.md`
4. Identificar mood y tematica (forest oscuro, dungeon humedo, town medieval)

**Validaciones**:
- Si no hay tile size definido: ERROR
- Si la zona no aparece en level design docs: ADVERTIR (spec puede ser generica)

---

## FASE 2: Clasificar Biome y Determinar Tema Visual

**Objetivo**: Definir caracteristicas visuales especificas del biome.

### Categorias de biome

| Biome | Palette Dominante | Tile Types Clave | Mood |
|-------|-------------------|------------------|------|
| Forest | Verde, marron, amarillo | Trees, grass, dirt paths, rocks | Natural, organico |
| Dungeon | Gris, negro, azul oscuro | Stone walls, floors, cracks, chains | Claustrofobico, hostil |
| Town | Marron, rojo, beige | Cobblestone, wood planks, roofs, doors | Civilizado, safe |
| Desert | Amarillo, naranja, blanco | Sand, dunes, cacti, ruins | Arido, desolado |
| Cave | Marron, gris, verde oscuro | Rock walls, stalactites, water pools | Subterraneo, misterioso |
| Snow | Blanco, azul claro, gris | Snow, ice, frozen trees | Frio, hostil |

**Elementos visuales por biome**:

**Forest**:
- Terrain: Grass (3 variantes), dirt (2 variantes), mud
- Vegetation: Trees (pine, oak), bushes, flowers, mushrooms
- Props: Fallen logs, stumps, rocks

**Dungeon**:
- Walls: Stone bricks (intact, cracked, mossy)
- Floors: Stone tiles, dirt, water puddles
- Props: Torches, chains, bones, crates

**Town**:
- Streets: Cobblestone, dirt roads
- Buildings: Wood walls, stone walls, roofs (thatch, tile)
- Props: Barrels, crates, signs, lanterns

**Decision**: Especificar palette dominante y lista de elementos visuales unicos del biome.

---

## FASE 3: Definir Tile Types con Variantes

**Objetivo**: Catalogo completo de tiles necesarios para construir niveles.

### Tabla de tile types

| Type | Variants | Autotile | Collision | Notes |
|------|----------|----------|-----------|-------|
| Grass | 3 | No | Walkable | Base terrain, random variants |
| Dirt Path | 2 | 4-bit | Walkable | Connects grass tiles |
| Stone Wall | 1 | 8-bit (47) | Solid | Full autotile (corners, edges) |
| Water | 2 | 4-bit | Solid | Shallow (walkable) vs deep (unwalkable) |
| Tree (tall) | 4 | No | Trunk solid | 2x3 tiles, foliage variants |
| Bush | 3 | No | Walkable | 1x1 decoration |
| Flower | 5 | No | Walkable | Color variants (red, blue, yellow, white, purple) |
| Rock (large) | 2 | No | Solid | 2x2 obstacle |
| Bridge | 1 | No | Walkable | 1x3 horizontal, connects over water |

### Categorias de tiles

**Terrain** (base layer):
- Grass, dirt, sand, stone floor, water, lava
- Siempre 1x1
- Autotile si conecta con otros terrains (transitions)

**Walls** (collision layer):
- Stone walls, wood fences, cliff edges
- 1x1 con autotile para corners
- Siempre solid collision

**Decorations** (objects layer):
- Bushes, flowers, small rocks, grass tufts
- 1x1, no collision
- Multiple color/shape variants para visual diversity

**Large Props** (objects layer):
- Trees (2x3), boulders (2x2), buildings (NxM)
- Multi-tile entities
- Partial collision (ej: tree trunk solid, foliage transparent)

**Interactables** (events layer):
- Chests, doors, switches, NPCs
- 1x1 o 1x2
- Trigger collision (not solid, but detectable)

**Especificaciones**:
- Minimo 10 tile types por tileset
- Maximo 50 tile types (mas alla requiere multiples tilesets)
- Cada tile type debe tener 1-5 variants (visual diversity sin overwhelm)

---

## FASE 4: Autotile Configuration

**Objetivo**: Definir que tiles usan autotile y con que sistema.

### Autotile Systems

**4-bit Autotile (16 tiles)**:
- Detecta 4 direcciones: arriba, abajo, izquierda, derecha
- 2^4 = 16 combinaciones
- Uso: Caminos, transiciones simples (grass-to-dirt)

Layout:
```
[0000] [0001] [0010] [0011]
[0100] [0101] [0110] [0111]
[1000] [1001] [1010] [1011]
[1100] [1101] [1110] [1111]
```

**8-bit Autotile (47 tiles)**:
- Detecta 8 direcciones: cardinal + diagonales
- 47 tiles unicos (eliminando simetrias)
- Uso: Walls, cliffs, plataformas (necesita inner/outer corners)

Layout (simplificado):
```
Full blob tileset con:
- 4 edges (top, bottom, left, right)
- 4 outer corners
- 4 inner corners
- 16 edge combinations
- 1 isolated tile
- Variants con multiple adjacencies
```

**Decision matrix**:

| Tile Type | Sistema | Razon |
|-----------|---------|-------|
| Grass-to-dirt transition | 4-bit | Solo necesita edges, no corners |
| Stone wall | 8-bit | Necesita inner corners para habitaciones |
| Water edge | 4-bit | Transition simple con ground |
| Cliff edge | 8-bit | Platformer necesita outer corners |
| Path | 4-bit | Caminos no requieren corners complejos |

### Configuracion en Godot

**TileSet resource**:
```gdscript
# Para 8-bit autotile (bitmask)
terrain_set = 0
terrain = 0
terrain_peering_bits = {
    "top": true,
    "bottom": true,
    "left": true,
    "right": true,
    "top_left": true,
    "top_right": true,
    "bottom_left": true,
    "bottom_right": true
}
```

**Output**: Tabla de todos los tiles que requieren autotile, especificando 4-bit vs 8-bit.

---

## FASE 5: Layer Structure

**Objetivo**: Definir como se apilan los tiles para construir niveles.

### Godot TileMap Layers

| Layer | Z-Index | Purpose | Collision | Example Content |
|-------|---------|---------|-----------|-----------------|
| Ground | 0 | Base terrain | No | Grass, dirt, stone floor |
| Ground Deco | 1 | Terrain details | No | Cracks, puddles, grass tufts |
| Objects | 2 | Props y obstaculos | Yes | Rocks, bushes, tree trunks |
| Above | 3 | Elementos sobre player | No | Tree foliage, roof overhangs |
| Collision | -1 | Debug collision | Yes | Invisible, solo hitboxes |
| Events | 10 | Triggers e interactables | Special | Invisible, event markers |

### Reglas de layering

1. **Ground**: Tiles que siempre estan debajo del player
2. **Objects**: Tiles con collision que interactuan con player
3. **Above**: Tiles que se dibujan sobre el player (player pasa POR DEBAJO)
4. **Y-sorting**: Objects layer debe tener Y-sort enabled para depth effect

### Ejemplo de stacking (forest)

```
Layer Above (z=3):
  - Tree foliage (top 2 rows del sprite 2x3)

Layer Objects (z=2, y-sort=true):
  - Tree trunk (bottom row del sprite 2x3) -> collision
  - Large rocks -> collision
  - Bushes -> no collision

Layer Ground Deco (z=1):
  - Small grass tufts
  - Flowers
  - Cracks in dirt

Layer Ground (z=0):
  - Grass tiles (autotile variants)
  - Dirt path (4-bit autotile)
```

**Output**: Tabla de layers con contenido especifico para esta zona.

---

## FASE 6: Variantes y Visual Diversity

**Objetivo**: Definir cuantas variantes por tile para evitar repeticion visual.

### Reglas de variantes

**Terrain tiles**:
- Minimo: 2 variants (alternating pattern elimina grid obviousness)
- Optimo: 3-4 variants (random selection se ve natural)
- Maximo: 5 variants (diminishing returns, aumenta filesize)

**Decoration tiles**:
- Minimo: 3 variants (bushes, rocks)
- Optimo: 5-7 variants (flowers con different colors)
- Maximo: 10 variants (solo para tiles muy comunes como grass tufts)

**Wall tiles**:
- Base: 1 variant (autotile ya genera diversity)
- Opcionales: 2-3 variants (intact, cracked, mossy) como diferentes terrain sets

### Tabla de variantes

| Tile Type | Variant Count | Selection Method | Notes |
|-----------|---------------|------------------|-------|
| Grass | 3 | Random | Subtle shape differences |
| Dirt | 2 | Alternating | Light vs dark brown |
| Stone Wall | 1 (base) | N/A | Autotile provides variation |
| Stone Wall Cracked | 1 | Manual | Different terrain, placed manually |
| Tree (pine) | 3 | Random | Different foliage density |
| Bush | 4 | Random | Round, oval, dense, sparse |
| Flower | 5 | Random | Red, blue, yellow, white, purple |
| Rock (small) | 3 | Random | Different shapes |

### Implementation en Godot

**Random variants**:
```gdscript
# Godot auto-picks random variant from atlas alternatives
# Setup en TileSet: Add Alternative Tile for each variant
```

**Manual placement**:
```gdscript
# Artist places cracked wall variant manualmente en level design
```

**Output**: Tabla completa de variant counts para cada tile type.

---

## FASE 7: Export Format y Tileset Layout

**Objetivo**: Specs de archivo para importar en Godot.

### Formato de archivo

**Opcion 1: Tileset Atlas** (recomendado)
```
forest_tileset.png
  - Grid: 16x16 per tile (o el tile size del art-bible)
  - Layout: Organizacion logica (terrain top-left, walls top-right, props bottom)
  - Margin: 0px
  - Spacing: 0px (tiles contiguos)
  - Total size: Multiplo de tile size
```

**Ejemplo layout (16x16 tiles, 256x256 atlas)**:

```
Columns: 16 tiles
Rows: 16 tiles
Total: 256 tiles capacity

Organization:
- Row 0-2: Grass variants y autotile
- Row 3-4: Dirt path autotile (4-bit)
- Row 5-9: Stone wall autotile (8-bit, 47 tiles)
- Row 10-11: Water autotile
- Row 12-15: Props (trees, bushes, rocks, flowers)
```

**Opcion 2: Multiple Small Atlases**
```
forest_terrain.png    (solo ground tiles)
forest_walls.png      (solo walls con autotile)
forest_props.png      (solo decorations)
```

Ventaja: Mas facil de mantener
Desventaja: Multiple TileSet resources en Godot

### Naming convention

- `{zone}_tileset.png` (atlas completo)
- `{zone}_{category}.png` (si se separa en multiples)

### Metadata

Crear archivo `{zone}_tileset.tres` (TileSet resource) con:
- Atlas texture
- Tile size
- Autotile configurations
- Collision shapes
- Custom data (terrain type, walkable, etc.)

**Output**: Specs de layout del atlas con organizacion visual clara.

---

## FASE 8: Generar Spec Document

**Objetivo**: Escribir `design/tilesets/{zone}-spec.md` completo.

### Template del documento

```markdown
# {Zone} Tileset Specification

**Biome**: [Forest/Dungeon/Town/etc]
**Tile Size**: [16x16]
**Palette**: [palette_forest.gpl]
**Perspective**: [Top-down]

## Visual Theme

Palette dominante: Verde (#2d5016), marron (#8b4513), amarillo (#f4e04d)
Mood: Natural, organico, peaceful durante dia

## Tile Types

| Type | Variants | Autotile | Collision | Layer | Notes |
|------|----------|----------|-----------|-------|-------|
| Grass | 3 | No | Walkable | Ground | Random selection |
| Dirt Path | 2 | 4-bit | Walkable | Ground | Connects areas |
| Stone Wall | 1 | 8-bit (47) | Solid | Objects | Full blob tileset |
| ... | ... | ... | ... | ... | ... |

## Autotile Configuration

| Tile Type | System | Tile Count | Bitmask Mode |
|-----------|--------|------------|--------------|
| Stone Wall | 8-bit | 47 | 3x3 minimal |
| Dirt Path | 4-bit | 16 | 2x2 |
| Water Edge | 4-bit | 16 | 2x2 |

## Layer Structure

| Layer | Z-Index | Y-Sort | Collision | Content |
|-------|---------|--------|-----------|---------|
| Ground | 0 | No | No | Grass, dirt, stone floor |
| Ground Deco | 1 | No | No | Cracks, puddles, tufts |
| Objects | 2 | Yes | Yes | Trees, rocks, bushes |
| Above | 3 | No | No | Tree foliage, overhangs |

## Tileset Atlas Layout

**File**: `forest_tileset.png`
**Size**: 256x256 (16x16 grid = 16 cols x 16 rows)

```
Rows 0-2:   Grass variants (9 tiles)
Rows 3-4:   Dirt path autotile (16 tiles)
Rows 5-9:   Stone wall autotile (47 tiles)
Rows 10-11: Water autotile (16 tiles)
Row 12:     Tree variants (4 trees x 3 tiles = 12 tiles)
Row 13:     Bush variants (4 tiles)
Row 14:     Flower variants (5 tiles)
Row 15:     Rock variants (3 tiles)
```

## Variant Counts

| Tile Type | Count | Selection |
|-----------|-------|-----------|
| Grass | 3 | Random |
| Tree (pine) | 3 | Random |
| Bush | 4 | Random |
| Flower | 5 | Random |
| Rock (small) | 3 | Random |

## Export Checklist

- [ ] Draw all terrain tiles (grass, dirt) con variants
- [ ] Draw autotile sets (stone wall 47 tiles, path 16 tiles)
- [ ] Draw props (trees como 2x3 multi-tile, bushes, rocks)
- [ ] Draw decorations (flowers, grass tufts)
- [ ] Organize en atlas segun layout
- [ ] Export como PNG (no compression artifacts)
- [ ] Create TileSet resource en Godot
- [ ] Configure autotile bitmasks
- [ ] Set up collision shapes
- [ ] Test painting level con TileMap

## Godot Integration Notes

**TileSet setup**:
- Create new TileSet resource
- Add atlas texture: `res://assets/tilesets/forest_tileset.png`
- Tile size: 16x16
- For autotile: Setup terrain sets con peering bits

**TileMap layers**:
- Create 4 TileMap nodes (Ground, GroundDeco, Objects, Above)
- Set Z-index y Y-sort segun tabla de layers
- Assign collision layer/mask a Objects layer
```

**Accion**: Escribir archivo completo con datos de todas las fases anteriores.

---

## FASE 9: Validaciones Finales

**Checklist**:

- [ ] Tile count total <= 256 (cabe en un atlas 16x16)
- [ ] Autotile configurations son correctas (4-bit=16, 8-bit=47)
- [ ] Todos los tiles tienen layer asignado
- [ ] Variant counts son razonables (2-5 para terrain, 3-7 para props)
- [ ] Atlas layout esta organizado logicamente (no random scatter)
- [ ] Collision esta definida para tiles solid
- [ ] Document incluye checklist de implementacion

**Warnings**:
- Si tile count > 256: Recomendar split en multiple atlases
- Si muchos autotiles (>3 sets): Advertir sobre complejidad de produccion
- Si layer count > 5: Puede impactar performance, considerar merge

**Output final**: Path absoluto del archivo generado.

---

## Transicion al Siguiente Paso

Una vez completada la spec:

1. **Siguiente**: `/palette crear {zone}` (si necesita palette custom para este biome)
2. **O**: Producir tiles en Aseprite siguiendo la spec
3. **Despues**: `/godot-setup` para configurar TileSet resource
4. **Finalmente**: Level design con TileMap usando estos tiles

**Entregable**: `design/tilesets/{zone}-spec.md` con catalogo completo de tiles, autotile configs, layers, y atlas layout.
