# Anti-patrones de testing

## 1. Testear el mock en vez del codigo

**Sintoma:** Tu test verifica que `mockDB.save()` fue llamado con ciertos argumentos.

**Problema:** Estas testeando que tu mock funciona, no que tu codigo funciona. Si la firma de la DB real cambia, tu test sigue pasando.

**Solucion:** Testea contra una DB real, un in-memory store, o un container de test. Solo mockea lo que esta fuera de tu control (APIs externas, servicios de terceros).

## 2. Metodos solo-para-test en produccion

**Sintoma:** Agregas `_getInternalState()` o `@VisibleForTesting` para que un test pueda verificar estado interno.

**Problema:** Tu diseno esta exponiendo internos. Estos metodos se convierten en API publica de facto.

**Solucion:** Refactoriza para que el estado sea observable via la API publica. Si no puedes, tu abstraccion esta mal partida.

## 3. Mocks incompletos

**Sintoma:** Mockeas un servicio solo para el happy path.

**Problema:** Tu codigo maneja errores, timeouts y datos vacios, pero tus mocks nunca los producen. Falsa confianza.

**Solucion:** Si mockeas, mockea TODOS los comportamientos que tu codigo maneja: respuesta exitosa, error, timeout, datos vacios, datos malformados.

## 4. Tests de integracion como ocurrencia tardia

**Sintoma:** Todos los unit tests pasan pero el sistema falla cuando los componentes se conectan.

**Problema:** Nunca testeaste que los componentes se comunican correctamente.

**Solucion:** Escribe tests de integracion DURANTE el desarrollo, no al final. Testea los contratos entre componentes.

## 5. Tests que dependen de orden de ejecucion

**Sintoma:** Un test pasa solo pero falla en suite (o viceversa).

**Problema:** Hay estado compartido entre tests (archivos, DB, variables globales).

**Solucion:** Cada test crea su propio estado y lo limpia. Usa setup/teardown. Si sospechas contaminacion, bisecciona: corre mitad de la suite + el test que falla, repite hasta aislar el contaminante.
