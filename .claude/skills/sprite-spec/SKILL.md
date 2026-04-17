---
name: sprite-spec
description: >
  Define sprite specifications para entities (player, enemies, NPCs, props).
  Lee art-bible, determina animation states con frame count y timing, define
  dimensions y hitbox, reglas de flipping, y formato de export. Output:
  design/sprites/{entity}-spec.md con tabla completa de animaciones y specs tecnicas.
argument-hint: "<nombre del entity> (ej: player, slime, skeleton)"
disable-model-invocation: true
agent: pixel-artist
allowed-tools:
  - Read
  - Grep
  - Glob
  - Write
---

# Sprite Specification

Define specs completas para sprites de entities: animation states, frame counts, timing, hitbox, y formato de export. Genera documento tecnico que el pixel artist puede implementar directamente.

## FASE 1: Leer Art-Bible y Contexto

**Objetivo**: Cargar restricciones tecnicas y esteticas del proyecto.

1. Buscar y leer `design/art-bible.md` o `docs/art-bible.md`
2. Extraer datos criticos:
   - Resolucion base del sprite (ej: 16x16, 32x32, 48x48)
   - Paleta de colores (cuantos colores max, nombre del archivo palette)
   - Estilo (pixel perfect, dithering permitido, outline yes/no)
   - Frame rate target (ej: 12 FPS, 8 FPS)
3. Si no existe art-bible: usar defaults (32x32, 12 FPS, outline negro 1px)
4. Buscar referencias del entity en game design docs con Grep

**Validaciones**:
- Si no hay resolucion definida: ERROR, no se puede continuar sin art-bible
- Si el entity no aparece en ningun design doc: ADVERTIR (spec puede estar incompleta)

---

## FASE 2: Determinar Entity Type y Categoria

**Objetivo**: Clasificar el entity para aplicar templates de animacion apropiados.

### Tipos de entity

| Type | Subcategoria | Animation Complexity | Ejemplo |
|------|--------------|----------------------|---------|
| Player | Controllable | Alta (8-12 states) | Protagonist, party members |
| Enemy | Hostile | Media (4-8 states) | Slime, skeleton, boss |
| NPC | Non-hostile | Baja (2-4 states) | Vendor, quest giver |
| Prop | Static/animated | Muy baja (1-2 states) | Chest, torch, door |

### Templates de animation states por tipo

**Player**:
- idle, walk, run, jump, fall, attack, hurt, death
- Opcional: crouch, dash, cast, interact

**Enemy basico**:
- idle, move, attack, hurt, death
- Opcional: spawn, taunt

**Boss enemy**:
- idle, move, attack_1, attack_2, attack_3, phase_transition, hurt, death
- Opcional: enrage, summon

**NPC**:
- idle, talk
- Opcional: walk, work (animation especifica al rol)

**Prop animado**:
- idle, open/activate
- Opcional: close, break

**Prop estatico**:
- default (frame unico)

**Decision**: Basado en el nombre del entity y busqueda en design docs, determinar tipo y subcategoria.

---

## FASE 3: Definir Animation States con Frame Count y Timing

**Objetivo**: Tabla completa de animaciones con specs precisas.

### Formato de tabla

| State | Frames | FPS | Loop | Duration | Notes |
|-------|--------|-----|------|----------|-------|
| idle | 4 | 8 | Yes | 0.5s | Breathing cycle, subtle movement |
| walk | 6 | 12 | Yes | 0.5s | Contact frames on 2 and 5 |
| attack | 8 | 16 | No | 0.5s | Hitbox active frames 4-5, recovery 6-8 |
| hurt | 3 | 12 | No | 0.25s | Invincibility during animation |
| death | 10 | 12 | No | 0.83s | Fade out on last frame |

### Reglas de timing

1. **Idle**: Loop infinito, FPS bajo (6-8), movimiento sutil
2. **Walk/Run**: Loop, FPS medio (10-12), frames de contacto alineados con SFX
3. **Attack**: No loop, FPS alto (12-16), marcar hitbox frames
4. **Hurt**: No loop, corto (2-4 frames), sincronizar con invincibility
5. **Death**: No loop, FPS medio, ultimo frame persiste (no desaparece el sprite)
6. **Transition states** (jump, fall): No loop, pueden encadenar con otras

### Frame count guidelines

- **Minimo viable**: 2-3 frames (walk simple, hurt)
- **Standard**: 4-6 frames (idle, walk, attacks basicos)
- **High quality**: 8-12 frames (attacks complejos, boss animations)
- **Excesivo**: >12 frames (solo para cinematics o bosses especiales)

**Output**: Tabla completa con TODAS las animaciones del entity, calculando duration = frames / FPS.

---

## FASE 4: Definir Sprite Dimensions y Hitbox

**Objetivo**: Specs tecnicas de tamaño, canvas, y collision.

### Canvas vs Sprite vs Hitbox

```
Canvas: 32x32px (resolucion base del art-bible)
  └─ Sprite bounds: 24x28px (area real del dibujo)
      └─ Hitbox: 12x16px (collision box para gameplay)
```

### Tabla de especificaciones

| Dimension | Width | Height | Offset X | Offset Y | Notes |
|-----------|-------|--------|----------|----------|-------|
| Canvas | 32 | 32 | - | - | Tamaño del archivo PNG |
| Sprite | 24 | 28 | 4 | 2 | Centrado en canvas, espacio para VFX |
| Hitbox | 12 | 16 | 10 | 12 | Collision box, centrada en feet |
| Hurtbox | 16 | 20 | 8 | 8 | Area de recepcion de damage (opcional) |

### Reglas de diseño

1. **Canvas**: Siempre cuadrado y potencia de 2 (16, 32, 64) o multiplo estandar (48)
2. **Sprite bounds**: Dejar 2-4px de padding para effects (swing trail, impact, dust)
3. **Hitbox**: Aprox 40-60% del sprite bounds, centrado en los pies para top-down, centrado vertical para platformer
4. **Hurtbox**: Opcional, si damage area difiere de collision (ej: cabeza vulnerable, escudo no)

**Ejemplo concreto**:

Para un skeleton (enemy) 32x32:
- Canvas: 32x32 (standard tile size)
- Sprite: 20x30 (alto y delgado, offset +6x, +1y)
- Hitbox: 10x10 (pequeño, solo el torso, offset +11x, +20y para pies)
- Hurtbox: 14x24 (todo el cuerpo excepto huesos de piernas, offset +9x, +6y)

---

## FASE 5: Reglas de Flipping y Direccionalidad

**Objetivo**: Definir como manejar multiples direcciones sin duplicar sprites.

### Estrategias de direccionalidad

| Direcciones | Strategy | Sprites Needed | Use Case |
|-------------|----------|----------------|----------|
| 2 (left/right) | Horizontal flip | 1 set | Platformer, side-scroller |
| 4 (cardinal) | Flip + 2 sets (up/down) | 2 sets | Top-down basico |
| 8 (cardinal + diagonal) | Flip + 4 sets | 4 sets | Top-down detallado, RPG |
| 1 (facing camera) | No flip | 1 set | Isometric, fixed perspective |

### Reglas de flipping

**Horizontal flip (default)**:
- Dibujar facing RIGHT como base
- Engine hace flip horizontal para LEFT
- Asimetrias intencionales (arma en mano derecha) se preservan

**Vertical flip** (NO USAR):
- Casi nunca se ve bien en pixel art
- Dibujar UP y DOWN por separado

**Diagonal handling**:
- Para 8-dir: dibujar las 4 direcciones principales (up, down, left, right)
- Engine reutiliza la direccion mas cercana para diagonales
- O dibujar las 4 diagonales por separado si el proyecto tiene budget

### Excepciones

- **Asymmetric attacks**: Si el personaje ataca con espada en mano derecha, el flip debe mantener la espada en la MISMA mano (requiere sprites separados para left/right attack)
- **Face detail**: Si el sprite tiene detalle facial asimetrico (cicatriz, parche), puede requerir sprites no-flipped

**Decision para este entity**: Especificar si usa flip o sprites separados, y cuantas direcciones soporta.

---

## FASE 6: Export Format y Naming Convention

**Objetivo**: Specs de archivos para integracion en Godot.

### Formato de archivo

**Opcion 1: Sprite sheet** (recomendado para Godot)
```
player_spritesheet.png
  - Grid: 32x32 por frame
  - Layout: horizontal por animacion, vertical por direccion
  - Rows: idle, walk, attack, hurt, death (5 rows)
  - Columns: max frames de la animacion mas larga (ej: 10)
  - Total: 32*10 = 320px ancho, 32*5 = 160px alto
```

**Opcion 2: Frames individuales**
```
player_idle_0.png
player_idle_1.png
player_walk_0.png
player_walk_1.png
...
```

**Opcion 3: Atlas con metadata** (mejor para proyectos grandes)
```
player_atlas.png  (packed)
player_atlas.json (frame positions y names)
```

### Naming convention

Pattern: `{entity}_{state}_{frame}.png` o `{entity}_{state}_{direction}_{frame}.png`

Ejemplos:
- `slime_idle_0.png`, `slime_idle_1.png`
- `skeleton_walk_right_0.png`, `skeleton_walk_right_1.png`
- `boss_attack2_3.png`

**Reglas**:
- Lowercase, underscore separators
- Frame index empieza en 0
- Direction solo si no usa flipping (right, left, up, down)
- State names match los definidos en la tabla de FASE 3

### Integracion en Godot

**AnimatedSprite2D setup**:
```gdscript
# Si usa sprite sheet:
sprite_frames = preload("res://assets/sprites/player_spritesheet.png")
hframes = 10  # columnas
vframes = 5   # filas

# Si usa frames individuales:
# Godot auto-detecta secuencia player_idle_*.png
```

**Metadata adicional**:
- Crear archivo `{entity}.tres` (SpriteFrames resource) con todas las animaciones configuradas
- O generar JSON con frame durations si son variables

---

## FASE 7: Generar Spec Document

**Objetivo**: Escribir `design/sprites/{entity}-spec.md` con toda la informacion.

### Template del documento

```markdown
# {Entity} Sprite Specification

**Type**: [Player/Enemy/NPC/Prop]
**Resolution**: [32x32]
**Palette**: [palette_main.gpl]
**Style**: [Pixel perfect, 1px black outline]

## Animation States

| State | Frames | FPS | Loop | Duration | Notes |
|-------|--------|-----|------|----------|-------|
| ... | ... | ... | ... | ... | ... |

## Dimensions

| Dimension | Width | Height | Offset X | Offset Y | Notes |
|-----------|-------|--------|----------|----------|-------|
| Canvas | 32 | 32 | - | - | PNG file size |
| Sprite | 24 | 28 | 4 | 2 | Centered, room for VFX |
| Hitbox | 12 | 16 | 10 | 12 | Collision box |

## Directionality

- **Directions**: 2 (left/right)
- **Method**: Horizontal flip (draw facing right)
- **Exceptions**: Attack animation uses separate left/right sprites (weapon hand)

## Export Format

- **Format**: Individual frames
- **Naming**: `{entity}_{state}_{frame}.png`
- **Location**: `assets/sprites/{entity}/`
- **Godot Resource**: `{entity}.tres` (SpriteFrames)

## Implementation Checklist

- [ ] Draw base sprite facing right (idle_0)
- [ ] Complete idle animation (4 frames)
- [ ] Complete walk animation (6 frames)
- [ ] Complete attack animation (8 frames)
- [ ] Complete hurt animation (3 frames)
- [ ] Complete death animation (10 frames)
- [ ] Export all frames as individual PNGs
- [ ] Create SpriteFrames resource in Godot
- [ ] Configure hitbox in CharacterBody2D scene
- [ ] Test all animations in game
```

**Accion**: Escribir el archivo completo con los datos recopilados en las fases anteriores.

---

## FASE 8: Validaciones Finales

**Checklist**:

- [ ] Todas las animaciones tienen frame count >= 1
- [ ] FPS values son razonables (4-24)
- [ ] Hitbox cabe dentro del canvas
- [ ] Naming convention es consistente
- [ ] Export format es compatible con Godot 4
- [ ] Total de sprites <= 100 (warning si excede, considerar sprite sheet)
- [ ] Document incluye checklist de implementacion

**Output final**: Path absoluto del archivo generado.

---

## Transicion al Siguiente Paso

Una vez completada la spec:

1. **Siguiente**: `/palette crear` (si no existe palette definida)
2. **O**: Comenzar produccion de sprites en Aseprite siguiendo la spec
3. **Despues**: `/godot-setup` para preparar proyecto y importar sprites

**Entregable**: `design/sprites/{entity}-spec.md` con 100% de la informacion necesaria para producir los sprites sin ambiguedades.
