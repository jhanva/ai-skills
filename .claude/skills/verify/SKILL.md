---
name: verify
description: >
  Verifica con evidencia fresca antes de cualquier claim de exito.
  Prohibido decir "listo" sin ejecutar verificacion y leer el output.
when_to_use: >
  Antes de reportar tarea completada, decir que tests pasan, que un bug
  esta arreglado, hacer commit, crear PR, o cualquier afirmacion de exito.
  Tambien cuando el usuario dice "verifica", "confirma", "esta listo?".
argument-hint: "[que verificar]"
---

# Verify — Verificacion antes de completar

## Ley de hierro

**PROHIBIDO decir que algo funciona sin ejecutar la verificacion y leer el output completo.** "Deberia funcionar" no es evidencia. Solo cuenta output real de un comando ejecutado AHORA.

## Proceso obligatorio

```
IDENTIFICAR comando de verificacion
  -> EJECUTAR (fresco, completo)
    -> LEER output completo
      -> EVALUAR: confirma exito?
        SI -> Reportar CON evidencia
        NO -> Reportar fallo, NO declarar exito parcial
```

## Que requiere cada claim

| Claim | Verificacion requerida |
|---|---|
| "Los tests pasan" | Ejecutar suite completa, mostrar output |
| "El linter esta limpio" | Ejecutar linter, mostrar 0 errores |
| "El build compila" | Ejecutar build, mostrar exito |
| "El bug esta arreglado" | Ejecutar caso que fallaba, mostrar que funciona |
| "La feature funciona" | Tests + demo manual si aplica |
| "No hay regresiones" | Suite completa, comparar con baseline |

## Senales de alerta en tu lenguaje

Si te descubres diciendo alguna de estas frases, DETENTE y verifica:

- "Deberia funcionar"
- "Probablemente esta bien"
- "Parece que pasa"
- "No deberia haber problemas"
- "Estoy seguro de que..."

Cualquier expresion de confianza SIN output de comando que la respalde = no verificado.

## Subagentes

- **NUNCA** confiar en el reporte de exito de un subagente sin verificar
- Despues de que un subagente reporta "completado", ejecutar verificaciones desde la sesion principal
- Si no puedes verificar, di explicitamente: "No pude verificar porque [razon]. El subagente reporta exito pero no tengo evidencia independiente"

## Argumento: $ARGUMENTS
