# Codegraph — Guia de consultas

Cargar esta referencia cuando el usuario haga preguntas contra un grafo
existente y el flujo basico de SKILL.md no alcance.

## Expansion de vocabulario (obligatoria si hay mismatch)

El matcher del CLI tokeniza labels partiendo camelCase/snake_case y
pondera por IDF (tokens raros pesan mas). No hay stemming, sinonimos ni
traduccion: si el usuario pregunta en otro idioma o con otra jerga que el
codigo, el match colapsa a ruido.

Flujo:

1. Volcar el vocabulario real del grafo:

```bash
python ${CLAUDE_SKILL_DIR}/scripts/codegraph.py vocab RUTA > codegraph-out/vocab.txt
```

2. Leer `codegraph-out/vocab.txt` y elegir hasta 12 tokens **presentes en
   esa lista** que correspondan semanticamente a la pregunta:
   - Traduccion: "autenticacion" -> `auth`, `token`, `session` SOLO si
     estan en el vocab.
   - Morfologia: "handlers" -> `handler` SOLO si esta.
   - Si un concepto de la pregunta no tiene token plausible, se omite.
   - Si NINGUN token matchea, decirle al usuario que el corpus no tiene
     vocabulario relevante para esa pregunta y parar. No fabricar.

3. Mostrar la expansion antes de consultar, para que sea auditable:

```
Query expandida (del vocab del grafo, N tokens): [token1, token2, ...]
```

4. Consultar usando los tokens unidos por espacios como pregunta:

```bash
python ${CLAUDE_SKILL_DIR}/scripts/codegraph.py query RUTA "token1 token2 token3"
```

## Interpretar el output

- `NODE label [kind] (source_file Lnn)` — entidad del subgrafo, ordenadas
  por relevancia a la pregunta.
- `EDGE a --relacion [CONFIANZA]--> b` — relacion tipada.
- El output se corta al presupuesto (`--budget N`, default 2000 tokens),
  seleccionando los nodos mas relevantes en vez de truncar a ciegas. Si
  el subgrafo quedo grande y falto contexto, subir el budget.

Al redactar la respuesta:

- Usar solo nodos y edges del output. Citar `source_file:linea`.
- Distinguir hechos (EXTRACTED) de deducciones (INFERRED) cuando la
  distincion importe para la pregunta.
- Si el grafo no cubre la pregunta, decirlo y ofrecer leer los archivos
  fuente directamente.

## Cerrar el feedback loop

Despues de responder, persistir el resultado:

```bash
python ${CLAUDE_SKILL_DIR}/scripts/codegraph.py save-answer RUTA \
  --question "pregunta original del usuario" \
  --answer "resumen de la respuesta (1-3 frases)" \
  --nodes "LabelNodo1" "LabelNodo2" \
  --outcome useful
```

- `--outcome useful` — los nodos citados respondieron bien (default).
- `--outcome dead_end` — el camino no llevo a nada; evita re-derivarlo.
- `--outcome corrected` — la respuesta previa era incorrecta.

El proximo `build` integra la respuesta como nodo `answer` con edges
`cites` hacia los nodos usados. Las sesiones futuras ven las respuestas
previas al consultar temas cercanos.

## path y explain

- `path "A" "B"`: matchea A y B contra labels (fuzzy por tokens) y
  devuelve el camino mas corto con relaciones y confianza por salto.
  Explicar cada salto en lenguaje claro: que significa, por que importa.
- `explain "X"`: nodo + todas sus conexiones agrupadas. Redactar 3-5
  frases: que es, con que se conecta, por que esas conexiones importan.
  Si dos proyectos comparten nombres, verificar el `source_file` del
  nodo elegido antes de afirmar.
- Ambos tambien cierran con `save-answer` (question = "Path de A a B" o
  "Explain X").
