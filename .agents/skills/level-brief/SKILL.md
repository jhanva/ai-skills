---
name: level-brief
description: >-
  Disenar un level brief: proposito del nivel, layout ASCII, encounter table, difficulty
  curve, secrets, tileset requirements. Produce design/levels/{name}.md listo para
  implementacion. Usala cuando el usuario quiere disenar un nivel, zona, o area de juego, o
  cuando dice "level-brief", "disenar nivel", "mapa", "zona", "area", "level design".
---


# Level Brief — Disenar niveles y zonas

## Uso en Codex

- Esta skill esta pensada para invocacion explicita con `$level-brief`.
- Cuando aqui se indique buscar patrones, usa `rg -n`; para listar archivos, usa `rg --files` o `find`; para leer fragmentos concretos, usa `sed -n`.
- Cuando aqui se hable de subagentes, usa los agentes integrados de Codex o los definidos en `.codex/agents/`, y solo delega si el usuario lo pidio explicitamente.
- Las referencias a `Read/Write/Edit/Grep/Glob/Bash` se traducen segun `AGENTS.md` del repo.

## Objetivo

Disenar un nivel completo con proposito claro, layout visual (ASCII map),
encounters, difficulty curve, secrets, y requirements de assets. El output
es `design/levels/{name}.md` listo para implementacion.

---

## FASE 1: Leer contexto del juego

### 1.1 Buscar game-concept.md

Leer `design/gdd/game-concept.md` (si existe) para extraer:

- Genero (RPG, platformer, roguelike, etc.)
- Mecanicas MVP (que mecanicas estan disponibles para usar en el nivel)
- Pillars (el nivel debe cumplirlos)

Si NO existe, inferir del argumento o preguntar:

```
No encontre design/gdd/game-concept.md.

¿Este nivel es para que tipo de juego?
a) RPG (explorar + combate por turnos)
b) Platformer (saltar + esquivar obstaculos)
c) Roguelike (procedural + permadeath)
d) Puzzle-platformer (resolver + movimiento)
e) Otro: [especifica]
```

### 1.2 Identificar nombre del nivel

Extraer del argumento (`lo que el usuario pase al invocar la skill`) el nombre o proposito del nivel.

Si vago, preguntar:

```
Nivel: "[ARGUMENTS]"

¿Que nombre especifico? Ejemplos:
- "forest-1" (primer nivel del bosque)
- "castle-dungeon" (mazmorra del castillo)
- "tutorial" (nivel de tutorial)
- "boss-arena-dragon" (arena de boss)

Nombre: ___
```

---

## FASE 2: Definir proposito del nivel

Todo nivel debe tener un proposito claro en el contexto del juego.

```
## Proposito del nivel

Cada nivel cumple una funcion especifica:

| Tipo | Proposito | Caracteristicas |
|---|---|---|
| Tutorial | Ensenar mecanicas | Bajo riesgo, instrucciones explicitas, progresion lineal |
| Introduce mechanic | Presentar mecanica nueva | Safe space para practicar, ramp up gradual |
| Challenge | Testear mastery de mecanica | Dificil pero justo, requiere dominar lo aprendido |
| Boss | Climax de zona/acto | Arena cerrada, mecanica unica, high stakes |
| Exploration | Recompensar curiosidad | Open-ended, secrets, minimal combat |
| Rest | Descanso entre desafios | Safe zone, save point, shops, dialogo |

¿Cual es el proposito de "[nombre del nivel]"?

Propuesta basada en nombre:
- [Proposito inferido]

¿Correcto? (si/no/ajustar)
```

---

## FASE 3: Layout con ASCII map

Crear mapa visual del nivel usando caracteres ASCII.

### 3.1 Leyenda standard

```
## Leyenda de simbolos

#  = Wall (no walkable)
.  = Floor (walkable)
D  = Door (interactuable)
E  = Enemy spawn
T  = Treasure/Loot
S  = Player spawn (start)
X  = Exit/Goal
L  = Lever/Switch
B  = Boss spawn
~  = Water (walkable, slow)
^  = Spike/Hazard (damage)
P  = Platform (platformer)
J  = Jump pad (platformer)
?  = Secret area entrance
```

Agregar simbolos custom si el nivel los necesita.

### 3.2 Generar layout

Dependiendo del genero, generar template:

**RPG (grid-based, top-down):**

```
Ejemplo: castle-dungeon (20x15 tiles)

####################
#S.................#
#.###.....###......#
#.#E#.....#T#......#
#.###.....###......#
#..................#
#......D...........#
#.......###########
#.......#.........#
#..E....D....E....X
#.......#.........#
#.......###########
#..................#
#........T.........#
####################

Dimensiones: 20 tiles ancho × 15 tiles alto
Tile size: [del art-bible.md, ej: 16x16]
Total area: 320x240 pixels
```

**Platformer (side-view, layered):**

```
Ejemplo: forest-1 (platformer, 40x20 tiles)

S = player spawn, P = platform, E = enemy, X = exit

########################################
#                                      #
#  S                                   #
#PPPP      PPP         PPP             #
#             P       P   P            #
#         E          P  T  P           #
#      PPPP       PPPP   PPPP          #
#                                      #
#   E        PPP              E        #
#  PPPP         P          PPPP        #
#                P                     #
#             PPPP                     #
#                         PPP        X #
# E                          P      PPP
#PPP     ^  ^  ^          PPPP         #
#      PPPPPPPPPP                      #
#                                      #
########################################

^ = spikes
```

Ajustar complejidad del layout segun el proposito:

- Tutorial: lineal, obvio
- Challenge: no-lineal, requiere backtracking o pensamiento
- Boss: arena simple, enfocado en boss fight
- Exploration: muchos caminos, secrets

---

## FASE 4: Encounter table

Definir enemigos, cantidades, y triggers.

```
## Encounters

| ID | Tipo de enemigo | Cantidad | Posicion (tile coords) | Trigger |
|---|---|---|---|---|
| E1 | [enemy type] | [N] | (x, y) | [on enter / scripted / patrol] |
| E2 | [enemy type] | [N] | (x, y) | [trigger] |

Ejemplo (RPG):

| ID | Tipo de enemigo | Cantidad | Posicion | Trigger |
|---|---|---|---|---|
| E1 | Slime | 1 | (3, 3) | On player enter tile (2-4, 2-4) |
| E2 | Skeleton | 2 | (9, 9) | On door D1 open |
| E3 | Goblin Archer | 1 | (15, 9) | Patrol route (14-16, 8-10) |

Ejemplo (Platformer):

| ID | Tipo de enemigo | Cantidad | Posicion | Trigger |
|---|---|---|---|---|
| E1 | Bat | 1 | (5, 8) | Patrol horizontal (5-10, 8) |
| E2 | Spike Trap | 3 | (15, 14) | Static hazard |
| E3 | Mini-boss Ogre | 1 | (35, 12) | On player x > 30 |
```

### Validacion de balance

```
Total enemigos: [N]
Dificultad esperada: [facil / medio / dificil]
Player level esperado: [lv]

¿El numero de enemigos es apropiado para el proposito del nivel?
- Tutorial: 0-2 enemigos, muy debiles
- Challenge: 5-10 enemigos, fuertes pero manejables
- Boss: 1 boss + 0-3 minions
```

---

## FASE 5: Difficulty curve (tension graph)

Visualizar como la dificultad/tension sube y baja a lo largo del nivel.

```
## Difficulty Curve

Tension graph (ASCII, Y=tension, X=progress):

High  |                    B
      |                  / |
Med   |      C1      C2     |  R
      |     /  \    /  \    | /
Low   | S--/    \--/    \--/ /
      +-------------------------
       Start              End

S  = Spawn (low tension, safe)
C1 = Challenge 1 (encounter/puzzle)
C2 = Challenge 2 (mas dificil)
B  = Boss/climax (peak tension)
R  = Resolution (post-boss, camino al exit)

Puntos de descanso:
- Despues de C1 (antes de C2)
- Despues de boss (antes de exit)

Regla: nunca tension alta sostenida > 2 minutos sin respiro.
```

---

## FASE 6: Secrets y caminos opcionales

```
## Secrets / Optional Paths

| ID | Tipo | Ubicacion | Recompensa | Pista |
|---|---|---|---|---|
| ?1 | [tipo] | [coords o descripcion] | [reward] | [como descubrir] |

Ejemplo:

| ID | Tipo | Ubicacion | Recompensa | Pista |
|---|---|---|---|---|
| ?1 | Hidden room | Behind wall (12, 5) | Rare sword | Wall crack visible si player mira con atencion |
| ?2 | Optional path | Upper route (8-15, 3-4) | 3 chests + harder enemies | Requires wall jump (advanced mechanic) |
| ?3 | Collectible | (18, 10) | Lore item (no combat benefit) | Detour del camino principal |

Regla: secrets son OPCIONALES. El jugador puede completar el nivel sin ellos.
```

---

## FASE 7: Tileset y asset requirements

```
## Tileset Requirements

Basado en el layout, listar tiles y sprites necesarios:

### Tiles (terrain)

- [Tile type 1] (ej: stone_floor)
- [Tile type 2] (ej: stone_wall)
- [Tile type 3] (ej: water)

Ejemplo (castle-dungeon):
- stone_floor (walkable)
- stone_wall (solid, autotile 4-bit)
- door_closed, door_open (animated, 2 frames)
- water_shallow (walkable, slow movement)
- spikes (hazard, animated, 3 frames)

### Objects (decorations, interactables)

- [Object 1] (ej: torch, animated)
- [Object 2] (ej: chest, 2 states: closed/open)
- [Object 3] (ej: lever, 2 states: up/down)

### Enemies (sprites)

- [Enemy type 1] con animaciones: idle, attack, hurt, death
- [Enemy type 2]
- [Boss] (si aplica)

### Special effects

- [Effect 1] (ej: door opening animation)
- [Effect 2] (ej: treasure sparkle)
```

---

## FASE 8: Music y ambience

```
## Audio

**Music track:** [nombre o descripcion]

Ejemplo:
- "dungeon_theme_1" (dark ambient, low tempo, ominous)
- Loop: si
- BPM: 90
- Instruments: strings, bass, percussion

**Ambience/SFX:**

- [SFX 1] — [trigger]
- [SFX 2] — [trigger]

Ejemplo:
- dripping_water — loop, random intervals (2-5s)
- torch_crackle — loop continuo en tiles con torch
- door_creak — on door open
- enemy_growl — on enemy aggro
```

---

## FASE 9: Escribir level brief

Producir `design/levels/{name}.md`:

```markdown
# Level Brief — [NOMBRE DEL NIVEL]

## Contexto

**Juego:** [nombre del juego]
**Genero:** [RPG / Platformer / Roguelike / etc.]
**Ubicacion en progresion:** [nivel 1-1, zona 2, post-tutorial, etc.]

---

## Proposito

[Descripcion del proposito: tutorial, challenge, boss, exploration, rest]

**Objetivos del jugador:**
1. [Objetivo 1, ej: "llegar al exit"]
2. [Objetivo 2, ej: "derrotar al boss"]
3. [Objetivo 3 opcional, ej: "encontrar 3 secrets"]

---

## Layout

**Dimensiones:** [W] tiles × [H] tiles ([W_px] × [H_px] pixels)

**Tile size:** [size] × [size] (del art-bible.md)

### ASCII Map

```
[ASCII map completo con leyenda]
```

### Leyenda

```
[Simbolos y significados]
```

---

## Encounters

[Tabla de enemigos con posiciones y triggers]

**Total enemigos:** [N]

**Dificultad esperada:** [facil / medio / dificil]

**Player level esperado:** [lv] (si aplica)

---

## Difficulty Curve

```
[ASCII tension graph]
```

**Puntos de descanso:**
- [Ubicacion 1]
- [Ubicacion 2]

**Pacing:** [estimado de tiempo para completar: X minutos]

---

## Secrets / Optional Content

[Tabla de secrets con ubicaciones y recompensas]

---

## Asset Requirements

### Tiles
- [Lista de tiles necesarios]

### Objects
- [Lista de objects/decorations]

### Enemies
- [Lista de enemy types con animaciones]

### Effects
- [Lista de effects especiales]

---

## Audio

**Music:** [nombre de track] — [descripcion]

**Ambience:**
- [Lista de SFX ambient]

**Triggers:**
- [SFX especificos con triggers]

---

## Implementation Notes

**Scripting:**
- [Evento 1: descripcion de como implementar]
- [Evento 2: descripcion]

Ejemplo:
- Door D1 opens cuando player activa lever L1
- Boss spawns cuando player cruza x > 30
- Exit se desbloquea cuando boss muere

**Camera:**
- [Comportamiento de camara: follow player, fixed, cinematic en boss, etc.]

**Save points:**
- [Ubicaciones de save/checkpoint]

---

## Testing Checklist

- [ ] Layout walkable (no hay tiles bloqueados sin intencion)
- [ ] Todos los encounters spawn correctamente
- [ ] Secrets son alcanzables (no softlock)
- [ ] Exit es accesible despues de completar objetivos
- [ ] Difficulty curve se siente apropiada (no frustrante, no aburrida)
- [ ] Audio sincronizado con eventos
- [ ] Transicion al siguiente nivel funciona

---

## Siguientes Pasos

1. Implementar layout en Tiled (o Godot TileMap)
2. Configurar collision layer
3. Implementar enemy spawns y triggers
4. Agregar objects y decorations
5. Integrar audio
6. Playtest y ajustar difficulty
```

---

## FASE 10: Transicion

```
## Level Brief completado: [NOMBRE]

Archivo creado: design/levels/{name}.md

Este documento define el nivel completo con layout, encounters,
difficulty, secrets, y asset requirements.

## Siguientes pasos recomendados

### Opcion A: Implementar en Tiled
Si usas Tiled, importar tileset y pintar el layout segun el ASCII map.
Configurar collision layer y event triggers.

### Opcion B: Implementar en Godot directo
Crear TileMap en Godot, configurar tileset, y pintar nivel.
Agregar enemy spawns como instancias de escenas.

### Opcion C: Disenar mas niveles
Si hay mas niveles pendientes, usa `/level-brief <nombre>` para
disenarlos antes de implementar.

¿Que hacemos ahora?
```

NO ejecutar automaticamente. Esperar decision del usuario.

---

## Anti-patrones

```
ANTI-PATRON: Layout sin proposito claro
  → Nivel se siente random, sin direccion
  Solucion: FASE 2 obliga a definir proposito explicito

ANTI-PATRON: Difficulty curve plana (todo igual)
  → Nivel aburrido, sin momentos memorables
  Solucion: FASE 5 visualiza tension, fuerza variacion

ANTI-PATRON: Secrets imposibles de descubrir
  → Frustracion, jugador nunca los encuentra
  Solucion: siempre dar pista visual o contextual

ANTI-PATRON: Too many enemies sin respiro
  → Fatiga, jugador se rinde
  Solucion: alternar challenge con descanso (FASE 5)

ANTI-PATRON: Assets no listados
  → Implementacion se frena porque falta arte
  Solucion: FASE 7 lista TODO lo necesario antes de implementar

ANTI-PATRON: No playtesting estimado
  → Nivel toma 2 horas cuando deberia ser 10 minutos
  Solucion: estimar pacing en FASE 5, validar con playtest
```

## Entrada esperada

Toma del prompt del usuario cualquier ruta, modo o contexto adicional que acompane a la invocacion de la skill.
