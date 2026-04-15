---
name: verify
description: Exige verificación fresca con comandos reales antes de afirmar éxito, tests verdes o bug resuelto. Úsala antes de reportar que algo quedó listo. No la uses como sustituto de investigar la causa raíz o de escribir el cambio.
---

# Verify — Verificacion antes de completar

## Uso en Codex

- Codex puede activar esta skill por contexto o puedes invocarla explícitamente con `$verify`.
- Para buscar y leer código, prioriza `rg`, `rg --files` y lecturas puntuales con `sed -n` en lugar de escaneos completos.
- Si el flujo menciona subagentes, en Codex usa `worker`, `explorer` o un agente personalizado solo cuando la tarea realmente lo justifique.
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

## Entrada esperada

Toma del prompt del usuario cualquier ruta, modo o contexto adicional que acompañe a la invocacion de la skill.
