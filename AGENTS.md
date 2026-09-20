# Reglas de trabajo - ai-skills

Estas reglas aplican a todo el repositorio desde Claude Code y Codex. El flujo detallado de
ramas, commits, pull requests y versiones vive en [docs/repo-workflow.md](docs/repo-workflow.md).

## Alcance

- Trabajar en espanol. El texto del repositorio se escribe sin tildes ni enes, segun la
  convencion existente.
- Este repositorio contiene skills, agentes y hooks reutilizables. Las aplicaciones finales
  viven en otros repos y consumen este contenido.
- El dominio de game development vive en `gamedev-skills`; no agregar aqui recursos de ese
  dominio.
- Mantener una sola copia de cada skill en `plugins/<plugin>/skills/<skill>/`. Claude Code y
  Codex leen ese mismo directorio mediante sus manifests.
- Presentar el contenido como propio y no atribuirlo a proyectos de terceros.
- No inventar modelos, herramientas MCP ni campos de configuracion. Comprobarlos o declarar la
  incertidumbre.

## Autorizacion

Se puede leer y editar el repo, ejecutar pruebas y hooks, crear ramas, commits y PR, e integrar
un PR que cumpla la lista de verificacion de [docs/repo-workflow.md](docs/repo-workflow.md).

Requiere permiso explicito para cada caso:

- escribir directo sobre `main` o `develop`
- reescribir historial o usar `push --force`, `rebase` publicado o `reset --hard`
- borrar o renombrar `main`, `develop`, una skill, un agente o un hook
- cambiar configuracion de GitHub, dependencias, servidores MCP, credenciales o pins de modelo
- actuar sobre un servicio externo, salvo cuando el usuario haya pedido expresamente ese flujo

## Skills portables

- Cada skill tiene `SKILL.md` con frontmatter valido y, cuando aplique,
  `agents/openai.yaml` con la politica equivalente de Codex.
- `SKILL.md` debe ser neutral al runtime: no usar comandos `/skill`, `$ARGUMENTS`, nombres de
  tools de un proveedor, tipos internos de subagente ni variables exclusivas del runtime.
- Referenciar archivos propios con enlaces relativos al directorio de la skill. Resolver esas
  rutas antes de ejecutar comandos.
- La descripcion del frontmatter explica cuando activar la skill, no todo su procedimiento. El
  cuerpo contiene el flujo y `references/` guarda detalle cargado bajo demanda.
- Una skill no puede depender de un agente custom. Puede aprovechar especialistas disponibles,
  pero debe incluir un fallback ejecutable por el agente principal.
- La invocacion explicita es `/skill` en Claude Code y `$skill` en Codex. Dentro de instrucciones
  compartidas se escribe `skill <nombre>` para mantener neutralidad.
- Al agregar, mover o renombrar una skill, actualizar catalogos, versiones y documentacion segun
  [docs/repo-workflow.md](docs/repo-workflow.md).

## Adaptadores de runtime

- `.codex/agents/`, `.codex/config.toml`, `.codex/hooks.json` y `.codex/hooks/` son adaptadores
  de Codex para este repo.
- `plugins/core/agents/` y `plugins/core/hooks/` son adaptadores de Claude Code.
- Un cambio de comportamiento de un agente o hook se replica en ambas capas cuando exista un
  equivalente, salvo pedido explicito en contrario.
- Los hooks deben funcionar en Windows, macOS y Linux; no asumir un binario unico de Python.
- Todo cambio de hooks, agentes Codex o manifests lleva pruebas en `tests/`.

## Trabajo eficiente

- Hacer lecturas puntuales con `rg`, `rg --files` y rangos pequenos antes de abrir archivos
  completos.
- Paralelizar inspecciones independientes solo cuando el entorno lo permita y no haya riesgo de
  conflictos.
- Aplicar brainstorming, TDD, revision y seguridad de forma proporcional al riesgo. Los cambios
  documentales o mecanicos no necesitan rituales que no aporten evidencia.
- Mantener `SKILL.md` por debajo de 500 lineas; mover ejemplos, anexos y playbooks a
  `references/`, y automatizacion a `scripts/`.

## Edicion y seguridad

- No crear `output/`, `tmp/`, `temp/` ni equivalentes dentro del repo.
- No versionar `.claude/settings.local.json`, `__pycache__/`, secretos ni archivos de entorno.
- No crear copias con sufijos `copia`, `nuevo`, `final` o `v2`.
- Usar UTF-8 sin BOM y respetar `.gitattributes`.
- Preservar cambios ajenos y evitar comandos destructivos.

## Verificacion y cierre

Antes de cada commit ejecutar:

```bash
python -m unittest discover -s tests
```

Ademas, validar los manifests cuando el CLI correspondiente este disponible. No declarar exito
sin leer la salida. Al cerrar, indicar archivos y capas modificadas, verificaciones realizadas y
cualquier limitacion pendiente.
