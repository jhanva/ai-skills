---
name: brainstorm
description: Guía diseño riguroso antes de implementar una feature o cambio no trivial. Úsala cuando el usuario quiera explorar enfoques, escribir una spec o diseñar antes de codificar. No la uses para cambios ya definidos o para preguntas puramente operativas.
---

# Brainstorm — Diseno antes de implementar

## Uso en Codex

- Esta skill esta pensada para invocacion explicita con `$brainstorm`.
- Trabaja con lecturas puntuales: `rg -n` para buscar, `rg --files` o `find` para listar, y `sed -n` para leer solo el fragmento necesario.
- Si falta contexto menor, asume una opcion razonable y dejala explicita; pregunta solo por bloqueos reales o tradeoffs con consecuencias.
- Delega solo si el usuario pidio paralelismo o delegacion.
## Regla absoluta

**PROHIBIDO implementar sin diseno aprobado.** Todo proyecto pasa por este proceso sin importar que tan "simple" parezca. La complejidad oculta se descubre aqui, no en produccion.

## Proceso

### Fase 1: Entender el problema

Aclara solo lo que sea bloqueante para disenar bien:

- Que problema se resuelve y para quien
- Que restricciones existen (tecnologia, tiempo, infraestructura)
- Que ya se intento o se descarto
- Cuales son los criterios de exito

Si ya puedes proponer una spec util con supuestos razonables, hazlo y marca los supuestos. Si necesitas preguntar, usa 1-3 preguntas concretas y, cuando ayude, ofrece opciones cerradas:

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

Cuando la spec ya este cerrada, transiciona directo a `$plan` o deja claro que ya esta lista para planificar.

## Anti-patrones

| Excusa | Por que es invalida |
|---|---|
| "Es muy simple para disenar" | Los bugs mas caros nacen de suposiciones no examinadas |
| "Ya se que quiero" | Saber que quieres no es lo mismo que saber como construirlo |
| "Solo es un CRUD" | Validaciones, permisos, edge cases, migraciones — nunca es "solo" un CRUD |
| "Ya empece a codear" | Codigo sin diseno es deuda tecnica desde el dia 1 |

## Entrada esperada

Toma del prompt del usuario cualquier ruta, modo o contexto adicional que acompañe a la invocacion de la skill.
