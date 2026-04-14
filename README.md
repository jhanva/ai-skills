# ai-skills

Skills de desarrollo propias para [Claude Code](https://claude.ai/code), escritas desde cero. Imponen flujos de trabajo disciplinados: TDD, debugging sistematico, diseno antes de implementacion, y verificacion con evidencia.

## Motivacion

Estas skills nacieron de revisar [obra/superpowers](https://github.com/obra/superpowers) y decidir reescribir los conceptos desde cero para tener control total del codigo, sin dependencia de terceros.

## Skills

| Skill | Invocacion | Proposito |
|---|---|---|
| `optimize` | Siempre activa | Optimizacion de tokens: effort level, filtrado de output, delegacion a subagentes, lecturas precisas |
| `/brainstorm` | Manual | Diseno antes de implementar. Dialogo socratico, multiples enfoques, spec escrita |
| `/plan` | Manual | Convertir spec aprobada en plan de implementacion con tareas de 2-5 min, sin placeholders |
| `/tdd` | Automatica | Test-driven development estricto. Ciclo RED-GREEN-REFACTOR obligatorio |
| `/debug` | Automatica | Debugging sistematico en 4 fases con investigacion de causa raiz |
| `/verify` | Automatica | Verificacion con evidencia antes de cualquier claim de exito |
| `/execute` | Manual | Ejecucion de plan con subagentes frescos y revision de 2 etapas (spec + calidad) |
| `/review` | Manual | Code review estructurado con severidades. Solicitar y recibir review |
| `/parallel` | Manual | Despachar agentes paralelos para problemas independientes |

**Siempre activa** = `user-invocable: false`, Claude la carga automaticamente como conocimiento de fondo
**Manual** = solo se invoca con `/nombre` (no se activa automaticamente)
**Automatica** = Claude la invoca cuando detecta contexto relevante (tambien invocable manualmente)

## Flujo de trabajo

```
/brainstorm  -->  /plan  -->  /execute (usa /tdd internamente)
                                  |
                              /review  -->  /verify  -->  merge
```

Para debugging:

```
/debug  -->  /tdd (para el fix)  -->  /verify
```

Para multiples problemas independientes:

```
/parallel  -->  /verify
```

## Estructura

```
.claude/skills/
  optimize/
    SKILL.md                       # optimizacion de tokens (siempre activa)
    scripts/filter-output.sh       # filtrado de output para comandos
  brainstorm/
    SKILL.md
  plan/
    SKILL.md
  tdd/
    SKILL.md
    testing-anti-patterns.md       # anti-patrones de testing
  debug/
    SKILL.md
    root-cause-tracing.md          # tecnica de rastreo de causa raiz
  verify/
    SKILL.md
  execute/
    SKILL.md
    model-selection.md             # guia de seleccion de modelo para subagentes
  review/
    SKILL.md
  parallel/
    SKILL.md
```

Cada skill es un directorio con `SKILL.md` como punto de entrada (frontmatter YAML + instrucciones) y archivos de soporte opcionales que se cargan on-demand.

## Instalacion

Clonar el repo y trabajar dentro del directorio. Las skills se detectan automaticamente por Claude Code al estar en `.claude/skills/`.

```bash
git clone git@github.com:jhanva/ai-skills.git
cd ai-skills
```

Para usar estas skills en **otro proyecto**, hay dos opciones:

**Opcion A — Copiar la carpeta de skills:**

```bash
cp -r /ruta/a/ai-skills/.claude/skills/ /tu/proyecto/.claude/skills/
```

**Opcion B — Agregar como directorio adicional:**

```bash
claude --add-dir /ruta/a/ai-skills
```

Las skills dentro de `.claude/skills/` en directorios adicionales se cargan automaticamente.

## Principios

1. **No codear sin disenar** — `/brainstorm` antes de todo
2. **No implementar sin test** — `/tdd` siempre activo
3. **No adivinar fixes** — `/debug` con causa raiz primero
4. **No decir "listo" sin evidencia** — `/verify` antes de reportar
5. **No confiar en reportes de subagentes** — verificar independientemente

## Ahorro de tokens

La skill `optimize` se carga automaticamente y aplica reglas de eficiencia en toda interaccion:

| Tecnica | Tokens ahorrados por uso |
|---|---|
| Read con offset/limit vs archivo completo | 500-2,500 |
| Effort low vs high en tarea simple | 10,000-40,000 |
| Subagente para tests vs inline | 1,000-5,000 en contexto principal |
| Filtrar output de comando | 500-3,000 |
| `/clear` entre tareas | todo el contexto acumulado |
| Modelo haiku vs opus en subagente mecanico | ~60% menos costo |

Ademas:

- **Subagentes frescos por tarea** — sin contaminacion de contexto previo
- **Texto completo en prompt** — los subagentes no leen archivos del plan
- **Skills on-demand** — solo se cargan cuando se invocan o Claude detecta relevancia
- **Archivos de referencia separados** — solo se cargan cuando la skill los necesita
- **Review de 2 etapas** — atrapa problemas temprano, evita re-trabajo costoso

## Licencia

Uso personal.
