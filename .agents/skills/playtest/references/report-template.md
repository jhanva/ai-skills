# Playtest Report Template

Lee este archivo solo cuando vayas a escribir `production/playtests/playtest-{date}-{feature}.md` o cuando necesites el formato de salida completo.

## Documento sugerido

```markdown
# Playtest Report: {feature}

## Scope
- Feature testeada
- Comportamientos incluidos

## Test Results
[Tabla pass/fail/partial]

## Bugs Found
[Tabla de bugs con severity y steps]

## Game Feel Assessment
[Ratings 1-5 + comentario]

## Sugerencias de Mejora
[Tabla con category, priority y effort]

## Proximos Pasos
- Fix blockers
- Balance tweaks
- Polish
- Opcionales
```

## Checklist de salida

- Fecha y metadata completos
- Test results con status
- Bugs documentados con severity y repro
- Ratings de game feel
- Sugerencias priorizadas
- Proximos pasos listados

## Edge cases

- Checklist demasiado largo: dividir por sub-features
- Bug reportado aunque el test paso: marcar PARTIAL y documentar igual
- Sin GDD ni story: pedir expected behavior manual
- Cobertura insuficiente: advertir si se ejecutan muy pocos tests
- Pass rate < 30%: sugerir fix basico antes de seguir playtesteando
