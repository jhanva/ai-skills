---
name: humanize
description: Diagnostica y reescribe texto para que suene menos artificial y más humano en español o inglés. Úsala cuando el usuario pida explícitamente humanizar, revisar o reescribir texto con voz más natural. No la uses para edición técnica menor sin foco en tono.
---

# Humanize — Texto con voz real

## Uso en Codex

- Esta skill esta pensada para invocacion explicita con `$humanize`.
- Trabaja con lecturas puntuales: `rg -n` para buscar, `rg --files` o `find` para listar, y `sed -n` para leer solo el fragmento necesario.
- Si falta contexto menor, infierelo por el propio texto y declaralo; pregunta solo si no tienes el contenido que debes revisar o reescribir.
- No delegues salvo que el usuario pida paralelismo o delegacion.

## Objetivo

Diagnosticar texto que suena artificial y, si el usuario lo pide, reescribirlo con una voz mas natural sin perder hechos, tono base ni intencion.

Los detectores suelen capturar uniformidad de ritmo, estructura formulaica y vocabulario predecible. La humanizacion efectiva corrige esos tres ejes; no se trata de meter typos ni sinonimos al azar.

## Modos

- `review` o sin argumento: detectar patrones de IA, explicar por que suenan artificiales y sugerir cambios.
- `rewrite`: devolver una reescritura completa, preservando el contenido.

## FASE 1: Cargar y clasificar

1. Resolver fuente:
   - si el prompt trae un archivo, leerlo
   - si el prompt trae el texto inline, usarlo
   - si no hay texto, pedirlo
2. Detectar idioma:
   - si es espanol o mixto, leer `references/es-markers.md`
   - si es ingles o mixto, leer `references/en-markers.md`
3. Detectar contexto y registro:
   - documentacion tecnica
   - informe o reporte
   - ensayo o articulo
   - email o mensaje
   - blog post
   - academico

## FASE 2: Diagnostico

Revisar siempre estos cinco ejes:

1. Vocabulario:
   - palabras comodin, frases formulaicas o adjetivos decorativos
2. Gramatica:
   - nominalizaciones, gerundios encadenados, voz pasiva innecesaria, conectores apilados
3. Estructura:
   - listas simetricas, aperturas que repiten la consigna, cierres tipo resumen, headers genericos
4. Ritmo:
   - parrafos y oraciones demasiado uniformes
5. Tono:
   - hedging vacio, balance forzado, entusiasmo generico, falta de voz propia

Si necesitas ejemplos concretos o listas detalladas, cargalos desde las referencias del idioma correspondiente.

## FASE 3: Reescritura o sugerencias

Lee `references/rewrite-patterns.md` cuando vayas a reescribir o a emitir el diagnostico final.

Reglas base:

1. Preservar hechos, intencion y restricciones del texto.
2. Variar la longitud de oraciones y parrafos.
3. Cambiar abstraccion hueca por detalle concreto cuando exista.
4. Reemplazar formalidad artificial por voz directa.
5. Mantener un registro consistente con el tipo de documento.

## FASE 4: Entrega

### Si estas en modo `review`

Entregar:

- score de naturalidad
- idioma y registro detectados
- hallazgos por vocabulario, gramatica, estructura, ritmo y tono
- sugerencias priorizadas por impacto

### Si estas en modo `rewrite`

Verificar:

- sin marcadores fuertes de IA
- sin nominalizaciones o gerundios innecesarios
- ritmo mas variado
- registro consistente
- hechos preservados

## Entrada esperada

Toma del prompt del usuario cualquier ruta, modo o contexto adicional que acompane a la invocacion de la skill.
