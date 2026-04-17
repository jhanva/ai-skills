---
name: design-system
description: >
  Disenar un sistema de juego especifico: inventario, dialogo, crafting,
  movement, abilities, etc. Produce spec con data model, formulas, edge cases,
  y acceptance criteria. Mismo rigor que /rpg-design.
when_to_use: >
  Cuando el usuario quiere disenar un sistema especifico del juego (no combate,
  para eso usar /rpg-design), o cuando dice "design-system", "inventario",
  "dialogo", "crafting", "movement", "abilities", "sistema de X".
argument-hint: "<nombre del sistema>"
disable-model-invocation: true
allowed-tools:
  - Read
  - Grep
  - Glob
  - Write
  - Agent
agent: game-designer
---

# Design System — Disenar sistemas de juego

## Objetivo

Disenar un sistema de juego con profundidad completa: scope, mecanicas core,
data model, formulas (si aplica), edge cases, tuning knobs, y acceptance
criteria. El output es `design/gdd/{system}.md` listo para `/plan` o `/tdd`.

---

## FASE 1: Leer contexto del proyecto

### 1.1 Buscar game-concept.md

Leer `design/gdd/game-concept.md` (si existe) para extraer:

- Pillars (validar que el sistema los cumpla)
- Genero (RPG, platformer, roguelike, etc.)
- Mecanicas MVP/NICE/FUTURE (donde esta este sistema)

Si NO existe, preguntar:

```
No encontre design/gdd/game-concept.md.

¿Este sistema es parte de que tipo de juego?
a) RPG (turn-based)
b) Platformer (2D movement)
c) Roguelike (procedural + permadeath)
d) Otro: [especifica]
```

### 1.2 Identificar sistema

Extraer del argumento (`$ARGUMENTS`) que sistema disenar.

Sistemas comunes:

| Sistema | Ejemplos de juegos | Complejidad |
|---|---|---|
| Inventario | Stardew Valley, Zelda, Pokemon | Media |
| Dialogo | Undertale, Disco Elysium, Visual Novels | Media-Alta |
| Crafting | Minecraft, Terraria, Stardew Valley | Alta |
| Movement | Celeste, Hollow Knight, Meat Boy | Media |
| Abilities/Skills | Hades, Dead Cells, Wizard of Legend | Alta |
| Quest system | Skyrim, Witcher, Dragon Age | Alta |
| Economy/Shops | Any RPG, sim games | Media |
| Save/Load | Todo juego con progresion | Media |
| Stealth | Mark of the Ninja, Gunpoint | Alta |

Si el sistema no esta en la lista, pedir descripcion:

```
Sistema: "[ARGUMENTS]"

¿Que hace este sistema? Describir en 2-3 frases:
[respuesta libre]
```

---

## FASE 2: Definir scope

Forzar decision explicita de que SI y que NO incluir.

```
## Scope del sistema: [NOMBRE]

### SI (incluido en este diseno)

Lista de mecanicas que SI estan en scope:

- [Mecanica 1]
- [Mecanica 2]
- [Mecanica 3]

### NO (excluido explicitamente)

Lista de mecanicas que NO estan en scope (evitar scope creep):

- [Mecanica X]
- [Mecanica Y]
- [Mecanica Z]

### Dependencias

Sistemas que este sistema requiere para funcionar:

- [Sistema A] (ej: inventario depende de item database)
- [Sistema B] (ej: crafting depende de inventario)

Si una dependencia NO existe, declarar "implementar stub" o "asumir mock".
```

Presentar propuesta de scope basada en el genero y MVP del game-concept.md.

Ejemplo (inventario para RPG):

```
## Scope: Inventario

### SI
- Slots de inventario (max 20 items)
- Items consumables (usar desde inventario)
- Items equippables (armas, armadura)
- Stacking (items identicos se apilan)
- Sorting (por tipo, nombre, raridad)

### NO
- Crafting (sistema separado)
- Durabilidad de items (FUTURE)
- Item trading/economy (FUTURE)
- Quest items (sistema de quests separado)

### Dependencias
- Item database (JSON con definiciones de items)
- Equipment system (aplicar stats de items equipados)
```

---

## FASE 3: Mecanicas core

Describir las reglas fundamentales del sistema.

### 3.1 Estados

Si el sistema es stateful, definir estados posibles:

```
## Estados del sistema

enum State {
    [ESTADO_1],  // [descripcion]
    [ESTADO_2],  // [descripcion]
    [ESTADO_3],  // [descripcion]
}

Ejemplo (dialogo):
enum DialogueState {
    IDLE,          // no hay dialogo activo
    DISPLAYING,    // texto apareciendo letra por letra
    WAITING_INPUT, // esperando player presione confirm
    BRANCHING,     // mostrando opciones de respuesta
    ENDED          // dialogo termino, limpiar UI
}
```

### 3.2 Transiciones

Si hay estados, definir como se transiciona entre ellos:

```
## Transiciones de estado

Diagrama de estado (ASCII):

IDLE --[interact with NPC]--> DISPLAYING
DISPLAYING --[text finished]--> WAITING_INPUT
WAITING_INPUT --[player confirm]--> DISPLAYING (next line)
WAITING_INPUT --[last line]--> BRANCHING (if choices exist)
BRANCHING --[player selects choice]--> DISPLAYING (branch)
DISPLAYING --[dialogue ends]--> ENDED
ENDED --[cleanup]--> IDLE

Triggers:
- [evento] → [estado origen] → [estado destino]
```

### 3.3 Player verbs

Que puede HACER el jugador con este sistema:

```
## Player Verbs (acciones disponibles)

| Verbo | Input | Efecto | Restricciones |
|---|---|---|---|
| [Verbo 1] | [tecla/boton] | [que pasa] | [cuando se puede usar] |
| [Verbo 2] | [tecla/boton] | [que pasa] | [cuando se puede usar] |

Ejemplo (inventario):
| Verbo | Input | Efecto | Restricciones |
|---|---|---|---|
| Open inventory | I | Abre UI de inventario | Solo fuera de combate |
| Use item | Click + Enter | Consume item | Solo items consumables |
| Equip item | Click + E | Equipa weapon/armor | Solo items equippables |
| Drop item | Click + D | Remueve item del inventario | Confirmacion requerida |
| Sort inventory | S | Ordena por tipo/raridad | — |
```

---

## FASE 4: Data model

Definir estructura de datos con pseudocodigo o JSON schema.

```
## Data Model

### Entities (objetos del sistema)

```gdscript / JSON schema (segun lenguaje del proyecto)

Ejemplo (inventario):

```gdscript
class_name InventoryItem
extends Resource

@export var id: String              # "potion_health_small"
@export var name: String            # "Small Health Potion"
@export var type: ItemType          # CONSUMABLE, WEAPON, ARMOR
@export var stackable: bool = false
@export var max_stack: int = 99
@export var icon: Texture2D
@export var rarity: Rarity          # COMMON, RARE, EPIC, LEGENDARY
@export var effects: Array[Effect]  # que hace al usarse

class_name Inventory
extends Node

var slots: Array[InventorySlot] = []
var max_slots: int = 20

func add_item(item: InventoryItem, quantity: int = 1) -> bool:
    # Intentar stack si stackable, sino nuevo slot
    # Retornar false si inventario lleno

func remove_item(item_id: String, quantity: int = 1) -> bool:
    # Remover N unidades del item
    # Retornar false si no hay suficiente cantidad

func use_item(slot_index: int) -> void:
    # Aplicar efectos del item
    # Si consumable, decrementar quantity

func equip_item(slot_index: int, equip_slot: EquipSlot) -> void:
    # Mover item del inventario a equipment slot
    # Si ya hay item equipado, swap
```

### Persistence

Si el sistema necesita guardarse:

```gdscript
func serialize() -> Dictionary:
    return {
        "slots": slots.map(func(slot): return slot.serialize()),
        "max_slots": max_slots
    }

func deserialize(data: Dictionary) -> void:
    max_slots = data["max_slots"]
    for slot_data in data["slots"]:
        var slot = InventorySlot.new()
        slot.deserialize(slot_data)
        slots.append(slot)
```

---

## FASE 5: Formulas (si aplica)

Si el sistema tiene calculos, definir formulas con escenarios de validacion.

Ejemplo (crafting):

```
## Formulas

### Crafting Success Rate

Si el sistema tiene chance de fallo:

```
success_rate = base_rate + (player_skill * 0.01) - (recipe_difficulty * 0.05)
success_rate = clamp(success_rate, 0.1, 0.95)  // min 10%, max 95%

roll = random(0.0, 1.0)
if roll <= success_rate:
    craft_success()
else:
    craft_failure()  // consume materiales, no da output
```

### Validacion

Generar tabla de escenarios:

| Skill | Recipe Difficulty | Base Rate | Final Rate | Resultado esperado |
|---|---|---|---|---|
| 0 | 10 | 50% | 0% (→ 10% min) | Muy dificil para principiante |
| 50 | 10 | 50% | 50% | Balanceado |
| 100 | 10 | 50% | 95% (cap) | Maestro casi siempre tiene exito |
| 100 | 100 | 50% | 0% (→ 10% min) | Recipe imposible sin buffs |

¿Los numeros se sienten justos? Ajustar coeficientes si no.
```

---

## FASE 6: Edge cases

Listar EXPLICITAMENTE todos los casos borde y como se manejan.

```
## Edge Cases

| Caso | Comportamiento esperado |
|---|---|
| [Caso 1] | [Como se resuelve] |
| [Caso 2] | [Como se resuelve] |

Ejemplo (inventario):

| Caso | Comportamiento esperado |
|---|---|
| Inventario lleno, intentar agregar item | Mensaje "Inventario lleno", item queda en el suelo |
| Usar item consumable con quantity = 1 | Item se consume, slot queda vacio |
| Equipar arma cuando ya hay una equipada | Swap: arma vieja vuelve a inventario, nueva se equipa |
| Dropear item equipado | Desequipar primero, luego dropear |
| Save/load con inventario modificado | Serializar completo, restaurar al cargar |
| Item stackable con quantity > max_stack | Split en multiples slots |
| Intentar usar item no-consumable | Mensaje "Este item no se puede usar aqui" |
| Inventario vacio, presionar sort | No hacer nada (o mensaje "Inventario vacio") |
```

Forzar completitud: si quedan casos sin definir, preguntar al usuario.

---

## FASE 7: Tuning knobs

Valores ajustables sin cambiar codigo. Declarar explicitamente.

```
## Tuning Knobs (valores configurables)

Estos valores deben estar en archivos de datos (JSON, Godot Resource),
NO hardcodeados en el codigo.

| Parametro | Valor inicial | Rango valido | Impacto |
|---|---|---|---|
| [Parametro 1] | [valor] | [min-max] | [que afecta] |

Ejemplo (inventario):

| Parametro | Valor inicial | Rango valido | Impacto |
|---|---|---|---|
| max_slots | 20 | 10-100 | Capacidad total del inventario |
| max_stack_size | 99 | 1-999 | Cuantos items stackables por slot |
| sort_default | "type" | type/rarity/name | Criterio de sorting por defecto |
| auto_stack | true | bool | Stack automatico al agregar item |

Formato export (Godot Resource):

```gdscript
class_name InventoryConfig
extends Resource

@export var max_slots: int = 20
@export var max_stack_size: int = 99
@export_enum("type", "rarity", "name") var sort_default: String = "type"
@export var auto_stack: bool = true
```

---

## FASE 8: Acceptance criteria

Definir checks MEDIBLES para saber que el sistema funciona.

```
## Acceptance Criteria

Lista de checks que deben pasar antes de considerar el sistema completo:

- [ ] [Criterio 1 — medible y verificable]
- [ ] [Criterio 2 — medible y verificable]
- [ ] [Criterio 3 — medible y verificable]

Ejemplo (inventario):

- [ ] Player puede agregar item al inventario (inventory.add_item() retorna true)
- [ ] Items stackables se apilan automaticamente si hay espacio
- [ ] Inventario lleno rechaza nuevos items (add_item() retorna false)
- [ ] Player puede usar item consumable (quantity decrementa, efecto se aplica)
- [ ] Player puede equipar arma (stats actualizan, arma aparece en equip slot)
- [ ] Inventario persiste entre save/load (items, quantities, orden)
- [ ] UI de inventario muestra items correctamente (icon, nombre, quantity)
- [ ] Sorting funciona (items se reordenan segun criterio elegido)

Tests recomendados:
- Test unitario para inventory.add_item() con inventario lleno
- Test unitario para stacking (agregar item stackable existente)
- Test de integracion para equip/unequip workflow
- Test de serializacion (save → load → verificar state identico)
```

---

## FASE 9: Escribir spec de sistema

Producir `design/gdd/{system}.md`:

```markdown
# System Design — [NOMBRE DEL SISTEMA]

## Contexto

[Referencia al game-concept.md y como este sistema cumple los pillars]

## Scope

### SI (incluido)
- [Mecanica 1]
- [Mecanica 2]

### NO (excluido)
- [Mecanica X]
- [Mecanica Y]

### Dependencias
- [Sistema A]
- [Sistema B]

---

## Mecanicas Core

### Estados

[Enum o lista de estados si aplica]

### Transiciones

[Diagrama ASCII de estados y transiciones]

### Player Verbs

[Tabla de acciones disponibles]

---

## Data Model

[Pseudocodigo o JSON schema de entities]

---

## Formulas

[Formulas con validacion de escenarios, si aplica]

---

## Edge Cases

[Tabla completa de casos borde y soluciones]

---

## Tuning Knobs

[Tabla de parametros configurables]

---

## Acceptance Criteria

[Checklist medible de criterios de completitud]

---

## Implementation Notes

[Notas tecnicas: algoritmos, optimizaciones, integracion con otros sistemas]

---

## Anti-Patrones

[Errores comunes al implementar este sistema y como evitarlos]

---

## Siguientes Pasos

1. `/plan` — Convertir esta spec en tareas de implementacion
2. `/tdd` — Implementar con test-driven development
3. `/verify` — Verificar que todos los acceptance criteria pasan
```

---

## FASE 10: Transicion

```
## Sistema disenado: [NOMBRE]

Archivo creado: design/gdd/{system}.md

Este documento define el sistema completo con scope, mecanicas,
data model, edge cases, y acceptance criteria.

## Siguientes pasos recomendados

### Opcion A: Planificar implementacion
Usa `/plan` para convertir esta spec en tareas de 2-5 minutos.

### Opcion B: Disenar otro sistema
Si hay otros sistemas MVP pendientes, usa `/design-system <nombre>`
para disenarlos antes de implementar.

### Opcion C: Implementar directamente con TDD
Si la spec esta clara, usa `/tdd` para implementar con tests primero.

¿Que hacemos ahora?
```

NO ejecutar automaticamente. Esperar decision del usuario.

---

## Anti-patrones

```
ANTI-PATRON: Scope vago ("inventario con features comunes")
  → No se sabe que implementar ni que excluir
  Solucion: lista explicita de SI/NO en FASE 2

ANTI-PATRON: Edge cases no documentados
  → Bugs descubiertos en produccion, no en diseno
  Solucion: FASE 6 obliga a listar explicitamente

ANTI-PATRON: Valores hardcodeados en codigo
  → Ajustar balance requiere recompilar
  Solucion: tuning knobs en data files (FASE 7)

ANTI-PATRON: Acceptance criteria subjetivos ("debe sentirse bien")
  → No se puede verificar objetivamente
  Solucion: criterios medibles y testables (FASE 8)

ANTI-PATRON: Disenar sin considerar dependencias
  → Sistema no funciona porque falta otro sistema
  Solucion: declarar dependencias en FASE 2, implementar stubs si faltan
```

## Argumento: $ARGUMENTS
