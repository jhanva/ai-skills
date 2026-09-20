---
name: secure
description: >
  Audita seguridad en proyectos locales: codigo, secretos, dependencias e infraestructura.
  Usar ante solicitudes de vulnerabilidades o antes de un deploy; admite modos quick y full.
argument-hint: "[quick|full] [ruta al proyecto]"
disable-model-invocation: true
allowed-tools:
  - Read
  - Grep
  - Glob
  - Agent
  - Bash(python:*)
  - Bash(python3:*)
  - Bash(py:*)
  - Bash(git diff:*)
  - Bash(git log:*)
  - Bash(git ls-files:*)
  - Bash(find:*)
  - Bash(wc:*)
  - Bash(which:*)
  - Bash(npm audit:*)
  - Bash(pip-audit:*)
  - Bash(cargo audit:*)
---

# Secure - Analisis de seguridad

## Contrato de solo lectura

No modificar, crear ni eliminar archivos del proyecto auditado. No ejecutar su aplicacion, no
instalar paquetes y no aplicar arreglos automaticos. Las herramientas de auditoria solo se usan
en modo de lectura. El unico output es el reporte de hallazgos.

## Alcance

- `quick`: archivos cambiados respecto a HEAD; si no hay cambios, ultimo commit.
- `full`: proyecto completo, excluyendo dependencias vendorizadas, caches y artefactos.

Usar la ruta indicada por el usuario o el directorio actual. Validar que exista. Detectar el stack
por sus manifests y cargar solo las referencias necesarias, resueltas desde esta skill:

- [secrets-patterns.md](references/secrets-patterns.md): siempre
- [code-patterns.md](references/code-patterns.md): codigo de aplicacion
- [infra-patterns.md](references/infra-patterns.md): Docker, CI o infraestructura

## Proceso

1. Enumerar archivos dentro del alcance y registrar exclusiones.
2. Ejecutar [scan-secrets.py](scripts/scan-secrets.py) con la ruta absoluta resuelta del script.
3. Revisar injection, autenticacion y autorizacion, criptografia, manejo de errores y datos
   sensibles con patrones adecuados al lenguaje.
4. Revisar permisos, pins, secretos y usuario efectivo en Docker, CI e infraestructura.
5. Consultar auditores de dependencias ya instalados, sin instalar ni actualizar nada.
6. Confirmar cada hallazgo en el archivo y linea antes de reportarlo.

En `full`, un proyecto mediano o grande puede dividirse entre especialistas de codigo,
infraestructura y dependencias, siempre en solo lectura y con alcances que no se solapen.

### Fallback sin subagente

Si no hay especialistas, el agente principal recorre esas tres areas en secuencia. Prioriza
secretos, superficies expuestas, autenticacion y configuracion de produccion; declara cualquier
zona no revisada por limites de tiempo o herramientas.

## Reporte

Ordenar por `CRITICO`, `ALTO`, `MEDIO` y `BAJO`. Cada hallazgo incluye:

- `archivo:linea`
- impacto y escenario explotable
- CWE y categoria OWASP cuando se puedan asignar con certeza
- correccion concreta

Cerrar con cantidades por severidad, modo, stack, numero de archivos y limitaciones. Si no hay
hallazgos, no afirmar seguridad absoluta: indicar que no se encontraron vulnerabilidades dentro
del alcance ejecutado.

Entrada: interpreta el resto del prompt del usuario como argumento de la skill.
