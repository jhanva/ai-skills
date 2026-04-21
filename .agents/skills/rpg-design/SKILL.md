---
name: rpg-design
description: Diseña sistemas RPG como stats, combate, turnos, status effects, balance e inventario. Úsala cuando el usuario pida explícitamente diseñar una mecánica RPG. No la uses para cambios de implementación menores sin trabajo de diseño.
---

# RPG Design — Diseno de sistemas RPG

## Uso en Codex

- Esta skill esta pensada para invocacion explicita con `$rpg-design`.
- Trabaja con lecturas puntuales: `rg -n` para buscar, `rg --files` o `find` para listar, y `sed -n` para leer solo el fragmento necesario.
- Si falta contexto menor, usa defaults razonables y declaralos; pregunta solo por decisiones que cambian el sistema o el scope.
- Delega solo si el usuario pidio paralelismo o delegacion.

## Objetivo

Disenar sistemas RPG con formulas auditables, tradeoffs claros y knobs de balance que luego puedan validarse con `$balance-check`.

## Carga just-in-time

- Lee `references/combat-and-progression.md` cuando definas stats, formulas de dano, progression, XP o economia.
- Lee `references/turns-effects-ai.md` cuando definas turnos, comandos, status effects o AI enemiga.

## FASE 1: Definir el sistema

Aclara primero que parte estas disenando:

- stats y atributos
- combate
- progresion
- inventario
- status effects
- AI enemiga
- economia

Luego fuerza un scope explicito:

- `MVP`
- `NICE`
- `FUTURE`

Regla: el MVP debe quedarse en 3-4 mecanicas maximo por sistema.

## FASE 2: Disenar la matematica base

Define:

- stats primarios
- stats derivados
- caps
- scaling por nivel
- formulas principales

Si el sistema toca dano, heal, XP o gold, carga `references/combat-and-progression.md`.

## FASE 3: Disenar comportamiento tactico

Define:

- modelo de turnos
- action types
- status effects
- reglas de stacking
- AI enemiga
- reglas anti-frustracion

Para esto, lee `references/turns-effects-ai.md`.

## FASE 4: Validacion

Antes de cerrar, verifica:

- que cada stat afecte mas de una mecanica o tenga una justificacion fuerte
- que el dano no escale mas rapido que la supervivencia
- que el sustain no haga trivial el combate
- que el sistema tenga knobs claros para balance

## FASE 5: Spec de salida

La spec final debe incluir:

1. scope `MVP/NICE/FUTURE`
2. stats y caps
3. formulas con pseudocodigo
4. modelo de turnos o resolucion
5. status effects y stacking
6. AI enemiga y reglas anti-frustracion
7. progression y economia
8. formato de datos para enemigos, skills e items

Transicion: recomendar `$balance-check` para validar numeros o `$plan` para implementar.

## Entrada esperada

Toma del prompt del usuario cualquier ruta, modo o contexto adicional que acompane a la invocacion de la skill.
