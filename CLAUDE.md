@AGENTS.md

# AI Skills — Custom Skills & Agents para Claude Code

Skills de desarrollo y agentes especializados propios, escritos desde cero. Imponen flujos de trabajo disciplinados: TDD, debugging sistematico, diseno antes de implementacion, y verificacion con evidencia.

Las skills, agentes y hooks de game development (Godot 4, pixel art, produccion de juegos) viven en el repositorio hermano `gamedev-skills` (https://github.com/jhanva/gamedev-skills) y se usan junto con este.
## Estructura

El repo es un marketplace de plugins. Cada skill vive una sola vez en `plugins/<plugin>/skills/<skill>/` (con `SKILL.md`, `references/`, `scripts/` y `agents/openai.yaml` para Codex).

```
.claude-plugin/marketplace.json    — Catalogo para Claude Code
.agents/plugins/marketplace.json   — Catalogo para Codex
plugins/core/                      — Flujo de desarrollo (12 skills, agente prompt-artist, hooks)
  skills/optimize                  — Optimizacion de tokens (siempre activa)
  skills/brainstorm                — Diseno antes de implementar
  skills/plan                      — Spec -> plan de implementacion
  skills/tdd                       — Test-driven development estricto (+ testing-anti-patterns.md)
  skills/debug                     — Debugging sistematico en 4 fases (+ root-cause-tracing.md)
  skills/verify                    — Verificacion antes de completar
  skills/execute                   — Ejecucion con subagentes + review (+ model-selection.md)
  skills/review                    — Code review estructurado
  skills/parallel                  — Agentes paralelos independientes
  skills/secure                    — Analisis de seguridad (references/, scripts/scan-secrets.py)
  skills/codegraph                 — Knowledge graph consultable (references/, scripts/)
  skills/humanize                  — Humanizar texto generado por IA (references/)
  agents/prompt-artist.md          — Agent: prompts para generacion de imagen
  references/prompt-artist/        — domains, techniques, platforms, text-safety
  hooks/hooks.json                 — SessionStart (session-context.sh) y PreToolUse (block-env-access.sh)
plugins/android/                   — android-arch, bitmap-safety, room-audit, ml-ondevice
plugins/image/                     — image-algo, image-pipeline
plugins/repo-ops/                  — git-identity, windows-symlink, browser-control
.codex/                            — Agentes custom, config y hooks nativos de Codex
```

Cada plugin lleva `.claude-plugin/plugin.json` (Claude Code) y `plugin.json` (formato portable Agent Plugins) con el mismo `name`, `version` y `description`.

## Skills disponibles

Instaladas desde el marketplace, las skills se invocan con prefijo de plugin: `/core:tdd`, `/android:room-audit`, `/image:image-algo`, `/repo-ops:git-identity`. La tabla usa el nombre corto.

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
| `/windows-symlink` | Solo usuario | Auditar/habilitar/reparar symlinks en Windows |
| `/browser-control` | Solo usuario | Control de browser via CDP (navegacion, screenshots, clicks, tabs) |
| `/codegraph` | Auto + usuario | Knowledge graph consultable del proyecto (build, query, path, explain) |
| `/git-identity` | Solo usuario | Identidades Git separadas: audit y setup de 4 capas |

"Siempre activa" = `user-invocable: false` (Claude la carga automaticamente, no aparece en menu `/`)

Instalacion: `/plugin marketplace add jhanva/ai-skills` y `/plugin install core@ai-skills` (idem `android`, `image`, `repo-ops`). Desarrollo local: `claude --plugin-dir ./plugins/core`.
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

### Agentes especializados
```
@prompt-artist    Transforma ideas en prompts optimizados para imagen
                  (Gemini, DALL-E, Midjourney, Stable Diffusion)
```

### Browser automation
```
/browser-control       Control de browser via CDP (screenshots, clicks, input, tabs)
                       Conecta al Chrome real del usuario via WebSocket
                       Zero frameworks — scripts Python inline con helpers CDP
```

### Knowledge graph
```
/codegraph build [ruta]        Construye/actualiza el grafo (incremental, zero deps)
/codegraph query [ruta] "..."  Responde desde el grafo sin releer el codigo
/codegraph path [ruta] A B     Camino mas corto entre dos conceptos
/codegraph explain [ruta] X    Un nodo y todas sus conexiones
                               Si codegraph-out/graph.json existe, las preguntas
                               de arquitectura se responden consultando el grafo
```

### Infraestructura
```
/git-identity          Auditoria de cuentas git (4 capas, audit/setup)
/git-identity setup    Configurar separacion de cuentas (macOS/Linux/Windows)
                       Soporta hosts diferentes (GitHub+GitLab)
                       y mismo host (GitHub+GitHub con SSH aliases)
/windows-symlink       Auditar symlinks en Windows (Developer Mode, core.symlinks)
/windows-symlink setup Habilitar soporte de symlinks
/windows-symlink repair Recuperar checkout con symlinks rotos
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

Al anadir o mover una skill: actualizar el `marketplace.json` de ambos runtimes, el `plugin.json` del plugin (subir `version`) y correr `claude plugin validate .`.
