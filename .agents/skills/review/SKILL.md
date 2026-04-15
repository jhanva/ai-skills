---
name: review
description: Realiza code review estructurado o ayuda a procesar feedback de review con criterio técnico. Úsala cuando el usuario pida explícitamente revisar cambios o responder observaciones. No la uses como reemplazo de verificación de comandos o de diseño inicial.
---

# Review — Code review estructurado

## Uso en Codex

- Esta skill está pensada para invocación explícita con `$review`.
- Cuando aquí se indique buscar patrones, usa `rg -n`; para listar archivos, usa `rg --files` o `find`; para leer fragmentos concretos, usa `sed -n`.
- Cuando aquí se hable de subagentes, usa los agentes integrados de Codex o los definidos en `.codex/agents/`, y solo delega si el usuario pidió paralelismo o delegación.
## Modo 1: Solicitar review

Despachar el agente `reviewer` de `.codex/agents/` con contexto preciso. Si no esta disponible, usar un `explorer` o `worker` en modo read-only con estas mismas instrucciones:

```
Eres un code reviewer senior. Revisa los cambios entre [BASE_SHA] y [HEAD_SHA].

Contexto: [que se implemento y por que]

Revisa:
1. Cumplimiento de spec: cada requerimiento implementado? Falta? Sobra?
2. Calidad: nombres claros, sin duplicacion, patrones consistentes
3. Testing: happy path + error cases, sin testear mocks
4. Seguridad: sin secrets, sin injection, inputs validados
5. Produccion: manejo de errores en boundaries, sin console.log de debug

Output:
## Fortalezas
- [lo que esta bien]

## Issues
### Critico (bloquea merge)
- [archivo:linea] Descripcion

### Importante (arreglar antes de merge)
- [archivo:linea] Descripcion

### Menor (nice to have)
- [archivo:linea] Descripcion

## Evaluacion
APROBADO / APROBADO_CON_CAMBIOS / CAMBIOS_REQUERIDOS
```

Para obtener SHAs: `git log --oneline -5` y `git rev-parse HEAD`

## Modo 2: Recibir review

```
LEER feedback completo
  -> ENTENDER que se pide
    -> VERIFICAR tecnicamente: tiene razon?
      -> EVALUAR: aplica a este contexto?
        SI -> Implementar
        NO -> Explicar por que no, con evidencia
```

### Respuestas prohibidas

- "Tienes toda la razon!" (sin verificar)
- "Gran punto!" (sycophancy)
- "Deja lo implemento ya" (sin verificar si aplica)

### Antes de implementar feedback

1. **Correcto tecnicamente?** Verificar en el codigo
2. **Aplica a este contexto?** El reviewer puede no tener todo el contexto
3. **Pasa YAGNI?** Si sugiere "implementar bien" algo, buscar si se usa: `rg -n "funcion" src/`
4. **Rompe algo?** Pasan los tests despues del cambio?

### Orden de implementacion

1. Issues criticos (bloqueantes)
2. Fixes simples (typos, nombres, imports)
3. Cambios complejos (refactors)

### Cuando rechazar feedback

- Rompe funcionalidad existente que el reviewer desconoce
- Ya se evaluo y descarto (explicar por que)
- Viola YAGNI: complejidad para caso inexistente
- Es tecnicamente incorrecto (mostrar evidencia)

Rechazar con evidencia tecnica, nunca con opinion.

## Entrada esperada

Toma del prompt del usuario cualquier ruta, modo o contexto adicional que acompañe a la invocacion de la skill.
