---
name: rpg-design
description: >
  Diseno de sistemas RPG: stats, formulas de dano, sistema de turnos,
  status effects, enemy AI, balance, inventario. Produce spec matematica
  lista para /plan o /tdd.
when_to_use: >
  Cuando el usuario quiere disenar un sistema de combate, stats, balance,
  inventario, o cualquier mecanica de juego RPG. Tambien cuando dice
  "rpg-design", "sistema de combate", "damage formula", "turn system",
  "balance", "enemy AI", "status effects", "inventario".
argument-hint: "[sistema o mecanica a disenar]"
disable-model-invocation: true
allowed-tools:
  - Read
  - Grep
  - Glob
  - Agent
  - WebFetch
  - WebSearch
---

# RPG Design — Diseno de sistemas RPG

## Objetivo

Disenar sistemas de juego RPG con fundamento matematico, formulas validables,
y balance testeable. El output es una spec con pseudocodigo y tablas de datos
lista para `/plan` o `/tdd`.

---

## FASE 1: Definir el sistema

### 1.1 Clasificar que se esta disenando

| Sistema | Preguntas clave |
|---|---|
| Stats/atributos | Cuantos stats base? Derivados? Cap levels? |
| Combate/dano | Turno o real-time? Fisico/magico? Elementos? |
| Progresion | XP curve? Stat growth? Skill trees? |
| Inventario | Slots? Equip effects? Raridad? Stacking? |
| Status effects | Duracion? Stacking? Interacciones? |
| Enemy AI | Patron-based? Weighted random? Context-aware? |
| Economy | Currency types? Inflation curve? Shops? |

### 1.2 Definir scope MVP

Listar las mecanicas MINIMAS para que el sistema funcione:

```
MVP: las mecanicas sin las cuales no hay juego
NICE: mecanicas que agregan profundidad
FUTURE: mecanicas que pueden esperar 3+ sprints
```

Forzar priorizacion — maximo 3-4 mecanicas en MVP.

---

## FASE 2: Stats y atributos

### 2.1 Stats base

Definir el set minimo de stats primarios. Regla: cada stat debe afectar
al menos 2 mecanicas diferentes, sino sobra.

| Stat | Abreviatura | Afecta |
|---|---|---|
| Hit Points | HP | Supervivencia, threshold triggers |
| Attack | ATK | Dano fisico, break potencial |
| Defense | DEF | Reduccion de dano fisico |
| Speed | SPD | Orden de turnos, evasion |
| Magic Attack | MATK | Dano magico (si aplica) |
| Magic Defense | MDEF | Reduccion de dano magico (si aplica) |

### 2.2 Stats derivados

Stats calculados a partir de los base + equipo + buffs:

```
effective_stat = base_stat + equipment_bonus + buff_bonus
                 (capped at MAX_STAT)

Ejemplos:
  effective_ATK = base_ATK + weapon.ATK + buff_ATK
  crit_rate = base_crit + (SPD * 0.1)  // capped at 50%
  evasion = SPD * 0.15                 // capped at 30%
```

### 2.3 Scaling por nivel

Definir curva de crecimiento por stat y clase/archetype:

```
stat_at_level(lv) = base + growth_rate * (lv - 1)

Ejemplo (warrior):
  HP(lv)  = 100 + 15 * (lv - 1)   // HP 100 → 835 at lv50
  ATK(lv) = 12  + 3  * (lv - 1)   // ATK 12 → 159 at lv50
  SPD(lv) = 8   + 1  * (lv - 1)   // SPD 8 → 57 at lv50
```

Validar: generar tabla lv1, lv10, lv25, lv50 y verificar que los numeros
se sienten razonables. Un personaje lv50 no debe one-shot a un lv49.

---

## FASE 3: Formulas de combate

### 3.1 Formula de dano

Disenar con estos criterios:
- **Determinista en base** — el jugador debe poder predecir el rango de dano
- **Varianza controlada** — random solo para spice, no para frustrar
- **DEF debe importar** — nunca ignorar defensa completamente
- **Escalamiento no-lineal** — dano no debe crecer mas rapido que HP

Formula hibrida recomendada:

```
raw_damage = ATK * skill_multiplier - DEF * 0.5
variance = raw_damage * random(0.9, 1.1)  // +/-10%
final_damage = max(1, floor(variance))     // minimo 1
```

### 3.2 Multiplicadores

| Factor | Rango tipico | Notas |
|---|---|---|
| Skill multiplier | 0.5 - 3.0 | Ataque basico = 1.0 |
| Elemental weakness | 1.5 - 2.0 | Simplicidad: usar 1.5x |
| Elemental resist | 0.25 - 0.5 | Nunca 0 (inmunidad frustra) |
| Critical hit | 1.5 - 2.0 | Multiplicar sobre final_damage |
| Buff/debuff | 0.5 - 1.5 | Sobre el stat, no sobre el dano |

### 3.3 Validacion de balance

Generar estos escenarios y verificar que los numeros funcionan:

```
1. Lv10 warrior vs lv10 slime       → 3-4 hits para matar
2. Lv10 warrior vs lv10 warrior     → 5-7 hits (PvP equilibrado)
3. Lv10 warrior vs lv15 boss        → 8-12 hits (desafiante pero posible)
4. Lv10 warrior vs lv10 slime x5    → grupo peligroso sin AoE
5. Heal amount vs damage per turn   → heal < 50% del dano promedio (no infinite sustain)
```

---

## FASE 4: Sistema de turnos

### 4.1 Elegir modelo

| Modelo | Mecanica | Ventaja | Complejidad |
|---|---|---|---|
| Round-robin | Cada uno actua 1 vez por ronda | Simple, predecible | Baja |
| Speed-based (CTB) | SPD determina frecuencia | Tactico, SPD importa | Media |
| ATB (barra) | Barra se llena en tiempo real | Tension, dinamico | Alta |
| Timeline visible | Turnos futuros visibles | Muy tactico | Alta |

### 4.2 CTB (recomendado para pixel RPG)

```
turn_order = priority queue sorted by tick_counter

Inicio de batalla:
  for each combatant:
    tick_counter = 1000 / SPD  // mas rapido = menor counter

Cada turno:
  1. Tomar combatant con menor tick_counter
  2. Restar su tick_counter a TODOS
  3. Combatant actua (player elige accion / AI decide)
  4. Recalcular tick_counter del que actuo:
     tick_counter = 1000 / effective_SPD
  5. Insertar de vuelta en la cola
```

### 4.3 Action types

```
enum ActionType {
    ATTACK,      // dano single target
    SKILL,       // dano/heal/buff con costo (MP, cooldown)
    ITEM,        // usar item del inventario
    DEFEND,      // reducir dano 50% + bonus al siguiente turno
    FLEE         // intentar escapar (SPD check)
}
```

### 4.4 Command Queue pattern

Cada accion es un Command serializable:

```
interface BattleCommand {
    val actor: CombatantId
    val targets: List<CombatantId>
    fun execute(state: BattleState): BattleResult
    fun animate(): AnimationSequence
}

// Resolucion:
1. Player selecciona accion → crea Command
2. Command se encola
3. Execute: aplica cambios al BattleState
4. Animate: reproduce animacion (independiente de logica)
5. Check: victoria? derrota? status effects tick?
```

---

## FASE 5: Status effects

### 5.1 Modelo de hooks

Cada status effect es un objeto con hooks de lifecycle:

```
interface StatusEffect {
    val id: String
    val duration: Int           // turnos restantes (-1 = permanente)
    val stackable: Boolean      // se acumula o refresca?

    fun onApply(target: Combatant)       // al aplicar
    fun onTurnStart(target: Combatant)   // inicio del turno del afectado
    fun onTurnEnd(target: Combatant)     // fin del turno del afectado
    fun onDamageReceived(damage: Int): Int // modificar dano recibido
    fun onDamageDealt(damage: Int): Int   // modificar dano infligido
    fun onRemove(target: Combatant)      // al expirar o curar
}
```

### 5.2 Efectos comunes

| Efecto | Hook | Comportamiento |
|---|---|---|
| Poison | onTurnEnd | dano = maxHP * 0.05 por turno |
| Burn | onTurnEnd | dano = maxHP * 0.08 por turno |
| Stun | onTurnStart | pierde turno, duration -= 1 |
| ATK Up | onDamageDealt | damage * 1.3 |
| DEF Down | onDamageReceived | damage * 1.3 |
| Regen | onTurnEnd | heal = maxHP * 0.05 por turno |
| Shield | onDamageReceived | absorbe X dano, luego se rompe |

### 5.3 Reglas de stacking

```
Mismo efecto aplicado de nuevo:
  - Si stackable: agregar instancia (max 3 stacks)
  - Si no stackable: refrescar duracion (no acumular potencia)

Efectos opuestos:
  - ATK Up + ATK Down = se cancelan mutuamente
  - Definir tabla de conflictos explicitamente
```

---

## FASE 6: Enemy AI

### 6.1 Weighted random con contexto

```
fun decideAction(self: Combatant, battle: BattleState): BattleCommand {
    val options = buildActionWeights(self, battle)
    return weightedRandom(options)
}

fun buildActionWeights(self: Combatant, battle: BattleState): Map<Action, Int> {
    val weights = mutableMapOf<Action, Int>()

    // Base: ataque siempre es opcion
    weights[Attack] = 50

    // Contexto: HP bajo → heal/defend
    if (self.hpPercent < 0.3 && self.canHeal) {
        weights[Heal] = 80
        weights[Defend] = 30
    }

    // Contexto: player debuffed → explotar
    if (battle.player.hasDebuff("DEF_DOWN")) {
        weights[PowerAttack] = 70
    }

    // Contexto: boss phase (HP < 50%) → patron especial
    if (self.isBoss && self.hpPercent < 0.5) {
        weights[UltimateSkill] = 60
    }

    return weights
}
```

### 6.2 Patron por tipo de enemigo

| Tipo | Comportamiento |
|---|---|
| Minion | 80% attack, 20% random skill |
| Healer | Heal allies < 50% HP, else attack weakest |
| Tank | Defend/taunt when allies low, else attack |
| Boss | Fase 1 (>50% HP): patron normal. Fase 2 (<50%): skills fuertes, mas agresivo |

### 6.3 Regla anti-frustration

```
- Nunca usar el mismo skill 3 veces consecutivas
- Nunca enfocar al mismo player 3 turnos seguidos (si hay party)
- Stun no debe re-aplicarse inmediatamente al expirar
- Boss hint: indicar visualmente cuando prepara ataque fuerte
```

---

## FASE 7: Balance y economia

### 7.1 XP y curva de nivel

Formula cuadratica (crece mas lento en niveles altos):

```
xp_for_level(lv) = base_xp * lv^exponent

Ejemplo:
  xp_for_level(lv) = 100 * lv^1.5
  Lv2:  283 XP
  Lv10: 3,162 XP
  Lv25: 12,500 XP
  Lv50: 35,355 XP
```

### 7.2 Encounter scaling

```
xp_reward = base_xp_enemy * level_modifier

level_modifier:
  enemy_level > player_level + 5: 1.5x (incentivo a desafio)
  enemy_level = player_level:     1.0x
  enemy_level < player_level - 5: 0.25x (anti-grinding)
```

### 7.3 Gold economy

```
Regla: un item tier-apropiado cuesta ~5 battles de gold
  gold_per_battle = item_cost / 5

Ejemplo lv10:
  sword_lv10 = 500 gold
  gold_per_battle_lv10 = 100 gold
  → jugador puede comprar sword despues de ~5 peleas
```

---

## FASE 8: Spec de salida

Producir documento con:

1. **Scope:** MVP vs NICE vs FUTURE con mecanicas asignadas
2. **Stats:** tabla de stats base + derivados + scaling curves
3. **Formulas:** dano, crit, evasion, heal — con pseudocodigo
4. **Turnos:** modelo elegido con algoritmo de orden
5. **Status effects:** tabla de efectos con hooks y stacking
6. **Enemy AI:** tabla de comportamientos por tipo + reglas anti-frustration
7. **Balance:** curvas de XP, gold economy, escenarios de validacion
8. **Data format:** estructura de datos para enemigos, skills, items (data-driven)

Transicion: "Usa `/plan` para convertir estos sistemas en tareas de implementacion."

## Argumento: $ARGUMENTS
