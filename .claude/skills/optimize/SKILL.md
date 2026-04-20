---
name: optimize
description: >
  Reglas de optimizacion de tokens y contexto que se aplican SIEMPRE.
  Lecturas precisas, delegacion a subagentes, filtrado de output, y seleccion de modelo.
when_to_use: >
  Siempre. Esta skill aplica a toda interaccion.
user-invocable: false
---

# Optimize — Reglas de eficiencia de tokens

Restricciones operativas accionables por el modelo. Aplican en cada accion.

## 1. Lecturas precisas

- **Read con offset/limit** — si necesitas una funcion, localiza con Grep y lee solo ese bloque con offset y limit. Si el archivo es corto (< 100 lineas) o desconocido, leelo completo en la primera lectura
- **No releas archivos** que ya estan en el contexto de esta sesion
- **Grep con output_mode ajustado** — usa `files_with_matches` (default) para localizar, `content` solo cuando necesites ver el codigo, `count` para dimensionar. Ajusta `head_limit` para controlar cuanto entra al contexto

## 2. Tool calls paralelos

Cuando necesites ejecutar herramientas independientes, lanzalas todas en un solo mensaje. Mismos tokens, menos turnos.

```
3 Reads independientes → 1 mensaje con 3 tool calls (1 turno)
3 Reads en 3 mensajes separados → 3 turnos, triple latencia
```

## 3. Delegar a subagentes (con umbral)

Delega operaciones cuyo output se espera > 50 lineas:

- Suites de tests completas
- Exploracion de codebase multi-archivo
- Logs largos, WebFetch

**No delegues si el output esperado es corto** (< 50 lineas). El overhead de un subagente (system prompt + CLAUDE.md + skills) supera el ahorro en esos casos.

Cuando delegues, especifica que necesitas de vuelta:

```
BIEN: "Corre npm test y reporta: cuantos pasan, cuantos fallan, y los nombres de los que fallan"
MAL:  "Corre npm test"
```

## 4. Filtrar output de comandos

Cuando ejecutes comandos con output largo, filtra con pipes en Bash antes de que entre al contexto. Nota: esto aplica a filtrar output de otros comandos, no a buscar en archivos (para eso usa la herramienta Grep).

```bash
# Tests — solo fallos
npm test 2>&1 | grep -A 5 -E '(FAIL|ERROR|error:)' | head -100

# Build — solo errores
npm run build 2>&1 | grep -i -E '(error|failed)' | head -50

# Logs — solo errores recientes
tail -100 app.log | grep -i error
```

## 5. Seleccion de modelo para subagentes

Usa el modelo de menor capacidad que pueda completar la tarea:

| Modelo | Usar para |
|---|---|
| haiku | Buscar archivos, leer/extraer info, tareas mecanicas |
| sonnet | Implementar, integrar, logica de negocio |
| opus | Arquitectura, review, debugging complejo |
