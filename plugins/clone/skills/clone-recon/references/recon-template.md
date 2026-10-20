# Recon: <app> (<android | windows>)

Corte: <lo que se reconstruye>
Para: <quien usa el clon>
Fecha: <AAAA-MM-DD>
Identificador: <paquete | proceso | titulo de ventana>

## Fuentes

| # | fuente | URL | notas |
| --- | --- | --- | --- |
| 1 | app instalada | - | capturas en clone/captures/original/ |

## Flujo principal

<una frase: lo que hace util a la app>

## Pantallas

Ver `screens.csv`. Total: <n> pantallas, <n> estados capturados, <n> solo features.

## Flujos

Ver `flows.csv`. Casos edge por flujo:

- F01 <nombre>: <casos edge>

## Componentes

| componente | variantes | estados | pantallas |
| --- | --- | --- | --- |
| Boton | primario, secundario, icono | normal, deshabilitado, cargando | S01, S03 |

## Modelo de datos inferido

```
<Entidad>  <campos>
           evidencia: <SIDs, articulos de ayuda>
           confianza: alta | media | supuesto
```

Relaciones: <Usuario 1-n Nota, Nota n-n Etiqueta, ...>

## Features

Ver `features.csv`. must: <n>, should: <n>, could: <n>, skip: <n>.

## Fuera de alcance

- <contenido licenciado, red de usuarios, datos del servidor, hardware, ...>

## Tamano

Pantallas <n>, flujos <n>, entidades <n>. Partes dificiles: <3>. Tamano: <S | M | L | XL>.
