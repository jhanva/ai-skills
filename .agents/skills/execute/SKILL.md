---
name: execute
description: Ejecuta un plan aprobado tarea por tarea, con verificación independiente y, si aplica, subagentes de Codex. Úsala cuando el usuario pida explícitamente implementar un plan existente. No la uses si todavía no hay spec o plan claros.
---

# Execute — Ejecucion de plan

## Uso en Codex

- Esta skill esta pensada para invocacion explicita con `$execute`.
- Trabaja con lecturas puntuales: `rg -n` para buscar, `rg --files` o `find` para listar, y `sed -n` para leer solo el fragmento necesario.
- Ejecuta localmente por defecto. Solo delega si el usuario pidio paralelismo o delegacion.
- Si falta contexto menor, usa el plan como fuente de verdad y explicita cualquier supuesto antes de tocar codigo.
## Proceso

### Paso 1: Cargar plan

- Leer el documento de plan completo
- Revisar criticamente: tiene sentido? Pasos claros? Gaps?
- Si hay problemas, reportar ANTES de ejecutar
- Si no hay plan: "Primero usa `$plan` para crear un plan"

### Paso 2: Extraer tareas

Extraer el texto completo de cada tarea. Si delegas, pasa el texto literal de la tarea; no mandes solo la ruta al plan.

### Paso 3: Ejecutar tarea por tarea

Para cada tarea, en orden secuencial (NUNCA en paralelo):

#### 3a. Resolver la tarea

Por defecto, ejecuta la tarea en la sesion principal. Si el usuario pidio delegacion, despacha `task_implementer` cuando exista; si no aplica, usa `worker` con un prompt equivalente:

```
Eres un implementador enfocado. Tu unica tarea:

[TEXTO COMPLETO DE LA TAREA]

Reglas:
- Sigue los pasos EXACTAMENTE
- Primero test (RED), verifica que falla
- Implementa lo minimo (GREEN)
- Ejecuta TODOS los tests
- No hagas commits salvo que el usuario lo haya pedido
- Si algo no esta claro, REPORTA en vez de adivinar

Reporta resultado:
- DONE: todo segun el plan
- DONE_CON_NOTAS: funciona pero hay observaciones
- NECESITO_CONTEXTO: falta informacion
- BLOQUEADO: no puedo completar, [razon]
```

Consulta [model-selection.md](model-selection.md) para elegir el modelo correcto.

#### 3b. Manejar resultado

Si trabajas localmente, pasa directo a la revision de la tarea. Si delegaste:

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
- **NUNCA** despachar subagentes en paralelo para el mismo plan — las tareas tienen dependencias
- **NUNCA** saltar revisiones para "ir mas rapido"
- **NUNCA** dejar que el subagente lea el plan completo (desperdicia tokens)
- **NUNCA** pedir a un subagente que haga commits sin autorizacion explicita

## Entrada esperada

Toma del prompt del usuario cualquier ruta, modo o contexto adicional que acompañe a la invocacion de la skill.
