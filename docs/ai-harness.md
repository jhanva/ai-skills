# AI harness para desarrollo de software con Codex

Estado: implementacion inicial

Fecha: 2026-09-20

## 1. Problema y contexto

Se quiere desarrollar software modular y escalable con Codex como interfaz principal. El objetivo
del harness es conservar un modelo de alta capacidad como coordinador y delegar trabajo acotado
a modelos mas economicos sin perder control arquitectonico, trazabilidad ni seguridad.

El sistema no intentara garantizar que un modelo siempre resuelva una tarea. Su garantia sera
mas precisa: ningun resultado se acepta silenciosamente si no satisface contratos y
validaciones independientes del modelo.

## 2. Decision arquitectonica

Se adopta una arquitectura multiagente jerarquica y centralizada, tambien conocida como
`orchestrator-worker`, `supervisor-worker` o `planner-executor`, con enrutamiento heterogeneo de
modelos y delegacion condicional.

La implementacion sera nativa primero:

1. Codex Desktop es la interfaz de control.
2. GPT-5.6 Sol conserva el hilo principal y la responsabilidad de integracion.
3. Los subagentes nativos usan GPT-5.6 Terra o GPT-5.6 Luna segun el contrato de tarea.
4. `codex exec` se reserva para flujos estables, aislables y automatizables.
5. No se crea un CLI ni un orquestador propio en la primera etapa.
6. Un orquestador externo solo se considera despues de obtener evidencia de que las
   capacidades nativas son insuficientes.

Esta decision favorece una topologia centralizada porque contiene mejor la propagacion de
errores que una red de agentes independientes y porque el desarrollo de software contiene muchas
decisiones secuenciales y acopladas.

## 3. Objetivos

- Mantener arquitectura, dominio, seguridad y aceptacion final bajo un coordinador fuerte.
- Delegar exploracion e implementacion acotada sin cambiar el modelo del chat principal.
- Entregar a cada worker solo el contexto necesario para su tarea.
- Reducir consumo de Sol sin degradar la calidad del codigo aceptado.
- Detectar fallos mediante validaciones deterministas y estados explicitos.
- Evitar conflictos de archivos y escrituras concurrentes sobre el mismo checkout.
- Hacer medible el costo total por tarea aceptada, incluidos reintentos y revisiones.
- Permitir evolucion gradual hacia automatizacion con `codex exec` y GitHub Actions.

## 4. Fuera de alcance inicial

- Construir un scheduler, cola distribuida o panel propio de agentes.
- Ejecutar cambios autonomos en produccion.
- Permitir merges decididos unicamente por un LLM.
- Mantener una memoria vectorial de todo el historial del proyecto.
- Enviar el historial completo del chat a cada worker.
- Ejecutar varios agentes escritores sobre el mismo checkout.
- Optimizar costo antes de establecer una linea base de calidad y consumo.
- Integrar servidores MCP no verificados o herramientas con permisos amplios por defecto.

## 5. Principios de diseno

1. Un agente probabilistico propone; una comprobacion determinista decide cuando sea posible.
2. La unidad de delegacion es un contrato pequeno, no una conversacion completa.
3. Sol conserva decisiones globales; los workers reciben autoridad local y temporal.
4. Una tarea solo se delega si tiene una frontera clara y un resultado verificable.
5. Varios lectores pueden trabajar en paralelo; un checkout tiene un solo escritor.
6. Trabajo de escritura paralelo requiere worktrees separados y ownership no superpuesto.
7. El costo se mide por resultado aceptado, no por llamada ni por precio nominal del modelo.
8. Un fallo debe terminar en rechazo, reintento limitado o escalamiento; nunca en exito aparente.
9. Contexto durable vive en archivos versionados, no solo en la memoria de un chat.
10. Seguridad, datos sensibles y cambios irreversibles siempre tienen gates reforzados.

## 6. Vista de arquitectura

```text
Persona desarrolladora
        |
        v
Codex Desktop: chat principal con Sol
        |
        +---- lee ----> AGENTS.md, specs, ADR, contratos y skills
        |
        +---- clasifica riesgo y selecciona ruta
        |                   |
        |          +--------+---------+
        |          |                  |
        |          v                  v
        |     Luna / lectura      Terra / escritura acotada
        |          |                  |
        |          +--------+---------+
        |                   |
        |                   v
        |          sobre de resultado estructurado
        |                   |
        v                   v
Revision de Sol <---- hooks y validadores locales
        |
        v
Git diff -> CI -> revision humana segun riesgo -> merge
```

La arquitectura separa cinco planos:

- Plano de interaccion: chat de Codex Desktop.
- Plano de control: Sol, politica de routing y contratos de tarea.
- Plano de ejecucion: subagentes nativos y, mas adelante, `codex exec`.
- Plano de conocimiento: repositorio, specs, ADR, skills y MCP allowlisted.
- Plano de aseguramiento: hooks, pruebas, CI, proteccion de rama y aprobaciones.

## 7. Componentes y responsabilidades

### 7.1 Chat principal con Sol

Sol es responsable de:

- entender el requerimiento y hacer preguntas antes de editar
- identificar dependencias entre modulos
- mantener coherencia arquitectonica y de dominio
- dividir el trabajo en contratos verificables
- asignar riesgo y modelo
- resolver ambiguedades antes de delegar
- revisar cambios, resultados de pruebas y riesgos residuales
- decidir si acepta, corrige, escala o detiene

Sol no debe delegar automaticamente toda implementacion. Conserva directamente las decisiones
con alto acoplamiento, alta ambiguedad o alto impacto.

### 7.2 Router de modelos

El router inicial no sera otro LLM ni un servicio. Sera una politica declarativa que Sol debe
aplicar antes de crear un subagente.

Cada tarea obtiene una puntuacion de 0 a 2 en seis dimensiones:

| Dimension | 0 | 1 | 2 |
|---|---|---|---|
| Ambiguedad | especificacion cerrada | una decision local | decisiones de dominio abiertas |
| Acoplamiento | un archivo o modulo | varios archivos relacionados | varios modulos o contratos |
| Radio de impacto | interno y reversible | API o datos locales | datos compartidos o produccion |
| Verificabilidad | prueba determinista | combinacion de pruebas y revision | resultado dificil de automatizar |
| Sensibilidad | docs, fixtures o UI menor | logica de negocio ordinaria | auth, RLS, pagos, impuestos o contabilidad |
| Reversibilidad | revert simple | migracion compatible | perdida de datos o cambio irreversible |

Reglas de ruta:

| Resultado | Ruta predeterminada |
|---|---|
| 0 a 3 | Luna para lectura o trabajo mecanico; Terra si escribe logica de produccion |
| 4 a 7 | Terra con pruebas y revision de Sol |
| 8 a 12 | Sol; puede usar workers solo para exploracion independiente |
| Sensibilidad = 2 | Sol conserva decision y revision final, sin importar el total |
| Verificacion inexistente | no delegar hasta crear un criterio comprobable |

La puntuacion orienta, no reemplaza los overrides de seguridad.

### 7.3 Perfiles de subagente

#### Explorer Luna

- Modelo: `gpt-5.6-luna`.
- Modo preferido: solo lectura.
- Trabajo: localizar simbolos, mapear dependencias, inventariar pruebas, resumir documentos y
  hacer cambios documentales o mecanicos de riesgo bajo cuando se autorice expresamente.
- No decide arquitectura ni modifica logica sensible.

#### Implementer Terra

- Modelo: `gpt-5.6-terra`.
- Trabajo: implementar un contrato acotado, escribir pruebas y ejecutar validaciones locales.
- Solo toca rutas permitidas por el contrato.
- No amplia alcance, agrega dependencias ni altera migraciones sin escalar.

#### Reviewer

- Modelo: Terra con esfuerzo alto para cambios ordinarios; Sol para riesgo alto.
- Modo: solo lectura.
- Trabajo: encontrar regresiones, violaciones del contrato, ausencia de pruebas y riesgos de
  seguridad.
- No reescribe el cambio que revisa; devuelve hallazgos verificables.

#### Sol orchestrator

- Modelo: `gpt-5.6-sol`.
- Trabajo: plan, decisiones globales, routing, integracion, escalamiento y aceptacion.
- Implementa directamente cuando delegar costaria mas contexto o coordinacion que ejecutar.

### 7.4 Contrato de tarea

Toda delegacion debe incluir un paquete de contexto autocontenido:

```yaml
task_id: billing-create-invoice
objective: Crear factura en borrador respetando aislamiento por tenant.
mode: write
allowed_paths:
  - apps/web/src/modules/billing/**
  - packages/db/tests/billing/**
forbidden_paths:
  - packages/db/migrations/**
inputs:
  - docs/architecture/tenancy.md
  - docs/modules/billing.md
decisions:
  - tenant_id se deriva de la sesion y nunca del body
acceptance:
  - typecheck pasa
  - pruebas unitarias de billing pasan
  - prueba de acceso cruzado entre tenants falla con 403
commands:
  - pnpm typecheck
  - pnpm test --filter billing
risk: medium
model: gpt-5.6-terra
max_attempts: 2
expected_result: result-envelope-v1
```

El contrato no incluye el historial completo del chat. Incluye referencias precisas, decisiones
ya tomadas y resultados esperados.

### 7.5 Sobre de resultado

El worker debe terminar con una respuesta estructurada:

```yaml
task_id: billing-create-invoice
status: passed
summary: Implementada creacion de factura en borrador.
changed_files:
  - apps/web/src/modules/billing/create-invoice.ts
  - packages/db/tests/billing/create-invoice.test.ts
checks:
  - command: pnpm typecheck
    result: passed
  - command: pnpm test --filter billing
    result: passed
assumptions: []
risks: []
out_of_scope: []
```

Estados validos:

- `passed`: contrato satisfecho con evidencia.
- `failed`: intento ejecutado y validacion fallida.
- `blocked`: falta informacion o autoridad.
- `partial`: existe un entregable util, pero no satisface todo el contrato.

Sol nunca convierte `partial` o `blocked` en `passed` mediante resumen narrativo.

### 7.6 Contexto durable

El repositorio es la memoria compartida. Debe contener:

- `AGENTS.md`: reglas breves, comandos, restricciones y definicion de terminado.
- Specs: comportamiento esperado de cada iniciativa.
- ADR: decisiones arquitectonicas, alternativas y consecuencias.
- Documentacion de dominio: invariantes y vocabulario del producto.
- Skills: procedimientos repetibles de planificacion, TDD, depuracion, revision y verificacion.
- Codigo y pruebas: fuente de verdad ejecutable.

Reglas de presupuesto de contexto:

- referenciar archivos y simbolos en lugar de pegarlos completos
- entregar solo decisiones que afectan la tarea
- resumir resultados de worker en el sobre, no copiar su transcript
- cargar referencias de una skill bajo demanda
- abrir un chat nuevo por epica o cambio importante
- evitar usar un unico chat para toda la vida del producto

### 7.7 Hooks

Los hooks sirven como feedback inmediato, no como unica autoridad de seguridad.

- `SessionStart`: comprobar herramientas y mostrar comandos relevantes.
- `SubagentStart`: registrar tarea, modelo, riesgo y permisos.
- `SubagentStop`: validar que exista sobre de resultado y, si falta evidencia, pedir una pasada
  adicional limitada.
- `PostToolUse`: observar ediciones o comandos y devolver advertencias puntuales.
- `Stop`: comprobar que el turno reporte verificaciones antes de terminar.

Los hooks deben ser pequenos, multiplataforma y con salida concisa. Sus handlers se prueban como
codigo ordinario. GitHub Actions sigue siendo la autoridad final.

### 7.8 Skills

Las skills contienen procedimientos, no politicas duras. El conjunto inicial recomendado es:

- `brainstorm`: aclarar y disenar antes de implementar.
- `plan`: transformar una spec aprobada en pasos verificables.
- `tdd`: ejecutar RED-GREEN-REFACTOR en cambios de comportamiento.
- `debug`: investigar causa raiz antes de corregir.
- `verify`: exigir evidencia fresca antes de declarar exito.
- `delegate-task`: construir el contrato y seleccionar el perfil de worker.
- `review-high-risk-change`: aplicar gates especificos de seguridad y dominio.

Las dos ultimas solo se crean despues de validar manualmente el flujo que encapsularan.

### 7.9 MCP

MCP se usa solo cuando el contexto requerido vive fuera del repositorio. Cada servidor debe tener
un proposito, permisos minimos y una politica de datos definida.

Usos candidatos:

- leer issues y pull requests de GitHub
- consultar documentacion oficial actualizada
- recuperar logs de un entorno no productivo
- leer tickets o decisiones externas cuando exista una fuente autorizada

No se entrega a un worker acceso a servicios externos que no necesita. Escritura en GitHub,
Supabase u otros servicios requiere un flujo expresamente autorizado y no se deriva de la mera
existencia de una conexion MCP.

### 7.10 Worktrees y ownership

En un chat local con subagentes nativos:

- lectores pueden ejecutarse en paralelo
- solo un agente puede escribir en el checkout por turno
- el contrato asigna rutas y evita ownership superpuesto

Cuando se necesiten dos implementaciones simultaneas:

1. Sol separa tareas sin dependencias y con conjuntos de rutas no superpuestos.
2. Cada tarea se ejecuta en un chat asociado a un worktree diferente.
3. Cada worktree produce un commit o diff revisable.
4. Sol integra en orden de dependencias.
5. Se ejecuta la suite completa despues de integrar.

No se resuelven conflictos automaticamente si cambian contratos de dominio, esquemas o
migraciones. Esos conflictos regresan a Sol o a una persona.

### 7.11 GitHub Actions

La CI debe separar checks rapidos de gates de dominio:

```text
static
  -> format, lint, typecheck, build

test
  -> unit, integration, contract

database
  -> migraciones en PostgreSQL efimero, RLS, aislamiento multiempresa

security
  -> secretos, dependencias, permisos, analisis estatico

acceptance
  -> todos los jobs obligatorios + aprobaciones requeridas
```

La revision de Codex puede agregar hallazgos, pero no reemplaza pruebas, proteccion de rama ni
aprobaciones obligatorias.

## 8. Flujo de ejecucion

### 8.1 Camino normal

1. La persona describe una necesidad en el chat con Sol.
2. Sol lee instrucciones, specs y codigo relevante.
3. Si existe ambiguedad material, Sol pregunta antes de modificar.
4. Sol produce un plan y separa decisiones globales de trabajo delegable.
5. El router puntua cada tarea y aplica overrides de seguridad.
6. Sol ejecuta directamente o crea un worker con contrato reducido.
7. El worker implementa, prueba y devuelve el sobre de resultado.
8. Hooks comprueban forma y evidencia basica.
9. Sol revisa diff, resultados, supuestos y riesgos.
10. Si pasa, se ejecuta la validacion completa correspondiente.
11. GitHub Actions aplica los gates de integracion.
12. Una persona aprueba cambios de riesgo alto o critico.

### 8.2 Recuperacion

```text
worker falla
  |
  +-- error determinista y corregible --> un reintento con el error exacto
  |
  +-- contrato ambiguo ----------------> regresar a Sol para redisenar
  |
  +-- segundo fallo -------------------> escalar a Sol
  |
  +-- riesgo o autoridad insuficiente -> needs-human
```

No se permiten reintentos ilimitados. Un reintento conserva el mismo `task_id` y registra el
motivo. Un contrato modificado crea una revision nueva.

## 9. Modelo de estados

```text
draft
  -> planned
  -> delegated | executing-by-sol
  -> validating
  -> review
  -> accepted
  -> integrated

delegated | validating | review
  -> retryable-failure
  -> escalated
  -> needs-human
  -> rejected
```

Solo `integrated` significa terminado. `accepted` significa que el resultado local es apto para
pasar a integracion, no que ya esta en la rama protegida.

## 10. Gates por riesgo del cambio

| Dominio | Modelo minimo | Validacion adicional | Aprobacion humana |
|---|---|---|---|
| Docs, fixtures, UI menor | Luna o Terra | lint y pruebas afectadas | opcional |
| Cambio interno reversible | Terra | unit e integration | segun impacto |
| Contratos entre modulos | Sol | contract tests y revision independiente | recomendada |
| Auth, permisos y datos sensibles | Sol | pruebas negativas y security review | obligatoria |
| Migraciones destructivas | Sol | restore rehearsal y backup plan | obligatoria |
| Reglas criticas de negocio | Sol | invariantes de dominio y pruebas de reconciliacion | obligatoria |
| Produccion e infraestructura | Sol | plan de rollback y entorno controlado | obligatoria |

## 11. Estrategia de pruebas del harness

### 11.1 Pruebas deterministas

- validar sintaxis de `.codex/config.toml` y perfiles de agentes
- validar esquema de contratos y sobres de resultado
- probar calculo del router con casos de frontera
- probar handlers de hooks en Windows y Linux
- probar que un resultado sin evidencia no se marque `passed`
- probar que rutas fuera de `allowed_paths` sean rechazadas por el gate
- probar limites de reintentos y estados terminales

### 11.2 Evals de agentes

Crear un corpus versionado de tareas representativas:

- exploracion de repositorio
- cambio modular de bajo riesgo
- cambio de contrato entre modulos
- politica RLS defectuosa
- migracion compatible y migracion destructiva
- bug ambiguo con causa raiz

Para cada caso medir:

- aceptacion funcional
- defectos encontrados despues de la primera entrega
- tokens o cuota consumida
- tiempo total
- numero de reintentos
- intervenciones humanas
- archivos fuera de alcance
- diferencias entre ruta Sol, Terra y Luna

### 11.3 Despliegue del router

1. Ejecutar en modo observacion: registrar la ruta recomendada sin delegar.
2. Comparar recomendacion contra decision humana durante al menos 30 tareas variadas.
3. Activar Luna solo para lectura y tareas mecanicas.
4. Activar Terra para contratos de riesgo bajo y medio.
5. Revisar umbrales mensualmente o cuando cambien los modelos.

## 12. Metricas y economia

La metrica primaria es costo por tarea aceptada:

```text
costo aceptado = coordinacion + workers + reintentos + revision + correccion posterior
```

Metricas obligatorias:

- tasa de aceptacion al primer intento por modelo y tipo de tarea
- reintentos medios
- tasa de escalamiento a Sol
- defectos escapados a CI y a revision humana
- tiempo hasta integracion
- cuota o tokens totales por tarea integrada
- porcentaje de tareas donde delegar fue mas caro que ejecutar con Sol

En planes ChatGPT, la optimizacion puede extender cuota disponible, pero no convierte de forma
directa cada token ahorrado en dolares recuperados de una suscripcion fija. En API, se compara el
costo monetario real. Ambas modalidades se reportan por separado.

## 13. Seguridad

- Ningun agente recibe credenciales de produccion por defecto.
- Luna opera en lectura salvo contrato explicito.
- Los MCP se allowlistean por rol.
- Los permisos de escritura se limitan al workspace necesario.
- Nunca se copian secretos a prompts, logs, sobres o outputs de hooks.
- Dependencias nuevas, cambios de permisos y migraciones requieren escalamiento.
- Los tests de RLS incluyen casos negativos entre tenants.
- Los comandos generados no omiten protecciones de rama ni aprobaciones.
- Los hooks son defensa adicional; CI y GitHub mantienen la autoridad de merge.

## 14. Evolucion por etapas

### Etapa 0: linea base

- Usar Sol como agente unico en un conjunto representativo de tareas.
- Registrar calidad, cuota, tiempo y retrabajo.
- Completar specs, ADR y gates CI minimos.

### Etapa 1: subagentes nativos

- Configurar explorer Luna, implementer Terra y reviewer.
- Delegar solo lectura y tareas de riesgo bajo.
- Mantener un solo escritor por checkout.
- Usar sobres de resultado en el chat.

### Etapa 2: enforcement local

- Agregar schemas y hooks pequenos.
- Automatizar comprobaciones rapidas al detener workers o turnos.
- Mantener GitHub Actions como gate final.

### Etapa 3: automatizacion selectiva

- Mover a `codex exec` solo flujos manuales ya estables.
- Usar sesiones efimeras, salida estructurada y permisos minimos.
- Ejecutar en worktrees o runners aislados.

### Etapa 4: decision sobre orquestador propio

Construir un control plane externo solo si se cumple al menos una condicion sostenida:

- el volumen excede la coordinacion interactiva humana
- se requieren colas, SLAs o reanudacion durable
- existen multiples repositorios o equipos ejecutando workers simultaneos
- el costo exige presupuestos y routing que Codex nativo no puede expresar
- las metricas muestran una ganancia suficiente para pagar mantenimiento y riesgo operacional

## 15. Decisiones explicitas

### Incluido

- chat principal con Sol
- perfiles nativos con distintos modelos
- router declarativo basado en riesgo
- contratos y resultados estructurados
- skills, hooks, MCP restringido, worktrees y CI
- reintentos limitados, escalamiento y gates humanos
- evals y metricas de costo por tarea aceptada

### Excluido

- CLI propio en la primera version
- agentes peer-to-peer o debates libres
- memoria global que copie todos los transcripts
- autonomia de produccion
- merges automaticos decididos por un agente
- paralelismo de escritores en el mismo checkout
- routing aprendido antes de acumular datos confiables

## 16. Criterios de verificacion

La primera version del harness se considera validada cuando:

1. El 100 % de las delegaciones usa un contrato con rutas, criterios y riesgo.
2. El 100 % de los resultados usa un estado valido y evidencia de checks.
3. Ningun worker modifica rutas fuera de su contrato en el corpus de eval.
4. Ningun cambio critico se integra sin aprobacion humana registrada.
5. Toda tarea fallida termina en `rejected`, `escalated` o `needs-human`.
6. No existen mas de dos intentos economicos antes de escalar a Sol.
7. Las tareas paralelas de escritura usan worktrees distintos.
8. CI valida tipos, lint, pruebas, build y gates de base de datos aplicables.
9. El router coincide con la clasificacion humana en al menos 90 % de 30 tareas de calibracion.
10. La delegacion reduce consumo o tiempo total sin aumentar defectos escapados frente a la linea
    base de Sol; de lo contrario, ese tipo de tarea vuelve a Sol.

## 17. Riesgos y mitigaciones

| Riesgo | Mitigacion |
|---|---|
| Delegacion excesiva | router conservador y linea base single-agent |
| Contexto insuficiente | contrato autocontenido y referencias resolubles |
| Contexto excesivo | paquetes pequenos y skills con carga progresiva |
| Conflictos de archivos | un escritor por checkout y worktrees para paralelo |
| Falso exito | estados cerrados, evidencia y gates deterministas |
| Bucle de correccion costoso | maximo de intentos y escalamiento |
| Error compartido entre agentes | revision independiente y pruebas externas al transcript |
| Cambio de comportamiento de modelos | evals antes de actualizar pins o umbrales |
| Sobreingenieria del harness | etapas y criterio explicito para crear control plane |
| Exposicion de secretos | permisos minimos, allowlist y secretos fuera del contexto |

## 18. Alternativas consideradas

### Sol para todo

Es la linea base y puede ser la mejor opcion para trabajo secuencial, ambiguo o altamente
acoplado. Tiene menos coordinacion y una sola fuente de decisiones, pero consume mas capacidad
del modelo fuerte en tareas mecanicas.

### Subagentes nativos sin contratos

Reduce configuracion inicial, pero dificulta medir costo, detectar ampliaciones de alcance y
comparar calidad. No ofrece suficiente disciplina para un proyecto de software sostenido.

### Orquestador propio desde el inicio

Ofrece control de colas, presupuestos y observabilidad, pero duplica capacidades nativas y crea
una plataforma que mantener antes de demostrar necesidad.

## 19. Fuentes

Documentacion oficial de OpenAI:

- Subagentes: https://learn.chatgpt.com/docs/agent-configuration/subagents
- Personalizacion: https://learn.chatgpt.com/docs/customization/overview
- Hooks: https://learn.chatgpt.com/docs/hooks
- Worktrees: https://learn.chatgpt.com/docs/environments/git-worktrees
- Modo no interactivo: https://learn.chatgpt.com/docs/non-interactive-mode
- GitHub Action: https://learn.chatgpt.com/docs/github-action
- Buenas practicas: https://learn.chatgpt.com/guides/best-practices
- Modelos y precios API: https://developers.openai.com/api/docs/models
- Precios y limites de Codex: https://learn.chatgpt.com/docs/pricing

Investigacion y sistemas de referencia:

- Towards a Science of Scaling Agent Systems: https://arxiv.org/abs/2512.08296
- ChatDev: https://arxiv.org/abs/2307.07924
- MetaGPT: https://arxiv.org/abs/2308.00352
- Agentless: https://arxiv.org/abs/2407.01489
- Anthropic multi-agent research system:
  https://www.anthropic.com/engineering/multi-agent-research-system
- Microsoft Agent Framework: https://github.com/microsoft/agent-framework
- Microsoft AutoGen (referencia historica, actualmente en mantenimiento):
  https://github.com/microsoft/autogen
- LangGraph: https://github.com/langchain-ai/langgraph
- SWE-agent: https://github.com/SWE-agent/SWE-agent

Estas referencias muestran patrones y tradeoffs, no prueban que una topologia sea optima para
este proyecto. La decision final se validara con las metricas y evals definidos en esta spec.

## 20. Estado de implementacion

Implementado en esta primera version:

- skill portable `orchestrate` con fallback sin subagentes
- router determinista por seis dimensiones de riesgo
- validacion de contratos y sobres de resultado mediante JSON
- rechazo de rutas absolutas, traversal y archivos fuera de alcance
- perfiles Codex `harness_explorer`, `harness_implementer` y `harness_reviewer`
- pins Luna/Terra y esfuerzo por rol
- hook `SubagentStop` con validacion de `RESULT_ENVELOPE`
- comandos multiplataforma para el hook
- eval de activacion manager-worker
- pruebas unitarias integradas en la suite del repositorio

Pendiente de validar con proyectos reales:

- calibracion del router con al menos 30 tareas representativas
- linea base comparativa Sol-only
- gates de dominio para autorizacion, datos sensibles y migraciones
- politicas de branch protection del repositorio consumidor
- automatizacion selectiva con `codex exec`

Estas tareas pendientes no bloquean el uso interactivo inicial. Si las metricas no muestran una
mejora frente a Sol-only, el tipo de tarea evaluado debe regresar al agente principal.
