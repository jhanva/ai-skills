---
type: llm
weight: 2
---

PASS si la respuesta presenta un test (pytest/unittest) ANTES de la implementacion de `parse_duration`, indica que ese test debe fallar primero, y la implementacion aparece despues como paso separado.
FAIL si entrega la implementacion sin test, si el test aparece solo despues del codigo como anadido, o si no menciona verificar que el test falla antes de implementar.
