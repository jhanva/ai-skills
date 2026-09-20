---
name: optimize
description: >
  Audita un flujo de trabajo para reducir contexto, latencia, costo y delegacion innecesaria.
  Usar cuando el usuario pide optimizar el trabajo del agente o diagnosticar consumo excesivo.
disable-model-invocation: true
---

# Optimize - Eficiencia de trabajo

## Diagnostico

1. Identificar lecturas repetidas, output ruidoso, pasos seriales independientes y delegaciones
   cuyo costo supera su valor.
2. Medir cuando haya datos disponibles; no inventar ahorros.
3. Proponer cambios pequenos y reversibles, ordenados por impacto.

## Principios

- Filtrar output antes de incorporarlo al contexto, conservando errores y evidencia relevante.
- Leer indices y rangos puntuales antes de archivos completos.
- Delegar solo tareas independientes, acotadas y con un resultado claramente especificado.
- Elegir capacidades segun complejidad y riesgo con los modelos realmente disponibles en el
  runtime; no asumir nombres o tiers.
- Mantener la verificacion en el agente coordinador.

Ejemplo de salida filtrada:

```bash
npm test 2>&1 | grep -A 5 -E '(FAIL|ERROR|error:)' | head -100
```

El resultado debe separar observaciones, propuesta, beneficio esperado y riesgo. Esta skill es
una auditoria explicita; no se carga automaticamente en cada interaccion.
