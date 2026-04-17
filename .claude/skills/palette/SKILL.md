---
name: palette
description: >
  Gestiona color palettes para pixel art: crear base palette con ramps,
  definir palette swap variants (enemy recolors, equipment tiers, seasons),
  validar reglas (max colors, outline, no AA), y exportar en GPL/JSON.
  Output: design/palette.md o design/palettes/{name}.md
argument-hint: "[crear | swap | revisar]"
disable-model-invocation: true
agent: pixel-artist
allowed-tools:
  - Read
  - Grep
  - Glob
  - Write
---

# Palette Management

Crea, valida, y gestiona color palettes para pixel art. Define base palette con ramps organizados, palette swap variants, reglas de uso, y export en formatos compatibles con Aseprite y Godot.

## FASE 1: Determinar Modo de Operacion

**Objetivo**: Identificar que accion ejecutar basado en el argumento.

### Modos disponibles

| Modo | Argumento | Accion | Output |
|------|-----------|--------|--------|
| Crear | `crear` | Crear base palette nueva | `design/palette.md` |
| Swap | `swap` | Definir palette swap variants | `design/palettes/{variant}.md` |
| Revisar | `revisar` | Validar palette existente | Report en conversacion |

**Decision**:
- Si argumento = "crear": FASE 2-6 (crear base palette)
- Si argumento = "swap": FASE 7 (palette swaps)
- Si argumento = "revisar": FASE 8 (validar existente)
- Si no hay argumento: Preguntar al usuario que modo necesita

---

## FASE 2: Leer Art-Bible y Contexto [MODO: CREAR]

**Objetivo**: Cargar restricciones de color del proyecto.

1. Buscar y leer `design/art-bible.md`
2. Extraer restricciones:
   - Max colors permitidos (ej: 32, 64, ilimitado)
   - Outline color (negro, dark gray, colored outlines)
   - Anti-aliasing policy (prohibido, permitido, solo para curves)
   - Palette philosophy (limited NES-style, GB-style, modern pixel art)
3. Buscar palettes de referencia en `design/palettes/` (si existen)
4. Identificar tematica del juego (fantasy, sci-fi, horror, cute)

**Defaults si no hay art-bible**:
- Max colors: 32 (NES extended)
- Outline: Negro puro (#000000)
- Anti-aliasing: Prohibido
- Style: Modern pixel art

---

## FASE 3: Definir Base Palette Categories [MODO: CREAR]

**Objetivo**: Organizar colores en categorias funcionales.

### Categorias standard

| Category | Colors | Purpose | Example Hex |
|----------|--------|---------|-------------|
| Skin | 4-6 | Character skin tones | #ffd1a3, #e8b796, #c68f6f, #8b5a3c |
| Nature | 6-8 | Grass, trees, foliage | #2d5016, #4b7d2a, #6ba841, #a0d860 |
| Earth | 4-6 | Dirt, rocks, stone | #8b4513, #a0522d, #c7956d, #e0c8a0 |
| Water | 3-4 | Water, ice, liquids | #2b5f75, #3b8ea5, #54c5d9, #a4e4f4 |
| Metal | 4-5 | Armor, weapons, coins | #4a4a4a, #787878, #a8a8a8, #d8d8d8, #f4e4c0 |
| UI | 4-6 | Menus, text, borders | #000000, #ffffff, #1a1a1a, #e0e0e0, #ffcc00 |
| Accent | 3-5 | Special effects, magic, highlights | #ff0000, #00ff00, #0000ff, #ff00ff, #ffff00 |

### Reglas de organizacion

1. **Skin tones**: 4 ramps (highlight, base, shadow, deep shadow)
2. **Nature**: 6-8 colores para cubrir multiple foliage types (dark forest, bright grass, autumn leaves)
3. **Earth**: 4-6 colores para terrain variety
4. **Water**: Minimo 3 (deep, mid, highlight) para depth effect
5. **Metal**: Ramp de grises + optional gold/bronze tint
6. **UI**: Alto contraste (black text on white, white text on black)
7. **Accent**: Colores saturados para VFX, magic, pickups importantes

**Output**: Tabla de categorias con color count estimado (total debe estar <= max colors del art-bible).

---

## FASE 4: Definir Color Ramps [MODO: CREAR]

**Objetivo**: Crear ramps de shadow → base → highlight para cada categoria.

### Teoria de ramps

**3-tone ramp** (minimo viable):
```
Shadow -> Base -> Highlight
#2d5016 -> #4b7d2a -> #6ba841
```

**4-tone ramp** (standard):
```
Deep Shadow -> Shadow -> Base -> Highlight
#1a3010 -> #2d5016 -> #4b7d2a -> #6ba841
```

**5-tone ramp** (high quality):
```
Deep Shadow -> Shadow -> Base -> Highlight -> Shine
#1a3010 -> #2d5016 -> #4b7d2a -> #6ba841 -> #a0d860
```

### Reglas de ramps

1. **Hue shifting**: Shadow no es solo "base mas oscuro", sino shift hacia azul/purpura
2. **Saturation**: Highlight tiene mas saturacion, shadow tiene menos
3. **Value steps**: Incrementos consistentes (no jumps bruscos)
4. **Readable at distance**: Ramp debe ser distinguible a 1x scale

### Tabla de ramps

| Category | Ramp Name | Deep Shadow | Shadow | Base | Highlight | Shine |
|----------|-----------|-------------|--------|------|-----------|-------|
| Skin | Light | - | #e8b796 | #ffd1a3 | #ffebcc | - |
| Skin | Medium | - | #c68f6f | #d4a574 | #e8b796 | - |
| Skin | Dark | - | #8b5a3c | #a0674f | #c68f6f | - |
| Nature | Grass | #1a3010 | #2d5016 | #4b7d2a | #6ba841 | #a0d860 |
| Nature | Dark Forest | #0d1a0d | #1a3010 | #2d5016 | #3f6b1f | - |
| Earth | Dirt | #5c3317 | #8b4513 | #a0522d | #c7956d | - |
| Water | Deep | #1a3d4d | #2b5f75 | #3b8ea5 | #54c5d9 | #a4e4f4 |
| Metal | Steel | #2a2a2a | #4a4a4a | #787878 | #a8a8a8 | #d8d8d8 |
| Metal | Gold | - | #c7956d | #e0b87e | #f4e4c0 | #fff8dc |

**Generacion de hex values**:
- Usar herramienta de color (Coolors, Adobe Color, Lospec Palette List)
- O algoritmo HSV: Shadow = base - 15% V, + 5 H shift blue; Highlight = base + 15% V, + 10% S

**Output**: Tabla completa de ramps con todos los hex values.

---

## FASE 5: Validar Reglas de Palette [MODO: CREAR]

**Objetivo**: Asegurar que la palette cumple restricciones tecnicas y esteticas.

### Checklist de validaciones

**Color count**:
- [ ] Total colors <= max del art-bible
- [ ] Si excede: Eliminar shines opcionales o merge categories similares

**Contrast**:
- [ ] UI text colors tienen contrast ratio >= 4.5:1 (WCAG AA)
- [ ] Outline color contrasta con todos los base colors

**Ramp consistency**:
- [ ] Todos los ramps tienen 3-5 tonos (no ramps de 2 o 6+)
- [ ] Value steps son consistentes (no jumps de >30% lightness)

**Hue distribution**:
- [ ] Palette cubre espectro (no todo greens/browns, falta blues/reds)
- [ ] Accent colors son distinguibles (no hay 3 reds similares)

**No duplicates**:
- [ ] No hay dos hex values identicos en categories diferentes
- [ ] Si hay duplicates intencionales (ej: black usado en UI y outline), documentar

**Pixel art viability**:
- [ ] Colores son distinguibles a 1x scale (no micro-differences)
- [ ] Outline color funciona en todos los backgrounds (test en light y dark)

**Warnings**:
- Si total colors > 48: Palette muy grande, dificil de mantener consistencia
- Si hay ramps con solo 2 tonos: Poco depth, recomendar agregar shadow o highlight
- Si accent colors son >10: Demasiados, pierden impacto visual

**Output**: Report de validacion con PASS/FAIL para cada regla.

---

## FASE 6: Export Formats [MODO: CREAR]

**Objetivo**: Generar archivos de palette en formatos usables.

### GPL Format (Aseprite)

```gpl
GIMP Palette
Name: Game Palette
Columns: 8
#
# Skin
255 209 163   Light Skin Base
232 183 150   Light Skin Shadow
198 143 111   Medium Skin Base
139  90  60   Dark Skin Base
#
# Nature
45  80  22    Dark Forest Base
75 125  42    Grass Shadow
107 168  65   Grass Base
160 216  96   Grass Highlight
#
# Earth
92  51  23    Dirt Shadow
139  69  19   Dirt Base
160  82  45   Dirt Highlight
#
# ... (resto de colores)
```

**File**: `design/palette.gpl`

### JSON Format (Godot/engine)

```json
{
  "name": "Game Palette",
  "colors": {
    "skin": {
      "light_base": "#ffd1a3",
      "light_shadow": "#e8b796",
      "medium_base": "#c68f6f",
      "dark_base": "#8b5a3c"
    },
    "nature": {
      "dark_forest_base": "#2d5016",
      "grass_shadow": "#4b7d2a",
      "grass_base": "#6ba841",
      "grass_highlight": "#a0d860"
    },
    "earth": {
      "dirt_shadow": "#5c3317",
      "dirt_base": "#8b4513",
      "dirt_highlight": "#a0522d"
    }
  },
  "rules": {
    "max_colors": 32,
    "outline": "#000000",
    "anti_aliasing": false
  }
}
```

**File**: `design/palette.json`

### Markdown Document (documentation)

Ver template en FASE 9.

**Accion**: Generar los 3 archivos (GPL, JSON, MD).

---

## FASE 7: Palette Swap Variants [MODO: SWAP]

**Objetivo**: Definir remapping de colores para variants (enemy recolors, seasons, equipment tiers).

### Use cases de palette swaps

| Use Case | Example | Remap Count |
|----------|---------|-------------|
| Enemy variants | Slime: green -> red, blue, yellow | 3 swaps |
| Equipment tiers | Sword: steel -> bronze, silver, gold, legendary | 4 swaps |
| Seasons | Forest: spring -> summer, autumn, winter | 3 swaps |
| Team colors | Player 1-4: red, blue, green, yellow | 4 swaps |
| Status effects | Character: normal -> poisoned (green), frozen (blue), burning (red) | 3 swaps |

### Tabla de palette swap

**Ejemplo: Slime variants**

| Variant | Purpose | Color Remap | Notes |
|---------|---------|-------------|-------|
| Green Slime | Base enemy | (no swap) | Base palette |
| Red Slime | Fire variant | grass_base -> red_base, grass_shadow -> red_shadow | More damage, fire immunity |
| Blue Slime | Water variant | grass_base -> blue_base, grass_shadow -> blue_shadow | Water immunity, slow attack |
| Yellow Slime | Electric variant | grass_base -> yellow_base, grass_shadow -> yellow_shadow | Fast movement, electric damage |

**Remap details**:

```json
{
  "slime_red": {
    "#4b7d2a": "#d32f2f",  // grass_shadow -> red_shadow
    "#6ba841": "#f44336",  // grass_base -> red_base
    "#a0d860": "#ff7961"   // grass_highlight -> red_highlight
  },
  "slime_blue": {
    "#4b7d2a": "#1976d2",  // grass_shadow -> blue_shadow
    "#6ba841": "#2196f3",  // grass_base -> blue_base
    "#a0d860": "#64b5f6"   // grass_highlight -> blue_highlight
  }
}
```

### Implementacion en Godot

**Shader approach**:
```gdscript
shader_type canvas_item;

uniform vec3 color_from_1 : source_color;
uniform vec3 color_to_1 : source_color;
uniform vec3 color_from_2 : source_color;
uniform vec3 color_to_2 : source_color;

void fragment() {
    vec4 tex = texture(TEXTURE, UV);
    if (distance(tex.rgb, color_from_1) < 0.01) {
        COLOR = vec4(color_to_1, tex.a);
    } else if (distance(tex.rgb, color_from_2) < 0.01) {
        COLOR = vec4(color_to_2, tex.a);
    } else {
        COLOR = tex;
    }
}
```

**Resource approach** (mejor para pixel art):
- Duplicar sprite con colores swapped en Aseprite
- Export como assets separados (`slime_green.png`, `slime_red.png`)
- Mas filesize, pero no depende de shaders

**Output**: Tabla de swaps + JSON con remaps + implementacion method recomendado.

---

## FASE 8: Revisar Palette Existente [MODO: REVISAR]

**Objetivo**: Validar palette actual contra reglas y detectar issues.

### Pasos de revision

1. **Leer palette actual** de `design/palette.md` o `design/palette.json`
2. **Extraer todos los hex values**
3. **Ejecutar validaciones de FASE 5**:
   - Color count
   - Contrast (UI colors)
   - Ramp consistency
   - Hue distribution
   - No duplicates
4. **Detectar issues adicionales**:
   - Colores muy similares (distance < 10% en HSV space)
   - Ramps con gaps (missing intermediate tone)
   - Accent colors que no destacan (low saturation)

### Report format

```
# Palette Review Report

## Summary
- Total colors: 28/32 (within limit)
- Categories: 7
- Ramps: 9
- Issues found: 3

## Issues

### CRITICAL
- None

### WARNING
1. UI text color (#333333) has contrast ratio 3.2:1 with background (#e0e0e0)
   - WCAG AA requires 4.5:1
   - Recommendation: Darken to #1a1a1a (6.8:1 ratio)

2. Nature category has duplicate: grass_base and foliage_base both use #6ba841
   - Recommendation: Shift foliage_base to #5ea838 (slightly darker)

3. Metal ramp has large jump: shadow #4a4a4a to highlight #a8a8a8 (gap of 46% lightness)
   - Missing mid-tone
   - Recommendation: Add #787878 between them

### INFO
- Accent red (#ff0000) and accent yellow (#ffff00) are very saturated (100%)
  - Acceptable for VFX/pickups, but consider slight desaturation if used on UI

## Recommendations

1. Add mid-tone to metal ramp
2. Darken UI text color for accessibility
3. Differentiate grass_base and foliage_base
4. Consider adding cool accent (cyan/magenta) for balance (currently only warm accents)
```

**Output**: Report completo en conversacion (no crear archivo).

---

## FASE 9: Generar Palette Document [MODO: CREAR]

**Objetivo**: Escribir `design/palette.md` con toda la informacion.

### Template del documento

```markdown
# Game Palette

**Total Colors**: 28
**Max Allowed**: 32
**Style**: Modern pixel art
**Outline**: #000000 (black)
**Anti-aliasing**: Prohibited

## Rules

1. Maximum 32 colors en toda la palette
2. Outline es siempre negro puro (#000000)
3. No anti-aliasing (pixel perfect edges)
4. Ramps deben tener 3-5 tonos
5. UI text debe tener contrast ratio >= 4.5:1

## Color Categories

### Skin (4 colors)

| Name | Hex | RGB | Use |
|------|-----|-----|-----|
| Light Base | #ffd1a3 | 255, 209, 163 | Light skin tone base |
| Light Shadow | #e8b796 | 232, 183, 150 | Light skin shadow |
| Medium Base | #c68f6f | 198, 143, 111 | Medium skin base |
| Dark Base | #8b5a3c | 139, 90, 60 | Dark skin base |

### Nature (6 colors)

| Name | Hex | RGB | Use |
|------|-----|-----|-----|
| Dark Forest Base | #2d5016 | 45, 80, 22 | Dark trees, deep forest |
| Grass Shadow | #4b7d2a | 75, 125, 42 | Grass shadow tone |
| Grass Base | #6ba841 | 107, 168, 65 | Main grass color |
| Grass Highlight | #a0d860 | 160, 216, 96 | Grass highlight |
| Autumn | #d4a140 | 212, 161, 64 | Autumn leaves |
| Spring | #b4e657 | 180, 230, 87 | Spring foliage |

### Earth (4 colors)

| Name | Hex | RGB | Use |
|------|-----|-----|-----|
| Dirt Shadow | #5c3317 | 92, 51, 23 | Dark dirt, deep soil |
| Dirt Base | #8b4513 | 139, 69, 19 | Main dirt color |
| Dirt Highlight | #a0522d | 160, 82, 45 | Light dirt, sand |
| Stone | #8a8a8a | 138, 138, 138 | Rocks, stone floor |

### Water (4 colors)

| Name | Hex | RGB | Use |
|------|-----|-----|-----|
| Deep | #2b5f75 | 43, 95, 117 | Deep water, ocean |
| Mid | #3b8ea5 | 59, 142, 165 | Mid-depth water |
| Shallow | #54c5d9 | 84, 197, 217 | Shallow water |
| Foam | #a4e4f4 | 164, 228, 244 | Water foam, highlights |

### Metal (5 colors)

| Name | Hex | RGB | Use |
|------|-----|-----|-----|
| Deep Shadow | #2a2a2a | 42, 42, 42 | Darkest metal |
| Shadow | #4a4a4a | 74, 74, 74 | Metal shadow |
| Base | #787878 | 120, 120, 120 | Base metal (steel) |
| Highlight | #a8a8a8 | 168, 168, 168 | Metal highlight |
| Shine | #d8d8d8 | 216, 216, 216 | Metal shine/edge |

### UI (3 colors)

| Name | Hex | RGB | Use |
|------|-----|-----|-----|
| Black | #000000 | 0, 0, 0 | Text, outlines, borders |
| White | #ffffff | 255, 255, 255 | Text on dark, highlights |
| Gray | #808080 | 128, 128, 128 | Disabled UI, secondary text |

### Accent (2 colors)

| Name | Hex | RGB | Use |
|------|-----|-----|-----|
| Red | #e74c3c | 231, 76, 60 | Danger, fire, enemy HP |
| Yellow | #f4d03f | 244, 208, 63 | Loot, coins, highlights |

## Visual Ramps

```
Skin (light):     [#e8b796] -> [#ffd1a3] -> [#ffebcc]
Nature (grass):   [#2d5016] -> [#4b7d2a] -> [#6ba841] -> [#a0d860]
Earth (dirt):     [#5c3317] -> [#8b4513] -> [#a0522d]
Water:            [#2b5f75] -> [#3b8ea5] -> [#54c5d9] -> [#a4e4f4]
Metal:            [#2a2a2a] -> [#4a4a4a] -> [#787878] -> [#a8a8a8] -> [#d8d8d8]
```

## Export Files

- `design/palette.gpl` — Aseprite palette (GPL format)
- `design/palette.json` — Engine integration (JSON)
- `design/palette.md` — This file (documentation)

## Palette Swaps

See `design/palettes/` for variant definitions:
- `slime-variants.md` — Red, blue, yellow slime recolors
- `seasons.md` — Spring, summer, autumn, winter palette swaps
```

**Accion**: Escribir archivo completo.

---

## FASE 10: Validaciones Finales

**Checklist**:

- [ ] Total colors <= max del art-bible
- [ ] Todas las categories tienen al menos 1 ramp completo (3+ tonos)
- [ ] UI colors tienen contrast adecuado
- [ ] Export files generados (GPL, JSON, MD)
- [ ] Document incluye visual ramps y use notes

**Output final**: Paths absolutos de archivos generados.

---

## Transicion al Siguiente Paso

Una vez completada la palette:

1. **Siguiente**: `/sprite-spec {entity}` o `/tileset-spec {zone}` (aplicar palette a assets)
2. **O**: Comenzar produccion en Aseprite con palette loaded
3. **Para swaps**: `/palette swap` para definir variants

**Entregables**:
- `design/palette.md` (documentation)
- `design/palette.gpl` (Aseprite)
- `design/palette.json` (engine integration)
- `design/palettes/{variant}.md` (si modo swap)
