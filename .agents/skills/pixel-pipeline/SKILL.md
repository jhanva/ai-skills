---
name: pixel-pipeline
description: Diseña pipelines de assets pixel art, sprites, tiles, atlas, paletas y exportación para integración en juegos. Úsala cuando el usuario pida explícitamente ayuda con assets pixel art. No la uses para arte raster general sin foco en pipeline pixel.
---

# Pixel Pipeline — Pipeline de assets pixel art

## Uso en Codex

- Esta skill esta pensada para invocacion explicita con `$pixel-pipeline`.
- Trabaja con lecturas puntuales: `rg -n` para buscar, `rg --files` o `find` para listar, y `sed -n` para leer solo el fragmento necesario.
- Si falta contexto menor, usa defaults conservadores de pixel art y dejalos explicitos; pregunta solo por decisiones que cambian el pipeline.
- Delega solo si el usuario pidio paralelismo o delegacion.

## Objetivo

Disenar el flujo completo desde produccion de assets pixel art hasta integracion en runtime: grid, sprites, tiles, paleta, atlas, UI y export.

## Carga just-in-time

- Lee `references/asset-conventions.md` cuando debas fijar grid, resolucion, naming, animaciones, tilesets o reglas de paleta.
- Lee `references/runtime-integration.md` cuando debas definir atlas, memoria, palette swap, UI o integracion con el engine.
- Lee `references/output-template.md` solo al preparar la spec final y la checklist de validacion.

## FASE 1: Definir convenciones base

Fija primero:

- tamano de tile
- tamano de character
- render resolution base
- regla de integer scaling
- regla de nearest filtering
- camera snap y restricciones pixel-perfect

Si la decision no es obvia, carga `references/asset-conventions.md`.

## FASE 2: Definir assets productivos

Para cada categoria, deja convenciones claras:

- sprites y estados de animacion
- formato data-driven de animaciones
- tilesets y autotile
- collision y layers
- paleta y variantes

Usa `references/asset-conventions.md` para naming, sets minimos y heuristicas.

## FASE 3: Definir integracion en runtime

Especifica:

- atlas por contexto
- budget de VRAM
- strategy de palette swap si aplica
- integracion de UI pixel art
- export/import con herramientas del pipeline

Para esto, carga `references/runtime-integration.md`.

## FASE 4: Validacion

Antes del cierre, valida como minimo:

- consistencia de resolucion y grid
- `Nearest` + integer scaling
- atlas y padding razonables
- ausencia de texturas sueltas en produccion
- ausencia de animaciones hardcodeadas sin data

Usa `references/output-template.md` para la checklist completa.

## FASE 5: Spec de salida

Entrega una spec que cubra:

1. convenciones base
2. sprites y animaciones
3. tilesets y layers
4. paleta y variantes
5. atlas y memoria
6. workflow de export
7. integracion con el engine
8. checklist de validacion

Transicion: recomendar `$plan` para convertir el pipeline en tareas.

## Entrada esperada

Toma del prompt del usuario cualquier ruta, modo o contexto adicional que acompane a la invocacion de la skill.
