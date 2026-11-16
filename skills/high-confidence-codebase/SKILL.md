---
name: high-confidence-codebase
description: Transforma um repositório em um ambiente de engenharia determinístico de alta confiança (metodologia Potato Pyramid) com diagnóstico inicial, linters pedagógicos para LLMs, fronteiras arquiteturais e verificação em runtime. Use quando o usuário pedir para aplicar engenharia determinística, Potato Pyramid, linters pedagógicos ou blindar o codebase para agentes.
metadata:
  author: Breno Acker
  version: 1.0.0
  type: personal
---

# MISSION: High-Confidence Codebase Transformation (Master Orchestrator)

## Contexto e Objetivo
Você está transformando este repositório em um **ambiente de engenharia determinístico de alta confiança** (baseado na metodologia *Potato Pyramid* / Grok Bot).
Seu objetivo **não é** escrever regras em prosa no `AGENTS.md`, mas sim empurrar todas as restrições arquiteturais, de estilo e de qualidade para **camadas determinísticas executáveis**: compilador, linters customizados com mensagens pedagógicas, analisadores de grafo de dependência e verificação automatizada em runtime.

---

## Regras Globais Invioláveis (Para Todos os Agentes)
1. **Isolamento:** Execute suas alterações em uma branch ou `git worktree` dedicada. Nunca commite direto na `main`.
2. **Zero Supressões:** É estritamente proibido usar `@ts-ignore`, `@ts-expect-error`, `eslint-disable`, `# type: ignore`, `# noqa` ou equivalentes para fazer o build passar. Corrija a causa raiz.
3. **Zero Comentários Desnecessários:** Não adicione comentários inline explicando o que o código faz ou justificando atalhos. O código e os tipos devem ser autoexplicativos.
4. **Zero Markdown Não Solicitado:** Não crie arquivos `.md` de resumo, relatório ou documentação extra, exceto os artefatos explicitamente exigidos na sua missão.
5. **Mensagens de Erro Pedagógicas para LLMs:** Toda regra de lint ou verificação customizada que você criar deve emitir uma mensagem de erro clara iniciada com `AGENTE:` explicando **por que** falhou e **qual API ou padrão exato** deve ser usado no lugar.

---

## Fase 0: Descoberta e Baseline (Execute Primeiro — Modo Read-Only)

Antes de executar qualquer um dos agentes especializados (`01`, `02` ou `03`), execute este diagnóstico no repositório atual e gere o arquivo `.agent-baseline.json` (temporário, não commitar):

### Passos de Diagnóstico:
1. **Detectar Stack e Ferramentas:**
   - Identifique linguagens (`TypeScript`, `JavaScript`, `Python`, `Go`, `Rust`, etc.), frameworks (`React`, `Next.js`, `FastAPI`, `Electron`, etc.) e gerenciadores de pacotes (`pnpm`, `npm`, `uv`, `poetry`).
   - Liste os linters, formatadores, typecheckers e frameworks de teste já configurados no projeto.
2. **Mapear Topologia de Diretórios:**
   - Liste a árvore de pastas até profundidade 3 (`src/`, `app/`, `packages/`, `tests/`, etc.).
   - Identifique fronteiras naturais (ex: UI vs. Domain vs. Infra/DB, ou Main vs. Renderer).
3. **Auditar Dívida Técnica Atual (Contagem de Violações):**
   - Conte ocorrências de comentários inline (`//`, `#`, `/* */`) no código-fonte.
   - Conte ocorrências de supressões (`@ts-ignore`, `eslint-disable`, `type: ignore`, `noqa`).
   - Conte ocorrências de APIs de alta nuance (ex: `useEffect`, `setTimeout`, `any`, `requests.`, `time.sleep`).
4. **Identificar Fluxos Críticos de Usuário:**
   - Mapeie as 3 a 5 principais jornadas/endpoints/telas da aplicação para alimentar o `feature-map.yaml`.

### Saída Esperada da Fase 0:
Salve um JSON estruturado em `.agent-baseline.json` contendo:
```json
{
  "stack": { "languages": [], "frameworks": [], "package_manager": "" },
  "tooling": { "typechecker": "", "linter": "", "test_runner": "" },
  "directories": [],
  "audit_counts": {
    "comments": 0,
    "type_suppressions": 0,
    "high_nuance_apis": {}
  },
  "critical_user_flows": []
}
```

---

## Ordem de Despacho dos Agentes Especializados

Após concluir a Fase 0, despache os agentes na seguinte ordem (cada agente deve abrir um PR independente e validar build + testes antes de concluir):

1. **Agente 01 ([01-AGENT-STATIC-AND-LINTS.md](./references/01-AGENT-STATIC-AND-LINTS.md)):** Endurece typechecker, configura linters pedagógicos, bane comentários/supressões e bloqueia arquivos `.md` não solicitados no CI/pre-commit.
2. **Agente 02 ([02-AGENT-ARCHITECTURE-BOUNDARIES.md](./references/02-AGENT-ARCHITECTURE-BOUNDARIES.md)):** Isola pastas por domínio/camada, instala travas de grafo de dependência (`dependency-cruiser` / `import-linter`) e cria um módulo *Golden File* limpo.
3. **Agente 03 ([03-AGENT-RUNTIME-VERIFICATION.md](./references/03-AGENT-RUNTIME-VERIFICATION.md)):** Cria o `feature-map.yaml`, constrói a CLI única de verificação em runtime + *property-based testing* e atualiza o `AGENTS.md` minimalista (< 60 linhas).
