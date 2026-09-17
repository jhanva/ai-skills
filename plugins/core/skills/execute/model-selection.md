# Seleccion de modelo para subagentes

Guia para elegir el modelo correcto al despachar subagentes implementadores. El objetivo es usar el modelo mas barato que pueda completar la tarea correctamente.

## Criterios

| Complejidad | Modelo | Cuando usar |
|---|---|---|
| Mecanica | haiku | Tareas de 1-2 archivos: crear archivo desde template, agregar import, instalar dependencia, rename, agregar campo a un tipo |
| Moderada | sonnet | Integracion entre modulos, logica de negocio con condiciones, refactors acotados, tests con setup complejo |
| Alta | opus | Decisiones de arquitectura, diseno de APIs, reviews de calidad, debugging multi-capa, tareas que requieren entender contexto amplio |

## Reglas

- En caso de duda, sube un nivel de modelo. Es mas barato re-ejecutar con modelo fuerte que debuggear output de modelo debil
- Las revisiones de calidad (Paso 4 del proceso) siempre con sonnet o superior
- Si un subagente con haiku reporta BLOQUEADO o NECESITO_CONTEXTO, re-despacha con sonnet antes de intervenir manualmente
