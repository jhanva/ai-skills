---
name: codegraph
description: >
  Convierte un proyecto (codigo, SQL, docs, configs) en un knowledge graph
  persistente y consultable. Extrae clases, funciones, imports, calls,
  herencia y referencias con tags de confianza (EXTRACTED/INFERRED/AMBIGUOUS),
  detecta comunidades, y responde preguntas de arquitectura desde el grafo
  en vez de releer archivos. Outputs: graph.json, GRAPH_REPORT.md y
  visualizacion HTML interactiva. Si codegraph-out/graph.json ya existe,
  las preguntas sobre el codebase se responden consultando el grafo.
when_to_use: >
  Cuando el usuario dice "codegraph", "knowledge graph", "mapea el proyecto",
  "grafo del codigo", o hace preguntas de arquitectura sobre un proyecto que
  ya tiene codegraph-out/ (como funciona X, que llama a Y, traza el flujo
  de Z, que depende de W).
argument-hint: "[build|query|path|explain|label] [ruta] [pregunta]"
allowed-tools:
  - Read
  - Write
  - Glob
  - Grep
  - Agent
  - Bash(python *)
  - Bash(python3 *)
---

# Codegraph — Knowledge graph de proyectos

Pipeline completo en un solo comando, zero dependencias (solo stdlib de
Python 3.10+, sin pip install). El grafo es persistente: se construye una
vez y las consultas posteriores leen `codegraph-out/graph.json` en vez de
re-escanear el proyecto.

Script principal: `${CLAUDE_SKILL_DIR}/scripts/codegraph.py`
(en Windows usar `python`, en macOS/Linux `python3`).

## Fast path — el grafo ya existe

Antes de cualquier otra cosa: si `codegraph-out/graph.json` existe en el
proyecto y la peticion es una pregunta en lenguaje natural sobre el codebase
(no un rebuild explicito), **saltar directo a la seccion Consultas**. No
re-detectar archivos, no reconstruir.

## Build — construir el grafo

```bash
python ${CLAUDE_SKILL_DIR}/scripts/codegraph.py build RUTA
```

- Sin ruta: usar `.` (directorio actual). No preguntar al usuario.
- Es **incremental por defecto**: archivos sin cambios salen del cache
  (hash de contenido). `--force` re-extrae todo e ignora la proteccion
  anti-encogimiento.
- Lenguajes: Python (ast nativo), JS/TS, Kotlin, Java, C#, Go, Rust,
  GDScript, shell, PowerShell, PHP, Ruby, Swift, C/C++, SQL, Markdown,
  JSON/YAML/TOML.
- No requiere API key ni LLM: la extraccion es deterministica. Nunca
  bloquearse esperando una key.

El comando imprime resumen del corpus, salud del grafo y comunidades
pendientes de nombrar. Si imprime `ERROR`, detenerse y reportarlo.

### Nombrar comunidades (siempre despues del primer build)

El build deja las comunidades sin nombre. Nombrarlas es tarea del agente:

1. Leer `codegraph-out/GRAPH_REPORT.md` (seccion Comunidades, muestra las
   20 principales con sus nodos).
2. Para cada comunidad, escribir un nombre de 2-5 palabras segun sus nodos
   (ej. "Gestion de sesiones", "Pipeline de assets").
3. Guardar los labels y regenerar:

```bash
# Escribir con Write el archivo codegraph-out/labels.tmp.json:
# {"0": "Nombre comunidad 0", "3": "Nombre comunidad 3", ...}
python ${CLAUDE_SKILL_DIR}/scripts/codegraph.py label RUTA --file codegraph-out/labels.tmp.json
```

### Reportar al usuario

Al terminar, pegar en el chat SOLO estas secciones del GRAPH_REPORT.md:
God Nodes, Conexiones sorprendentes, y Preguntas sugeridas. No pegar el
reporte completo. Cerrar ofreciendo trazar la pregunta sugerida mas
interesante (la que cruza mas comunidades).

Outputs generados en `RUTA/codegraph-out/`:

```
graph.json       — grafo completo (node-link, compatible d3/GraphRAG)
GRAPH_REPORT.md  — god nodes, comunidades, conexiones, preguntas
graph.html       — visualizacion interactiva (abrir en browser, offline)
```

`codegraph-out/` es committeable: el equipo comparte un solo grafo.

## Consultas — responder desde el grafo

Tres comandos. Elegir segun la forma de la pregunta:

| Pregunta | Comando |
|---|---|
| "Como funciona X" / "que se conecta con X" | `query "..."` (BFS, contexto amplio) |
| "Como llega X hasta Y" / trazar cadena | `query "..." --dfs` |
| "Que relacion hay entre A y B" | `path "A" "B"` |
| "Explica X" / "que es X" | `explain "X"` |

```bash
python ${CLAUDE_SKILL_DIR}/scripts/codegraph.py query RUTA "pregunta" [--dfs] [--budget 2000]
python ${CLAUDE_SKILL_DIR}/scripts/codegraph.py path RUTA "ConceptoA" "ConceptoB"
python ${CLAUDE_SKILL_DIR}/scripts/codegraph.py explain RUTA "Concepto"
```

Reglas para responder (detalles en `references/query-guide.md`):

1. **Vocabulario primero si hay mismatch**: el matcher parte camelCase y
   snake_case pero no traduce sinonimos ni idiomas. Si la pregunta usa
   vocabulario distinto al del codigo (o el query devuelve 0 nodos),
   correr `vocab`, elegir tokens reales del grafo que correspondan a la
   intencion, y re-consultar con esos tokens. Mostrar la expansion al
   usuario. Nunca inventar tokens que no esten en el vocabulario.
2. **Responder solo con lo que el grafo contiene.** Citar
   `source_file:linea` al afirmar hechos concretos. Si el grafo no
   alcanza, decirlo y ofrecer leer el archivo fuente — no alucinar edges.
3. **Cerrar el loop**: guardar la respuesta con `save-answer` para que el
   proximo build la integre como nodo del grafo.

## Pase semantico opcional (docs/conceptos, usa tokens)

El build ya extrae estructura de Markdown gratis (headings, links,
referencias a simbolos). Solo si el usuario pide analisis semantico
profundo de docs, despachar subagentes con el prompt de
`references/semantic-extraction.md` y fusionar con `merge-fragments`.
No hacerlo por defecto.

## Reglas de honestidad

- Nunca inventar un edge ni una relacion que el grafo no contiene.
- Las llamadas ambiguas se descartan, no se adivinan — el reporte dice
  cuantas.
- Mostrar siempre el tag de confianza al citar edges INFERRED.
- Si el build reporta advertencias de salud del grafo, decirselo al
  usuario en el resumen final.

## Argumento: $ARGUMENTS
