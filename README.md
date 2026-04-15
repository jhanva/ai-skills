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

| Skill | Invocacion | Proposito |
|---|---|---|
| `/rpg-design` | Manual | Diseno de sistemas RPG (stats, formulas, turnos, balance, enemy AI) |
| `/game-arch` | Manual | Arquitectura de juegos 2D (game loop, FSM, commands, save system) |
| `/pixel-pipeline` | Manual | Pipeline de assets pixel art (sprites, tiles, atlas, palette swap) |

### Texto

| Skill | Invocacion | Proposito |
|---|---|---|
| `/humanize` | Manual | Humanizar texto generado por IA: diagnostico (`review`) y reescritura (`rewrite`) |

**Siempre activa** = `user-invocable: false`, Claude la carga automaticamente como conocimiento de fondo
**Manual** = solo se invoca con `/nombre` (no se activa automaticamente)
**Automatica** = Claude la invoca cuando detecta contexto relevante (tambien invocable manualmente)

## Agentes

| Agente | Proposito |
|---|---|
| `@prompt-artist` | Transforma ideas en prompts narrativos optimizados para generacion de imagenes (Gemini, DALL-E, Midjourney, Stable Diffusion). Formula de 7 componentes con pesos por dominio |

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
/rpg-design       -->  /plan  -->  /execute
  (sistemas RPG)      (tareas)    (implementar con /tdd)

/game-arch        -->  /plan  -->  /execute
  (arquitectura)      (tareas)    (implementar)

/pixel-pipeline   -->  assets listos para integracion
  (sprites, tiles, atlas)
```

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
  agents/
    prompt-artist.md                   # agente: prompts para imagen
    prompt-artist/
      domains.md                       # 9 perfiles de dominio con pesos
      techniques.md                    # catalogo de tecnicas visuales
      platforms.md                     # adaptacion Gemini/MJ/DALL-E/SD
      text-safety.md                   # texto en imagenes y safety filters
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
