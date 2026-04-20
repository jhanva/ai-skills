---
name: story
description: >-
  Detallar una user story de juego desde una seccion del GDD. Extrae requerimientos, define
  scope explicito (que SI, que NO), lista archivos a crear/modificar, genera acceptance
  criteria medibles, estima size (S/M/L), identifica dependencies. Output:
  production/stories/{system}-{feature}.md listo para $plan.
---

# Story Detailing

Convertir secciones del GDD en user stories ejecutables. Output: `production/stories/{system}-{feature}.md`.

Entrada: `$story {system}/{feature}` (ej: combat/damage-formula, inventory/equip).

## FASE 1: Leer seccion del GDD

Buscar `design/gdd/{system}.md` seccion `## {Feature}`. Si no existe: error, usar `$brainstorm {system}` primero.

Extraer: formulas/reglas, comportamientos esperados, valores/constantes, interacciones con otros sistemas, assets referenciados.

## FASE 2: Extraer requerimientos

Tabla: `# → requerimiento → fuente (seccion del GDD)`. Cada requerimiento debe ser verificable (tiene output observable). Sin ambiguedad.

## FASE 3: Definir scope

**In Scope**: lista explicita de lo que se implementa.
**Out of Scope**: lista explicita de lo que NO (features de otras secciones, dependencies no implementadas, nice-to-have, optimizaciones prematuras).

Si el usuario quiere incluir algo de out-of-scope: advertir que expande la story, sugerir story separada.

## FASE 4: Archivos a crear/modificar

Buscar archivos existentes relacionados en el proyecto. Tabla: `action (CREATE/MODIFY) → file → purpose → type (Script/Scene/Resource/Asset)`.

## FASE 5: Acceptance criteria

Tabla: `# → criteria → how to verify`. Reglas:
- 3-7 criteria por story
- Verificable ejecutando el juego
- Valores concretos (HP=50, ~5%, 1.5x, color=yellow)
- NO criteria vagos ("funciona bien", "se ve bien")
- NO criteria de implementacion ("usa clase X") — eso es HOW, no WHAT

Mapear: cada requerimiento de FASE 2 debe tener al menos 1 criterio. Warning si queda requerimiento sin cubrir.

## FASE 6: Estimar size

| Factor | Weight |
|--------|--------|
| Archivos nuevos | x1 |
| Archivos modificados | x0.5 |
| Logica compleja | x2 |
| Assets nuevos | x1.5 |
| Dependencies externas | x2 |

Score 0-4 → S (1-2h), 5-9 → M (3-5h), 10+ → L (6-10h).

Si score > 15: sugerir dividir en sub-stories.

## FASE 7: Dependencies

Tabla: `dependency → type (data model/game mechanic/asset/engine) → status (REQUIRED/OPTIONAL/BUILT-IN) → location`.

Verificar si dependencies REQUIRED existen en el proyecto. Si no: advertir, sugerir orden de implementacion.

## FASE 8: Output

Escribir `production/stories/{system}-{feature}.md` con: size, status TODO, priority, description (1-2 parrafos), requirements, scope (in/out), files, acceptance criteria, dependencies, implementation notes, estimate breakdown.

## Edge cases

- **GDD vago** (<5 lineas): error, expandir con `$brainstorm` primero
- **Story demasiado grande** (score >15): sugerir division con sub-stories concretas
- **Dependencies circulares**: error, sugerir extraer dependency comun
