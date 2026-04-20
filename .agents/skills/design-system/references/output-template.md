# Design System Output Template

Lee este archivo solo cuando vayas a producir `design/gdd/{system}.md` o cuando necesites la plantilla de salida completa.

## Documento sugerido

```markdown
# System Design — [NOMBRE DEL SISTEMA]

## Contexto
[Relacion con pillars y con el game concept]

## Scope
### SI
- [...]
### NO
- [...]
### Dependencias
- [...]

## Mecanicas Core
- Estados
- Transiciones
- Player verbs

## Data Model
[Pseudocodigo o schema]

## Formulas
[Solo si aplica]

## Edge Cases
[Tabla de casos borde]

## Tuning Knobs
[Parametros configurables]

## Acceptance Criteria
[Checklist medible]

## Implementation Notes
[Notas tecnicas y de integracion]
```

## Anti-patrones a revisar

- Scope vago
- Edge cases no documentados
- Valores hardcodeados en codigo
- Acceptance criteria subjetivos
- Dependencias ignoradas

## Cierre sugerido

- Recomendar `$plan` para dividir en tareas
- Recomendar `$tdd` para implementar
- Recomendar `$verify` para validar criterios
