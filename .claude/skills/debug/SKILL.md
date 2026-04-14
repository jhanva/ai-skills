---
name: debug
description: >
  Debugging sistematico en 4 fases con investigacion de causa raiz obligatoria.
  Prohibido adivinar soluciones o aplicar fixes sin entender el problema.
when_to_use: >
  Cuando hay un bug, error, test fallando, comportamiento inesperado,
  o el usuario dice "no funciona", "falla", "error", "bug", "rompio".
argument-hint: "[descripcion del error o problema]"
---

# Debug — Debugging sistematico

## Ley de hierro

**PROHIBIDO aplicar fixes sin investigar la causa raiz.** Debugging sistematico: 15-30 min. Adivinar y probar: 2-3 horas.

## Fase 1: Investigar causa raiz

### 1. Leer el error COMPLETO
- Cada linea del stacktrace, no solo la primera
- Identificar: archivo, linea, tipo de error, mensaje
- Si hay errores encadenados (caused by), empezar por el mas profundo

### 2. Reproducir consistentemente
- Ejecutar el escenario que falla y confirmar
- Si es intermitente: condiciones de carrera, estado compartido, orden de ejecucion
- Documentar pasos exactos de reproduccion

### 3. Revisar cambios recientes
- `git diff` y `git log --oneline -10`
- Funcionaba antes = bug en cambios recientes
- No funcionaba antes = bug de integracion

### 4. Rastreo hacia atras (sistemas multi-componente)

Trazar el flujo de datos HACIA ATRAS desde el error:

```
Error en capa 5 (UI muestra "undefined")
  <- Capa 4 (API retorna null en campo X)
    <- Capa 3 (query no encuentra registro)
      <- Capa 2 (ID incorrecto)
        <- Capa 1 (formulario envia ID equivocado)  <-- CAUSA RAIZ
```

Consulta [root-cause-tracing.md](root-cause-tracing.md) para tecnica detallada.

### 5. Buscar ejemplos funcionales
- Hay casos similares que SI funcionan? Que es diferente?
- Hay tests existentes para este flujo?

## Fase 2: Analizar patrones

- Comparar caso que falla vs caso que funciona
- Identificar la diferencia MINIMA
- Buscar en el codebase: mismo patron en otros lugares? Tambien fallan?

## Fase 3: Hipotesis y prueba

1. Formular UNA hipotesis: "El bug ocurre porque X es null cuando se llama Y"
2. Disenar test minimo que pruebe o descarte la hipotesis
3. Ejecutar
4. Si es incorrecta, formular otra con la nueva evidencia
5. **Una sola variable a la vez** — cambios multiples invalidan el experimento

## Fase 4: Implementar fix

1. Escribir test que reproduce el bug (debe fallar = RED)
2. Implementar fix minimo — una sola correccion, no refactorizar de paso
3. Verificar que el test pasa Y no hay regresiones
4. Si el fix toca mas de un archivo: estoy arreglando sintoma o causa?

## Regla de los 3 intentos

> Si 3 fixes no resuelven el problema, **el problema es de arquitectura, no de implementacion.** Detente y replantea.

## Anti-patrones

| Excusa | Respuesta |
|---|---|
| "Ya se que es" | Si lo sabes, explicalo. Si no puedes explicarlo, no lo sabes |
| "Agrego un try-catch" | Eso esconde el bug, no lo arregla |
| "Funciona en mi maquina" | El bug es de ambiente — investigalo |
| "Voy a reescribir el modulo" | Encuentra el bug, arregla el bug. Despues refactoriza |
| "Es un bug del framework" | Verifica primero que no sea tu codigo |

## Argumento: $ARGUMENTS
