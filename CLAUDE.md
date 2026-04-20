# AI Skills — Custom Skills & Agents para Claude Code

Skills de desarrollo y agentes especializados propios, escritos desde cero. Imponen flujos de trabajo disciplinados: TDD, debugging sistematico, diseno antes de implementacion, y verificacion con evidencia.

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
  rpg-design/SKILL.md              — Diseno de sistemas RPG (stats, combate, balance)
  game-arch/SKILL.md               — Arquitectura de juegos 2D (game loop, FSM, commands)
  pixel-pipeline/SKILL.md          — Pipeline de assets pixel art (sprites, tiles, atlas)
  game-start/SKILL.md              — Onboarding de proyecto Godot (setup guiado)
  game-concept/SKILL.md            — Formalizar concepto de juego (pillars, core loop, MVP)
  art-bible/SKILL.md               — Identidad visual (paleta, estilo, restricciones)
  design-system/SKILL.md           — GDD por sistema (inventario, dialogo, crafting)
  level-brief/SKILL.md             — Diseno de nivel (layout, encounters, dificultad)
  balance-check/SKILL.md           — Validacion de balance numerico
  sprite-spec/SKILL.md             — Spec de sprite sheet (frames, estados, hitbox)
  tileset-spec/SKILL.md            — Spec de tileset (autotile, variantes, layers)
  palette/SKILL.md                 — Gestion de paletas de color (ramps, swaps)
  sound-brief/SKILL.md             — Brief de audio (SFX, musica, Godot integration)
  godot-setup/SKILL.md             — Config proyecto Godot (autoloads, input, display)
  scene-design/SKILL.md            — Diseno de escena Godot (node tree, signals)
  sprint/SKILL.md                  — Planificacion de sprints (1-2 semanas, 3-5 stories)
  story/SKILL.md                   — GDD -> user story con scope y acceptance criteria
  scope-check/SKILL.md             — Validacion de scope (MVP alcanzable? velocity, riesgos)
  playtest/SKILL.md                — Sesion de playtest con checklist y game feel rating
  smoke-test/SKILL.md              — Smoke test pre-merge/pre-release (automated + manual)

.claude/commands/
  git-identity.md                  — Auditoria y setup de cuentas git separadas

.claude/agents/
  prompt-artist.md                 — Agent: prompts para generacion de imagen
  prompt-artist/domains.md         — 9 perfiles de dominio con pesos
  prompt-artist/techniques.md      — Catalogo de tecnicas visuales
  prompt-artist/platforms.md       — Adaptacion Gemini/MJ/DALL-E/SD
  prompt-artist/text-safety.md     — Texto en imagenes y safety filters
  gamedev/creative-director.md     — Director: vision arte + diseno (opus)
  gamedev/technical-director.md    — Director: arquitectura + calidad (opus)
  gamedev/pixel-artist.md          — Especialista: sprites, tiles, animacion
  gamedev/sound-designer.md        — Especialista: SFX, musica
  gamedev/game-designer.md         — Especialista: sistemas, mecanicas, balance
  gamedev/level-designer.md        — Especialista: niveles, encounters
  gamedev/godot-architect.md       — Especialista: engine patterns, escenas
  gamedev/qa-analyst.md            — Especialista: testing, playtesting
  gamedev/producer.md              — Especialista: sprints, scope, milestones

.claude/hooks/
  _parse.sh                        — Biblioteca compartida (JSON parsing)
  block-env-access.sh              — Bloquea acceso a archivos .env
  validate-gameplay-code.sh        — No hardcoded values, delta time, layer separation
  validate-assets.sh               — Naming convention, JSON valido en data files
  check-design-coverage.sh         — Codigo sin GDD = warning
  session-context.sh               — Contexto del proyecto al iniciar sesion
```

## Skills disponibles

| Skill | Invocacion | Proposito |
|---|---|---|
| `optimize` | Siempre activa | Filtrado de output, delegacion con umbral, seleccion de modelo |
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
| `/rpg-design` | Solo usuario | Diseno de sistemas RPG (stats, formulas, turnos, balance, enemy AI) |
| `/game-arch` | Solo usuario | Arquitectura de juegos 2D (game loop, FSM, commands, save system) |
| `/pixel-pipeline` | Solo usuario | Pipeline de assets pixel art (sprites, tiles, atlas, palette swap) |
| `/game-start` | Solo usuario | Onboarding: Godot config, estructura, GDScript vs C# |
| `/game-concept` | Solo usuario | Formalizar idea en concept doc (pillars, core loop, MVP) |
| `/art-bible` | Solo usuario | Identidad visual: paleta, estilo, restricciones pixel art |
| `/design-system` | Solo usuario | GDD para un sistema especifico (inventario, dialogo, crafting) |
| `/level-brief` | Solo usuario | Disenar nivel: layout ASCII, encounters, dificultad |
| `/balance-check` | Auto + usuario | Validar balance numerico (damage curves, economy) |
| `/sprite-spec` | Solo usuario | Spec de sprite sheet: frames, estados, dimensiones, hitbox |
| `/tileset-spec` | Solo usuario | Spec de tileset: autotile rules, variantes, layers |
| `/palette` | Solo usuario | Crear/gestionar paletas de color (ramps, swaps) |
| `/sound-brief` | Solo usuario | Brief de audio: SFX list, musica, integracion Godot |
| `/godot-setup` | Solo usuario | Config proyecto Godot: autoloads, input, display |
| `/scene-design` | Solo usuario | Disenar escena: node tree, signals, scripts |
| `/sprint` | Solo usuario | Planificacion de sprint (stories, capacity, acceptance criteria) |
| `/story` | Solo usuario | GDD -> user story (scope, files, estimacion S/M/L, dependencies) |
| `/scope-check` | Auto + usuario | Validar si MVP es alcanzable (velocity, proyeccion, riesgos) |
| `/playtest` | Solo usuario | Playtest estructurado (funcionalidad + game feel + bugs) |
| `/smoke-test` | Solo usuario | Smoke test pre-merge/pre-release (automated + manual) |

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

### Game development

Workflow completo para juegos 2D pixel art con Godot 4. 9 agentes en jerarquia de estudio + 5 hooks.

#### Concepto → Diseno → Arte → Arquitectura → Produccion → QA
```
/game-start  -->  /brainstorm  -->  /game-concept  -->  /art-bible
                                         |
                  /design-system  -->  /rpg-design  -->  /balance-check
                  /level-brief
                                                            |
/palette  -->  /pixel-pipeline                     /game-arch  -->  /godot-setup
/sprite-spec   /tileset-spec                       /scene-design
/sound-brief                                            |
                                                        v
/scope-check  -->  /sprint  -->  /story  -->  /plan  -->  /execute (usa /tdd)
                                                              |
                                                    /playtest  -->  /smoke-test
                                                              |
                                                    /review  -->  /verify  -->  merge
```

#### Agentes gamedev (jerarquia de estudio)
```
Tier 1 — Directores (opus)
  creative-director ──── pixel-artist, sound-designer, game-designer, level-designer
  technical-director ─── godot-architect, qa-analyst, producer
```

### Agentes especializados
```
@prompt-artist    Transforma ideas en prompts optimizados para imagen
                  (Gemini, DALL-E, Midjourney, Stable Diffusion)
```

### Comandos
```
/git-identity          Auditoria de cuentas git (4 capas)
/git-identity setup    Configurar separacion de cuentas (macOS/Linux/Windows)
                       Soporta hosts diferentes (GitHub+GitLab)
                       y mismo host (GitHub+GitHub con SSH aliases)
```

Para debugging: `/debug` (aplica `/tdd` para el fix y `/verify` para confirmar)

## Principios

1. **No codear sin disenar** — `/brainstorm` antes de todo
2. **No implementar sin test** — `/tdd` siempre activo
3. **No adivinar fixes** — `/debug` con causa raiz primero
4. **No decir "listo" sin evidencia** — `/verify` antes de reportar
5. **No confiar en reportes de subagentes** — verificar independientemente
6. **No referenciar origenes externos** — no mencionar repos, librerias o proyectos de terceros como inspiracion u origen en documentacion del proyecto. El contenido se presenta como propio

## Ahorro de tokens

La skill `optimize` se carga automaticamente y aplica estas reglas en toda interaccion:

- Filtrar output de comandos con pipes antes de que entre al contexto
- Delegar a subagentes solo cuando output esperado > 50 lineas
- Seleccion de modelo para subagentes (haiku/sonnet/opus)
