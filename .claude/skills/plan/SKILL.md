---
name: plan
description: >
  Convierte una spec aprobada en un plan de implementacion con tareas de 2-5 minutos.
  Codigo exacto, rutas reales, cero placeholders.
when_to_use: >
  Despues de que una spec fue aprobada con /brainstorm, o cuando el usuario
  dice "planificar", "crear plan", "como implemento esto".
argument-hint: "[ruta a spec.md o descripcion]"
disable-model-invocation: true
---

# Plan — Spec a plan de implementacion

## Regla absoluta

**CERO PLACEHOLDERS.** Cada paso tiene codigo real, comandos reales, y output esperado real. El plan debe ser ejecutable por alguien sin contexto del codebase.

## Proceso

### Paso 1: Cargar y validar spec

- Lee el documento de spec completo
- Verifica que esta aprobada y completa
- Si no hay spec: "Primero usa `/brainstorm` para crear una spec"

### Paso 2: Mapear archivos

Antes de definir tareas, documenta el terreno:

```markdown
## Mapa de archivos
- Modificar: src/auth/login.ts (agregar validacion 2FA)
- Crear: src/auth/two-factor.ts (logica de 2FA)
- Crear: tests/auth/two-factor.test.ts
- Modificar: package.json (agregar: otplib)
```

### Paso 3: Definir tareas

Cada tarea sigue esta estructura:

```markdown
### Tarea N: [titulo descriptivo]

**Archivos:** crear/modificar [rutas exactas]

**Paso 1 — Test que falla:**
[codigo completo del test]

**Paso 2 — Verificar que falla:**
[comando exacto y output esperado]

**Paso 3 — Implementar:**
[codigo completo]

**Paso 4 — Verificar que pasa:**
[comando exacto y output esperado]

**Paso 5 — Commit:**
git add [archivos especificos]
git commit -m "[mensaje descriptivo]"
```

### Granularidad

Cada tarea es UNA sola accion:

- Instalar una dependencia
- Crear un modelo/tipo
- Implementar una funcion
- Agregar una ruta/endpoint
- Escribir test de un caso edge

Si una tarea necesita mas de 2 archivos de produccion (excluyendo tests), es demasiado grande — dividela.

### Paso 4: Auto-revision

- [ ] Cada requerimiento de la spec tiene al menos una tarea
- [ ] No hay placeholders (`...`, `// TODO`, `/* implementar */`)
- [ ] Los tipos/interfaces son consistentes entre tareas
- [ ] Los imports y rutas de archivo son correctos
- [ ] El orden de ejecucion es logico (dependencias primero)

### Paso 5: Ofrecer ejecucion

```
Plan listo con N tareas. Como quieres ejecutarlo?
a) Con subagentes (recomendado) — usa /execute
b) Paso a paso en esta sesion
c) Revisar/ajustar el plan primero
```

## Reglas de calidad

- Nombres de variables y funciones consistentes en todo el plan
- Cada test testea UN comportamiento con nombre descriptivo
- Commits atomicos: un commit por tarea
- Si hay mas de 10 tareas, agrupa en fases logicas

## Argumento: $ARGUMENTS
