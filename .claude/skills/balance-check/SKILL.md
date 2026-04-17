---
name: balance-check
description: >
  Validar balance de sistemas de juego: generar tabla de escenarios, validar
  ratios (damage-to-HP, gold-to-item, XP-to-level), identificar outliers y
  breakpoints. Recomienda ajustes con valores concretos. Output en conversacion.
when_to_use: >
  Despues de definir formulas de combate/economia/progresion, o cuando el usuario
  dice "balance", "los numeros no cuadran", "damage feels off", "balance-check",
  "validar formulas", "testear escenarios".
argument-hint: "[sistema o aspecto a balancear]"
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash(python3 *)
agent: game-designer
---

# Balance Check — Validacion de balance de juego

## Objetivo

Validar matematicamente que los sistemas de juego (combate, economia, progresion)
estan balanceados. Generar tabla de escenarios, identificar outliers y breakpoints,
recomendar ajustes. El output es un reporte en la conversacion (NO archivo).

---

## FASE 1: Identificar sistema a balancear

Extraer del argumento (`$ARGUMENTS`) que sistema revisar.

Si vago o vacio, buscar GDDs existentes:

```bash
find design/gdd/ -name "*.md" -type f
```

Presentar opciones:

```
## Sistemas disponibles para balance check

Encontre estos sistemas disenados:

a) Combate (design/gdd/combat.md o rpg-design output)
b) Economia (design/gdd/economy.md)
c) Progresion (design/gdd/progression.md)
d) [Otro sistema encontrado]
e) Custom (especifica sistema y archivo)

¿Cual sistema balancear?
```

---

## FASE 2: Leer GDDs relevantes

Leer archivos de diseno para extraer:

- Formulas (damage, XP, gold, etc.)
- Stats base y scaling
- Valores de items/enemigos/levels
- Constraints declarados (ej: "un item tier-apropiado cuesta ~5 battles")

Si NO hay formulas definidas, reportar error:

```
ERROR: No encontre formulas en [archivo].

Balance check requiere formulas matematicas para validar.

Sugerencia:
1. Usa `/rpg-design` para disenar combate con formulas
2. Usa `/design-system` para disenar economia con formulas
3. Luego corre `/balance-check` de nuevo
```

---

## FASE 3: Generar tabla de escenarios

Crear matriz de escenarios cross-level y cross-enemy.

Ejemplo (combate):

```
## Escenarios de combate

Formula extraida:
  damage = ATK * skill_mult - DEF * 0.5
  variance = damage * random(0.9, 1.1)
  final = max(1, floor(variance))

Stats scaling:
  Player HP(lv)  = 100 + 15 * (lv - 1)
  Player ATK(lv) = 12  + 3  * (lv - 1)
  Enemy HP(lv)   = 80  + 12 * (lv - 1)
  Enemy ATK(lv)  = 10  + 2.5 * (lv - 1)

Generar escenarios: player lv1, 10, 25, 50 × enemy lv1, 10, 25, 50
```

Ejecutar calculo con script Python (inline):

```python
# Script de balance check
import math

def player_stats(lv):
    return {
        'hp': 100 + 15 * (lv - 1),
        'atk': 12 + 3 * (lv - 1),
        'def': 8 + 2 * (lv - 1)
    }

def enemy_stats(lv):
    return {
        'hp': 80 + 12 * (lv - 1),
        'atk': 10 + 2.5 * (lv - 1),
        'def': 6 + 1.5 * (lv - 1)
    }

def damage(atk, defense, mult=1.0):
    raw = atk * mult - defense * 0.5
    return max(1, math.floor(raw * 1.0))  # sin variance para simplificar

def hits_to_kill(attacker_atk, target_hp, target_def, mult=1.0):
    dmg = damage(attacker_atk, target_def, mult)
    return math.ceil(target_hp / dmg)

# Matriz de escenarios
player_levels = [1, 10, 25, 50]
enemy_levels = [1, 10, 25, 50]

print("Player lv | Enemy lv | P→E dmg | Hits to kill | E→P dmg | Hits to die | Ratio")
print("----------|----------|---------|--------------|---------|-------------|------")

for plv in player_levels:
    for elv in enemy_levels:
        p = player_stats(plv)
        e = enemy_stats(elv)
        
        p_to_e_dmg = damage(p['atk'], e['def'])
        e_to_p_dmg = damage(e['atk'], p['def'])
        
        hits_to_kill_enemy = hits_to_kill(p['atk'], e['hp'], e['def'])
        hits_to_die = hits_to_kill(e['atk'], p['hp'], p['def'])
        
        ratio = hits_to_die / hits_to_kill_enemy if hits_to_kill_enemy > 0 else 0
        
        print(f"{plv:9} | {elv:8} | {p_to_e_dmg:7} | {hits_to_kill_enemy:12} | {e_to_p_dmg:7} | {hits_to_die:11} | {ratio:.2f}")
```

Ejecutar:

```bash
python3 -c "[script inline arriba]"
```

---

## FASE 4: Validar ratios

Analizar output de la tabla:

### 4.1 Criterios de balance

```
## Criterios de validacion

Combate balanceado:

1. Same level (player lv = enemy lv):
   Ratio hits_to_die / hits_to_kill ≈ 1.5 - 2.0
   → Player puede matar al enemigo en ~5-7 hits
   → Player sobrevive ~8-12 hits (tiene ventaja, no overwhelm)

2. Over-leveled (player lv > enemy lv + 5):
   Ratio > 3.0
   → Player domina, mata en 2-3 hits, enemigo tickle

3. Under-leveled (player lv < enemy lv - 5):
   Ratio < 1.0
   → Peligroso pero posible, requiere skill/items

4. Boss (enemy lv = player lv + 5):
   Ratio ≈ 0.8 - 1.2
   → Boss dificil, equilibrado, requiere estrategia

Economia balanceada:

1. Gold per battle / Item cost ≈ 5-7
   → Jugador compra item tier-apropiado cada 5-7 batallas

2. XP per battle / XP to next level ≈ 10-15
   → Jugador sube de nivel cada 10-15 batallas

3. Heal cost / Damage per battle < 1.0
   → Curarse es viable, no infinite sustain loop
```

### 4.2 Identificar outliers

Buscar en la tabla:

```
OUTLIERS (valores fuera de rango esperado):

- Player lv1 vs Enemy lv50: ratio < 0.1 → one-shot city (esperado)
- Player lv50 vs Enemy lv1: ratio > 10.0 → trivial (esperado)
- Player lv10 vs Enemy lv10: ratio = 0.8 → PROBLEMA
  ↑ Esperado: 1.5-2.0, obtenido: 0.8
  → Player muere antes de matar enemigo (desfavorable)

RECOMENDACION:
  - Incrementar player ATK scaling: 12 + 3.5 * (lv - 1)  [era 3.0]
  - O decrementar enemy HP scaling: 80 + 10 * (lv - 1)  [era 12]
```

### 4.3 Identificar breakpoints

```
BREAKPOINTS (niveles donde el balance cambia drasticamente):

Ejemplo:
- Player lv24 vs Enemy lv25: ratio = 1.4 (ok)
- Player lv25 vs Enemy lv25: ratio = 2.8 (SALTO)
  ↑ Algo cambia en lv25 que duplica la ventaja del player

Posibles causas:
- Stat scaling no-lineal (ej: ATK = base + rate * lv^1.2)
- Equipment tier jump (lv25 unlock "legendary weapon" con +50 ATK)
- Skill unlock (lv25 unlock AoE que cambia el meta)

RECOMENDACION:
  Revisar que causa el salto. Si es intencional (power spike deseado),
  OK. Si no, suavizar la curva.
```

---

## FASE 5: Validar economia (si aplica)

Si el sistema incluye gold/items, validar ratios economicos:

```
## Validacion de economia

Formula extraida:
  gold_per_battle = enemy_lv * 10
  item_cost_tier(tier) = tier * 500
  xp_per_battle = enemy_lv * 20
  xp_to_level(lv) = 100 * lv^1.5

Escenarios:

| Player lv | Enemy lv | Gold/battle | Item tier | Item cost | Battles to buy | XP/battle | XP to next lv | Battles to lv |
|---|---|---|---|---|---|---|---|---|
| 1  | 1  | 10  | 1 | 500  | 50  | 20  | 283   | 14  |
| 10 | 10 | 100 | 2 | 1000 | 10  | 200 | 3162  | 16  |
| 25 | 25 | 250 | 5 | 2500 | 10  | 500 | 12500 | 25  |
| 50 | 50 | 500 | 10| 5000 | 10  | 1000| 35355 | 35  |

ANALISIS:

1. Battles to buy item: ~10-50 rango muy amplio
   - Lv1: 50 battles es EXCESIVO para primer item
   - Lv10+: 10 battles es OK

   RECOMENDACION:
     Ajustar gold_per_battle en early game:
     gold = max(50, enemy_lv * 10)
     → Lv1 enemigo da 50 gold (10 battles para item)

2. Battles to level up: 14-35, crece con nivel (OK, esperado)
   - Grind aumenta en late game (deseado para alargar juego)

3. Item cost vs gold income: ratio estable en lv10+ (OK)
```

---

## FASE 6: Generar recomendaciones

Consolidar hallazgos en recomendaciones accionables:

```
## RECOMENDACIONES DE BALANCE

### CRITICO (rompe el juego)

1. **Player lv10 vs Enemy lv10: ratio 0.8 (esperado 1.5-2.0)**
   - Causa: Enemy ATK scaling demasiado alto
   - Fix: Cambiar enemy ATK de `10 + 2.5 * (lv - 1)` a `10 + 2.0 * (lv - 1)`
   - Impacto: Ratio sube a ~1.6 (balanceado)

2. **Early game gold income muy bajo (50 battles para primer item)**
   - Causa: gold_per_battle linear sin floor
   - Fix: `gold = max(50, enemy_lv * 10)`
   - Impacto: Lv1-5 enemies dan min 50 gold (10 battles para item)

### ALTO (afecta experiencia pero no rompe)

3. **Breakpoint en lv25 (ratio salta de 1.4 a 2.8)**
   - Causa: [investigar: equipment tier? skill unlock?]
   - Fix: Suavizar la curva, o hacer el power spike intencional y comunicarlo
   - Impacto: Progresion mas consistente

### MEDIO (mejora calidad de vida)

4. **XP to level up crece rapido en late game (35 battles en lv50)**
   - Causa: XP curve exponencial
   - Fix: Opcional — reducir exponente de 1.5 a 1.3
   - Impacto: Late game grind menos pesado

### NOTAS

- Todos los ajustes son en `design/gdd/[archivo].md` y data files
- Despues de ajustar, re-correr `/balance-check` para validar
```

---

## FASE 7: Output en conversacion

Presentar reporte completo en la conversacion (NO escribir archivo):

```
====================================
BALANCE CHECK REPORT: [Sistema]
====================================

FORMULAS ANALIZADAS:
[Lista de formulas extraidas]

ESCENARIOS GENERADOS:
[Tabla con resultados numericos]

OUTLIERS DETECTADOS:
[Lista de valores fuera de rango]

BREAKPOINTS DETECTADOS:
[Lista de niveles con cambios drasticos]

RECOMENDACIONES:
[Lista priorizada: CRITICO / ALTO / MEDIO]

====================================
SIGUIENTES PASOS:
1. Ajustar valores en [archivo]
2. Re-correr `/balance-check` para validar fixes
3. Playtest con valores nuevos
====================================
```

---

## FASE 8: Transicion

```
## Balance Check completado

Reporte generado arriba. Revisa las recomendaciones CRITICAS primero.

## Siguientes pasos recomendados

### Opcion A: Ajustar valores
Edita `design/gdd/[archivo].md` con los valores recomendados,
luego re-corre `/balance-check` para validar que los outliers
desaparecieron.

### Opcion B: Playtest
Si los numeros se ven bien en papel, implementar y playtest
para validar que se SIENTEN bien en practica.

### Opcion C: Iterar formulas
Si las recomendaciones no son suficientes, redisenar las formulas
con `/rpg-design` o `/design-system`.

¿Que hacemos ahora?
```

NO ejecutar automaticamente. Esperar decision del usuario.

---

## Anti-patrones

```
ANTI-PATRON: Balancear sin formulas definidas
  → No hay nada que validar, pure guessing
  Solucion: FASE 2 fuerza que existan formulas antes de continuar

ANTI-PATRON: Solo testear escenarios "felices" (same level)
  → No descubrir edge cases (over/under-leveled)
  Solucion: FASE 3 genera matriz completa de niveles

ANTI-PATRON: No documentar breakpoints
  → Power spikes sorprenden al dev 6 meses despues
  Solucion: FASE 4.3 identifica y documenta explicitamente

ANTI-PATRON: Recomendaciones vagas ("ajustar ATK")
  → Dev no sabe cuanto ajustar
  Solucion: FASE 6 da valores concretos y justificacion

ANTI-PATRON: No re-validar despues de ajustar
  → Fix puede introducir nuevos outliers
  Solucion: siempre re-correr balance-check despues de cambios

ANTI-PATRON: Confiar solo en numeros, no playtest
  → Algo puede verse bien en papel pero sentirse mal
  Solucion: balance-check es validacion matematica, playtest es validacion final
```

## Argumento: $ARGUMENTS
