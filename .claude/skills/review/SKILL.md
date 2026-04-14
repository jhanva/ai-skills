---
name: review
description: >
  Code review estructurado con severidades. Solicitar review con subagente
  revisor o manejar feedback recibido con evaluacion tecnica, no sycophancy.
when_to_use: >
  Despues de implementar una feature, antes de merge, cuando el usuario dice
  "review", "revisa", "revisar codigo", o cuando se recibe feedback de un reviewer.
argument-hint: "[SHA base o descripcion]"
disable-model-invocation: true
---

# Review — Code review estructurado

## Modo 1: Solicitar review

Despachar subagente revisor con contexto preciso:

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
3. **Pasa YAGNI?** Si sugiere "implementar bien" algo, buscar si se usa: `grep -r "funcion" src/`
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

## Argumento: $ARGUMENTS
