# Art Bible Output Template

Lee este archivo solo cuando vayas a redactar `design/art-bible.md` o cuando necesites el checklist y los anti-patrones completos.

## Documento sugerido

```markdown
# Art Bible — [Nombre del Juego]

## Vision
[2-3 frases del look & feel y la fantasia visual]

## Resolucion
- Tile size
- Character size
- Base resolution
- Integer scaling
- Target resolutions

## Paleta
- Tipo (estricta / guia)
- Categorias de color
- Total de colores
- Formato de export

## Estilo de Sprites
- Outline
- Shading
- Anti-aliasing
- Pixel density
- Direcciones soportadas

## Animaciones
- Tabla de frame counts standard
- Convenciones de timing
- Naming convention

## Restricciones Tecnicas
- Godot 4 settings
- Import settings
- Camera snapping
- Atlas organization

## UI Style
- Panels
- Font
- Icon size
- Cursor

## Reglas de Produccion
- Checklist por sprite
- Validacion visual

## Referencias Visuales
- Juegos de referencia
- Arte inspiracional
```

## Checklist por sprite

- Tamano correcto
- Paleta respetada
- Outline consistente
- Shading consistente
- Export PNG indexado
- Naming convention correcta

## Anti-patrones a revisar

- Mezclar resoluciones base
- Linear filtering en sprites
- Paleta inconsistente entre assets
- Animaciones con timing arbitrario
- Sub-pixel positioning sin camera snap
- Paleta de 50+ colores sin justificacion
- Pixel density no definida

## Cierre sugerido

- Recomendar `$pixel-pipeline` si falta pipeline de assets
- Recomendar `$design-system` si falta una mecanica MVP
- Recomendar `$plan` si concepto + arte ya estan listos
