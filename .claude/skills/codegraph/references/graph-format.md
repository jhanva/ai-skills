# Codegraph — Formato del grafo

Referencia del schema de `codegraph-out/graph.json` para uso programatico
(GraphRAG, scripts propios, otras herramientas).

## Documento

Formato node-link (compatible d3 y NetworkX `node_link_graph`):

```json
{
  "directed": true,
  "multigraph": false,
  "graph": {"root": "...", "date": "...", "total_files": 0,
            "by_category": {}, "tool": "codegraph", "version": 1},
  "nodes": [...],
  "links": [...]
}
```

## Nodos

```json
{
  "id": "src_auth_session_sessionmanager",
  "label": "SessionManager",
  "kind": "class",
  "file_type": "code",
  "source_file": "src/auth/session.py",
  "source_location": "L4",
  "community": 3
}
```

- `id`: deterministico. `{ruta_relativa_sin_extension}_{simbolo}`, todo
  normalizado a `[a-z0-9_]`, con TODOS los niveles de directorio (asi dos
  archivos con el mismo nombre en carpetas distintas no colisionan).
  Nodos de archivo usan solo la ruta. Modulos externos: `external_{nombre}`.
- `kind`: `file`, `class`, `interface`, `enum`, `object`, `function`,
  `method`, `table`, `view`, `concept`, `doc`, `config`, `external`,
  `answer`.
- `file_type`: `code`, `sql`, `document`, `config`, `external`,
  `concept`, `answer`.
- `community`: entero asignado por clustering de modularidad. Los nombres
  legibles viven en `codegraph-out/labels.json`.
- Nodos `answer` llevan ademas `answer` (texto) y `outcome`
  (`useful|dead_end|corrected`).

## Edges

```json
{
  "source": "src_auth_session_create_session",
  "target": "src_db_queries_insert_session",
  "relation": "calls",
  "confidence": "INFERRED",
  "confidence_score": 0.95,
  "source_file": "src/auth/session.py",
  "source_location": "L7"
}
```

Relaciones: `contains`, `imports`, `calls`, `inherits`, `references`,
`foreign_key`, `joins`, `cites`, y las semanticas de subagentes
(`conceptually_related_to`, `rationale_for`, `implements`).

## Rubrica de confianza

| Tag | Score | Cuando |
|---|---|---|
| EXTRACTED | 1.0 | Explicito en el fuente: import, call en el mismo archivo, herencia local, FK |
| INFERRED | 0.95 | Callee/base con definicion unica en el corpus (mismo lenguaje) |
| INFERRED | 0.75 | Varias definiciones, desambiguada por mismo directorio |
| INFERRED | 0.55-0.85 | Deducciones del pase semantico (segun evidencia) |
| AMBIGUOUS | 0.1-0.3 | Incierto, marcado para revision |

Las llamadas con multiples definiciones candidatas sin desambiguar se
**descartan** (no se emiten edges); el build reporta cuantas.

## Otros archivos de codegraph-out/

- `manifest.json` — ruta relativa -> hash de contenido (base del build
  incremental).
- `cache/*.json` — extraccion por archivo, clave = hash. Se limpia solo.
- `labels.json` — `{"anchors": {"id_nodo_representativo": "nombre"}}`.
  Los labels se anclan al nodo de mayor grado de cada comunidad (no al id
  numerico, que cambia entre rebuilds). El comando `label` recibe ids
  numericos del build actual y los convierte a anclas automaticamente.
- `semantic.json` — capa persistente de fragmentos LLM + respuestas
  guardadas; sobrevive rebuilds.
