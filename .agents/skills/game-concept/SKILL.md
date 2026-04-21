---
name: game-concept
description: >-
  Disenar el concepto de un juego: 3 pillars, core loop, mecanicas MVP/NICE/FUTURE, look &
  feel, target audience. Produce game-concept.md listo para $art-bible o $design-system.
  Usala cuando el usuario quiere definir el concepto de un juego nuevo, o cuando dice
  "game-concept", "concepto del juego", "pillars", "core loop", "que tipo de juego",
  "definir juego".
---

# Game Concept

## Uso en Codex

- Esta skill esta pensada para invocacion explicita con `$game-concept`.
- Trabaja con lecturas puntuales: `rg -n` para buscar, `rg --files` o `find` para listar, y `sed -n` para leer solo el fragmento necesario.
- Si falta contexto menor, propone una opcion por defecto y dejala explicita; pregunta solo por decisiones que cambian genero, hook o alcance.
- Delega solo si el usuario pidio paralelismo o delegacion.

Definir los fundamentos de diseno de un juego: pillars, core loop, mecanicas priorizadas, y target audience. Output: `design/gdd/game-concept.md`.

## FASE 1: Extraer idea inicial

Si el usuario paso argumento, usarlo como punto de partida.
Sino, preguntar: tipo de juego (RPG, platformer, roguelike, puzzle-platformer, action RPG, otro) y hook (que lo diferencia: mecanica unica, combinacion inusual, estetica distintiva, o narrativa).

## FASE 2: Definir 3 pillars

Los pillars son los 3 valores core del diseno. Toda decision posterior se valida contra estos.

Proponer pillars basados en la idea del usuario. Cada pillar debe ser especifico y accionable — NO usar palabras vagas como "fun", "engaging", "polished". Un buen pillar se puede validar contra una mecanica concreta.

Confirmar con el usuario antes de continuar.

## FASE 3: Core loop

El core loop es el ciclo que el jugador repite constantemente. Debe ser satisfactorio en si mismo.

Presentar plantilla adaptada al genero (ej: RPG → Explorar → Encounter → Combate → Loot/XP → Upgrade → loop). Confirmar con el usuario.

## FASE 4: Mecanicas (MVP / NICE / FUTURE)

Forzar priorizacion brutal:

- **MVP** (max 4 mecanicas): sin esto no hay juego
- **NICE**: agregan profundidad, no esenciales
- **FUTURE**: pueden esperar 3+ sprints

Presentar lista inicial basada en genero, pedir al usuario agregar/quitar/mover entre categorias.

## FASE 5: Look & Feel

Definir la experiencia estetica y emocional en 2-3 frases. Incluir: estilo visual, paleta general, tipo de musica, y que emocion evoca.

## FASE 6: Target

Definir:
- **Plataforma**: PC, mobile, web, consola
- **Audiencia**: casual, core, hardcore
- **Session length**: corta (5-15 min), media (30-60 min), larga (1-3 hrs)

## FASE 7: Escribir game-concept.md

Generar `design/gdd/game-concept.md` con secciones: Tagline, Genre, Hook, Pillars (con ejemplo de mecanica que lo cumple), Core Loop (con diagrama), Mecanicas (MVP/NICE/FUTURE como checklists), Look & Feel, Target, Success Criteria (3 criterios medibles), Out of Scope (que NO es este juego), Siguientes pasos.

## FASE 8: Transicion

Mostrar path del archivo creado y opciones: `$art-bible`, `$design-system <sistema>`, `$rpg-design`, o `$plan`. NO ejecutar automaticamente — esperar decision del usuario.

## Anti-patrones

- **Mas de 4 mecanicas en MVP** → scope creep, proyecto nunca termina
- **Pillars vagos** ("fun", "engaging") → no son accionables ni medibles
- **Core loop sin satisfaccion intrinseca** → jugador necesita zanahoria externa
- **No definir out-of-scope** → features se infiltran sin criterio
- **Target audience "todos"** → juego generico que no satisface a nadie
