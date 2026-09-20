---
name: execute
description: >
  Ejecuta un plan aprobado por tareas, con verificacion de cumplimiento y calidad.
  Usar cuando existe un plan y el usuario pide implementarlo.
argument-hint: "[ruta al plan]"
disable-model-invocation: true
---

# Execute - Ejecucion de planes

## Preparar

1. Leer el plan completo y comprobar que sus rutas y dependencias siguen vigentes.
2. Reportar antes de editar cualquier ambiguedad que cambie alcance o arquitectura.
3. Extraer cada tarea con sus criterios, archivos, pruebas y dependencias.
4. Confirmar una rama de trabajo segura segun las reglas del proyecto.

Si no existe un plan util, detenerse y proponer la skill `plan`.

## Ejecutar

Procesar primero las dependencias. Las tareas independientes pueden correr en paralelo solo si
no comparten archivos ni estado. Para cada tarea:

1. Entregar al implementador el texto de la tarea y el contexto minimo necesario.
2. Aplicar RED-GREEN-REFACTOR cuando cambia comportamiento y es viable probarlo.
3. Leer el diff; no confiar solo en el resumen del implementador.
4. Revisar cumplimiento de la spec, calidad, seguridad y pruebas.
5. Corregir bloqueantes antes de avanzar a una tarea dependiente.

Un especialista de implementacion disponible puede encargarse de una tarea acotada. El agente
coordinador conserva la responsabilidad de integrar y verificar el resultado.

### Fallback sin subagente

Si el entorno no ofrece especialistas, el agente principal ejecuta cada tarea directamente con
el mismo orden, limites de archivos y revisiones. La ausencia de subagentes nunca bloquea el plan.

## Verificar y cerrar

- Ejecutar las pruebas especificas y luego la suite completa relevante.
- Ejecutar lint, build o validadores del repo cuando existan.
- Comparar el resultado final contra todos los criterios del plan.
- Reportar comandos, resultados, archivos cambiados y limites pendientes.
- Usar la skill `verify` antes de afirmar que el trabajo esta listo.

Entrada: interpreta el resto del prompt del usuario como argumento de la skill.
