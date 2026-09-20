---
description: Execute debe completar un plan aun cuando el entorno no tenga subagentes
tags: [execute, fallback, explicito]
max_turns: 8
allowed_tools: [Read, Glob, Grep, Skill]
expected_outcome: Activa execute y explica que el agente principal ejecutara y verificara las tareas sin bloquearse
---

Usa /execute con `docs/plan.md`. En este entorno no hay subagentes disponibles; implementa el plan igualmente.
