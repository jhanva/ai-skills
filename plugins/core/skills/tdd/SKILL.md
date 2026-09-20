---
name: tdd
description: >
  Aplica RED-GREEN-REFACTOR a cambios de comportamiento comprobables.
  Usar al implementar features o bugs con una suite viable; no para docs, exploracion o cambios puramente mecanicos.
argument-hint: "[que se va a implementar]"
---

# TDD — Test-Driven Development

## Alcance

Para comportamiento nuevo o corregido, escribir primero una prueba que demuestre el fallo. Si el
entorno no permite una prueba automatizada razonable, acordar una verificacion reproducible y
explicar la limitacion. No forzar TDD sobre documentacion, configuracion declarativa sin harness,
prototipos descartables o cambios mecanicos sin comportamiento.

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

Entrada: interpreta el resto del prompt del usuario como argumento de la skill.
