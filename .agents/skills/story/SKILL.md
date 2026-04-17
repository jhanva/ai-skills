---
name: story
description: >-
  Detallar una user story de juego desde una seccion del GDD. Extrae requerimientos, define
  scope explicito (que SI, que NO), lista archivos a crear/modificar, genera acceptance
  criteria medibles, estima size (S/M/L), identifica dependencies. Output:
  production/stories/{system}-{feature}.md listo para /plan.
---


# Story Detailing

## Uso en Codex

- Esta skill esta pensada para invocacion explicita con `$story`.
- Cuando aqui se indique buscar patrones, usa `rg -n`; para listar archivos, usa `rg --files` o `find`; para leer fragmentos concretos, usa `sed -n`.
- Cuando aqui se hable de subagentes, usa los agentes integrados de Codex o los definidos en `.codex/agents/`, y solo delega si el usuario lo pidio explicitamente.
- Las referencias a `Read/Write/Edit/Grep/Glob/Bash` se traducen segun `AGENTS.md` del repo.

Agent que convierte secciones del GDD en user stories ejecutables con scope claro,
acceptance criteria medibles, y estimacion realista. Para desarrollo de juegos 2D
pixel art en Godot 4 (GDScript/C#).

## Objetivo

Transformar diseño (GDD) en trabajo implementable con:
- Requerimientos concretos extraidos del GDD
- Scope explicito (inclusiones y exclusiones)
- Archivos a crear/modificar (tabla detallada)
- Acceptance criteria medibles
- Estimacion S/M/L
- Dependencies identificadas

## Entrada

```
/story <seccion-del-gdd>
/story combat/damage-formula
/story inventory/equip
/story ui/health-bar
/story enemy-ai/patrol
```

Formato: `{system}/{feature}`

## FASE 1: Leer seccion del GDD

### 1.1 Localizar GDD

Buscar `design/gdd/{system}.md` o `design/gdd/{system}/{feature}.md`:

```
Ejemplo para /story combat/damage-formula:
- Buscar design/gdd/combat.md
- Si existe, leer seccion "## Damage Formula"
- Si no, buscar design/gdd/combat/damage-formula.md
```

Si no existe:
- Error: "GDD no encontrado para {system}. Usa `/brainstorm {system}` para crear el GDD primero."

### 1.2 Extraer contenido de la seccion

Leer la seccion completa. Buscar:
- Formulas o reglas de juego
- Comportamientos esperados
- Valores o constantes
- Interacciones con otros sistemas
- Referencias a assets (sprites, sounds, animations)

Ejemplo de contenido:
```markdown
## Damage Formula

Damage = ATK * (1 - DEF/100) * CritMultiplier

- ATK: stat del atacante
- DEF: stat del defensor (max 75%, min 0%)
- CritMultiplier: 1.5 si critical hit (5% chance), 1.0 si no
- Damage minimo: 1 (siempre hace al menos 1 de daño)

Visual feedback:
- Damage number aparece sobre el objetivo
- Color rojo para damage normal, amarillo para crit
- Shake del sprite del objetivo
```

## FASE 2: Extraer requerimientos

### 2.1 Convertir diseño en lista de requerimientos

Por cada elemento del diseño, crear un requerimiento concreto:

| # | Requerimiento | Fuente (seccion del GDD) |
|---|---------------|--------------------------|
| 1 | Calcular damage usando formula ATK * (1 - DEF/100) * CritMultiplier | Damage Formula |
| 2 | DEF capped entre 0% y 75% | Damage Formula |
| 3 | Critical hit tiene 5% de chance | Damage Formula |
| 4 | Critical hit multiplica damage por 1.5 | Damage Formula |
| 5 | Damage minimo es 1 | Damage Formula |
| 6 | Mostrar damage number sobre objetivo | Visual feedback |
| 7 | Color amarillo para crit, rojo para normal | Visual feedback |
| 8 | Shake sprite del objetivo al recibir damage | Visual feedback |

### 2.2 Validar completitud

Checklist:
- [ ] Todos los elementos del GDD tienen al menos 1 requerimiento
- [ ] Cada requerimiento es verificable (tiene output observable)
- [ ] No hay ambiguedad ("calculo correcto" → especificar formula)

## FASE 3: Definir scope

### 3.1 Que SI incluye (In Scope)

Lista explicita de lo que DEBE implementarse en esta story:

```markdown
## In Scope

- Calculo de damage con formula completa
- Critical hit chance y multiplier
- Damage capping (min 1, DEF max 75%)
- Damage number visual (TextLabel sobre objetivo)
- Color coding (rojo/amarillo)
- Sprite shake animation
```

### 3.2 Que NO incluye (Out of Scope)

Lista explicita de lo que NO se implementa (aunque este relacionado):

```markdown
## Out of Scope

- Elemental damage types (fire, ice, etc.)
- Status effects (poison, stun)
- Equipment that modifies ATK/DEF (inventory integration)
- Damage over time
- Area of effect damage
- Sound effects (audio no implementado aun)
```

### 3.3 Reglas para scope

**In Scope:** Todo lo mencionado explicitamente en la seccion del GDD

**Out of Scope:** 
- Features de otras secciones del GDD
- Features que dependen de sistemas no implementados
- Nice-to-have que no estan en el GDD
- Optimizaciones prematuras

Si el usuario quiere incluir algo de Out of Scope:
- Advertir que expande la story
- Sugerir crear story separada
- Re-estimar si se incluye

## FASE 4: Listar archivos a crear/modificar

### 4.1 Analizar estructura del proyecto

Buscar archivos existentes relacionados:

```
Grep: "class.*Combat|func.*damage" (buscar codigo existente)
Glob: src/**/{combat,battle,damage}*.gd
```

### 4.2 Tabla de archivos

Formato:

| Action | File | Purpose | Type |
|--------|------|---------|------|
| CREATE | src/combat/damage_calculator.gd | Calculo de damage con formula | Script |
| MODIFY | src/entities/stats.gd | Agregar ATK, DEF stats | Script |
| CREATE | src/ui/damage_number.tscn | Scene del damage number visual | Scene |
| CREATE | src/ui/damage_number.gd | Script del damage number | Script |
| MODIFY | src/entities/character.gd | Llamar damage_calculator al recibir hit | Script |
| CREATE | assets/animations/hit_shake.tres | Animation para sprite shake | Resource |

Actions: CREATE, MODIFY, DELETE (rare)
Types: Script, Scene, Resource, Asset, Config

### 4.3 Validar project structure

Si detectas que los archivos rompen convenciones de Godot:
- Warning: "src/combat/ no existe. Estructura recomendada: src/systems/combat/"
- Sugerir estructura

Estructura recomendada:
```
src/
  systems/         (game systems: combat, inventory, etc.)
  entities/        (player, enemies, items)
  ui/              (HUD, menus, damage numbers)
  utils/           (helpers, extensions)
assets/
  sprites/
  animations/
  data/
scenes/
  levels/
  ui/
```

## FASE 5: Definir acceptance criteria

### 5.1 Formato de tabla

| # | Criteria | How to verify |
|---|----------|---------------|
| 1 | Player attack reduces enemy HP by calculated damage | Run combat scene, attack enemy, check HP value |
| 2 | DEF reduces damage (50 DEF → 50% reduction) | Set enemy DEF=50, ATK=100, verify damage=50 |
| 3 | DEF capped at 75% reduction | Set enemy DEF=200, verify damage > 0 |
| 4 | Critical hits occur ~5% of time | Attack 100 times, count crits, verify ~5 |
| 5 | Critical hits deal 1.5x damage | Trigger crit, compare damage to non-crit |
| 6 | Minimum damage is 1 | Set ATK=1, enemy DEF=100, verify damage=1 |
| 7 | Damage number appears above target | Attack enemy, observe yellow/red number |
| 8 | Crit damage shows yellow, normal shows red | Compare color on crit vs normal hit |
| 9 | Target sprite shakes when hit | Attack enemy, observe sprite animation |

### 5.2 Reglas para criteria

**Mandatory:**
- 3-7 criteria por story (no mas, no menos)
- Cada criterio verificable ejecutando el juego
- Valores concretos (HP=50, ~5%, 1.5x, color=yellow)
- Steps de verificacion claros

**Prohibido:**
- Criteria vagos: "funciona bien", "se ve bien", "no crashea"
- Criteria de implementacion: "usa clase DamageCalculator" (eso es HOW, no WHAT)
- Criteria de performance: "calcula en <1ms" (a menos que sea requerimiento del GDD)

### 5.3 Mapear requerimientos a criteria

Cada requerimiento de FASE 2 debe tener al menos 1 criterio:

| Requerimiento | Criteria # | Cubierto? |
|---------------|------------|-----------|
| 1. Formula ATK * (1-DEF/100) | 2 | Si |
| 2. DEF capped 0-75% | 3, 6 | Si |
| 3. Crit 5% chance | 4 | Si |
| 4. Crit 1.5x damage | 5 | Si |
| 5. Min damage 1 | 6 | Si |
| 6. Damage number visual | 7 | Si |
| 7. Color coding | 8 | Si |
| 8. Sprite shake | 9 | Si |

Si requerimiento sin criterio:
- Warning: "Requerimiento {X} no tiene acceptance criteria"
- Generar criterio faltante

## FASE 6: Estimar size

### 6.1 Calcular complejidad

Factores:

| Factor | Weight | Value (esta story) |
|--------|--------|-------------------|
| Archivos a crear | x1 | 4 (damage_calculator, damage_number.gd, damage_number.tscn, hit_shake) |
| Archivos a modificar | x0.5 | 2 (stats.gd, character.gd) |
| Logica compleja | x2 | 1 (formula con caps y crit chance) |
| Assets nuevos | x1.5 | 1 (animation) |
| Dependencies externas | x2 | 0 |

Total: 4 + (2*0.5) + (1*2) + (1*1.5) + 0 = 8.5

### 6.2 Mapear a size

| Score | Size | Tiempo |
|-------|------|--------|
| 0-4   | S    | 1-2h   |
| 5-9   | M    | 3-5h   |
| 10+   | L    | 6-10h  |

Esta story: score 8.5 → **M** (3-5h)

### 6.3 Validar con heuristica

Heuristica rapida (override al score si detectas estos patterns):

**Forzar L si:**
- 6+ archivos nuevos
- Integra 3+ sistemas
- Requiere assets que no existen (sprites, sounds) y no hay asset pipeline
- Toca Godot editor internals (custom nodes, plugins)

**Forzar S si:**
- 1-2 archivos
- Logica trivial (getters/setters, data passing)
- No dependencies
- Copy-paste de pattern existente

Esta story: no triggers de override → confirmar **M**

## FASE 7: Identificar dependencies

### 7.1 Buscar dependencies de codigo

Dependencies son features que DEBEN existir antes de implementar esta story:

```markdown
## Dependencies

| Dependency | Type | Status | Location |
|------------|------|--------|----------|
| Character stats (ATK, DEF) | Data model | REQUIRED | src/entities/stats.gd |
| Hit detection | Game mechanic | REQUIRED | src/combat/hit_detection.gd |
| Scene tree access to target | Engine feature | BUILT-IN | Godot API |
```

Types:
- **Data model:** clases, structs, recursos que esta story necesita leer/escribir
- **Game mechanic:** sistemas que deben funcionar antes (ej: turn system para damage)
- **Asset:** sprites, animations que esta story consume
- **Engine feature:** APIs de Godot (built-in, no es blocker)

Status:
- **REQUIRED:** debe existir o implementarse antes de esta story
- **OPTIONAL:** nice-to-have pero story funciona sin esto
- **BUILT-IN:** parte de Godot, no es blocker

### 7.2 Verificar status de dependencies

Por cada dependency REQUIRED:

```
Grep: "class.*Stats|var.*ATK" en src/
```

Si existe: Status = EXISTS
Si no existe: Status = TODO, advertir al usuario

### 7.3 Sugerir orden de implementacion

Si hay dependencies TODO:

```markdown
## Implementation Order

1. Implementar `stats.gd` con ATK/DEF (story: combat/base-stats)
2. Implementar `hit_detection.gd` (story: combat/hit-detection)
3. LUEGO implementar esta story (combat/damage-formula)
```

## FASE 8: Output del story file

### 8.1 Formato del archivo

Crear `production/stories/{system}-{feature}.md`:

```markdown
# Story: {system}/{feature}

**Size:** {S/M/L} ({tiempo-estimado})
**Status:** TODO
**Priority:** {High/Medium/Low} (basado en MVP del game-concept.md)

## Description

{1-2 parrafos describiendo que implementa esta story}

Ejemplo:
"Implementa el calculo de damage para combate usando la formula ATK * (1 - DEF/100)
con critical hits al 5% que multiplican damage por 1.5. Incluye visual feedback:
damage numbers que aparecen sobre el objetivo con color coding (amarillo=crit,
rojo=normal) y shake animation del sprite."

## Requirements

| # | Requerimiento | Fuente |
|---|---------------|--------|
| 1 | ... | ... |

## Scope

### In Scope
- Item 1
- Item 2

### Out of Scope
- Item 1
- Item 2

## Files to Create/Modify

| Action | File | Purpose | Type |
|--------|------|---------|------|
| CREATE | src/... | ... | Script |

## Acceptance Criteria

| # | Criteria | How to verify |
|---|----------|---------------|
| 1 | ... | ... |

## Dependencies

| Dependency | Type | Status | Location |
|------------|------|--------|----------|
| ... | ... | ... | ... |

## Implementation Notes

{Notas tecnicas, warnings, edge cases}

Ejemplo:
- DEF debe clampearse ANTES de aplicar la formula
- Random.randf() para crit chance (seeded RNG si hay replay system)
- Damage number debe usar z-index alto para aparecer sobre otros sprites

## Estimate Breakdown

| Factor | Value | Weight | Score |
|--------|-------|--------|-------|
| Archivos nuevos | 4 | x1 | 4 |
| Archivos modificados | 2 | x0.5 | 1 |
| Logica compleja | 1 | x2 | 2 |
| Assets nuevos | 1 | x1.5 | 1.5 |
| Total | | | 8.5 |

**Size:** M (5-9 score)
**Tiempo estimado:** 3-5h
```

### 8.2 Validar output

Checklist antes de escribir archivo:
- [ ] Description clara (1-2 parrafos)
- [ ] Requirements mapeados del GDD
- [ ] Scope explicito (In/Out)
- [ ] Archivos listados con purpose
- [ ] Acceptance criteria (3-7 items) con valores concretos
- [ ] Dependencies identificadas y verificadas
- [ ] Estimacion justificada con breakdown

## FASE 9: Transicion al usuario

Mensaje final:

```
Story creada: {system}/{feature}
Size: {S/M/L} ({tiempo})
Acceptance criteria: {count}

{si hay dependencies TODO:}
⚠️  Dependencies requeridas:
- {dependency-1} (TODO)
- {dependency-2} (TODO)

Implementa dependencies primero, o usa `/story {dependency}` para crearlas.

Proximo paso:
- `/plan` para convertir esta story en tareas de implementacion
- `/execute` para implementar (usa `/tdd` internamente)

Archivo generado: production/stories/{system}-{feature}.md
```

## Edge cases

### Seccion del GDD vacia o muy vaga
Si la seccion del GDD es < 5 lineas o no tiene detalles:
- Error: "Seccion {system}/{feature} muy vaga. Usa `/brainstorm {system}` para expandir el GDD primero."

### Story demasiado grande (score > 15)
Warning: "Esta story es muy grande (score {X}). Dividir en sub-stories?"
Sugerir division:
```
Original: combat/full-battle-system (L, score 18)
Dividir en:
- combat/damage-formula (M)
- combat/turn-order (M)
- combat/victory-conditions (S)
```

### Dependencies circulares
Si story A necesita B y B necesita A:
- Error: "Dependencia circular: {A} ↔ {B}"
- Sugerir refactor: extraer dependency comun C que ambos usan

### Sin archivos en proyecto
Si Glob no encuentra archivos de Godot:
- Warning: "No se encontro estructura de proyecto Godot. Es proyecto nuevo?"
- Sugerir estructura basica

## Output esperado

Archivo markdown estructurado de 80-150 lineas con:
- Description, requirements, scope, files, acceptance criteria, dependencies, estimacion

Tiempo de ejecucion: 1-2 min
