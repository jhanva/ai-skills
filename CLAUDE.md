@AGENTS.md

# Adaptador Claude Code

Este archivo contiene solo el contexto permanente especifico de Claude Code. Las reglas
compartidas viven en `AGENTS.md`; el catalogo, la instalacion y los ejemplos viven en `README.md`.

- La fuente distribuible esta en `plugins/<plugin>/`.
- Los agentes y hooks de Claude Code viven dentro de cada plugin.
- Las skills se invocan como `/plugin:skill` cuando el plugin esta instalado.
- Para desarrollo local se usa `claude --plugin-dir ./plugins/<plugin>`.
- Antes de publicar se ejecutan la suite y `claude plugin validate .`.

No duplicar aqui catalogos, planes, arquitectura ni procedimientos de las skills.
