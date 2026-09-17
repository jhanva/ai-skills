# Rastreo de causa raiz

Tecnica de rastreo hacia atras a traves de la cadena de llamadas para encontrar donde los datos se corrompen o desaparecen.

## Proceso

1. **Empezar por el error visible** — el sintoma que el usuario ve
2. **Trazar hacia atras** — seguir el flujo de datos en reversa, capa por capa
3. **En cada capa, verificar**: los datos que entran son correctos? Los que salen?
4. **Encontrar el punto de quiebre** — la capa donde datos correctos entran y datos incorrectos salen

## Ejemplo real

```
Sintoma: UI muestra "NaN" en el total del carrito

Capa 5: Componente CartTotal recibe `total = NaN`
Capa 4: calculateTotal() retorna NaN
Capa 3: items.reduce((sum, item) => sum + item.price * item.qty, 0) => NaN
Capa 2: item.price es "19.99" (string, no number) para items del cache
Capa 1: el cache serializa a JSON y al deserializar no convierte price a number
         ^--- CAUSA RAIZ
```

Fix: parsear price a number al deserializar del cache. No en calculateTotal, no en el componente.

## Tips para stacktraces

- Lee de ABAJO hacia ARRIBA — el origen esta en las lineas mas profundas
- Ignora frames de librerias/frameworks — enfocate en tu codigo
- Si el stacktrace esta truncado, reproduce con mas verbosidad (`--verbose`, `DEBUG=*`, etc.)
- En errores async, busca la linea "at async" o "at processTicksAndRejections" — arriba de esa esta tu codigo

## Validacion en cada capa (defense in depth)

Cuando debuggeas un valor incorrecto, agrega validacion temporal en cada capa:

```javascript
// Capa 1: entrada
console.assert(typeof price === 'number', `price should be number, got ${typeof price}`);

// Capa 2: logica
if (isNaN(subtotal)) throw new Error(`subtotal is NaN for item ${item.id}`);

// Capa 3: salida
console.assert(Number.isFinite(total), `total should be finite, got ${total}`);
```

Despues de encontrar el bug, deja las validaciones que prevengan recurrencia y elimina las temporales.

## Esperas basadas en condicion

Para tests flaky por timeouts arbitrarios:

```javascript
// MAL — depende del timing
await sleep(5000);
expect(status).toBe('ready');

// BIEN — espera la condicion
await waitFor(() => getStatus() === 'ready', {
  timeout: 5000,
  interval: 100,
  message: 'El servicio no alcanzo estado ready'
});
```
