# AGENT 02: Architectural Boundaries, Dependency Graph & Golden Files

## Papel e Escopo
Você é o **Agente de Arquitetura e Isolamento**. Sua missão é garantir que a estrutura de diretórios do repositório comunique claramente as responsabilidades de cada módulo, que importações cruzadas proibidas sejam bloqueadas automaticamente no CI e que exista um módulo de referência impecável (*Golden File*) para futuros agentes copiarem.

---

## Tarefas Executáveis

### Tarefa 1: Analisar e Consolidar Fronteiras de Diretórios
1. Inspecione a estrutura atual de pastas do projeto.
2. Garanta separação clara entre camadas de execução e domínio. Exemplos:
   - **Frontend / Fullstack:** `ui/` (ou `components/`), `features/`, `domain/`, `core/` (abstrações internas seguras), `infrastructure/` (APIs, DB, storage).
   - **Electron / Desktop:** `electron-main/` vs. `electron-renderer/` vs. `shared/`.
   - **Backend:** `api/` (rotas/controllers), `application/` (casos de uso), `domain/` (regras puras e entidades), `infrastructure/` (repositórios DB, clientes externos).
3. Se houver arquivos misturando responsabilidades críticas (ex: chamadas diretas de banco de dados dentro de componentes de UI ou rotas HTTP), extraia e mova para a camada correta.

### Tarefa 2: Configurar Análise de Grafo de Dependências no CI
Instale e configure um verificador estático de dependências que falhe o build em caso de violação arquitetural:

- **Se JavaScript / TypeScript (`dependency-cruiser`):**
  1. Instale `dependency-cruiser` como devDependency.
  2. Crie `.dependency-cruiser.cjs` definindo regras `forbidden` com mensagens iniciadas por `AGENTE:`:
     - `domain` não pode importar de `infrastructure`, `api` ou `ui`.
     - `ui` / `components` não pode importar diretamente de `database` ou `infrastructure`.
     - Proibir dependências circulares (`no-circular`).
  3. Adicione o script `"deps:check": "depcruise src --config .dependency-cruiser.cjs"` no `package.json`.

- **Se Python (`import-linter`):**
  1. Instale `import-linter` nas dependências de desenvolvimento.
  2. Crie `.importlinter` definindo contratos `forbidden` e `layers` isolando `domain` de `infrastructure` e `api`.
  3. Adicione `lint-imports` ao pipeline de CI e `Makefile`/`pyproject.toml`.

### Tarefa 3: Criar um Módulo Canônico (*Golden File*)
1. Escolha a feature mais representativa e limpa do repositório (ex: uma feature de CRUD completa ou fluxo principal de negócio).
2. Refatore-a para ser o **padrão ouro absoluto** do projeto:
   - 100% aderente às regras estritas de tipagem e lint.
   - Zero comentários inline, zero `any`, zero gambiarras.
   - Separação exemplar entre schema/validação, lógica de domínio, acesso a dados e testes.
3. Remova arquivos de exemplo obsoletos ou padrões duplicados antigos que possam confundir futuros agentes.

### Tarefa 4: Integrar ao CI
Adicione a execução do verificador de grafo de dependências (`npm run deps:check` ou `lint-imports`) no workflow de CI (`.github/workflows/`).

---

## Critérios de Aceite (Definition of Done)
- [ ] O comando de verificação de dependências (`deps:check` ou `lint-imports`) roda localmente e no CI com exit code `0`.
- [ ] Foi validado que uma importação ilegal simulada falha o comando com mensagem clara explicando para qual camada mover o código.
- [ ] Existe um módulo de referência limpo e livre de código legado duplicado no diretório principal de features.
- [ ] Build e suíte de testes passam sem regressões.
