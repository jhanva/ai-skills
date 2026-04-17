---
name: game-concept
description: >
  Disenar el concepto de un juego: 3 pillars, core loop, mecanicas MVP/NICE/FUTURE,
  look & feel, target audience. Produce game-concept.md listo para /art-bible
  o /design-system.
when_to_use: >
  Cuando el usuario quiere definir el concepto de un juego nuevo, o cuando
  dice "game-concept", "concepto del juego", "pillars", "core loop", "que
  tipo de juego", "definir juego".
argument-hint: "<idea o genero del juego>"
disable-model-invocation: true
allowed-tools:
  - Read
  - Grep
  - Glob
  - Write
agent: game-designer
---

# Game Concept — Disenar concepto de juego

## Objetivo

Definir los fundamentos de diseno de un juego: pillars (que lo hace especial),
core loop (que repite el jugador), mecanicas priorizadas, y target audience.
El output es `design/gdd/game-concept.md` que sirve de base para todas las
demas decisiones de diseno.

---

## FASE 1: Extraer idea inicial

Si el usuario paso argumento (`$ARGUMENTS`), usar eso como punto de partida.
Sino, preguntar con opciones:

```
## ¿Que tipo de juego quieres hacer?

Describe la idea en 1-2 frases, o elige un template:

a) RPG de turnos estilo JRPG clasico (explorar + combate por turnos)
b) Platformer con mecanica unica (describir mecanica)
c) Roguelike con meta-progression (runs cortas + unlock permanente)
d) Puzzle-platformer (puzzles integrados en movimiento)
e) Action RPG (combate en tiempo real + stats)
f) Otro: [describir]

¿Que opcion?
```

Luego preguntar:

```
## ¿Que hace a este juego DIFERENTE?

Todo juego necesita un hook, algo que lo diferencie de los demas
del mismo genero. Puede ser:

- Mecanica unica (ej: time rewind en Braid, grappling en Celeste)
- Combinacion inusual (ej: roguelike + deck-building en Slay the Spire)
- Estetica distintiva (ej: hand-drawn en Hollow Knight, GB en Gato Roboto)
- Narrativa (ej: storytelling ambiental, sin dialogo explicito)

¿Cual es el hook de tu juego? [respuesta libre]
```

---

## FASE 2: Definir 3 pillars

Los pillars son los 3 valores core del diseno. Toda decision posterior
se valida contra estos.

Presentar ejemplos de pillars conocidos:

```
## Ejemplos de Pillars (referencia)

Celeste:
  1. Tight controls (precision en movimiento)
  2. Challenging but fair (dificil pero justo, respawn instantaneo)
  3. Accessibility (assist mode para todos los skill levels)

Hades:
  1. Fast-paced combat (combate dinamico, responsive)
  2. Narrative progression (historia avanza con cada muerte)
  3. Build variety (synergies entre abilities)

Stardew Valley:
  1. Player-driven progression (sin presion de tiempo)
  2. Multiple paths to enjoy (farming, fishing, social, mining)
  3. Cozy atmosphere (wholesome, sin stakes altos)
```

Luego preguntar:

```
## Define los 3 Pillars de tu juego

Basado en tu idea ("[idea del usuario]"), propongo estos pillars.
Modifica o reemplaza segun tu vision:

Propuesta:
  1. [pillar derivado de la idea]
  2. [pillar derivado del hook]
  3. [pillar derivado del genero]

¿Estos pillars representan tu vision?
- Si: continuar
- No: ajustar (¿que cambiarias?)
```

---

## FASE 3: Core loop

El core loop es el ciclo que el jugador repite constantemente.
Debe ser satisfactorio en si mismo.

Presentar plantillas por genero:

```
## Plantillas de Core Loop

RPG de turnos:
  Explorar → Encounter → Combate → Loot/XP → Upgrade → Explorar

Platformer:
  Movimiento → Obstaculo → Superar → Checkpoint → Movimiento

Roguelike:
  Build → Run → Muerte → Meta-unlock → Build

Action RPG:
  Combate → Loot → Equip → Combate mas duro

Puzzle-platformer:
  Observar → Intentar → Fallar → Aprender → Resolver
```

Presentar loop basado en el genero declarado en `/game-start` (si existe)
o inferir del argumento:

```
## Core Loop de tu juego

Basado en "[genero]", el core loop seria:

[plantilla adaptada]

¿Este loop captura la experiencia que quieres? ¿Ajustes?
```

---

## FASE 4: Mecanicas (MVP / NICE / FUTURE)

Forzar priorizacion brutal. MVP = minimo viable para que el juego funcione.

```
## Priorizar mecanicas

Listar TODAS las mecanicas que imaginas, luego categorizarlas.

Regla: MVP maximo 4 mecanicas. Si hay mas de 4, recortar.

Ejemplo (RPG de turnos):

MVP (sin esto no hay juego):
  - Movimiento por grid (4 direcciones)
  - Combate por turnos (attack/defend/item)
  - Inventario basico (items consumables)
  - Save/load

NICE (agregan profundidad, no son esenciales):
  - Skills con MP (no solo attack basico)
  - Equipo (armas/armadura modifican stats)
  - Status effects (poison, stun, buff)
  - Shops (comprar items/equipo)

FUTURE (pueden esperar 3+ sprints):
  - Party members (mas de 1 character)
  - Crafting
  - Side quests
  - New Game+
```

Presentar lista inicial basada en el genero:

```
## Mecanicas de tu juego ("[genero]")

Lista inicial basada en genero:

MVP:
  - [mecanica 1]
  - [mecanica 2]
  - [mecanica 3]
  - [mecanica 4]

NICE:
  - [mecanica 5]
  - [mecanica 6]
  - [mecanica 7]

FUTURE:
  - [mecanica 8+]

¿Agregar, quitar, o mover mecanicas entre categorias?
```

---

## FASE 5: Look & Feel

Definir la experiencia estetica y emocional en 2-3 frases.

```
## Look & Feel

Describe la estetica y el tono del juego. Ejemplos:

- "Pixel art 16-bit vibrante, paleta saturada, mundo colorido y optimista.
   Musica upbeat chiptune. Se siente como un sabado de dibujos animados."

- "Pixel art monocromatico (4 tonos de gris), estetica sombria post-apocaliptica.
   Musica ambient minimalista. Se siente solitario y contemplativo."

- "Pixel art detallado estilo SNES, paleta natural (verdes, marrones, azules).
   Musica orquestada fantastica. Se siente como una aventura epica."

¿Como se ve y se siente tu juego? [respuesta libre]
```

---

## FASE 6: Target

Definir plataforma, audiencia, y session length.

```
## Target Audience & Platform

### Plataforma
a) PC (Steam, itch.io)
b) Mobile (Android/iOS)
c) Web (navegador, HTML5 export)
d) Consola (Switch, PlayStation, Xbox — requiere devkit)

¿Plataforma target?

### Audiencia
a) Casual (poco tiempo, baja curva de aprendizaje)
b) Core gamers (familiarizados con el genero, buscan desafio)
c) Hardcore (dominan mecanicas complejas, buscan mastery)

¿Audiencia target?

### Session length (cuanto juega por sesion)
a) Corta (5-15 min) — ideal para mobile, roguelikes
b) Media (30-60 min) — tipico de PC/consola
c) Larga (1-3 hrs) — RPGs extensos, binge-friendly

¿Session length esperada?
```

---

## FASE 7: Escribir game-concept.md

Generar documento en `design/gdd/game-concept.md`:

```markdown
# Game Concept — [Nombre del Juego]

## Tagline

[1 frase que vende el juego]

Ejemplo: "A fast-paced roguelike where every death teaches you the boss patterns."

## Genre

[Genero] ([subgenero si aplica])

Ejemplo: RPG (turn-based, pixel art, story-driven)

## Hook

[Que hace a este juego especial. 2-3 frases.]

---

## Pillars

Los 3 valores core del diseno. Toda decision se valida contra estos.

1. **[Pillar 1]**
   - [Descripcion corta]
   - Ejemplo mecanica que lo cumple: [ejemplo]

2. **[Pillar 2]**
   - [Descripcion corta]
   - Ejemplo mecanica que lo cumple: [ejemplo]

3. **[Pillar 3]**
   - [Descripcion corta]
   - Ejemplo mecanica que lo cumple: [ejemplo]

---

## Core Loop

El ciclo que el jugador repite constantemente:

```
[Step 1] → [Step 2] → [Step 3] → [Step 4] → [loop back to Step 1]
```

Ejemplo:
```
Explore → Encounter → Fight → Loot → Upgrade → Explore
```

**Satisfaccion del loop:**
- [Por que Step X es satisfactorio]
- [Como Step Y refuerza engagement]

---

## Mecanicas

### MVP (minimo viable)

Sin estas mecanicas, el juego no funciona:

- [ ] [Mecanica 1]
- [ ] [Mecanica 2]
- [ ] [Mecanica 3]
- [ ] [Mecanica 4]

### NICE (agregan profundidad)

Mecanicas que mejoran el juego pero no son esenciales para MVP:

- [ ] [Mecanica 5]
- [ ] [Mecanica 6]
- [ ] [Mecanica 7]

### FUTURE (post-MVP)

Mecanicas que pueden esperar 3+ sprints:

- [ ] [Mecanica 8]
- [ ] [Mecanica 9]

---

## Look & Feel

[2-3 frases describiendo estetica, tono, y experiencia emocional]

**Referencias visuales:**
- [Juego/arte de referencia 1]
- [Juego/arte de referencia 2]

**Referencias de audio:**
- [Juego/OST de referencia 1]
- [Estilo musical: chiptune, orchestral, ambient, etc.]

---

## Target

**Plataforma:** [PC / Mobile / Web / Console]

**Audiencia:** [Casual / Core / Hardcore]

**Session length:** [5-15 min / 30-60 min / 1-3 hrs]

**Scope estimado:** [Horas de desarrollo para MVP]

---

## Success Criteria

¿Como sabemos que el juego funciona?

- [ ] [Criterio medible 1, ej: "player completa tutorial sin frustracion"]
- [ ] [Criterio medible 2, ej: "core loop es repetible 10+ veces sin aburrir"]
- [ ] [Criterio medible 3, ej: "primera victoria se siente satisfactoria"]

---

## Out of Scope (que NO es este juego)

Declaracion explicita de lo que el juego NO es, para evitar scope creep:

- NO es [cosa 1]
- NO tiene [feature 2]
- NO intenta [objetivo 3]

Ejemplo:
- NO es multiplayer
- NO tiene crafting (en MVP)
- NO intenta ser open-world

---

## Siguientes pasos

1. `/art-bible` — Definir estetica y pipeline de assets
2. `/design-system <sistema>` — Disenar mecanicas MVP individuales
3. `/rpg-design` — Si es RPG, disenar combate/stats/balance
4. `/plan` — Convertir este concepto en plan de implementacion
```

Escribir el archivo con contenido completo basado en las respuestas del usuario.

---

## FASE 8: Transicion

```
## Game Concept completado

Archivo creado: design/gdd/game-concept.md

Este documento es la base de todas las decisiones futuras de diseno.
Antes de implementar features, validar que cumplan los 3 pillars.

## Siguientes pasos recomendados

### Opcion A: Definir estetica
Usa `/art-bible` para definir resolucion, paleta, estilo de sprites,
y pipeline de assets. Esto produce `design/art-bible.md`.

### Opcion B: Disenar sistema especifico
Si ya tienes claro una mecanica MVP, usa:
- `/design-system <nombre>` para inventario, dialogo, crafting, etc.
- `/rpg-design` para combate/stats/balance (si es RPG)

### Opcion C: Planificar implementacion
Si el concepto esta completo, usa `/plan` para convertirlo en
tareas de 2-5 minutos.

¿Que hacemos ahora?
```

NO ejecutar automaticamente el siguiente paso. Esperar decision del usuario.

---

## Anti-patrones

```
ANTI-PATRON: Mas de 4 mecanicas en MVP
  → Scope creep, proyecto nunca termina
  Solucion: forzar priorizacion brutal en FASE 4

ANTI-PATRON: Pillars vagos ("fun", "engaging", "polished")
  → No son accionables ni medibles
  Solucion: pillars deben ser especificos y validables

ANTI-PATRON: Core loop sin satisfaccion intrinseca
  → Jugador necesita zanahoria externa (achievements, rewards)
  Solucion: el loop mismo debe ser satisfactorio (ej: movimiento en Celeste)

ANTI-PATRON: No definir out-of-scope
  → Features se infiltran sin criterio
  Solucion: seccion explicita de "que NO es este juego"

ANTI-PATRON: Target audience "todos"
  → Juego generico que no satisface a nadie
  Solucion: elegir UN target y disenar para ese
```

## Argumento: $ARGUMENTS
