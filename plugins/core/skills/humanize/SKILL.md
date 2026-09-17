---
name: humanize
description: >
  Humaniza texto generado por IA en español e inglés. Diagnostica patrones
  detectables (vocabulario, estructura, ritmo, tono) y los transforma para
  producir texto con voz natural. Dos modos: review (diagnóstico) y rewrite
  (transformación). Soporte nativo de español con marcadores específicos.
  Usar cuando: el usuario dice "humanizar", "suena a IA", "hazlo mas natural",
  o pide revisar/mejorar texto que parece generado por IA.
argument-hint: "[review|rewrite] [archivo o texto]"
disable-model-invocation: true
allowed-tools:
  - Read
  - Grep
  - Glob
  - Edit
  - Write
  - Agent
  - Bash(wc:*)
---

# Humanize — Texto con voz real

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

Argumento recibido: $ARGUMENTS

