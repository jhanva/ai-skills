# Scene Design — Node Patterns

Lee este archivo solo cuando necesites un ejemplo concreto de arbol de nodos o una tabla de nodos para una scene tipica.

## Player scene base

```text
Player (CharacterBody2D)
  ├─ AnimatedSprite2D
  ├─ CollisionShape2D
  ├─ Area2D (Hurtbox)
  ├─ Area2D (AttackHitbox)
  ├─ AudioStreamPlayer2D
  ├─ Node (StateMachine)
  └─ Marker2D (SpawnPoint)
```

## Tabla minima

| Node | Type | Purpose |
|---|---|---|
| Root | CharacterBody2D / Control / Node2D | comportamiento principal |
| Visual | Sprite2D / AnimatedSprite2D | representacion visual |
| Collision | CollisionShape2D / Area2D | fisica, hurtboxes, hitboxes |
| Audio | AudioStreamPlayer / AudioStreamPlayer2D | feedback |
| Logic | Node | state machine, AI o helpers |

## Reglas

- El root define la responsabilidad principal
- Visual y collision deben colgar del nodo correcto
- Audio y logic deben existir solo si aportan algo concreto
- Evitar trees profundos si una tabla de nodos basta
