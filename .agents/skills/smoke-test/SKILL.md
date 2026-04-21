---
name: smoke-test
description: >-
  Smoke test rapido antes de merge o release de juego 2D en Godot 4. Lista cambios recientes
  (git diff), ejecuta checklist automatico (JSON valido, no hardcoded values, no TODOs sin
  owner, tests pasan si hay runner), checklist manual (juego arranca, player se mueve,
  feature funciona, no regresiones). Veredicto: PASS/FAIL con blockers.
---

# Smoke Test

## Uso en Codex

- Esta skill esta pensada para invocacion explicita con `$smoke-test`.
- Trabaja con lecturas puntuales: `rg -n` para buscar, `rg --files` o `find` para listar, y `sed -n` para leer solo el fragmento necesario.
- Si falta contexto menor, usa el modo `pre-merge` y un baseline conservador; pregunta solo si el objetivo del smoke test cambia.
- Delega solo si el usuario pidio paralelismo o delegacion.

Verificacion rapida de sanidad antes de merge o release. NO es playtest completo. Veredicto: PASS/FAIL.

Modes: `pre-merge` (cambios del branch, default), `pre-release` (cambios desde ultimo tag).

## FASE 1: Listar cambios

Obtener archivos modificados (git diff vs main o vs ultimo tag segun mode).

Categorizar: Script (.gd/.cs), Scene (.tscn), Data (.json/.csv/.tres), Asset (.png/.wav), Config (project.godot).

Risk: HIGH (core systems), MEDIUM (features), LOW (data/assets).

## FASE 2: Checklist automatico

### JSON valid
Parsear cada .json modificado. FAIL si invalido.

### Hardcoded gameplay values
Buscar numeros magicos en scripts de gameplay (`var damage = 10`, `const MAX_HP = 100`). WARNING (no blocker).

### TODOs sin owner
Buscar TODOs sin formato `TODO(nombre):`. WARNING (no blocker).

### Tests
Si hay test runner (GUT o directorio tests/): ejecutar. FAIL si tests fallan. Si no hay runner: skip.

Veredicto automatico: algun FAIL → FAIL, todo PASS/WARNING → PASS.

## FASE 3: Checklist manual

Pedir al usuario que abra el juego. Tests secuenciales:

1. **Juego arranca**: sin crash, sin errores en consola
2. **Player se mueve**: 4 direcciones, sin lag/glitches
3. **Feature principal funciona**: basado en cambios detectados en FASE 1
4. **No regresiones**: quick playthrough 1-2 min, features no modificadas siguen funcionando

FAIL en cualquier test → marcar como blocker con severity (S1=crash, S2=major feature broken, S3=minor).

## FASE 4: Veredicto final

Combinar automatico + manual. PASS: safe to merge/release. FAIL: listar blockers con severity.

## FASE 5: Recomendaciones (si PASS con warnings)

Tabla: `warning → impact → effort → priority`. Sugerir fixes concretos. No bloquean merge.

## FASE 6: Pre-release checks adicionales [solo pre-release]

Validar: version number actualizado, export preset runnable, CHANGELOG actualizado. Warnings si no.

Output y formato de veredicto: leer `references/report-template.md`.

## Diferencia con $playtest

| | $smoke-test | $playtest |
|---|---|---|
| Duracion | 5-8 min | 15-30 min |
| Scope | Cambios recientes | Feature completa |
| Depth | Shallow (sanity) | Deep (funcionalidad + feel) |
| When | Pre-merge/release | Post-implementation |
