# Seleccion de modelo para subagentes

Guia para elegir el modelo correcto al despachar subagentes implementadores. El objetivo es usar el modelo mas barato que pueda completar la tarea correctamente.

## Criterios

| Complejidad | Modelo | Cuando usar |
|---|---|---|
| Mecanica | `gpt-5.4-mini` | Tareas de 1-2 archivos: crear archivo desde template, agregar import, instalar dependencia, rename, agregar campo a un tipo |
| Moderada | `gpt-5.2` | Integracion entre modulos, logica de negocio con condiciones, refactors acotados, tests con setup complejo |
| Alta | `gpt-5.4` | Decisiones de arquitectura, diseno de APIs, reviews de calidad, debugging multi-capa, tareas que requieren entender contexto amplio |

## Reglas

- En caso de duda, sube un nivel de modelo. Es mas barato re-ejecutar con modelo fuerte que debuggear output de modelo debil
- Las revisiones de calidad (Paso 4 del proceso) siempre con `gpt-5.2` o superior
- Si un subagente con `gpt-5.4-mini` reporta BLOQUEADO o NECESITO_CONTEXTO, re-despacha con `gpt-5.2` antes de intervenir manualmente
- Si existe el agente custom `task_implementer`, prefiere usarlo para tareas de plan en lugar de improvisar instrucciones cada vez
