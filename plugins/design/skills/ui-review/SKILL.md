---
name: ui-review
description: >
  Auditoria de solo lectura de interfaces existentes contra criterios verificables:
  accesibilidad (contraste, foco, nombres accesibles, orden de lectura), area tactil,
  responsive, tipografia, color por tokens, motion, formularios, estados y navegacion.
  Reporta con severidades y archivo:linea, igual que /review. Cubre Jetpack Compose y web.
  Usar cuando: el usuario dice "revisa la UI", "auditoria de accesibilidad", "ui review",
  "esta pantalla cumple", "revisa el diseno", o antes de dar por terminada una pantalla.
argument-hint: "[ruta o pantalla] [--stack compose|web]"
disable-model-invocation: true
allowed-tools:
  - Read
  - Grep
  - Glob
  - Agent
  - Bash(python:*)
  - Bash(python3:*)
  - Bash(py:*)
  - Bash(git diff:*)
---

# UI Review — Auditoria de interfaz con evidencia

Solo lectura. No se modifica ningun archivo: se leen composables, componentes, estilos y
recursos, y se reporta. Los arreglos se hacen despues con `/tdd`.

## Resolver alcance

1. Argumento con ruta o nombre de pantalla -> auditar eso.
2. Sin argumento -> archivos de UI cambiados (`git diff --name-only HEAD` filtrado por
   `*.kt` bajo `ui/`, `*.tsx`, `*.jsx`, `*.vue`, `*.html`, `*.css`). Si no hay cambios, preguntar.
3. Stack: `compose` si los archivos son `.kt` con `@Composable`; `web` en el resto. Si hay ambos,
   auditar por separado.
4. Si existe `design-system/**/MASTER.md`, leerlo: sus tokens, escala y checklist son el contrato
   a verificar. Si existe `pages/<pantalla>.md`, prevalece para esa pantalla.

## Paso 0: detector determinista

Antes de gastar un agente, correr las reglas mecanicas:

```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/detect.py" <rutas> [--json]
```

Exit 1 = hallazgos (cada uno con `archivo:linea`, regla, severidad y la guia que incumple); 0 =
limpio. Estos hallazgos van al reporte tal cual, en la seccion `Detector`, y el agente **no los
repite**: se concentra en lo que un regex no ve (contraste efectivo, orden de lectura, estados,
copy, composicion). Si el plugin tiene el hook activo, el detector ya corrio en cada edicion;
igual se corre aqui para tener la foto completa.

## Despachar el auditor

Despachar el agente `ui-reviewer` del plugin con Agent tool (`subagent_type: "design:ui-reviewer"`;
`ui-reviewer` si el plugin se carga con `--plugin-dir`). Es de solo lectura y conoce el formato.
El prompt aporta:

```
Audita la UI en: [rutas]
Stack: [compose|web]
Sistema de diseno: [ruta a MASTER.md y page override, o "no hay"]
Producto: [ruta a PRODUCT.md o "no hay"]
Modo de la superficie: [persuadir|operar|leer|experimentar, de MASTER/pages]
Hallazgos del detector (no repetir): [pegar salida de detect.py]
Contexto: [que hace la pantalla y para quien]

Verifica en este orden y detente en cada categoria hasta agotarla:
1. Accesibilidad critica: contraste real de cada par texto/fondo, foco visible, nombre accesible
   de cada control, orden de lectura, color como unico medio
2. Interaccion: area tactil minima, feedback al pulsar, alternativa a gestos y hover
3. Layout: sin scroll horizontal, insets y teclado, espacio reservado para contenido asincrono
4. Tipografia y color: tamanos base, escala respetada, tokens en vez de literales, modo oscuro
5. Motion: proposito, duraciones, reduced motion
6. Formularios, estados (vacio/carga/error) y navegacion atras
7. Composicion (solo modo persuadir/experimentar): eyebrows, hero, familias de layout, zigzag,
   tarjetas iguales, bento (guias comp-*)

Para cada categoria consulta el criterio exacto con:
python "${CLAUDE_PLUGIN_ROOT}/scripts/search.py" "<tema>" --domain ux -n 3
python "${CLAUDE_PLUGIN_ROOT}/scripts/search.py" "<tema>" --stack [stack] -n 3
```

## Verificar el reporte

El reporte del agente no se reenvia sin mas: abrir 2-3 hallazgos criticos o importantes y
confirmar que el archivo y la linea existen y dicen lo que el agente afirma. Si un hallazgo
no se sostiene, se elimina del reporte final y se anota que se descarto.

Para contraste, calcular en vez de estimar:

```bash
python -c "import sys; sys.path.insert(0, r'${CLAUDE_PLUGIN_ROOT}/scripts'); import catalog; print(catalog.contrast_ratio('#RRGGBB', '#RRGGBB'))"
```

## Formato del reporte

```
## UI Review — [pantalla o rutas]

### Detector (mecanico)
- [archivo:linea] regla `id` -> guia `id-guia`

### Critico (bloquea entrega)
- [archivo:linea] Hallazgo. Criterio: `id-guia` (WCAG x.x.x). Evidencia: [valor medido o codigo]

### Importante (arreglar antes de merge)
- [archivo:linea] ...

### Menor
- [archivo:linea] ...

### Cumple
- [lo que esta bien, concreto: "todos los IconButton tienen contentDescription de accion"]

## Evaluacion
APROBADO / APROBADO_CON_CAMBIOS / CAMBIOS_REQUERIDOS
```

Cada hallazgo cita el `id` de la guia del catalogo para que el arreglo sea trazable. Sin
hallazgos en una severidad, omitir la seccion. Sin sycophancy: si la pantalla falla
accesibilidad, es CAMBIOS_REQUERIDOS aunque se vea bien.

Argumento recibido: $ARGUMENTS
