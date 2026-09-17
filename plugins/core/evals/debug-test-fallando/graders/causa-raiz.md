---
type: llm
weight: 2
---

PASS si la respuesta investiga antes de arreglar: menciona revisar cambios recientes (git diff/log), rastrear de donde viene `payload` sin `user_id`, o formular una hipotesis concreta a verificar, y deja claro que el fix se aplica despues de confirmar la causa.
FAIL si propone directamente un fix como `payload.get('user_id')`, un try/except o un valor por defecto sin haber investigado por que falta la clave.
