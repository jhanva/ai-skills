---
name: brainstorm
description: >
  Guia un proceso de diseno riguroso ANTES de escribir codigo.
  Dialogo socratico, multiples enfoques con tradeoffs, spec escrita.
  Usar cuando: el usuario quiere construir algo nuevo, agregar una feature no trivial, redisenar un modulo, o dice "brainstorm" o "disenar".
argument-hint: "[descripcion del problema o feature]"
disable-model-invocation: true
---

# Brainstorm — Diseno antes de implementar

## Cuando usarlo

Usar este proceso para features no triviales, arquitectura nueva, requisitos ambiguos o decisiones
con tradeoffs reales. Un fix pequeno, cambio mecanico o tarea con spec completa puede ir directo a
planificacion o implementacion tras una comprobacion breve del alcance.

## Proceso

### Fase 1: Entender el problema

Haz preguntas UNA POR UNA para entender el contexto completo:

- Que problema se resuelve y para quien
- Que restricciones existen (tecnologia, tiempo, infraestructura)
- Que ya se intento o se descarto
- Cuales son los criterios de exito

Preferir preguntas de opcion multiple para reducir friccion:

```
Como se consumiran estos datos?
a) API REST desde un frontend
b) Batch processing nocturno
c) Streaming en tiempo real
d) Otro: ___
```

### Fase 2: Explorar enfoques

Propone exactamente 2-3 enfoques con tradeoffs claros:

```markdown
## Enfoque A: [nombre]
- Como funciona: ...
- Ventaja: ...
- Desventaja: ...
- Mejor cuando: ...

## Enfoque B: [nombre]
- Como funciona: ...
- Ventaja: ...
- Desventaja: ...
- Mejor cuando: ...
```

NO elijas por el usuario. Presenta los tradeoffs y deja que decida.

### Fase 3: Disenar la solucion

Con el enfoque elegido, presenta el diseno en secciones digeribles:

1. Estructura de datos / modelos
2. Componentes y sus responsabilidades
3. Flujo de datos entre componentes
4. Casos edge y como se manejan
5. Estrategia de testing

**Principio clave:** unidades pequenas con fronteras claras e interfaces bien definidas. Cada componente debe poder testearse en aislamiento.

### Fase 4: Escribir spec

Escribe un documento `spec.md` (o donde el usuario indique) con:

- Problema y contexto
- Enfoque elegido y justificacion
- Diseno detallado
- Decisiones explicitas (que se incluye Y que se excluye)
- Criterios de verificacion medibles

### Fase 5: Auto-revision

Antes de presentar al usuario, verifica:

- [ ] No hay placeholders ni TODOs
- [ ] Las secciones son consistentes entre si
- [ ] El scope esta claro (que SI y que NO)
- [ ] No hay ambiguedades
- [ ] Los criterios de verificacion son medibles

### Fase 6: Transicion

Cuando el usuario aprueba la spec: "Spec aprobada. Usa la skill `plan` para convertirla en un plan de implementacion paso a paso."

## Anti-patrones

| Excusa | Por que es invalida |
|---|---|
| "No necesito aclarar el alcance" | Las suposiciones no examinadas crean retrabajo |
| "Ya se que quiero" | Saber que quieres no es lo mismo que saber como construirlo |
| "Solo es un CRUD" | Validaciones, permisos, edge cases, migraciones — nunca es "solo" un CRUD |
| "Ya empece a codear" | Codigo sin diseno es deuda tecnica desde el dia 1 |

Entrada: interpreta el resto del prompt del usuario como argumento de la skill.
