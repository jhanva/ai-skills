# Palette Output Template

Lee este archivo solo cuando vayas a escribir `design/palette.md`, exportar variantes o validar el entregable final.

## Documento sugerido

```markdown
# Game Palette

## Rules
- max colors
- outline rule
- anti-aliasing
- contrast for UI

## Color Categories
- Skin
- Nature
- Earth
- Water
- Metal
- UI
- Accent

## Visual Ramps
[Rampas resumidas]

## Export Files
- palette.gpl
- palette.json
- palette.md

## Palette Swaps
- enemy recolors
- seasons
- equipment tiers
```

## Validaciones finales

- Total colors <= max del art-bible
- Categories con ramp completo
- UI colors con contraste suficiente
- Archivos de export definidos
- Variants claros si modo swap

## Cierre sugerido

- Recomendar `$sprite-spec` o `$tileset-spec`
- Recomendar `$palette swap` si faltan variantes
