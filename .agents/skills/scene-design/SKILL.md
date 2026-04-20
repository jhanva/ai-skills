---
name: scene-design
description: >-
  Define scene design para entities (player, enemies, UI): node tree hierarchy, signals,
  scripts con responsabilidades, y data flow. Lee GDD del sistema, define estructura de
  nodos Godot (CharacterBody2D, AnimatedSprite2D, CollisionShape2D, etc), y genera
  design/scenes/{scene-name}.md con specs completas para implementacion.
---

# Scene Design

Arquitectura completa de scenes en Godot: node hierarchy, signals, scripts, y data flow. Output: `design/scenes/{scene-name}.md`.

## FASE 1: Leer GDD y contexto

Buscar documentacion del sistema relevante (player controller, combat, enemies, UI flow, levels). Extraer: requisitos funcionales (que debe hacer), inputs/outputs, dependencies (autoloads, resources, otras scenes).

Si no hay design doc: WARNING (scene sera generica).

## FASE 2: Clasificar scene type

| Type | Root Node | Use Case | Complexity |
|------|-----------|----------|------------|
| Character | CharacterBody2D | Player, enemies, NPCs | Medium-High |
| Projectile | Area2D | Bullets, arrows, spells | Low |
| UI Screen | Control | Menus, HUD, dialogs | Medium |
| Level | Node2D | Levels, rooms, zones | High |
| Interactable | Area2D | Chests, doors, switches | Low-Medium |
| Particle Effect | GPUParticles2D | Explosions, magic, dust | Low |

Clasificar la scene y aplicar template de node tree base.

## FASE 3: Definir node tree hierarchy

Leer `references/node-patterns.md` para ejemplo concreto de arbol y tabla de nodos.

Reglas:
1. **Root node**: tipo apropiado para funcionalidad principal (CharacterBody2D para fisica, Area2D para triggers, Control para UI)
2. **Visual nodes**: children directos del root (Sprite2D, AnimatedSprite2D)
3. **Collision nodes**: siempre children del physics node
4. **Audio nodes**: children del root o del triggering node (AudioStreamPlayer2D para spatial, AudioStreamPlayer para global)
5. **Logic nodes**: custom nodes (Node type) para state machines, AI

Entregable: arbol ASCII, tabla `node → type → purpose → script → properties`, justificacion de root y children.

## FASE 4: Definir signals

**Emitted (hacia afuera)**: eventos que otros systems necesitan (health_changed, died, attack_performed).

**Internal**: comunicacion entre children (animation_finished, area_entered, timeout).

Tabla: `signal → emitted by → parameters → connected to → when → purpose`.

Incluir signal definitions en script (con typed parameters) y connections en `_ready()`.

## FASE 5: Definir scripts y responsabilidades

Reglas:
1. **1 script = 1 concern** — no mezclar input + animation + combat
2. **Root script**: coordina children, no implementa toda la logica
3. **Component scripts**: hurtbox, hitbox, state machine son reutilizables
4. **Max 300 lineas** — si excede, refactorizar en components

Tabla: `script → node → responsibility → dependencies → LOC estimate`.

## FASE 6: Definir data flow

Documentar flujo de datos: input → script processing → physics → position → animation → collision → signals → external systems.

Tablas de: resources cargados (type, path, loaded by, when), events emitidos al EventBus, external dependencies (autoloads, built-in).

## FASE 7: Generar scene design document

Escribir `design/scenes/{scene-name}.md`. Leer `references/output-template.md` para estructura, implementation checklist, y validaciones finales.
