---
description: Orchestrate debe activarse para disenar una delegacion manager-worker verificable
tags: [orchestrate, delegacion, contextual]
max_turns: 8
allowed_tools: [Read, Glob, Grep, Skill]
expected_outcome: Activa orchestrate y propone contratos acotados, routing por riesgo y resultados verificables
---

Tengo un agente principal costoso y workers mas economicos. Divide una implementacion modular entre
un manager y workers sin compartir todo el historial. Necesito routing por riesgo, limites de
archivos, resultados estructurados y una regla para evitar ciclos de reintentos.
