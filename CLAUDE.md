# AI Skills — Custom Development Skills para Claude Code

Skills de desarrollo propias, escritas desde cero. Imponen flujos de trabajo disciplinados: TDD, debugging sistematico, diseno antes de implementacion, y verificacion con evidencia.

## Estructura

```
.claude/skills/
  optimize/SKILL.md                — Optimizacion de tokens (siempre activa)
  optimize/scripts/filter-output.sh — Filtrado de output para comandos
  brainstorm/SKILL.md              — Diseno antes de implementar
  plan/SKILL.md                    — Spec -> plan de implementacion
  tdd/SKILL.md                     — Test-driven development estricto
  tdd/testing-anti-patterns.md     — Anti-patrones de testing (referencia)
  debug/SKILL.md                   — Debugging sistematico en 4 fases
  debug/root-cause-tracing.md      — Rastreo de causa raiz (referencia)
  verify/SKILL.md                  — Verificacion antes de completar
  execute/SKILL.md                 — Ejecucion con subagentes + review
  execute/model-selection.md       — Guia de seleccion de modelo (referencia)
  review/SKILL.md                  — Code review estructurado
  parallel/SKILL.md                — Agentes paralelos independientes
  secure/SKILL.md                  — Analisis de seguridad (quick/full)
  secure/references/secrets-patterns.md  — Patrones de deteccion de secrets
  secure/references/code-patterns.md     — Patrones de seguridad en codigo
  secure/references/infra-patterns.md    — Patrones de seguridad en infra
  secure/scripts/scan-secrets.py         — Scanner de secrets (Python, zero deps)
```

## Skills disponibles

| Skill | Invocacion | Proposito |
|---|---|---|
| `optimize` | Siempre activa | Optimizacion de tokens, effort, filtrado, delegacion |
| `/brainstorm` | Solo usuario | Diseno antes de implementar |
| `/plan` | Solo usuario | Spec -> plan con tareas de 2-5 min |
| `/tdd` | Auto + usuario | TDD estricto RED-GREEN-REFACTOR |
| `/debug` | Auto + usuario | Debugging sistematico con causa raiz |
| `/verify` | Auto + usuario | Verificacion con evidencia antes de completar |
| `/execute` | Solo usuario | Ejecucion de plan con subagentes |
| `/review` | Solo usuario | Code review con severidades |
| `/parallel` | Solo usuario | Despachar agentes para problemas independientes |
| `/secure` | Solo usuario | Analisis de seguridad (quick: diff only, full: proyecto completo) |

"Siempre activa" = `user-invocable: false` (Claude la carga automaticamente, no aparece en menu `/`)
"Solo usuario" = `disable-model-invocation: true` (se invoca manualmente con `/nombre`)
"Auto + usuario" = Claude puede invocarlo automaticamente cuando detecta el contexto relevante

## Flujo recomendado

```
/brainstorm  -->  /plan  -->  /execute (usa /tdd internamente)
                                  |
                              /review  -->  /verify  -->  merge
```

Para debugging: `/debug` (aplica `/tdd` para el fix y `/verify` para confirmar)

Para seguridad: `/secure quick` (archivos cambiados) o `/secure full` (proyecto completo)

## Principios

1. **No codear sin disenar** — `/brainstorm` antes de todo
2. **No implementar sin test** — `/tdd` siempre activo
3. **No adivinar fixes** — `/debug` con causa raiz primero
4. **No decir "listo" sin evidencia** — `/verify` antes de reportar
5. **No confiar en reportes de subagentes** — verificar independientemente

## Ahorro de tokens

La skill `optimize` se carga automaticamente y aplica estas reglas en toda interaccion:

- Leer archivos con precision (Grep antes de Read, offset/limit)
- Ajustar effort level por complejidad de tarea (low/medium/high/max)
- Delegar operaciones verbosas a subagentes (tests, logs, exploracion)
- Filtrar output de comandos antes de que entre al contexto
- Compaction con foco (`/compact focus on X`)
- Seleccion de modelo para subagentes (haiku/sonnet/opus)
- Prompts especificos para minimizar lecturas innecesarias
