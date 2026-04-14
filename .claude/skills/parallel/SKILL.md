---
name: parallel
description: >
  Despacha multiples subagentes simultaneos para resolver problemas independientes.
  Solo cuando los problemas no se afectan entre si.
when_to_use: >
  Cuando hay 3+ tests fallando con causas diferentes, multiples subsistemas
  rotos independientemente, o tareas de investigacion que no se solapan.
argument-hint: "[descripcion de problemas o 'auto' para analizar tests]"
disable-model-invocation: true
---

# Parallel — Agentes paralelos para problemas independientes

## Cuando SI usar

- 3+ archivos de test fallando con causas raiz DIFERENTES
- Multiples subsistemas rotos de forma INDEPENDIENTE
- Investigacion en areas distintas del codebase
- Fixes en modulos sin dependencias compartidas

## Cuando NO usar

- Los fallos estan relacionados (un cambio rompio varias cosas)
- Los agentes modificarian los mismos archivos
- Se necesita estado completo del sistema
- Las tareas tienen dependencias secuenciales

## Proceso

### 1. Identificar dominios independientes

```
6 tests fallan en 3 archivos:

Dominio A: auth/login.test.ts (2 tests) — error de validacion
Dominio B: api/users.test.ts (3 tests) — error de serializacion
Dominio C: db/migrations.test.ts (1 test) — schema desactualizado

Verificacion: A no importa de B/C? B no importa de A/C? -> Independientes
```

### 2. Crear prompts enfocados

Cada subagente recibe prompt:

- **Enfocado**: un dominio, un problema
- **Auto-contenido**: todo el contexto incluido
- **Especifico en output**: que debe reportar
- **Acotado**: que archivos puede y NO puede tocar

```
Eres un agente enfocado en [DOMINIO].

Problema: [descripcion]
Archivos relevantes: [lista]
Archivos que NO debes modificar: [lista]

Tarea:
1. Investiga causa raiz en [archivos]
2. Implementa fix con TDD (test que falla -> fix -> verificar)
3. Ejecuta solo tus tests: [comando]

Reporta: causa raiz, fix aplicado, tests que pasan, archivos modificados
```

### 3. Despachar en paralelo

Usar multiples Agent tool calls en UN SOLO mensaje:

```
Agent(dominio_A, prompt_A)
Agent(dominio_B, prompt_B)
Agent(dominio_C, prompt_C)
```

### 4. Integrar resultados

- Leer cada reporte
- **NO confiar ciegamente** — verificar con `/verify`
- Ejecutar suite COMPLETA desde sesion principal
- Si hay conflictos (dos agentes tocaron mismo archivo), resolver manualmente
- Reportar resultado consolidado

## Errores comunes

| Error | Correccion |
|---|---|
| Prompt demasiado amplio | Limitar a un dominio y archivos especificos |
| Sin contexto | Incluir: error, archivos, comandos de test |
| Sin restricciones | Decir que archivos NO tocar |
| Output vago | Pedir estructura: causa, fix, evidencia |
| Confiar en reportes | SIEMPRE verificar con suite completa |

## Argumento: $ARGUMENTS
