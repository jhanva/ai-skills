# Smoke Test Report Template

Lee este archivo solo cuando vayas a emitir el veredicto final o cuando necesites el formato de PASS/FAIL completo.

## PASS sugerido

```markdown
# Smoke Test: PASS

## Summary
- Automated checks: PASS
- Manual checks: PASS
- Blockers: 0

## Warnings
- [...]
```

## FAIL sugerido

```markdown
# Smoke Test: FAIL

## Blockers
[Tabla de blockers]

## Details
[Detalle por blocker]

## Action Required
- Fix blockers
- Re-run smoke test
```

## Pre-release extras

- Validar version number
- Validar export preset runnable
- Validar CHANGELOG

## Edge cases

- Git diff vacio
- Solo cambios LOW risk
- Tests muy lentos
- Respuesta manual ambigua
- Pre-merge en main
