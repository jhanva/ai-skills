---
name: sprite-spec
description: >-
  Define sprite specifications para entities (player, enemies, NPCs, props). Lee art-bible,
  determina animation states con frame count y timing, define dimensions y hitbox, reglas de
  flipping, y formato de export. Output: design/sprites/{entity}-spec.md con tabla completa
  de animaciones y specs tecnicas.
---

# Sprite Specification

## Uso en Codex

- Esta skill esta pensada para invocacion explicita con `$sprite-spec`.
- Trabaja con lecturas puntuales: `rg -n` para buscar, `rg --files` o `find` para listar, y `sed -n` para leer solo el fragmento necesario.
- Si falta contexto menor, propone un set base de estados y timings y dejalo explicito; pregunta solo por requisitos que cambian el scope del sprite.
- Delega solo si el usuario pidio paralelismo o delegacion.

Specs completas para sprites de entities: animation states, frame counts, timing, hitbox, y formato de export. Output: `design/sprites/{entity}-spec.md`.

## FASE 1: Leer art-bible y contexto

Leer `design/art-bible.md` para extraer: resolucion base, paleta, estilo (outline, shading), frame rate target. Si no existe: ERROR, no se puede continuar sin art-bible.

Buscar referencias del entity en design docs.

## FASE 2: Clasificar entity type

| Type | Animation Complexity | States tipicos |
|------|----------------------|----------------|
| Player | Alta (8-12 states) | idle, walk, run, jump, fall, attack, hurt, death + opcionales |
| Enemy basico | Media (4-8) | idle, move, attack, hurt, death |
| Boss | Alta (8-12) | idle, move, attack_1/2/3, phase_transition, hurt, death |
| NPC | Baja (2-4) | idle, talk + opcionales |
| Prop animado | Muy baja (1-2) | idle, open/activate |

## FASE 3: Animation states con timing

Tabla: `state → frames → FPS → loop → duration → notes`.

Reglas de timing:
- Idle: loop, FPS 6-8, movimiento sutil
- Walk/Run: loop, FPS 10-12, contact frames alineados con SFX
- Attack: no loop, FPS 12-16, marcar hitbox active frames
- Hurt: no loop, 2-4 frames, sincronizar con invincibility
- Death: no loop, FPS medio, ultimo frame persiste

Frame count guidelines: minimo 2-3, standard 4-6, high quality 8-12, >12 solo para cinematics.

## FASE 4: Dimensiones y hitbox

Definir tres capas:
- **Canvas**: tamano del PNG (cuadrado, potencia de 2 o multiplo estandar)
- **Sprite bounds**: area real del dibujo (padding 2-4px para effects)
- **Hitbox**: collision box (~40-60% del sprite, centrado en pies para top-down)
- **Hurtbox** (opcional): area de recepcion de damage si difiere de hitbox

Tabla: `dimension → width → height → offset X → offset Y → notes`.

## FASE 5: Flipping y direccionalidad

| Direcciones | Strategy | Sprites necesarios |
|-------------|----------|-------------------|
| 2 (left/right) | Horizontal flip | 1 set |
| 4 (cardinal) | Flip + 2 sets (up/down) | 2 sets |
| 8 (con diagonal) | Flip + 4 sets | 4 sets |

Regla: dibujar facing RIGHT como base, engine flippea para LEFT.

Excepciones: ataques asimetricos (arma en mano derecha) pueden requerir sprites separados.

## FASE 6: Export format y naming

**Formato**: sprite sheet (recomendado), frames individuales, o atlas con metadata.

**Naming**: `{entity}_{state}_{frame}.png` — lowercase, underscore, frame index desde 0.

**Integracion Godot**: SpriteFrames resource (.tres) con todas las animaciones configuradas.

## FASE 7: Generar spec document

Escribir `design/sprites/{entity}-spec.md` con: type, resolution, palette, style, tabla de animations, dimensions, directionality, export format, implementation checklist.

## FASE 8: Validaciones finales

- Todas las animaciones tienen frame count >= 1
- FPS values razonables (4-24)
- Hitbox cabe dentro del canvas
- Naming convention consistente
- Total sprites <= 100 (warning si excede)
