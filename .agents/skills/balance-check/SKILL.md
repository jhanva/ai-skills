---
name: balance-check
description: >-
  Validar balance de sistemas de juego: generar tabla de escenarios, validar ratios
  (damage-to-HP, gold-to-item, XP-to-level), identificar outliers y breakpoints. Recomienda
  ajustes con valores concretos. Output en conversacion. Usala cuando Despues de definir
  formulas de combate/economia/progresion, o cuando el usuario dice "balance", "los numeros
  no cuadran", "damage feels off", "balance-check", "validar formulas", "testear
  escenarios".
---

# Balance Check

Validar matematicamente que los sistemas (combate, economia, progresion) estan balanceados. Generar escenarios, identificar outliers y breakpoints, recomendar ajustes con valores concretos. Output: reporte en conversacion (NO archivo).

## FASE 1: Identificar sistema a balancear

Del argumento o buscando GDDs existentes en `design/gdd/`. Si no hay formulas definidas: ERROR — balance check requiere formulas matematicas.

## FASE 2: Leer GDDs relevantes

Extraer: formulas (damage, XP, gold), stats base y scaling, valores de items/enemigos/levels, constraints declarados.

## FASE 3: Generar tabla de escenarios

Crear matriz cross-level y cross-enemy. Ejecutar calculos con script Python inline.

Para combate: player levels [1, 10, 25, 50] × enemy levels [1, 10, 25, 50]. Calcular: damage player→enemy, hits to kill, damage enemy→player, hits to die, ratio.

Para economia: gold/battle, item cost por tier, battles to buy, XP/battle, XP to level, battles to level.

## FASE 4: Validar ratios

### Combate balanceado
- **Same level** (player = enemy): ratio hits_to_die/hits_to_kill ≈ 1.5-2.0
- **Over-leveled** (+5): ratio > 3.0 (player domina)
- **Under-leveled** (-5): ratio < 1.0 (peligroso pero posible)
- **Boss** (enemy +5): ratio ≈ 0.8-1.2 (requiere estrategia)

### Economia balanceada
- Gold/battle ÷ item cost ≈ 5-7 battles para item tier-apropiado
- XP/battle ÷ XP to level ≈ 10-15 battles por nivel
- Heal cost / damage per battle < 1.0 (curarse es viable)

### Outliers
Valores fuera de rango esperado. Dar valor actual vs esperado y recomendacion concreta (que cambiar y a cuanto).

### Breakpoints
Niveles donde el balance cambia drasticamente. Investigar causa (scaling no-lineal, equipment tier jump, skill unlock). Si es intencional (power spike): OK. Si no: suavizar curva.

## FASE 5: Validar economia (si aplica)

Si el sistema incluye gold/items: generar tabla de escenarios economicos, validar ratios, detectar early game problemas (primer item demasiado caro?) y late game grind.

## FASE 6: Generar recomendaciones

Priorizar:
- **CRITICO** (rompe el juego): causa, fix con valores concretos, impacto
- **ALTO** (afecta experiencia): causa, fix, impacto
- **MEDIO** (mejora QoL): causa, fix opcional, impacto

Todos los ajustes son en design docs y data files. Siempre re-correr balance-check despues de cambios.

## FASE 7: Output

Reporte en conversacion: formulas analizadas, escenarios generados (tabla), outliers, breakpoints, recomendaciones priorizadas, siguientes pasos.

## Anti-patrones

- **Balancear sin formulas** → pure guessing, no hay nada que validar
- **Solo escenarios "felices"** (same level) → no descubre edge cases
- **No documentar breakpoints** → power spikes sorprenden meses despues
- **Recomendaciones vagas** ("ajustar ATK") → dar valores concretos
- **No re-validar** despues de ajustar → fix puede crear nuevos outliers
- **Solo numeros, no playtest** → balance check es validacion matematica, playtest es la final
