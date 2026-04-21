---
name: tdd
description: Impone RED-GREEN-REFACTOR al escribir o modificar código de producción. Úsala cuando la tarea implique implementación o fix con cambios de comportamiento. No la uses para trabajo read-only, documentación pura o planificación sin código.
---

# TDD — Test-Driven Development

## Uso en Codex

- Codex puede activar esta skill por contexto o puedes invocarla explicitamente con `$tdd`.
- Para buscar y leer codigo, prioriza `rg`, `rg --files` y lecturas puntuales con `sed -n` en lugar de escaneos completos.
- Trabaja localmente por defecto. Solo delega si el usuario pidio paralelismo o delegacion.
- Si falta contexto menor, define el comportamiento esperado antes de escribir el test y dejalo explicito.
## Ley de hierro

**PROHIBIDO escribir codigo de produccion sin un test que falle primero.** Si se escribio codigo antes del test, se borra y se empieza de nuevo. Sin excepciones.

## Ciclo obligatorio

### RED — Escribir test que falla

- UN solo test, UN solo comportamiento
- Nombre descriptivo: `test_login_fails_with_expired_token`
- Codigo real, no mocks (salvo APIs externas inevitables)
- Debe compilar/parsear sin errores de sintaxis

### VERIFICAR RED (obligatorio)

Ejecuta el test. Confirma que falla POR LA RAZON ESPERADA:

- Falla porque la funcion no existe = correcto
- Falla porque el assert no se cumple = correcto
- Falla por error de sintaxis = arregla el test primero
- Pasa inmediatamente = el test no testea nada, reescribelo

### GREEN — Implementar lo minimo

- SOLO el codigo necesario para que el test pase
- No agregues features adicionales
- No refactorices
- No "mejores" nada

### VERIFICAR GREEN (obligatorio)

Ejecuta TODOS los tests (no solo el nuevo):

- Todos pasan = continua
- Nuevo pasa pero otro fallo = arregla la regresion ANTES de continuar
- Output limpio, sin warnings relevantes

### REFACTOR — Solo despues de green

- Elimina duplicacion
- Mejora nombres
- Extrae helpers SI hay patron claro
- Despues de cada cambio, ejecuta tests de nuevo
- Si un test falla durante refactor, deshaz el cambio

## Anti-patrones

| Excusa | Respuesta |
|---|---|
| "Es muy simple para testear" | Los bugs mas tontos son los mas caros |
| "Testeo despues" | Despues nunca llega. Tests retrofit son peores |
| "Solo voy a agregar esta cosita" | Un test, un comportamiento. Otro test para la cosita |
| "Borrar codigo es desperdicio" | El desperdicio es debuggear sin tests durante horas |
| "Los mocks estan bien para todo" | Los mocks testean que tu mock funciona, no tu codigo |
| "TDD me hace mas lento" | Mas lento la primera hora, ahorra dias despues |

Consulta [testing-anti-patterns.md](testing-anti-patterns.md) para anti-patrones detallados de testing.

## Checklist final

- [ ] Cada funcion de produccion tiene al menos un test
- [ ] Todos los tests pasan con output limpio
- [ ] Tests cubren happy path Y al menos un caso de error
- [ ] No hay tests comentados o skipped

## Entrada esperada

Toma del prompt del usuario cualquier ruta, modo o contexto adicional que acompañe a la invocacion de la skill.
