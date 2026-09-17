---
description: Un bug reportado debe activar debug e investigar causa raiz antes de proponer fix
tags: [debug, contextual]
max_turns: 8
allowed_tools: [Read, Glob, Grep, Skill]
expected_outcome: Pide o describe reproduccion, lee el stacktrace completo, formula hipotesis; no propone try/except ni un parche a ciegas
---

El test `test_login_returns_token` empezo a fallar con `KeyError: 'user_id'` en `auth/handler.py` linea 42, dentro de `build_session(payload)`. Ayer pasaba. Arreglalo.
