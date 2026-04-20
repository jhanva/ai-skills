---
name: level-brief
description: >-
  Disenar un level brief: proposito del nivel, layout ASCII, encounter table, difficulty
  curve, secrets, tileset requirements. Produce design/levels/{name}.md listo para
  implementacion. Usala cuando el usuario quiere disenar un nivel, zona, o area de juego, o
  cuando dice "level-brief", "disenar nivel", "mapa", "zona", "area", "level design".
---

# Level Brief

Disenar nivel completo: proposito, layout ASCII, encounters, difficulty curve, secrets, y asset requirements. Output: `design/levels/{name}.md`.

## FASE 1: Leer contexto del juego

Leer `design/gdd/game-concept.md` para genero, mecanicas MVP disponibles, y pillars. Si no existe, preguntar tipo de juego.

Identificar nombre del nivel del argumento. Si vago, pedir nombre especifico (ej: "forest-1", "castle-dungeon", "tutorial").

## FASE 2: Definir proposito del nivel

| Tipo | Proposito | Caracteristicas |
|---|---|---|
| Tutorial | Ensenar mecanicas | Bajo riesgo, progresion lineal |
| Introduce mechanic | Presentar mecanica nueva | Safe space, ramp up gradual |
| Challenge | Testear mastery | Dificil pero justo |
| Boss | Climax de zona | Arena cerrada, mecanica unica, high stakes |
| Exploration | Recompensar curiosidad | Open-ended, secrets, minimal combat |
| Rest | Descanso entre desafios | Safe zone, save point, shops |

Proponer proposito basado en nombre del nivel. Confirmar con usuario.

## FASE 3: Layout ASCII

Crear mapa visual usando leyenda standard:

```
#=Wall  .=Floor  D=Door  E=Enemy  T=Treasure  S=Start
X=Exit  L=Lever  B=Boss  ~=Water  ^=Hazard  ?=Secret
```

Ajustar complejidad segun proposito: tutorial→lineal, challenge→no-lineal, boss→arena simple, exploration→muchos caminos.

Especificar dimensiones (tiles ancho × alto) y total area en pixels.

## FASE 4: Encounter table

Tabla: `ID → tipo enemigo → cantidad → posicion → trigger` (on enter, scripted, patrol).

Validar balance: total enemigos apropiado para el proposito del nivel (tutorial: 0-2, challenge: 5-10, boss: 1 + 0-3 minions).

## FASE 5: Difficulty curve

Tension graph ASCII (Y=tension, X=progress):

```
High  |              B
Med   |    C1    C2   |  R
Low   | S-/  \--/  \-/ /
      +-------------------
       Start          End
```

Puntos de descanso despues de cada challenge. Regla: nunca tension alta sostenida > 2 minutos sin respiro.

## FASE 6: Secrets y caminos opcionales

Tabla: `ID → tipo → ubicacion → recompensa → pista`. Regla: secrets son OPCIONALES — el jugador puede completar el nivel sin ellos.

## FASE 7: Tileset y asset requirements

Listar tiles (terrain con tipo de autotile), objects/decorations, enemies con animaciones requeridas, y special effects.

## FASE 8: Music y ambience

Track name, mood, loop, BPM. SFX ambientales con triggers.

## FASE 9: Escribir level brief

Escribir `design/levels/{name}.md`. Leer `references/output-template.md` para estructura, testing checklist, anti-patrones, y cierre.
