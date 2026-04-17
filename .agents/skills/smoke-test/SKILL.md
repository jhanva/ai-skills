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
- Cuando aqui se indique buscar patrones, usa `rg -n`; para listar archivos, usa `rg --files` o `find`; para leer fragmentos concretos, usa `sed -n`.
- Cuando aqui se hable de subagentes, usa los agentes integrados de Codex o los definidos en `.codex/agents/`, y solo delega si el usuario lo pidio explicitamente.
- Las referencias a `Read/Write/Edit/Grep/Glob/Bash` se traducen segun `AGENTS.md` del repo.

Agent que ejecuta smoke test rapido antes de merge o release de juegos 2D pixel art
en Godot 4. Diseñado para solo dev principiante en gamedev con experiencia en Android/Kotlin.

## Objetivo

Validar que los cambios recientes no rompieron el juego:
- Checklist automatico: validaciones que pueden ejecutarse sin abrir el juego
- Checklist manual: validaciones que requieren correr el juego
- Veredicto: PASS (safe to merge/release) o FAIL (blockers encontrados)

**NO** es un playtest completo (usa `/playtest` para eso). Es una verificacion rapida
de sanidad antes de integrar cambios.

## Entrada

```
/smoke-test [mode]
/smoke-test pre-merge
/smoke-test pre-release
/smoke-test
```

Modes:
- **pre-merge:** antes de merge a main branch (scope: cambios del branch actual)
- **pre-release:** antes de release/tag (scope: cambios desde ultimo tag)
- **default (sin argumento):** pre-merge

## FASE 1: Listar cambios

### 1.1 Determinar scope segun mode

**Pre-merge mode:**
```bash
# Archivos modificados en branch actual vs main
git diff --name-only main...HEAD
```

**Pre-release mode:**
```bash
# Ultimo tag
git describe --tags --abbrev=0

# Archivos modificados desde ultimo tag
git diff --name-only <ultimo-tag>...HEAD
```

### 1.2 Categorizar archivos

Por cada archivo modificado, categorizar:

| File | Type | System | Risk |
|------|------|--------|------|
| src/combat/damage.gd | Script | combat | MEDIUM |
| assets/data/items.json | Data | inventory | LOW |
| scenes/player.tscn | Scene | player | HIGH |
| assets/sprites/enemy.png | Asset | enemy | LOW |

Types:
- **Script:** .gd, .cs (logica de juego)
- **Scene:** .tscn (escenas de Godot)
- **Data:** .json, .csv, .tres (datos de configuracion)
- **Asset:** .png, .wav, .ogg (assets visuales/audio)
- **Config:** project.godot, export_presets.cfg

Risk:
- **HIGH:** cambios en core systems (player, combat, save/load)
- **MEDIUM:** cambios en features (UI, inventory, enemies)
- **LOW:** cambios en data/assets (valores, sprites, sounds)

### 1.3 Crear summary de cambios

```markdown
## Changes Summary

Total files: 12
- Scripts: 5 (combat, inventory, player, enemy-ai, utils)
- Scenes: 3 (player, enemy, level-1)
- Data: 2 (items.json, stats.json)
- Assets: 2 (enemy.png, hit.wav)

Risk breakdown:
- HIGH: 2 (player.gd, player.tscn)
- MEDIUM: 3 (combat/damage.gd, inventory/pickup.gd, enemy-ai/patrol.gd)
- LOW: 7 (data, assets)
```

## FASE 2: Checklist automatico

Tests que pueden ejecutarse sin abrir el juego.

### 2.1 Validar JSON files

Por cada archivo .json modificado:

```bash
python3 -c "import json; json.load(open('assets/data/items.json'))"
```

Si falla:
- Error: "JSON invalido: {archivo}"
- Mostrar error de parseo
- Marcar como FAIL

Si pasa:
- PASS: "JSON valido: {archivo}"

### 2.2 Detectar hardcoded gameplay values

Buscar numeros magicos en scripts de gameplay:

```bash
# Buscar en archivos .gd modificados en src/gameplay/, src/combat/, src/systems/
grep -E "^\s*(var|const)\s+\w+\s*=\s*[0-9]+" <archivos-modificados>
```

Flags de hardcoded values:
- `var damage = 10` (deberia estar en data/balance.json)
- `const MAX_HP = 100` (deberia ser configurable)
- `if gold < 50:` (deberia leer de item cost)

Si detecta hardcoded values:
- Warning: "Hardcoded value en {archivo}:{linea}: {valor}"
- Listar todos los casos encontrados
- No es blocker (PASS), pero reportar para review

### 2.3 Detectar TODOs sin owner

Buscar TODOs en archivos modificados:

```bash
grep -n "TODO" <archivos-modificados>
```

Por cada TODO, parsear formato:

```gdscript
# TODO: fix this
# TODO(jvargas): refactor damage calculation
# TODO: implement sound effects
```

Si TODO NO tiene owner (formato: `TODO(nombre):`):
- Warning: "TODO sin owner en {archivo}:{linea}"
- Listar todos los TODOs sin owner
- No es blocker, pero reportar

Si TODO tiene owner:
- OK: "TODO con owner: {owner}"

### 2.4 Ejecutar tests (si hay test runner)

Buscar test runner en proyecto:

```bash
# GUT (Godot Unit Test)
find . -name ".gutconfig.json"

# O directorio tests/
ls -d tests/
```

Si existe test runner:
```bash
# Ejecutar tests (ejemplo con GUT)
# Formato depende del setup del proyecto
godot --headless --script res://addons/gut/gut_cmdln.gd
```

Si tests pasan:
- PASS: "Tests pasan ({count} tests)"

Si tests fallan:
- FAIL: "Tests fallan ({count} failed)"
- Listar tests que fallaron
- Marcar como blocker

Si NO hay test runner:
- Skip: "No test runner configurado"

### 2.5 Summary del checklist automatico

Tabla de resultados:

| Check | Status | Details |
|-------|--------|---------|
| JSON valid | PASS | 2 files checked |
| Hardcoded values | WARNING | 3 found in combat/damage.gd |
| TODOs with owner | WARNING | 1 TODO without owner |
| Tests | PASS | 15/15 passed |

Veredicto automatico:
- Si algun check es FAIL → FAIL
- Si todos son PASS/WARNING → PASS (warnings no bloquean)

## FASE 3: Checklist manual

Tests que requieren correr el juego. Guiar al usuario paso a paso.

### 3.1 Introducir checklist manual

```
Checklist automatico: {PASS/FAIL}

Ahora voy a guiarte por el checklist manual.
Abre el juego en Godot y ejecuta la escena principal.

Listo? (Responde "si" cuando el juego este corriendo)
```

Esperar confirmacion del usuario.

### 3.2 Test 1: Juego arranca sin crash

```
Test 1: Juego arranca

Pasos:
1. Presiona Play en Godot (F5)
2. Observa si el juego carga

Preguntas:
- El juego arranco? (si/no)
- Ves errores en la consola de Godot? (si/no)
- Si hay errores, cuales? (copia/pega)
```

Si el usuario reporta crash o error:
- FAIL: "Juego no arranca"
- Capturar error del usuario
- Marcar como blocker S1

Si el juego arranca:
- PASS: "Juego arranca correctamente"

### 3.3 Test 2: Player se mueve correctamente

```
Test 2: Player movement

Pasos:
1. Mueve al player (WASD o flechas)
2. Observa si responde

Preguntas:
- El player se mueve en las 4 direcciones? (si/no)
- Hay lag o glitches visuales? (si/no)
- Se siente diferente que antes? (si/no/no-se)
```

Si el usuario reporta problemas:
- FAIL: "Player movement broken"
- Capturar detalles
- Marcar como blocker S2

Si el player se mueve bien:
- PASS: "Player movement OK"

### 3.4 Test 3: Feature principal funciona

Basado en los cambios de FASE 1, identificar feature principal modificada:

Ejemplo:
```
Cambios detectados en: combat/damage.gd

Test 3: Combat damage

Pasos:
1. Inicia un combate (encuentra un enemigo)
2. Ataca al enemigo
3. Observa si el damage se aplica

Preguntas:
- El damage se calcula? (si/no)
- El enemy HP disminuye? (si/no)
- Ves errores en consola? (si/no)
```

Si el usuario reporta problemas:
- FAIL: "Feature {nombre} broken"
- Capturar detalles
- Marcar como blocker S2

Si la feature funciona:
- PASS: "Feature {nombre} OK"

### 3.5 Test 4: No regresiones obvias

```
Test 4: Regresiones

Ejecuta un quick playthrough (1-2 minutos):
1. Juega normalmente
2. Prueba features que NO modificaste

Preguntas:
- Algo que funcionaba antes ahora esta roto? (si/no)
- Si si, que se rompio? (describe)
```

Si el usuario reporta regresion:
- FAIL: "Regresion detectada: {feature}"
- Capturar detalles
- Marcar como blocker S2

Si no hay regresiones:
- PASS: "No regresiones detectadas"

### 3.6 Summary del checklist manual

Tabla de resultados:

| Test | Status | Details |
|------|--------|---------|
| Juego arranca | PASS | No crashes |
| Player movement | PASS | 4-directional OK |
| Feature: combat damage | PASS | Damage applies correctly |
| No regresiones | PASS | Inventory still works |

Veredicto manual:
- Si algun test es FAIL → FAIL
- Si todos son PASS → PASS

## FASE 4: Veredicto final

### 4.1 Combinar resultados

| Category | Status | Blockers |
|----------|--------|----------|
| Checklist automatico | PASS | 0 |
| Checklist manual | PASS | 0 |

Veredicto:
- **PASS:** ambos checklists PASS → safe to merge/release
- **FAIL:** algun checklist FAIL → blockers encontrados

### 4.2 Listar blockers (si FAIL)

Si hay blockers, crear tabla:

| # | Blocker | Severity | Category | Details |
|---|---------|----------|----------|---------|
| 1 | Tests failing | S1 | Automated | 3 tests failed in combat suite |
| 2 | Player movement broken | S2 | Manual | Player doesnt move right |

Severity:
- **S1:** game-breaking (crash, no arranca, tests fallan)
- **S2:** major feature broken (player movement, core mechanic)
- **S3:** minor issue (visual glitch, performance)

### 4.3 Output del veredicto

**Si PASS:**
```markdown
# Smoke Test: PASS ✓

Safe to {merge/release}.

## Summary
- Automated checks: PASS
- Manual checks: PASS
- Blockers: 0

## Warnings (no bloquean)
- 3 hardcoded values en combat/damage.gd
- 1 TODO sin owner en inventory/pickup.gd

Considera arreglar warnings en proximo PR.
```

**Si FAIL:**
```markdown
# Smoke Test: FAIL ✗

NOT safe to {merge/release}.

## Blockers ({count})

| # | Blocker | Severity | Category |
|---|---------|----------|----------|
| 1 | Tests failing | S1 | Automated |
| 2 | Player movement broken | S2 | Manual |

## Details

### Blocker #1: Tests failing
- Category: Automated
- Severity: S1
- Details: 3 tests failed in combat suite (test_damage, test_crit, test_defense)

### Blocker #2: Player movement broken
- Category: Manual
- Severity: S2
- Details: Player doesnt move right (only moves left/up/down)

## Action Required

Arregla los blockers antes de merge/release.

Usa `/debug` para investigar causa raiz:
/debug <descripcion-del-blocker>

Re-ejecuta smoke test despues de arreglar:
/smoke-test
```

## FASE 5: Recomendaciones (si PASS con warnings)

Si el veredicto es PASS pero hay warnings:

### 5.1 Priorizar warnings

| Warning | Impact | Effort | Priority |
|---------|--------|--------|----------|
| Hardcoded values | Balance changes require code edit | S | MEDIUM |
| TODOs sin owner | Tracking issues | S | LOW |

### 5.2 Sugerir fixes

```markdown
## Warnings encontrados (no blockers)

1. **Hardcoded values (3 found)**
   - Location: combat/damage.gd
   - Impact: Balance changes require code edit
   - Fix: Mover valores a assets/data/balance.json
   - Effort: S (1h)

2. **TODO sin owner (1 found)**
   - Location: inventory/pickup.gd:45
   - Impact: No accountability
   - Fix: Agregar owner (TODO(nombre):)
   - Effort: S (1min)

Estos no bloquean merge, pero considera arreglarlos pronto.
```

## FASE 6: Pre-release checks adicionales

Si mode es **pre-release**, agregar checks adicionales:

### 6.1 Validar version number

Buscar version en project.godot:

```bash
grep "config/version" project.godot
```

Si version no cambio desde ultimo tag:
- Warning: "Version number no actualizado"
- Sugerir incrementar version

### 6.2 Validar export presets

Buscar export_presets.cfg:

```bash
cat export_presets.cfg | grep "runnable"
```

Si runnable=false:
- Warning: "Export preset no marcado como runnable"

### 6.3 Validar changelog

Buscar CHANGELOG.md:

```bash
grep "## \[Unreleased\]" CHANGELOG.md
```

Si no hay cambios en Unreleased:
- Warning: "CHANGELOG no actualizado"
- Listar cambios recientes para agregar

### 6.4 Summary de pre-release checks

| Check | Status | Action |
|-------|--------|--------|
| Version number | WARNING | Update version in project.godot |
| Export preset | PASS | Runnable=true |
| CHANGELOG | WARNING | Add recent changes to Unreleased |

## Edge cases

### Sin cambios (git diff vacio)
Si no hay archivos modificados:
- Info: "No hay cambios desde {base}. Smoke test no necesario."
- Terminar con PASS

### Cambios solo en assets/data
Si todos los cambios son LOW risk (assets, data):
- Info: "Solo cambios en assets/data. Smoke test simplificado."
- Skip checklist manual test 3 (feature principal)
- Solo ejecutar tests 1, 2, 4

### Tests tardan mucho (> 2 min)
Si los tests automaticos tardan mucho:
- Info: "Tests corriendo... (esto puede tardar {tiempo-estimado})"
- Mostrar progress si es posible

### Usuario reporta "no se" en checklist manual
Si usuario no sabe si algo funciona:
- Warning: "Respuesta ambigua en test {numero}"
- Re-preguntar con mas detalles
- Si sigue sin saber: marcar como PARTIAL (no PASS, no FAIL)

### Pre-merge desde main branch
Si el usuario esta en main branch:
- Warning: "Estas en main branch. Pre-merge smoke test compara main con main (vacio)."
- Sugerir crear branch: "Crea un branch para tus cambios: git checkout -b feature/nombre"

## Output esperado

Reporte en conversacion (no archivo) de 40-80 lineas con:
- Summary de cambios (archivos modificados por categoria)
- Resultados de checklist automatico (tabla)
- Resultados de checklist manual (tabla)
- Veredicto: PASS/FAIL
- Si FAIL: lista de blockers con severity
- Si PASS con warnings: lista de warnings priorizados

Tiempo de ejecucion: 3-5 min (automated) + 2-3 min (manual) = 5-8 min total

## Diferencia con /playtest

| Feature | /smoke-test | /playtest |
|---------|-------------|-----------|
| Duracion | 5-8 min | 15-30 min |
| Scope | Cambios recientes | Feature completa |
| Depth | Shallow (sanity check) | Deep (funcionalidad + feel) |
| Output | Conversacion | Archivo .md |
| When | Pre-merge, pre-release | Post-implementation |
| Automatico | Si (checklist automatico) | No |

Usa `/smoke-test` antes de merge para validar que no rompiste nada.
Usa `/playtest` despues de implementar feature para validar calidad y game feel.
