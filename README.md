# ai-skills

Skills de desarrollo, agentes especializados y comandos propios para [Claude Code](https://claude.ai/code). Imponen flujos de trabajo disciplinados: TDD, debugging sistematico, diseno antes de implementacion, y verificacion con evidencia.

## Skills

### Core (desarrollo general)

| Skill | Invocacion | Proposito |
|---|---|---|
| `optimize` | Siempre activa | Optimizacion de tokens: lecturas precisas, filtrado de output, delegacion a subagentes |
| `/brainstorm` | Manual | Diseno antes de implementar. Dialogo socratico, multiples enfoques, spec escrita |
| `/plan` | Manual | Convertir spec aprobada en plan de implementacion con tareas de 2-5 min |
| `/tdd` | Automatica | Test-driven development estricto. Ciclo RED-GREEN-REFACTOR obligatorio |
| `/debug` | Automatica | Debugging sistematico en 4 fases con investigacion de causa raiz |
| `/verify` | Automatica | Verificacion con evidencia antes de cualquier claim de exito |
| `/execute` | Manual | Ejecucion de plan con subagentes frescos y revision de 2 etapas (spec + calidad) |
| `/review` | Manual | Code review estructurado con severidades |
| `/parallel` | Manual | Despachar agentes paralelos para problemas independientes |
| `/secure` | Manual | Analisis de seguridad: secrets, injection, auth, crypto, infra. Modo quick o full |

### Android

| Skill | Invocacion | Proposito |
|---|---|---|
| `/android-arch` | Manual | Validacion de boundaries de Clean Architecture Android |
| `/bitmap-safety` | Manual | Auditoria de pipelines de procesamiento de imagen (memory, threading, errors) |
| `/room-audit` | Manual | Auditoria de seguridad de datos con Room (migraciones, schema, data safety) |

### Imagen

| Skill | Invocacion | Proposito |
|---|---|---|
| `/image-algo` | Manual | Diseno de algoritmos de imagen (hashing, similarity, clustering) |
| `/ml-ondevice` | Manual | Integracion de modelos ML on-device en Android |
| `/image-pipeline` | Manual | Diseno de pipelines de procesamiento de imagen multi-paso |

### Game development

Workflow completo para juegos 2D pixel art (RPG, platformer, roguelike) con Godot 4. Soporta GDScript y C#. 9 agentes especializados organizados en jerarquia de estudio + 4 hooks de validacion automatica.

#### Onboarding

| Skill | Invocacion | Agente | Proposito |
|---|---|---|---|
| `/game-start` | Manual | — | Setup guiado: Godot config, estructura de proyecto, GDScript vs C# |

#### Concepto

| Skill | Invocacion | Agente | Proposito |
|---|---|---|---|
| `/game-concept` | Manual | game-designer | Formalizar idea en concept doc (genero, pillars, target audience) |
| `/art-bible` | Manual | pixel-artist + creative-director | Identidad visual: paleta, estilo, resoluciones, restricciones |

#### Diseno

| Skill | Invocacion | Agente | Proposito |
|---|---|---|---|
| `/rpg-design` | Manual | game-designer | Sistemas RPG (stats, formulas, turnos, balance, enemy AI) |
| `/design-system` | Manual | game-designer | GDD para un sistema especifico (inventario, dialog, crafting) |
| `/level-brief` | Manual | level-designer | Disenar nivel: layout, encounters, curva de dificultad, pacing |
| `/balance-check` | Automatica | game-designer | Validar balance numerico (damage curves, economy sinks/faucets) |

#### Arte y assets

| Skill | Invocacion | Agente | Proposito |
|---|---|---|---|
| `/pixel-pipeline` | Manual | pixel-artist | Pipeline completo de pixel art (sprites, tiles, atlas, palette swap) |
| `/sprite-spec` | Manual | pixel-artist | Spec de sprite sheet: frames, estados, dimensiones, hitbox |
| `/tileset-spec` | Manual | pixel-artist | Spec de tileset: tile size, autotile rules, variantes |
| `/palette` | Manual | pixel-artist | Crear/gestionar paletas de color (ramps, restrictions) |
| `/sound-brief` | Manual | sound-designer | Brief de audio: SFX list, mood board musical, integracion Godot |

#### Arquitectura

| Skill | Invocacion | Agente | Proposito |
|---|---|---|---|
| `/game-arch` | Manual | godot-architect | Arquitectura de juegos 2D (game loop, FSM, commands, save system) |
| `/godot-setup` | Manual | godot-architect | Config proyecto Godot: autoloads, input map, export, folder structure |
| `/scene-design` | Manual | godot-architect | Disenar escena: node tree, signals, script responsibilities |

#### Produccion

| Skill | Invocacion | Agente | Proposito |
|---|---|---|---|
| `/sprint` | Manual | producer | Planificar sprint: stories, estimacion, prioridades |
| `/story` | Manual | producer | Crear dev story desde seccion de GDD |
| `/scope-check` | Automatica | producer | Verificar que el scope es realista vs tiempo disponible |

#### QA

| Skill | Invocacion | Agente | Proposito |
|---|---|---|---|
| `/playtest` | Manual | qa-analyst | Reporte estructurado de playtest session |
| `/smoke-test` | Manual | qa-analyst | Checklist rapido pre-merge/pre-release |

### Texto

| Skill | Invocacion | Proposito |
|---|---|---|
| `/humanize` | Manual | Humanizar texto generado por IA: diagnostico (`review`) y reescritura (`rewrite`) |

**Siempre activa** = `user-invocable: false`, Claude la carga automaticamente como conocimiento de fondo
**Manual** = solo se invoca con `/nombre` (no se activa automaticamente)
**Automatica** = Claude la invoca cuando detecta contexto relevante (tambien invocable manualmente)

## Agentes

### Generales

| Agente | Proposito |
|---|---|
| `@prompt-artist` | Transforma ideas en prompts narrativos optimizados para generacion de imagenes (Gemini, DALL-E, Midjourney, Stable Diffusion). Formula de 7 componentes con pesos por dominio |

### Game dev — Jerarquia de estudio

9 agentes organizados en 2 niveles. Directores para sintesis cross-dominio (opus, se activan poco). Especialistas para trabajo de dominio (sonnet, se activan frecuentemente).

```
Tier 1 — Directores (opus, auto-activacion en decisiones cross-dominio)
  creative-director ──── pixel-artist
    (vision, coherencia       sound-designer
     arte + diseno)           game-designer
                              level-designer

  technical-director ─── godot-architect
    (arquitectura,            qa-analyst
     codigo + calidad)        producer
```

| Agente | Tier | Modelo | Dominio | Se activa cuando... |
|---|---|---|---|---|
| `creative-director` | Director | opus | Vision global, coherencia arte/diseno | Conflicto entre dominios creativos, review de concepto |
| `technical-director` | Director | opus | Arquitectura global, performance | Conflicto codigo/performance, decision arquitectural |
| `pixel-artist` | Especialista | sonnet | Sprites, tiles, animacion, paletas, atlas | Editando `assets/sprites/`, `assets/tiles/` |
| `sound-designer` | Especialista | sonnet | SFX, musica, audio pipeline | Editando `assets/audio/`, definiendo audio en GDD |
| `game-designer` | Especialista | sonnet | Sistemas, mecanicas, balance, economia | Escribiendo GDDs en `design/`, discutiendo mecanicas |
| `level-designer` | Especialista | sonnet | Niveles, encounters, dificultad, world building | Editando `design/levels/`, discutiendo layout |
| `godot-architect` | Especialista | sonnet | Escenas, signals, GDScript/C#, patterns Godot | Editando `.gd`, `.cs`, `.tscn`, `.tres` |
| `qa-analyst` | Especialista | sonnet | Tests, bug triage, playtesting | Post-implementacion, pre-release |
| `producer` | Especialista | sonnet | Sprints, scope, milestones, stories | Planificando trabajo, revisando progreso |

## Hooks (game dev)

4 hooks de validacion automatica para codigo y assets de juegos. Comparten biblioteca `_parse.sh` para parsing JSON (cero duplicacion).

| Hook | Evento | Que valida |
|---|---|---|
| `validate-gameplay-code.sh` | PreToolUse (git commit) | No hardcoded values en `src/gameplay/`, delta time usage, no imports de UI en gameplay |
| `validate-assets.sh` | PostToolUse (Write/Edit) | Naming convention en `assets/` (lowercase_snake), JSON valido en data files |
| `check-design-coverage.sh` | PostToolUse (Write/Edit) | Advierte si existe codigo en `src/gameplay/X/` sin su `design/gdd/X.md` correspondiente |
| `session-context.sh` | SessionStart | Muestra branch, sprint activo, archivos modificados sin commit |

## Comandos

| Comando | Proposito |
|---|---|
| `/git-identity` | Auditoria de cuentas git (4 capas: includeIf, shell guards, pre-commit hook, SSH keys) |
| `/git-identity setup` | Configurar separacion de cuentas (macOS/Linux/Windows, mismo host o hosts diferentes) |

## Flujos de trabajo

### Desarrollo general

```
/brainstorm  -->  /plan  -->  /execute (usa /tdd internamente)
                                  |
                              /review  -->  /verify  -->  merge
```

### Debugging

```
/debug  -->  /tdd (para el fix)  -->  /verify
```

### Features de imagen

```
/image-algo     -->  /image-pipeline  -->  /plan  -->  /execute
  (algoritmo)       (arquitectura)       (tareas)    (implementar)

/ml-ondevice    -->  /image-pipeline  -->  /plan  -->  /execute
  (modelo ML)       (arquitectura)       (tareas)    (implementar)
```

### Game development

```
Concepto:
  /brainstorm  -->  /game-concept  -->  /art-bible
                         |
Diseno:                  |
  /design-system  -->  /rpg-design     -->  /balance-check
  /level-brief                                  |
                                                v
Arte:                                    Arquitectura:
  /palette  -->  /pixel-pipeline           /game-arch  -->  /godot-setup
  /sprite-spec   /tileset-spec             /scene-design
  /sound-brief                                  |
                                                v
Produccion:                              QA:
  /sprint  -->  /story  -->  /plan         /playtest  -->  /smoke-test
                  |
                  v
            /execute (usa /tdd)  -->  /review  -->  /verify
```

Integracion con skills generales: `/tdd` para todo codigo, `/debug` para bugs, `/verify` antes de completar, `/review` para code review de GDScript/C#.

### Auditorias

```
/android-arch    (boundaries de Clean Architecture)
/bitmap-safety   (memory, threading, error handling de imagen)
/room-audit      (migraciones, schema, data safety)
/secure quick    (solo archivos cambiados, antes de commit/PR)
/secure full     (proyecto completo, antes de deploy/release)
```

### Texto

```
/humanize review [archivo]    (diagnostico sin modificar)
/humanize rewrite [archivo]   (reescritura completa)
```

### Multiples problemas independientes

```
/parallel  -->  /verify
```

## Estructura

```
.claude/
  skills/
    optimize/SKILL.md                  # optimizacion de tokens (siempre activa)
    brainstorm/SKILL.md                # diseno antes de implementar
    plan/SKILL.md                      # spec -> plan de implementacion
    tdd/
      SKILL.md                         # TDD estricto
      testing-anti-patterns.md         # anti-patrones de testing
    debug/
      SKILL.md                         # debugging sistematico
      root-cause-tracing.md            # rastreo de causa raiz
    verify/SKILL.md                    # verificacion con evidencia
    execute/
      SKILL.md                         # ejecucion con subagentes
      model-selection.md               # guia de seleccion de modelo
    review/SKILL.md                    # code review estructurado
    parallel/SKILL.md                  # agentes paralelos
    secure/
      SKILL.md                         # analisis de seguridad (quick/full)
      references/
        secrets-patterns.md            # 30+ regex para detectar secrets
        code-patterns.md               # injection, auth, crypto
        infra-patterns.md              # Docker, CI/CD, supply chain
      scripts/
        scan-secrets.py                # scanner de secrets (Python, zero deps)
    android-arch/SKILL.md              # Clean Architecture Android
    bitmap-safety/SKILL.md             # pipelines de imagen Android
    room-audit/SKILL.md                # seguridad de datos Room
    image-algo/SKILL.md                # algoritmos de imagen
    ml-ondevice/SKILL.md               # ML on-device Android
    image-pipeline/SKILL.md            # pipelines de imagen multi-paso
    humanize/SKILL.md                  # humanizar texto de IA
    rpg-design/SKILL.md                # sistemas RPG
    game-arch/SKILL.md                 # arquitectura de juegos 2D
    pixel-pipeline/SKILL.md            # pipeline de assets pixel art
    game-start/SKILL.md               # onboarding de proyecto Godot
    game-concept/SKILL.md             # formalizar concepto de juego
    art-bible/SKILL.md                # identidad visual y paleta
    design-system/SKILL.md            # GDD por sistema
    level-brief/SKILL.md              # diseno de nivel
    balance-check/SKILL.md            # validacion de balance numerico
    sprite-spec/SKILL.md              # spec de sprite sheet
    tileset-spec/SKILL.md             # spec de tileset
    palette/SKILL.md                  # gestion de paletas de color
    sound-brief/SKILL.md              # brief de audio
    godot-setup/SKILL.md              # config proyecto Godot
    scene-design/SKILL.md             # diseno de escena Godot
    sprint/SKILL.md                   # planificacion de sprint
    story/SKILL.md                    # dev story desde GDD
    scope-check/SKILL.md              # verificacion de scope
    playtest/SKILL.md                 # reporte de playtest
    smoke-test/SKILL.md               # checklist pre-release
  agents/
    prompt-artist.md                   # agente: prompts para imagen
    prompt-artist/
      domains.md                       # 9 perfiles de dominio con pesos
      techniques.md                    # catalogo de tecnicas visuales
      platforms.md                     # adaptacion Gemini/MJ/DALL-E/SD
      text-safety.md                   # texto en imagenes y safety filters
    gamedev/
      creative-director.md             # director: vision arte + diseno
      technical-director.md            # director: arquitectura + calidad
      pixel-artist.md                  # especialista: sprites, tiles, animacion
      sound-designer.md                # especialista: SFX, musica
      game-designer.md                 # especialista: sistemas, mecanicas, balance
      level-designer.md                # especialista: niveles, encounters
      godot-architect.md               # especialista: engine patterns, escenas
      qa-analyst.md                    # especialista: testing, playtesting
      producer.md                      # especialista: sprints, scope, milestones
  hooks/
    _parse.sh                          # biblioteca compartida (JSON parsing)
    validate-gameplay-code.sh          # hook: no hardcoded values, delta time
    validate-assets.sh                 # hook: naming, JSON valido
    check-design-coverage.sh           # hook: codigo sin GDD = warning
    session-context.sh                 # hook: contexto al iniciar sesion
  commands/
    git-identity.md                    # auditoria y setup de cuentas git
```

Cada skill es un directorio con `SKILL.md` como punto de entrada (frontmatter YAML + instrucciones) y archivos de soporte opcionales que se cargan on-demand.

## Instalacion

Clonar el repo y trabajar dentro del directorio. Las skills se detectan automaticamente por Claude Code al estar en `.claude/skills/`.

```bash
git clone git@github.com:jhanva/ai-skills.git
cd ai-skills
```

Para usar estas skills en **otro proyecto**, hay dos opciones:

**Opcion A — Copiar la carpeta de skills:**

```bash
cp -r /ruta/a/ai-skills/.claude/skills/ /tu/proyecto/.claude/skills/
```

**Opcion B — Agregar como directorio adicional:**

```bash
claude --add-dir /ruta/a/ai-skills
```

Las skills dentro de `.claude/skills/` en directorios adicionales se cargan automaticamente.

## Principios

1. **No codear sin disenar** — `/brainstorm` antes de todo
2. **No implementar sin test** — `/tdd` siempre activo
3. **No adivinar fixes** — `/debug` con causa raiz primero
4. **No decir "listo" sin evidencia** — `/verify` antes de reportar
5. **No confiar en reportes de subagentes** — verificar independientemente
6. **No referenciar origenes externos** — no mencionar repos o proyectos de terceros como inspiracion en documentacion

## Ahorro de tokens

La skill `optimize` se carga automaticamente y aplica reglas de eficiencia en toda interaccion:

| Tecnica | Tokens ahorrados por uso |
|---|---|
| Read con offset/limit vs archivo completo | 500-2,500 |
| Effort low vs high en tarea simple | 10,000-40,000 |
| Subagente para tests vs inline | 1,000-5,000 en contexto principal |
| Filtrar output de comando | 500-3,000 |
| `/clear` entre tareas | todo el contexto acumulado |
| Modelo haiku vs opus en subagente mecanico | ~60% menos costo |

Ademas:

- **Subagentes frescos por tarea** — sin contaminacion de contexto previo
- **Texto completo en prompt** — los subagentes no leen archivos del plan
- **Skills on-demand** — solo se cargan cuando se invocan o Claude detecta relevancia
- **Archivos de referencia separados** — solo se cargan cuando la skill los necesita
- **Review de 2 etapas** — atrapa problemas temprano, evita re-trabajo costoso

## Licencia

Uso personal.
