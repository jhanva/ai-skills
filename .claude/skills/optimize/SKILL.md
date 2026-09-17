---
name: optimize
description: >
  Filtrado de output, delegacion con umbral, seleccion de modelo para
  subagentes. Usar cuando: siempre, en toda interaccion.
user-invocable: false
---

# Optimize — Eficiencia de tokens

## 1. Filtrar output de comandos

Filtra con pipes en Bash antes de que entre al contexto:

```bash
npm test 2>&1 | grep -A 5 -E '(FAIL|ERROR|error:)' | head -100
npm run build 2>&1 | grep -i -E '(error|failed)' | head -50
```

## 2. Delegar a subagentes (con umbral)

Delega operaciones cuyo output se espera > 50 lineas. No delegues si es corto — el overhead del subagente supera el ahorro.

Cuando delegues, especifica que necesitas de vuelta:

```
BIEN: "Corre npm test y reporta: cuantos pasan, cuantos fallan, y los que fallan"
MAL:  "Corre npm test"
```

## 3. Seleccion de modelo para subagentes

Usa el modelo de menor capacidad que pueda completar la tarea:

- haiku: busqueda, lectura/extraccion, tareas mecanicas
- sonnet: implementacion, integracion, logica de negocio
- opus: arquitectura, review, debugging complejo

Criterios completos y reglas de escalacion: .claude/skills/execute/model-selection.md (fuente canonica).
