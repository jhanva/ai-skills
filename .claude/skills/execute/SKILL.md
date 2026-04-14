---
name: execute
description: >
  Ejecuta un plan de implementacion despachando un subagente fresco por tarea
  con revision de 2 etapas: cumplimiento de spec y calidad de codigo.
when_to_use: >
  Despues de crear un plan con /plan, cuando el usuario dice "ejecutar",
  "implementar el plan", "correr el plan".
argument-hint: "[ruta al plan]"
disable-model-invocation: true
---

# Execute — Ejecucion con subagentes

## Proceso

### Paso 1: Cargar plan

- Leer el documento de plan completo
- Revisar criticamente: tiene sentido? Pasos claros? Gaps?
- Si hay problemas, reportar ANTES de ejecutar
- Si no hay plan: "Primero usa `/plan` para crear un plan"

### Paso 2: Extraer tareas

Extraer el texto completo de cada tarea. Cada subagente recibe el texto literal — nunca la ruta al archivo del plan. Esto ahorra tokens de lectura de archivos.

### Paso 3: Ejecutar tarea por tarea

Para cada tarea, en orden secuencial (NUNCA en paralelo):

#### 3a. Despachar implementador

Crear subagente con Agent tool:

```
Eres un implementador enfocado. Tu unica tarea:

[TEXTO COMPLETO DE LA TAREA]

Reglas:
- Sigue los pasos EXACTAMENTE
- Primero test (RED), verifica que falla
- Implementa lo minimo (GREEN)
- Ejecuta TODOS los tests
- Haz commit con el mensaje indicado
- Si algo no esta claro, REPORTA en vez de adivinar

Reporta resultado:
- DONE: todo segun el plan
- DONE_CON_NOTAS: funciona pero hay observaciones
- NECESITO_CONTEXTO: falta informacion
- BLOQUEADO: no puedo completar, [razon]
```

Consulta [model-selection.md](model-selection.md) para elegir el modelo correcto.

#### 3b. Manejar resultado

- **DONE**: Proceder a revision
- **DONE_CON_NOTAS**: Leer notas, decidir si requieren accion
- **NECESITO_CONTEXTO**: Proporcionar contexto y re-despachar
- **BLOQUEADO**: Evaluar, reportar al usuario si no se resuelve

### Paso 4: Revision de 2 etapas (despues de cada tarea)

#### Etapa 1 — Spec

- Cada requerimiento esta implementado?
- Comportamiento coincide con lo especificado?
- No se agrego nada extra? (over-building)
- No falto nada? (under-building)

**No confiar en el reporte del implementador. Leer el codigo.**

#### Etapa 2 — Calidad

- Tests cubren happy path y error cases
- Sin codigo duplicado innecesario
- Nombres descriptivos
- Sin vulnerabilidades (injection, XSS, secrets hardcodeados)
- Sigue patrones del proyecto

Si hay problemas criticos, crear tarea de correccion ANTES de continuar.

### Paso 5: Completar

- Ejecutar suite de tests completa desde sesion principal
- Ejecutar linter si existe
- Reportar con evidencia (usa `/verify`)

## Reglas de seguridad

- **NUNCA** ejecutar en main/master — crear branch de feature primero
- **NUNCA** despachar subagentes en paralelo — las tareas tienen dependencias
- **NUNCA** saltar revisiones para "ir mas rapido"
- **NUNCA** dejar que el subagente lea el plan completo (desperdicia tokens)

## Argumento: $ARGUMENTS
