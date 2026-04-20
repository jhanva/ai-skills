# Scene Design Output Template

Lee este archivo solo cuando vayas a escribir `design/scenes/{scene-name}.md` o cuando necesites la plantilla completa.

## Documento sugerido

```markdown
# [Scene Name] Scene Design

## Node Tree
[Arbol ASCII]

## Nodes
[Tabla node / type / purpose / properties]

## Signals
[Tabla emitted by / parameters / connected to / purpose]

## Scripts
[Tabla script / node / responsibility / LOC]

## Data Flow
[Pasos del flujo principal]

## Resources
[Tabla tipo / path / usage]

## External Dependencies
[Autoloads, input, scenes externas]

## Implementation Checklist
[Checklist accionable]

## Testing Notes
[Movimiento, combate, salud, UI, etc.]
```

## Validaciones finales

- Node tree <= 15 nodes salvo justificacion
- Scripts con single responsibility
- Signals con purpose claro
- Data flow sin dependencias circulares
- Resources y external deps listadas

## Cierre sugerido

- Implementar scene
- Usar `$tdd` si toca state machine o logica critica
- Integrar en test level
