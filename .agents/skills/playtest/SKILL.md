---
name: playtest
description: >-
  Guiar sesion de playtest estructurado para features o niveles de juego 2D en Godot 4. Lee
  GDD del sistema para conocer expected behavior, genera test checklist, guia al usuario
  paso a paso, registra resultados (funcionalidad pass/fail, game feel 1-5, bugs con
  severity S1-S4, sugerencias). Output: production/playtests/playtest-{date}-{feature}.md
---

# Playtest

## Uso en Codex

- Esta skill esta pensada para invocacion explicita con `$playtest`.
- Cuando aqui se indique buscar patrones, usa `rg -n`; para listar archivos, usa `rg --files` o `find`; para leer fragmentos concretos, usa `sed -n`.
- Cuando aqui se hable de subagentes, usa los agentes integrados de Codex o los definidos en `.codex/agents/`, y solo delega si el usuario lo pidio explicitamente.
- Cuando un ejemplo heredado mencione tools de Claude, aplica la traduccion de `AGENTS.md` y expresa la accion con herramientas reales de Codex (`rg`, `find`, `sed -n`, shell puntual y patch nativo).

Validar que feature, sistema, o nivel funciona y se siente bien. Output: `production/playtests/playtest-{date}-{feature}.md`.

## FASE 1: Definir alcance

Parsear input (`{system}/{feature}` o `{level-name}`). Confirmar con el usuario que comportamientos estan incluidos.

## FASE 2: Leer expected behavior

Del GDD (`design/gdd/{system}.md` o `design/levels/{level}.md`): listar que debe pasar, valores esperados, visual/audio feedback, edge cases.

Si no hay GDD: buscar story file como fallback. Si no hay story: pedir listado manual.

## FASE 3: Generar test checklist

Tabla: `# → test case → expected result → category`.

Categories: Functionality (60%), Visual/Audio Feedback (30%), Edge Cases (10%).

Agregar: test cases de integracion (si interactua con otros sistemas) y edge cases (valores extremos, inputs rapidos, estados invalidos).

Total: 5-15 test cases, ordenados happy path primero.

## FASE 4: Guiar paso a paso

Por cada test case:
1. Mostrar instruccion (pasos + expected result)
2. Esperar resultado del usuario (pass/fail/partial)
3. Si fail: capturar actual result, documentar bug con severity (S1=crash, S2=major, S3=minor, S4=cosmetic), steps to reproduce

Mostrar progress tracking despues de cada test.

## FASE 5: Game feel assessment

Ratings 1-5 para cada area:
- **Controls**: responsiveness (1=frustante → 5=perfecto)
- **Visual Feedback**: claridad (1=no veo que pasa → 5=excelente)
- **Pacing**: ritmo (1=frustrante → 5=muy divertido)
- **Difficulty** (si aplica): balance (1=imposible → 5=satisfactorio)
- **Overall**: impression general

Tabla: `area → rating → comentario`.

## FASE 6: Sugerencias

Pedir sugerencias al usuario. Categorizar: `sugerencia → category (Balance/Polish/UX/Bug Fix/New Feature) → priority (HIGH/MEDIUM/LOW) → effort (S/M/L)`.

## FASE 7: Output

Escribir reporte. Leer `references/report-template.md` para plantilla, checklist de salida, y edge cases del flujo.
