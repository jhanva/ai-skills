---
name: plan
description: Convierte una spec aprobada en un plan de implementación concreto, pequeño y ejecutable, sin placeholders. Úsala cuando el usuario pida explícitamente planificar una solución ya diseñada. No la uses para brainstorming ni para programar sin diseño aprobado.
---

# Plan — Spec a plan de implementacion

## Uso en Codex

- Esta skill esta pensada para invocacion explicita con `$plan`.
- Trabaja con lecturas puntuales: `rg -n` para buscar, `rg --files` o `find` para listar, y `sed -n` para leer solo el fragmento necesario.
- Si falta contexto menor, asume una convencion razonable y dejala explicita; pregunta solo si faltan datos que cambian el plan.
- Delega solo si el usuario pidio paralelismo o delegacion.
## Regla absoluta

**CERO PLACEHOLDERS.** Cada paso tiene codigo real, comandos reales, y output esperado real. El plan debe ser ejecutable por alguien sin contexto del codebase.

## Proceso

### Paso 1: Cargar y validar spec

- Lee el documento de spec completo
- Verifica que esta aprobada y completa
- Si no hay spec: "Primero usa `$brainstorm` para crear una spec"

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

**Paso 5 — Cierre de la tarea:**
[verificacion final, riesgos restantes y siguiente paso]
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

### Paso 5: Transicion

Cierra con el siguiente paso recomendado:

- si el usuario quiere implementacion a partir de este plan, continuar con `$execute`
- si el plan necesita ajuste, marcar que puntos revisar antes de ejecutar

## Reglas de calidad

- Nombres de variables y funciones consistentes en todo el plan
- Cada test testea UN comportamiento con nombre descriptivo
- Si el usuario pidio commits atomicos, proponer un commit por tarea o por grupo coherente
- Si hay mas de 10 tareas, agrupa en fases logicas

## Entrada esperada

Toma del prompt del usuario cualquier ruta, modo o contexto adicional que acompañe a la invocacion de la skill.
