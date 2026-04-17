---
name: playtest
description: >
  Guiar sesion de playtest estructurado para features o niveles de juego 2D en Godot 4.
  Lee GDD del sistema para conocer expected behavior, genera test checklist, guia al
  usuario paso a paso, registra resultados (funcionalidad pass/fail, game feel 1-5,
  bugs con severity S1-S4, sugerencias). Output: production/playtests/playtest-{date}-{feature}.md
argument-hint: "<feature o area testeada>"
disable-model-invocation: true
allowed-tools:
  - Read
  - Grep
  - Glob
  - Write
agent: qa-analyst
---

# Playtest

Agent que conduce sesiones de playtest estructurado para juegos 2D pixel art en
Godot 4. Diseñado para solo dev principiante en gamedev con experiencia en Android/Kotlin.

## Objetivo

Validar que una feature, sistema, o nivel funciona correctamente y se siente bien:
- Funcionalidad: cada comportamiento esperado funciona (pass/fail)
- Game feel: que tan bien se siente la mecanica (1-5 rating + comentario)
- Bugs: encontrar y documentar con severity y steps to reproduce
- Sugerencias: mejoras basadas en la experiencia de juego

Output: reporte de playtest en `production/playtests/playtest-{date}-{feature}.md`

## Entrada

```
/playtest <feature-o-area>
/playtest combat/damage-formula
/playtest level-1
/playtest player-movement
/playtest inventory
```

## FASE 1: Definir alcance del playtest

### 1.1 Parsear input

Formato esperado: `{system}/{feature}` o `{level-name}`

Ejemplos:
- `combat/damage-formula` → system: combat, feature: damage-formula
- `level-1` → level: level-1
- `player-movement` → system: player, feature: movement

### 1.2 Confirmar con el usuario

Pregunta:
```
Vas a testear: {system}/{feature}

Esto incluye:
- {comportamiento-1}
- {comportamiento-2}
- {comportamiento-3}

Es correcto? O quieres ajustar el alcance?
```

Si el usuario ajusta:
- Actualizar alcance
- Listar nuevos comportamientos incluidos

## FASE 2: Leer GDD del sistema (expected behavior)

### 2.1 Buscar GDD relevante

Para feature de sistema:
```
Buscar: design/gdd/{system}.md
Leer seccion: ## {Feature}
```

Para level:
```
Buscar: design/levels/{level-name}.md
O: design/gdd/levels.md seccion {level-name}
```

### 2.2 Extraer expected behavior

Del GDD, listar:
- Que debe pasar cuando el usuario hace X
- Valores esperados (damage, speed, HP, etc.)
- Visual/audio feedback esperado
- Edge cases mencionados

Ejemplo (combat/damage-formula):
```markdown
Expected behavior (del GDD):
1. Damage = ATK * (1 - DEF/100) * CritMultiplier
2. DEF max 75%, min 0%
3. Crit chance 5%, multiplier 1.5x
4. Min damage 1
5. Damage number aparece sobre objetivo
6. Color amarillo para crit, rojo para normal
7. Sprite shake al recibir damage
```

### 2.3 Si no hay GDD

Si no existe GDD:
- Warning: "No se encontro GDD para {system}. Expected behavior basado en story/codigo."
- Buscar story file: `production/stories/{system}-{feature}.md`
- Si existe, leer acceptance criteria como expected behavior
- Si no existe story: "No hay GDD ni story. Lista comportamientos esperados manualmente."

## FASE 3: Generar test checklist

### 3.1 Convertir expected behavior en test cases

Por cada comportamiento esperado, crear test case:

| # | Test Case | Expected Result | Category |
|---|-----------|-----------------|----------|
| 1 | Attack enemy with ATK=10, DEF=0 | Damage = 10 | Functionality |
| 2 | Attack enemy with ATK=10, DEF=50 | Damage = 5 (50% reduction) | Functionality |
| 3 | Attack enemy with ATK=10, DEF=100 | Damage >= 1 (capped at 75% reduction) | Functionality |
| 4 | Attack enemy 100 times | ~5 critical hits | Functionality |
| 5 | Critical hit occurs | Damage = normal * 1.5 | Functionality |
| 6 | Hit enemy | Damage number appears above target | Visual Feedback |
| 7 | Critical hit | Damage number is yellow | Visual Feedback |
| 8 | Normal hit | Damage number is red | Visual Feedback |
| 9 | Hit enemy | Enemy sprite shakes | Visual Feedback |

Categories:
- **Functionality:** feature funciona como diseñado
- **Visual Feedback:** jugador puede ver que paso
- **Audio Feedback:** jugador puede oir que paso
- **Edge Cases:** comportamiento en limites (valores extremos, inputs invalidos)

### 3.2 Agregar test cases de integracion

Si la feature interactua con otros sistemas:

Ejemplo (combat integra con stats, UI, animation):
```
| 10 | Player stats increase | Damage increases proportionally | Integration |
| 11 | Enemy dies (HP=0) | Combat ends, victory screen | Integration |
```

### 3.3 Agregar test cases de edge cases

Pensar en:
- Valores extremos (ATK=0, DEF=999, HP=1)
- Inputs rapidos (spam attack button)
- Estados invalidos (attack when no target, attack self)

Ejemplo:
```
| 12 | Attack with ATK=0 | Damage = 1 (min damage) | Edge Case |
| 13 | Spam attack button | Only 1 attack per turn | Edge Case |
| 14 | Attack when no enemy | No damage dealt, error message? | Edge Case |
```

### 3.4 Validar checklist

Checklist debe tener:
- 5-15 test cases (no muy corto, no exhaustivo)
- Mix de Functionality (60%), Visual/Audio (30%), Edge Cases (10%)
- Test cases ordenados logicamente (happy path primero, edge cases al final)

## FASE 4: Guiar al usuario paso a paso

### 4.1 Mostrar checklist al usuario

```
Test Checklist para {feature}:

Total test cases: {count}

Voy a guiarte paso a paso. Por cada test:
1. Te digo que hacer
2. Te digo que esperar
3. Me dices que paso (pass/fail/partial)

Listo para empezar? (Responde "si" cuando tengas el juego abierto)
```

Esperar confirmacion del usuario.

### 4.2 Ejecutar test cases uno por uno

Por cada test case:

**Paso 1: Instruccion**
```
Test #{numero}: {test-case}

Pasos:
1. {step-1}
2. {step-2}
3. {step-3}

Expected result: {expected-result}

Ejecuta el test y dime: pass, fail, o partial (con detalles)
```

**Paso 2: Capturar resultado**

Esperar respuesta del usuario. Parsear:
- **pass:** test paso correctamente
- **fail:** test fallo, expected != actual
- **partial:** test paso pero con issues menores

Si fail o partial:
```
Que paso? (describe actual result)
```

Capturar actual result del usuario.

**Paso 3: Capturar bugs si fail**

Si el test fallo:
```
Esto es un bug. Voy a documentarlo.

Steps to reproduce:
1. {paso-1-del-test}
2. {paso-2-del-test}

Expected: {expected-result}
Actual: {actual-result-del-usuario}

Severity:
S1 = Crash/game-breaking
S2 = Major feature broken
S3 = Minor issue, workaround exists
S4 = Visual/cosmetic

Que severity le das? (S1/S2/S3/S4)
```

Capturar severity del usuario.

Agregar bug a lista:

| Bug # | Test Case | Severity | Expected | Actual | Steps to Reproduce |
|-------|-----------|----------|----------|--------|-------------------|
| 1 | Test #3 | S2 | Damage >= 1 | Damage = 0 | 1. Set enemy DEF=100, 2. Attack, 3. Observe damage=0 |

### 4.3 Completar todos los test cases

Repetir FASE 4.2 para cada test case de la checklist.

Progress tracking:
```
Progress: {completados}/{total} tests
Pass: {pass-count}
Fail: {fail-count}
Partial: {partial-count}
```

## FASE 5: Game feel assessment

Despues de completar todos los test cases funcionales:

### 5.1 Preguntas de game feel

Por cada area de game feel:

**Controls (como se siente controlar)**
```
Controls (1-5):
1 = Frustante, no responde
2 = Torpe, delay notable
3 = Funcional, acceptable
4 = Responsive, se siente bien
5 = Perfecto, muy satisfactorio

Rating: ?
Comentario libre: ?
```

**Visual Feedback**
```
Visual Feedback (1-5):
1 = No puedo ver que pasa
2 = Feedback minimo, confuso
3 = Puedo ver lo basico
4 = Feedback claro, informativo
5 = Excelente, muy claro y pulido

Rating: ?
Comentario: ?
```

**Pacing (ritmo del gameplay)**
```
Pacing (1-5):
1 = Muy lento o muy rapido, frustrante
2 = Ritmo incomodo
3 = Ritmo acceptable
4 = Buen ritmo, engaging
5 = Perfecto, muy divertido

Rating: ?
Comentario: ?
```

**Difficulty (si aplicable)**
```
Difficulty (1-5):
1 = Imposible
2 = Muy dificil, frustrante
3 = Desafiante pero justo
4 = Bien balanceado
5 = Perfecto, muy satisfactorio

Rating: ?
Comentario: ?
```

### 5.2 Overall feel

```
Overall (1-5):
1 = Broken, no jugable
2 = Funciona pero no es divertido
3 = Funcional, acceptable
4 = Divertido, buen foundation
5 = Excelente, muy pulido

Rating: ?
Comentario general: ?
```

### 5.3 Capturar respuestas

Crear tabla:

| Area | Rating | Comentario |
|------|--------|------------|
| Controls | 4 | Responsive, pero el attack button a veces no registra si presiono muy rapido |
| Visual Feedback | 3 | Damage numbers son claros, pero el shake es muy sutil |
| Pacing | 4 | Buen ritmo de combate, no muy lento |
| Difficulty | 3 | Enemies muy faciles, seria mejor con mas HP |
| **Overall** | **4** | Funciona bien, divertido, necesita polish |

## FASE 6: Sugerencias de mejora

### 6.1 Pedir sugerencias al usuario

```
Basado en el playtest, que mejorarias?

Sugerencias (pueden ser features nuevas, tweaks, polish, fixes):
- Sugerencia 1
- Sugerencia 2
- ...
```

### 6.2 Categorizar sugerencias

Por cada sugerencia, clasificar:

| # | Sugerencia | Category | Priority | Effort |
|---|------------|----------|----------|--------|
| 1 | Aumentar enemy HP 50% | Balance | HIGH | S (ajustar valor) |
| 2 | Shake mas pronunciado | Polish | MEDIUM | S (ajustar tween) |
| 3 | Attack button buffer para spam clicks | UX | LOW | M (implementar queue) |
| 4 | Sound effects para hits | Audio | MEDIUM | M (agregar audio) |

Categories:
- **Balance:** numeros, difficulty, progression
- **Polish:** visual/audio feedback, animations, juice
- **UX:** controls, UI, player experience
- **Bug Fix:** arreglar bug encontrado en playtest
- **New Feature:** agregar algo que no existia

Priority:
- **HIGH:** bloquea la diversion, debe arreglarse
- **MEDIUM:** mejoraria la experiencia notablemente
- **LOW:** nice-to-have, puede esperar

Effort:
- **S:** 1-2h (ajustar valores, tweaks)
- **M:** 3-5h (nueva logica, assets)
- **L:** 6-10h (sistema nuevo)

## FASE 7: Output del playtest report

### 7.1 Formato del archivo

Crear `production/playtests/playtest-{date}-{feature}.md`:

```markdown
# Playtest Report: {feature}

**Fecha:** {YYYY-MM-DD}
**Tester:** {nombre-del-usuario o "dev"}
**Build:** {version o commit hash si esta disponible}
**Duracion:** {minutos de playtest}

## Scope

Feature testeada: {system}/{feature}

Comportamientos incluidos:
- {comportamiento-1}
- {comportamiento-2}

## Test Results

| # | Test Case | Expected Result | Status | Actual Result | Notes |
|---|-----------|-----------------|--------|---------------|-------|
| 1 | Attack enemy ATK=10 DEF=0 | Damage = 10 | PASS | Damage = 10 | - |
| 2 | Attack enemy ATK=10 DEF=50 | Damage = 5 | PASS | Damage = 5 | - |
| 3 | Attack enemy ATK=10 DEF=100 | Damage >= 1 | FAIL | Damage = 0 | Bug #1 |
| 4 | Attack 100 times | ~5 crits | PARTIAL | 8 crits | Crit rate parece alto |
| ... | ... | ... | ... | ... | ... |

**Summary:**
- Total tests: 12
- Pass: 8 (66.7%)
- Fail: 2 (16.7%)
- Partial: 2 (16.7%)

## Bugs Found

| Bug # | Severity | Test Case | Expected | Actual | Steps to Reproduce |
|-------|----------|-----------|----------|--------|-------------------|
| 1 | S2 | Attack DEF=100 | Damage >= 1 | Damage = 0 | 1. Set enemy DEF=100, 2. Attack, 3. Observe 0 damage |
| 2 | S4 | Damage number color | Yellow on crit | White on crit | 1. Trigger crit, 2. Observe damage number color |

### Bug Breakdown
- S1 (Critical): 0
- S2 (Major): 1
- S3 (Minor): 0
- S4 (Cosmetic): 1

## Game Feel Assessment

| Area | Rating | Comentario |
|------|--------|------------|
| Controls | 4/5 | Responsive, attack button a veces no registra en spam |
| Visual Feedback | 3/5 | Damage numbers claros, shake muy sutil |
| Pacing | 4/5 | Buen ritmo, no muy lento |
| Difficulty | 3/5 | Enemies muy faciles, necesitan mas HP |
| **Overall** | **4/5** | Divertido, buen foundation, necesita polish |

## Sugerencias de Mejora

| # | Sugerencia | Category | Priority | Effort | Notes |
|---|------------|----------|----------|--------|-------|
| 1 | Fix bug #1 (damage=0) | Bug Fix | HIGH | S | Revisar DEF capping logic |
| 2 | Aumentar enemy HP 50% | Balance | HIGH | S | Ajustar base_hp en enemy stats |
| 3 | Shake mas pronunciado | Polish | MEDIUM | S | Aumentar magnitude del tween |
| 4 | Fix crit rate (parece > 5%) | Bug Fix | MEDIUM | S | Verificar Random.randf() |
| 5 | Sound effects para hits | Audio | MEDIUM | M | Agregar audio player + assets |
| 6 | Attack button buffer | UX | LOW | M | Implementar input queue |

## Proximos Pasos

1. **Fix blockers (S1/S2 bugs):**
   - Bug #1: damage=0 con high DEF

2. **Balance tweaks:**
   - Aumentar enemy HP
   - Verificar crit rate

3. **Polish:**
   - Shake animation
   - Damage number color (bug #2)

4. **Opcional:**
   - Sound effects
   - Input buffer

## Notes

{Notas adicionales del tester, observaciones, contexto}

Ejemplo:
- Combat flow se siente bien, base solida
- Visual feedback necesita mas juice
- Difficulty muy baja, no hay challenge
- Considerar agregar mas enemy types para variedad
```

### 7.2 Validar output

Checklist antes de escribir archivo:
- [ ] Fecha y metadata completos
- [ ] Test results con status (pass/fail/partial)
- [ ] Bugs documentados con severity y steps
- [ ] Game feel ratings (1-5) con comentarios
- [ ] Sugerencias categorizadas y priorizadas
- [ ] Proximos pasos listados

## FASE 8: Transicion al usuario

### 8.1 Mensaje final

```
Playtest completado: {feature}

Resultados:
- Tests: {pass}/{total} pass ({pass-rate}%)
- Bugs: {bugs-count} ({S1-count} critical, {S2-count} major)
- Overall feel: {overall-rating}/5

{si hay bugs S1 o S2:}
⚠️  Bugs blocker encontrados:
- Bug #{numero}: {descripcion} (S{severity})

Estos bugs bloquean progreso. Usa `/debug` para investigar causa raiz.

{si no hay bugs blocker:}
✓ No hay bugs blocker. Feature jugable.

Sugerencias HIGH priority:
- {sugerencia-1}
- {sugerencia-2}

Proximo paso:
- Arreglar bugs (si hay)
- Implementar sugerencias HIGH con `/plan` + `/execute`
- Re-playtest despues de cambios

Archivo generado: production/playtests/playtest-{date}-{feature}.md
```

### 8.2 Auto-invoke /debug si hay bugs S1/S2

Si hay bugs con severity S1 o S2:
```
Detecte {count} bugs blocker. Quieres que investigue con /debug?

(Si usuario dice si, invocar /debug para el primer bug S1/S2)
```

## Edge cases

### Feature muy grande (15+ test cases)
Si el checklist tiene 15+ test cases:
- Warning: "Checklist muy largo ({count} tests). Dividir en sesiones mas cortas?"
- Sugerir dividir por sub-features
- Ejemplo: combat → combat/damage, combat/turns, combat/victory

### Usuario reporta bug pero test paso
Si usuario dice "encontre un bug" pero el test relacionado paso:
- Agregar bug a lista de todas formas
- Marcar test como PARTIAL
- Nota: "Bug encontrado fuera del test case, reproducible?"

### No hay GDD ni story
Si no hay documentacion de expected behavior:
- Warning: "No hay GDD. No puedo generar checklist automaticamente."
- Pedir al usuario que liste expected behaviors manualmente
- Generar checklist basado en su input

### Playtest muy corto (< 5 test cases ejecutados)
Si usuario completa < 5 tests:
- Warning: "Playtest muy corto. Coverage insuficiente."
- Sugerir completar mas tests antes de generar reporte

### Todos los tests fallan
Si pass rate < 30%:
- Warning: "Feature muy rota ({pass-rate}% pass). Considera no playtest hasta fix basico."
- Listar top 3 bugs mas severos
- Sugerir arreglar antes de continuar playtest

## Output esperado

Archivo markdown estructurado de 100-200 lineas con:
- Test results table (pass/fail/partial)
- Bugs table (severity, steps to reproduce)
- Game feel ratings con comentarios
- Sugerencias priorizadas
- Proximos pasos

Tiempo de ejecucion: 10-20 min (dependiendo de cantidad de test cases y interaccion con usuario)
