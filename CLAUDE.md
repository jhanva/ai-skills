@AGENTS.md

# AI Skills — Custom Skills & Agents para Claude Code

Skills de desarrollo y agentes especializados propios, escritos desde cero. Imponen flujos de trabajo disciplinados: TDD, debugging sistematico, diseno antes de implementacion, y verificacion con evidencia.

Las skills, agentes y hooks de game development (Godot 4, pixel art, produccion de juegos) viven en el repositorio hermano `gamedev-skills` (https://github.com/jhanva/gamedev-skills) y se usan junto con este.
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
  windows-symlink/SKILL.md         — Soporte de symlinks en Windows (audit, setup, repair)
  windows-symlink/references/windows-requirements.md  — Prerequisitos y permisos Windows
  windows-symlink/references/git-recovery.md           — Recuperacion de symlinks rotos en Git
  windows-symlink/scripts/audit-windows-symlink.ps1    — Script de auditoria PowerShell
  windows-symlink/scripts/setup-windows-symlink.ps1    — Script de setup PowerShell
  browser-control/SKILL.md          — Control de browser via CDP (navegacion, screenshots, input, tabs)
  browser-control/references/cdp_helpers.py       — Libreria Python CDP autocontenida
  browser-control/references/connection-guide.md  — Setup y troubleshooting de conexion al browser
  browser-control/references/interaction-patterns.md — Patrones para mecanicas web complejas
  codegraph/SKILL.md               — Knowledge graph consultable de proyectos (build, query, comunidades)
  codegraph/references/query-guide.md          — Expansion de vocabulario y flujo de consultas
  codegraph/references/semantic-extraction.md  — Pase semantico opcional con subagentes
  codegraph/references/graph-format.md         — Schema de graph.json y rubrica de confianza
  codegraph/scripts/codegraph.py               — CLI zero-deps (pipeline completo en un comando)
  codegraph/scripts/cg_extract.py              — Extractores por lenguaje (ast + regex)
  codegraph/scripts/cg_analyze.py              — Clustering Louvain, god nodes, reporte
  codegraph/scripts/cg_query.py                — Query/path/explain con scoring IDF
  codegraph/scripts/cg_html.py                 — Visualizacion HTML autocontenida
  git-identity/SKILL.md            — Identidades Git separadas (4 capas, audit/setup)
  git-identity/references/setup.md — Referencia para modo setup

.claude/agents/
  prompt-artist.md                 — Agent: prompts para generacion de imagen
  prompt-artist/domains.md         — 9 perfiles de dominio con pesos
  prompt-artist/techniques.md      — Catalogo de tecnicas visuales
  prompt-artist/platforms.md       — Adaptacion Gemini/MJ/DALL-E/SD
  prompt-artist/text-safety.md     — Texto en imagenes y safety filters

.claude/hooks/
  _parse.sh                        — Biblioteca compartida (JSON parsing)
  block-env-access.sh              — Bloquea acceso a archivos .env
  session-context.sh               — Contexto del repositorio al iniciar sesion
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
| `/windows-symlink` | Solo usuario | Auditar/habilitar/reparar symlinks en Windows |
| `/browser-control` | Solo usuario | Control de browser via CDP (navegacion, screenshots, clicks, tabs) |
| `/codegraph` | Auto + usuario | Knowledge graph consultable del proyecto (build, query, path, explain) |
| `/git-identity` | Solo usuario | Identidades Git separadas: audit y setup de 4 capas |

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
