# Godot Architect Patterns

Lee este archivo cuando necesites patrones de arquitectura o criterios de refactor.

## Primero detecta contexto

- lenguaje dominante: `.gd` o `.cs`
- tipo de scene: gameplay, UI, level, battle, manager

## Patrones clave

- scene composition sobre god nodes
- signals para desacoplar, direct calls para ownership claro
- autoloads solo para servicios realmente globales
- `Resource` para data; `Node` para behavior
- gameplay data fuera de scripts hardcoded

## Anti-patrones

- trees demasiado profundos
- signal spaghetti
- `_process` y `_physics_process` mezclados
- dependencias circulares
- scenes con demasiadas responsabilidades

## Entregable sugerido

- problema detectado
- propuesta de estructura
- signals/dependencies
- riesgos o migracion
- equivalencia corta a Android/Kotlin si ayuda
