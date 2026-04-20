# Level Brief Output Template

Lee este archivo solo cuando vayas a redactar `design/levels/{name}.md` o cuando necesites la plantilla completa.

## Documento sugerido

```markdown
# Level Brief — [NOMBRE DEL NIVEL]

## Contexto
- Juego
- Genero
- Ubicacion en la progresion

## Proposito
- Objetivos del jugador
- Tipo de nivel

## Layout
- Dimensiones
- Tile size
- ASCII map
- Leyenda

## Encounters
- Tabla de enemigos
- Dificultad esperada
- Nivel esperado del player

## Difficulty Curve
- Tension graph
- Puntos de descanso
- Pacing

## Secrets / Optional Content
- Tabla de secretos

## Asset Requirements
- Tiles
- Objects
- Enemies
- Effects

## Audio
- Music
- Ambience
- Triggers

## Implementation Notes
- Scripting
- Camera
- Save points

## Testing Checklist
- Walkability
- Spawns
- Secrets
- Exit
- Difficulty
- Audio
- Transicion al siguiente nivel
```

## Anti-patrones a revisar

- Layout sin proposito claro
- Difficulty curve plana
- Secrets imposibles de descubrir
- Fatiga por encounters sin descanso
- Assets no listados
- Pacing no estimado

## Cierre sugerido

- Recomendar Tiled o Godot segun el flujo del usuario
- Recomendar otro `$level-brief` si faltan niveles
