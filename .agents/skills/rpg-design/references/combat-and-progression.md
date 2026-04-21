# RPG Design — Combat and Progression

Lee este archivo solo cuando disenes formulas o curvas.

## Stats

Regla util: cada stat debe afectar al menos dos decisiones o sistemas, o probablemente sobra.

Ejemplos comunes:

- `HP`
- `ATK`
- `DEF`
- `SPD`
- `MATK`
- `MDEF`

## Formulas de dano

Objetivos:

- base predecible
- varianza pequena
- defensa relevante
- escalamiento controlado

Baseline frecuente:

```text
raw_damage = ATK * skill_multiplier - DEF * mitigation_factor
final_damage = max(1, floor(raw_damage * variance))
```

## Multiplicadores

Usar rangos acotados ayuda a evitar explosiones:

- elemental weakness: normalmente 1.5x-2x
- elemental resist: normalmente 0.25x-0.5x
- crit: normalmente 1.5x-2x

## Progression

Decide:

- curva por nivel
- caps
- scaling por clase o arquetipo

Valida siempre varios checkpoints, por ejemplo `lv1`, `lv10`, `lv25`, `lv50`.

## Economia

Comprueba al menos:

- XP por nivel
- rewards por encounter
- costo de items por tier
- anti-grinding

Una heuristica util: un item tier-apropiado no deberia requerir ni una pelea ni cincuenta; define un rango explicito.
