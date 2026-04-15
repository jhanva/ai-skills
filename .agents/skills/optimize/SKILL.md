---
name: optimize
description: "Sirve como referencia explícita para reducir costo y contexto en Codex: lecturas precisas, paralelismo seguro y delegación prudente. Las reglas base ya viven en el AGENTS.md del repo; invócala cuando el usuario quiera optimizar workflow, costo o consumo de contexto. No la uses como sustituto de implementar o verificar."
---

# Optimize — Reglas de eficiencia de tokens

## Uso en Codex

- Las reglas siempre activas de eficiencia viven en el `AGENTS.md` del repo para que Codex las aplique como instrucciones globales oficiales del proyecto.
- Invoca `$optimize` cuando quieras revisar explícitamente costo, contexto, paralelismo seguro o selección de agentes/modelos.
- En Codex, prioriza `rg`, `rg --files`, lecturas puntuales con `sed -n` y `multi_tool_use.parallel` para lecturas independientes.

Restricciones operativas accionables por el modelo. Aplican en cada accion.

## 1. Lecturas precisas

- **Lecturas puntuales** — si necesitas una funcion, lee solo ese bloque con `sed -n '120,150p' archivo` o localiza primero con `rg -n "nombreFuncion"`.
- **No releas archivos** que ya estan en el contexto de esta sesion
- **Busqueda antes de lectura** — usa `rg -n` para localizar, `rg --files` para listar y solo despues abre el fragmento minimo necesario

## 2. Tool calls paralelos

Cuando necesites ejecutar herramientas independientes (ej: 3 lecturas, `rg` + `find`, o varios `sed -n`), lanzalas en paralelo. Reduce latencia sin costo extra de tokens.

## 3. Delegar a subagentes (con umbral)

Delega operaciones cuyo output se espera > 50 lineas:

- Suites de tests completas
- Exploracion de codebase multi-archivo
- Logs largos, browsing web

**No delegues si el output esperado es corto** (< 50 lineas). El overhead de un subagente (prompt base + AGENTS + skills) supera el ahorro en esos casos.

En Codex, prefiere:
- `explorer` para exploracion read-only
- `worker` o `task_implementer` para ejecucion acotada
- `reviewer` para evaluaciones de calidad
- `security_auditor` para auditorias de seguridad read-only

Cuando delegues, especifica que necesitas de vuelta:

```
BIEN: "Corre npm test y reporta: cuantos pasan, cuantos fallan, y los nombres de los que fallan"
MAL:  "Corre npm test"
```

## 4. Filtrar output de comandos

Cuando ejecutes comandos con output largo, filtra con pipes antes de que entre al contexto:

```bash
# Tests — solo fallos
npm test 2>&1 | grep -A 5 -E '(FAIL|ERROR|error:)' | head -100

# Build — solo errores
npm run build 2>&1 | grep -i -E '(error|failed)' | head -50

# Logs — solo errores recientes
tail -100 app.log | grep -i error
```

## 5. Seleccion de modelo para subagentes

Usa el modelo mas barato que pueda completar la tarea:

| Modelo | Usar para |
|---|---|
| `gpt-5.4-mini` | Buscar archivos, extraer info, tareas mecanicas |
| `gpt-5.2` | Implementar, integrar, logica de negocio |
| `gpt-5.4` | Arquitectura, review, debugging complejo |
