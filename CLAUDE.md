# AI Skills — Custom Development Skills para Claude Code

Skills de desarrollo propias, escritas desde cero. Imponen flujos de trabajo disciplinados: TDD, debugging sistematico, diseno antes de implementacion, y verificacion con evidencia.

## Estructura

```
.claude/skills/
  optimize/SKILL.md                — Optimizacion de tokens (siempre activa)
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
  android-arch/SKILL.md            — Validacion de Clean Architecture Android
  bitmap-safety/SKILL.md           — Auditoria de pipelines de imagen
  room-audit/SKILL.md              — Auditoria de seguridad de datos Room
  image-algo/SKILL.md              — Diseno de algoritmos de imagen
  ml-ondevice/SKILL.md             — Integracion de ML on-device Android
  image-pipeline/SKILL.md          — Diseno de pipelines de imagen
  humanize/SKILL.md                — Humanizar texto generado por IA
```

## Skills disponibles

| Skill | Invocacion | Proposito |
|---|---|---|
| `optimize` | Siempre activa | Lecturas precisas, delegacion con umbral, filtrado, modelo por tarea |
| `/brainstorm` | Solo usuario | Diseno antes de implementar |
| `/plan` | Solo usuario | Spec -> plan con tareas de 2-5 min |
| `/tdd` | Auto + usuario | TDD estricto RED-GREEN-REFACTOR |
| `/debug` | Auto + usuario | Debugging sistematico con causa raiz |
| `/verify` | Auto + usuario | Verificacion con evidencia antes de completar |
| `/execute` | Solo usuario | Ejecucion de plan con subagentes |
| `/review` | Solo usuario | Code review con severidades |
| `/parallel` | Solo usuario | Despachar agentes para problemas independientes |
| `/secure` | Solo usuario | Analisis de seguridad (quick: diff only, full: proyecto completo) |
| `/android-arch` | Solo usuario | Validacion de boundaries de Clean Architecture Android |
| `/bitmap-safety` | Solo usuario | Auditoria de pipelines de procesamiento de imagen |
| `/room-audit` | Solo usuario | Auditoria de seguridad de datos con Room |
| `/image-algo` | Solo usuario | Diseno de algoritmos de imagen (hashing, similarity, clustering) |
| `/ml-ondevice` | Solo usuario | Integracion de modelos ML on-device en Android |
| `/image-pipeline` | Solo usuario | Diseno de pipelines de procesamiento de imagen multi-paso |
| `/humanize` | Solo usuario | Humanizar texto de IA: diagnostico y reescritura (review/rewrite) |

"Siempre activa" = `user-invocable: false` (Claude la carga automaticamente, no aparece en menu `/`)
"Solo usuario" = `disable-model-invocation: true` (se invoca manualmente con `/nombre`)
"Auto + usuario" = Claude puede invocarlo automaticamente cuando detecta el contexto relevante

## Flujo recomendado

### General
```
/brainstorm  -->  /plan  -->  /execute (usa /tdd internamente)
                                  |
                              /review  -->  /verify  -->  merge
```

### Features de imagen
```
/image-algo     -->  /image-pipeline  -->  /plan  -->  /execute
  (algoritmo)       (arquitectura)       (tareas)    (implementar)

/ml-ondevice    -->  /image-pipeline  -->  /plan  -->  /execute
  (modelo ML)       (arquitectura)       (tareas)    (implementar)
```

### Auditorias
```
/android-arch    (boundaries de Clean Architecture)
/bitmap-safety   (memory, threading, error handling de imagen)
/room-audit      (migraciones, schema, data safety)
/secure          (seguridad general: secrets, vulnerabilidades)
```

### Texto
```
/humanize review [archivo]    (diagnostico sin modificar)
/humanize rewrite [archivo]   (reescritura completa)
```

Para debugging: `/debug` (aplica `/tdd` para el fix y `/verify` para confirmar)

## Principios

1. **No codear sin disenar** — `/brainstorm` antes de todo
2. **No implementar sin test** — `/tdd` siempre activo
3. **No adivinar fixes** — `/debug` con causa raiz primero
4. **No decir "listo" sin evidencia** — `/verify` antes de reportar
5. **No confiar en reportes de subagentes** — verificar independientemente

## Ahorro de tokens

La skill `optimize` se carga automaticamente y aplica estas reglas en toda interaccion:

- Lecturas precisas (offset/limit, Grep con output_mode ajustado)
- Tool calls paralelos para herramientas independientes
- Delegar a subagentes solo cuando output esperado > 50 lineas
- Filtrar output de comandos con pipes antes de que entre al contexto
- Seleccion de modelo para subagentes (haiku/sonnet/opus)
