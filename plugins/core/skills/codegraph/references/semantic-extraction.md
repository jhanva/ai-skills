# Codegraph — Pase semantico con subagentes

Cargar SOLO cuando el usuario pide analisis semantico profundo de docs
(conceptos, decisiones de diseno, relaciones que la extraccion
deterministica no ve). El build normal ya extrae headings, links y
referencias a simbolos de Markdown sin costo.

## Flujo

1. Listar los archivos de docs a analizar (Glob sobre `*.md`, papers
   convertidos a texto, etc). Excluir los ya cubiertos si solo cambio
   una parte del corpus.
2. Partir en chunks de 15-20 archivos, agrupando por directorio.
3. Crear la carpeta `codegraph-out/fragments/`.
4. Despachar TODOS los subagentes en un solo mensaje (Agent tool,
   `subagent_type="general-purpose"` — necesitan Write). Un agente por
   chunk, con el prompt de abajo.
5. Verificar que cada `codegraph-out/fragments/chunk_NN.json` existe en
   disco. Si falta mas de la mitad, reportar y no continuar.
6. Fusionar y reconstruir:

```bash
python ${CLAUDE_SKILL_DIR}/scripts/codegraph.py merge-fragments RUTA
python ${CLAUDE_SKILL_DIR}/scripts/codegraph.py build RUTA
```

## Prompt para cada subagente

Sustituir FILE_LIST, CHUNK_NUM y CHUNK_PATH (ruta absoluta del fragmento
a escribir):

```
Eres un subagente de extraccion de knowledge graph. Lee los archivos
listados y extrae un fragmento de grafo. Escribe SOLO JSON valido con el
schema de abajo en la ruta CHUNK_PATH usando el Write tool.

Archivos (chunk CHUNK_NUM):
FILE_LIST

Reglas:
- Extrae conceptos con nombre propio, decisiones de diseno, y relaciones
  entre conceptos o hacia simbolos de codigo mencionados.
- confidence EXTRACTED solo si la relacion es explicita en el texto
  (cita, link, "X usa Y"). INFERRED para deducciones razonables con
  confidence_score: 0.95 evidencia directa, 0.85 fuerte, 0.75 razonable,
  0.65 debil. AMBIGUOUS (0.1-0.3) si es incierto — no lo omitas.
- IDs: minusculas, solo [a-z0-9_], formato {ruta_del_archivo}_{concepto}
  con la ruta relativa completa (segmentos unidos por _, sin extension).
  El mismo concepto debe producir siempre el mismo ID: nunca agregar
  sufijos de chunk.
- Para referirte a un simbolo de codigo existente usa su ID canonico:
  {ruta_relativa_sin_extension}_{simbolo} normalizado igual. Si no estas
  seguro de la ruta, omite el edge.
- source_file: la ruta del archivo de origen tal como aparece en
  FILE_LIST, sin acortar.
- No inventes relaciones. Maximo 40 nodos por chunk.

Schema:
{"nodes":[{"id":"docs_diseno_pipeline_de_assets","label":"Pipeline de assets",
"kind":"concept","file_type":"concept","source_file":"docs/diseno.md",
"source_location":"L12"}],
"edges":[{"source":"id_a","target":"id_b","relation":"references|
conceptually_related_to|rationale_for|implements","confidence":"EXTRACTED|
INFERRED|AMBIGUOUS","confidence_score":0.85,"source_file":"docs/diseno.md",
"source_location":"L20"}]}
```

## Validacion

`merge-fragments` valida cada fragmento: descarta JSON invalido, nodos
sin id/label, y normaliza confidence fuera de rango. En el `build`
posterior, los edges cuyos extremos no existen en el grafo se omiten y
se cuentan en el resumen de salud — revisar ese numero: si es alto, los
subagentes estan generando IDs que no matchean el formato canonico.
