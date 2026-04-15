---
name: execute
description: Ejecuta un plan aprobado tarea por tarea, con verificación independiente y, si aplica, subagentes de Codex. Úsala cuando el usuario pida explícitamente implementar un plan existente. No la uses si todavía no hay spec o plan claros.
---

# Execute — Ejecucion con subagentes

## Uso en Codex

- Esta skill está pensada para invocación explícita con `$execute`.
- Cuando aquí se indique buscar patrones, usa `rg -n`; para listar archivos, usa `rg --files` o `find`; para leer fragmentos concretos, usa `sed -n`.
- Cuando aquí se hable de subagentes, usa los agentes integrados de Codex o los definidos en `.codex/agents/`, y solo delega si el usuario pidió paralelismo o delegación.
## Proceso

### Paso 1: Cargar plan

- Leer el documento de plan completo
- Revisar criticamente: tiene sentido? Pasos claros? Gaps?
- Si hay problemas, reportar ANTES de ejecutar
- Si no hay plan: "Primero usa `$plan` para crear un plan"

### Paso 2: Extraer tareas

Extraer el texto completo de cada tarea. Cada subagente recibe el texto literal — nunca la ruta al archivo del plan. Esto ahorra tokens de lectura de archivos.

### Paso 3: Ejecutar tarea por tarea

Para cada tarea, en orden secuencial (NUNCA en paralelo):

#### 3a. Despachar implementador

Despachar un agente `task_implementer` de `.codex/agents/` cuando exista. Si no existe o no aplica, usar un `worker` con un prompt equivalente:

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
- Reportar con evidencia (usa `$verify`)

## Reglas de seguridad

- **NUNCA** ejecutar en main/master — crear branch de feature primero
- **NUNCA** despachar subagentes en paralelo — las tareas tienen dependencias
- **NUNCA** saltar revisiones para "ir mas rapido"
- **NUNCA** dejar que el subagente lea el plan completo (desperdicia tokens)

## Entrada esperada

Toma del prompt del usuario cualquier ruta, modo o contexto adicional que acompañe a la invocacion de la skill.
