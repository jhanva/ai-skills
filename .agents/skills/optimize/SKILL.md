---
name: optimize
description: "Referencia para reducir costo y contexto en Codex: filtrado de output, delegacion prudente, seleccion de modelo."
---

# Optimize — Eficiencia de tokens

## Uso en Codex

- `AGENTS.md` cubre lecturas puntuales, inspecciones paralelas cuando aplican, filtrado de output ruidoso y verificacion fresca.
- `$optimize` conserva lo que sigue siendo especifico de esta skill: umbral de delegacion y seleccion de modelo para subagentes.
- Invoca `$optimize` para revisar costo, contexto o seleccion de modelos.

## 1. Filtrar output de comandos

Filtra con pipes antes de que entre al contexto:

```bash
npm test 2>&1 | grep -A 5 -E '(FAIL|ERROR|error:)' | head -100
npm run build 2>&1 | grep -i -E '(error|failed)' | head -50
```

## 2. Delegar a subagentes (con umbral)

Delega operaciones cuyo output se espera > 50 lineas. No delegues si es corto — el overhead del subagente supera el ahorro.

En Codex, prefiere:
- `explorer` para exploracion read-only
- `worker` o `task_implementer` para ejecucion acotada
- `reviewer` para evaluaciones de calidad
- `security_auditor` para auditorias de seguridad read-only

Cuando delegues, especifica que necesitas de vuelta:

```
BIEN: "Corre npm test y reporta: cuantos pasan, cuantos fallan, y los que fallan"
MAL:  "Corre npm test"
```

## 3. Seleccion de modelo para subagentes

Usa el modelo de menor capacidad que pueda completar la tarea:

| Tier | Usar para |
|---|---|
| Ligero | Buscar archivos, extraer info, tareas mecanicas |
| Medio | Implementar, integrar, logica de negocio |
| Pesado | Arquitectura, review, debugging complejo |

Los model IDs concretos se configuran en `.codex/config.toml`.
