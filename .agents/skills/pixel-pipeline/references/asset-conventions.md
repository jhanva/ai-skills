# Pixel Pipeline — Asset Conventions

Lee este archivo solo cuando definas convenciones de produccion.

## Resolucion y grid

Patrones comunes:

| Resolucion | Mejor para |
|---|---|
| 8x8 | retro extremo, icons, props pequenos |
| 16x16 | RPG clasico y balance produccion/detalle |
| 32x32 | sprites mas expresivos |
| 48x48 | personajes mas detallados sobre tiles mas pequenos |

Regla: elegir un tamano de tile y uno de character y mantenerlos consistentes.

## Pixel-perfect minimo

- integer scaling
- nearest filtering
- no rotaciones sub-pixel
- camera snap a pixel grid
- misma densidad de pixel por unidad

## Naming

Baseline recomendado:

```text
{entity}_{animation}_{frame}.png
```

## Animaciones

Sets minimos orientativos:

- player: `idle`, `walk`, `attack`, `hurt`, `death`, opcional `cast`
- enemy: `idle`, `attack`, `hurt`, `death`, opcional `special`
- npc: `idle`, `talk`

Guarda animaciones como data, no como ifs hardcodeados.

## Tilesets

Separacion comun:

- terrain
- buildings
- decorations
- interactables

Empieza con autotile 4-bit y sube a 8-bit solo si el juego realmente gana con ello.

## Paleta

Reglas practicas:

- maximo acotado de colores para cohesion
- 4-8 colores por sprite como referencia
- ramps cortas y consistentes
- outline consistente
- sin anti-aliasing suave si quieres pixel art duro
