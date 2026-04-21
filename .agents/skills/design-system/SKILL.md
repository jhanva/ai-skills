---
name: design-system
description: >-
  Disenar un sistema de juego especifico: inventario, dialogo, crafting, movement,
  abilities, etc. Produce spec con data model, formulas, edge cases, y acceptance criteria.
  Mismo rigor que $rpg-design. Usala cuando el usuario quiere disenar un sistema especifico
  del juego (no combate, para eso usar $rpg-design), o cuando dice "design-system",
  "inventario", "dialogo", "crafting", "movement", "abilities", "sistema de X".
---

# Design System

## Uso en Codex

- Esta skill esta pensada para invocacion explicita con `$design-system`.
- Trabaja con lecturas puntuales: `rg -n` para buscar, `rg --files` o `find` para listar, y `sed -n` para leer solo el fragmento necesario.
- Si falta contexto menor, asume una convencion razonable y dejala explicita; pregunta solo cuando el scope o las dependencias cambien el sistema.
- Delega solo si el usuario pidio paralelismo o delegacion.

Disenar un sistema de juego con profundidad completa: scope, mecanicas core, data model, formulas, edge cases, tuning knobs, y acceptance criteria. Output: `design/gdd/{system}.md`.

## FASE 1: Leer contexto

Leer `design/gdd/game-concept.md` (si existe) para extraer pillars, genero, y donde esta este sistema en la priorizacion MVP/NICE/FUTURE. Si no existe, preguntar genero.

Identificar sistema del argumento del usuario. Si ambiguo, pedir descripcion en 2-3 frases.

## FASE 2: Definir scope

Forzar decision explicita:

- **SI (in scope)**: mecanicas que se implementan en este diseno
- **NO (out of scope)**: mecanicas excluidas explicitamente para evitar scope creep
- **Dependencies**: sistemas que este requiere para funcionar (si no existe, declarar "stub" o "mock")

Proponer scope basado en genero y MVP del game-concept.

## FASE 3: Mecanicas core

### Estados
Si el sistema es stateful, definir estados posibles (enum) con transiciones y triggers.

### Player verbs
Que puede HACER el jugador: tabla `verbo → input → efecto → restricciones`.

## FASE 4: Data model

Definir estructura de datos con pseudocodigo o JSON schema. Incluir: entities (clases/resources con propiedades), API publica (funciones principales con tipos de retorno), y persistence (serialize/deserialize si el sistema necesita guardarse).

## FASE 5: Formulas (si aplica)

Si el sistema tiene calculos, definir formulas con tabla de escenarios de validacion. Verificar que los numeros se sienten justos en los extremos.

## FASE 6: Edge cases

Listar EXPLICITAMENTE todos los casos borde y como se manejan. Tabla: `caso → comportamiento esperado`.

Forzar completitud: si quedan casos sin definir, preguntar al usuario.

## FASE 7: Tuning knobs

Valores ajustables sin cambiar codigo. Tabla: `parametro → valor inicial → rango valido → impacto`.

Estos valores deben estar en archivos de datos (JSON, Godot Resource), NO hardcodeados.

## FASE 8: Acceptance criteria

Checks MEDIBLES para saber que el sistema funciona. 5-10 criterios verificables ejecutando el juego, con valores concretos esperados.

Incluir tests recomendados: unitarios para logica, integracion para workflows, serializacion para persistence.

## FASE 9: Escribir spec

Escribir `design/gdd/{system}.md`. Leer `references/output-template.md` para estructura, anti-patrones, y siguientes pasos.
