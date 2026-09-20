# Arquitectura de skills y plugins

Este repositorio tiene dos usos distintos. El desarrollo local necesita leer la
fuente viva; la distribucion necesita paquetes versionados y reproducibles. No se
deben confundir ambos flujos.

## Fuente unica

Cada skill vive una sola vez en `plugins/<plugin>/skills/<skill>/`. El mismo
`SKILL.md` debe funcionar en cualquier runtime compatible con Agent Skills. Los
metadatos propios de Codex viven en `agents/openai.yaml`; los componentes
exclusivos de Claude Code viven en la capa del plugin correspondiente.

Una skill compartida:

- describe capacidades, entradas, limites y criterios de exito
- usa links relativos para sus scripts y referencias
- no presupone nombres de tools, tipos de subagente ni macros de un runtime
- funciona desde el agente principal aunque la delegacion no este disponible
- carga anexos solo cuando la tarea los necesita

## Desarrollo vivo

`scripts/link-user-skills.py` crea enlaces individuales desde
`~/.agents/skills/` hacia la fuente del repo. Los enlaces individuales permiten
combinar plugins sin reemplazar skills personales ya instaladas.

```bash
python scripts/link-user-skills.py --plugin core --dry-run
python scripts/link-user-skills.py --plugin core
python scripts/link-user-skills.py --status
```

En Windows se requiere Developer Mode o una terminal elevada para crear symlinks.
Si esa politica no se puede cambiar, `--junction` crea junctions de directorio vivas de forma
explicita. El script no cambia configuracion del sistema.

## Distribucion estable

Los marketplaces instalan una copia versionada del plugin. Este es el flujo para
otros equipos y maquinas; no es el ciclo rapido de edicion local. Cada cambio de
una skill actualiza el manifest del plugin, el marketplace de Claude Code y la
documentacion de publicacion.

## Contrato de plugin

Una instalacion del plugin debe conservar su comportamiento principal usando solo
archivos incluidos bajo la raiz del plugin. Agentes especializados y hooks pueden
mejorar el flujo, pero una skill no puede fallar cuando esos componentes no estan
disponibles en el runtime consumidor.

## Presupuesto de contexto

Los nombres y descripciones de todas las skills se cargan antes de seleccionar
una. Por eso:

- cada descripcion tiene un maximo de 300 caracteres
- el catalogo completo mantiene menos de 5000 caracteres de descripcion
- un `SKILL.md` largo actua como router hacia `references/`
- las reglas permanentes van en `AGENTS.md`; los procedimientos, en skills

## Verificacion

La suite determinista valida manifests, rutas, portabilidad, hooks y scripts. Los
evals de agente miden activacion, resultado y eficiencia con ejecuciones reales.
Los resultados generados viven en `plugins/*/evals/results/` y no se versionan.
