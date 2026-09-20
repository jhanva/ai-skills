---
name: review
description: >
  Revisa cambios con severidades, evidencia y evaluacion tecnica del feedback.
  Usar al terminar una feature, antes de merge o al recibir comentarios de revision.
argument-hint: "[SHA base o descripcion]"
disable-model-invocation: true
---

# Review - Revision estructurada

## Solicitar revision

Determinar el rango exacto con Git y aportar contexto sobre la intencion del cambio. Si existe un
especialista de revision de solo lectura, pedirle que inspeccione:

1. cumplimiento de requerimientos y ausencia de alcance extra
2. errores funcionales, regresiones y condiciones de borde
3. seguridad, validacion de entradas y manejo de errores
4. cobertura y calidad de las pruebas
5. consistencia con los patrones del proyecto

Cada issue debe incluir severidad, `archivo:linea`, impacto y correccion concreta. No reportar
preferencias estilisticas como defectos si no violan una regla verificable.

### Fallback sin subagente

Si no hay especialista, el agente principal hace una segunda lectura independiente del diff,
consulta las reglas del repo y ejecuta las pruebas relevantes. Mantiene el mismo formato y umbral
de evidencia.

## Formato

```markdown
## Issues
### Critico
- `archivo:linea` - impacto y correccion

### Importante
- `archivo:linea` - impacto y correccion

### Menor
- `archivo:linea` - mejora justificada

## Evaluacion
APROBADO | APROBADO_CON_CAMBIOS | CAMBIOS_REQUERIDOS
```

Si no hay issues, decirlo de forma explicita y mencionar cualquier riesgo o prueba no cubierta.

## Recibir feedback

1. Leer el feedback completo.
2. Verificarlo contra codigo, requisitos y pruebas.
3. Implementar lo correcto por prioridad: critico, simple, complejo.
4. Rechazar con evidencia lo que sea incorrecto, rompa comportamiento o agregue complejidad sin
   un caso real.
5. Volver a ejecutar las verificaciones afectadas.

Evitar asentir o editar antes de comprobar el comentario.

Entrada: interpreta el resto del prompt del usuario como argumento de la skill.
