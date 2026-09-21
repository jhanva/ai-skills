---
name: orchestrate
description: >
  Coordina un manager y workers especializados con routing por riesgo, contratos de tarea,
  resultados estructurados y escalamiento. Usar al delegar trabajo complejo o costoso.
---

# Orchestrate - Manager-worker verificable

## Objetivo

Delegar solo tareas con fronteras claras. El manager conserva contexto global, decisiones de
arquitectura, integracion y aceptacion. Los workers reciben el contexto minimo y autoridad
limitada.

## Roles

- **Manager:** descompone, puntua riesgo, entrega contratos, revisa e integra.
- **Explorer:** investiga en solo lectura y devuelve evidencia resumida.
- **Implementer:** modifica un alcance acotado y ejecuta las verificaciones indicadas.
- **Reviewer:** revisa en solo lectura; no corrige su propio hallazgo.

Los especialistas son opcionales. Si el runtime no permite delegar, el agente principal ejecuta
los mismos contratos uno por uno.

## Proceso

1. Confirmar que existe una spec o plan aprobado.
2. Separar decisiones globales de tareas delegables.
3. Crear un contrato por tarea con objetivo, rutas, restricciones y criterios medibles.
4. Puntuar riesgo con [harness.py](scripts/harness.py).
5. Ejecutar directamente o asignar el rol recomendado.
6. Exigir un sobre de resultado con evidencia fresca.
7. Leer el diff y verificar desde el manager; no confiar solo en el resumen.
8. Reintentar como maximo una vez con el error exacto y luego escalar.

## Contrato minimo

```json
{
  "task_id": "billing-create-invoice",
  "objective": "Crear factura en borrador con aislamiento por tenant.",
  "mode": "write",
  "allowed_paths": ["apps/web/src/modules/billing/**"],
  "forbidden_paths": ["packages/db/migrations/**"],
  "acceptance": ["typecheck pasa", "pruebas de billing pasan"],
  "commands": ["pnpm typecheck", "pnpm test --filter billing"],
  "risk_dimensions": {
    "ambiguity": 0,
    "coupling": 1,
    "blast_radius": 1,
    "verifiability": 0,
    "sensitivity": 1,
    "reversibility": 0
  },
  "max_attempts": 2,
  "expected_result": "result-envelope-v1"
}
```

Cada dimension usa valores 0, 1 o 2. Una sensibilidad de 2 siempre escala al manager. Una tarea
sin criterios de aceptacion verificables no se delega.

## Resultado requerido

El worker termina con una sola linea `RESULT_ENVELOPE:` seguida de JSON valido:

```text
RESULT_ENVELOPE: {"task_id":"billing-create-invoice","status":"passed","summary":"Implementado y verificado.","changed_files":["apps/web/src/modules/billing/create-invoice.ts"],"checks":[{"command":"pnpm typecheck","result":"passed"}],"assumptions":[],"risks":[],"out_of_scope":[]}
```

Estados validos: `passed`, `failed`, `blocked` y `partial`. `partial` o `blocked` nunca se
convierten en `passed` mediante un resumen narrativo.

## Paralelismo

- Paralelizar lectores independientes.
- Mantener un solo escritor por checkout.
- Usar workspaces aislados para escritores concurrentes.
- No asignar rutas superpuestas.
- Ejecutar la suite integrada despues de combinar resultados.

## Escalamiento

Escalar inmediatamente cuando hay decisiones abiertas de arquitectura, cambios destructivos,
seguridad, autorizacion, datos sensibles, contratos entre modulos o ausencia de una prueba
confiable.

## Fallback sin subagente

El agente principal conserva el contrato, ejecuta la tarea localmente y produce el mismo sobre de
resultado. La falta de workers nunca elimina las validaciones ni permite ampliar el alcance.

Entrada: interpreta el resto del prompt del usuario como el trabajo que se debe orquestar.
