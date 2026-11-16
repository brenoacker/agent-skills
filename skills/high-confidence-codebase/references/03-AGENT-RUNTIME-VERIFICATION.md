# AGENT 03: Runtime Verification CLI, Property-Based Testing & Minimal AGENTS.md

## Papel e Escopo
Você é o **Agente de Verificação**. Sua missão é construir a infraestrutura que permite aos agentes validar o próprio código em execução real (*runtime*), testar invariantes com *property-based testing* e gerar artefatos visuais (screenshots, vídeos e diagramas de estado) para revisão humana rápida. Ao final, você deve consolidar um `AGENTS.md` enxuto (< 60 linhas).

---

## Tarefas Executáveis

### Tarefa 1: Criar o `feature-map.yaml`
1. Identifique as principais funcionalidades do sistema do ponto de vista do usuário final (use `.agent-baseline.json` ou inspecione as rotas/telas do projeto).
2. Crie o arquivo `feature-map.yaml` na raiz do repositório mapeando cada feature com:
   - `description`: O que a feature faz para o usuário.
   - `route` ou `endpoint`: Ponto de entrada.
   - `interactions` / `payload`: Passos ou dados de entrada para exercitar o fluxo.
   - `assertions`: O que prova objetivamente que funciona (elementos visíveis, status HTTP, zero erros de console, invariantes de resposta).

### Tarefa 2: Construir a CLI Única de Verificação em Runtime
Em vez de agentes escreverem scripts descartáveis a cada tarefa, crie uma CLI reutilizável e padronizada:
- **Se Aplicação Web / Frontend / Fullstack:**
  - Crie `scripts/verify-feature.ts` (ou `.py`) usando **Playwright** (com Chrome DevTools Protocol / captura de console e network).
  - O comando `npm run verify -- <feature_name>` (ou `python -m scripts.verify_feature <feature_name>`) deve:
    1. Ler a definição da feature em `feature-map.yaml`.
    2. Garantir que o servidor local esteja rodando.
    3. Executar o fluxo gravando vídeo e capturando screenshot do estado final em `.artifacts/<feature_name>/`.
    4. Falhar com exit code `1` se houver qualquer `pageerror`, `console.error` não esperado, resposta HTTP `>= 500` ou falha de asserção.
- **Se API / Backend / CLI:**
  - Crie a CLI de verificação executando o fluxo end-to-end contra o ambiente de teste isolado, salvando o trace/log estruturado da execução em `.artifacts/<feature_name>/execution-proof.json`.
- Adicione `.artifacts/` ao `.gitignore`.

### Tarefa 3: Implementar Property-Based Testing (Invariantes)
Adicione pelo menos uma suíte de testes baseados em propriedades testando invariantes críticas do sistema:
- **Se TypeScript / JavaScript:** Instale `fast-check` e crie testes em `tests/properties/` validando invariantes de funções críticas de domínio ou transições de estado (ex: idempotência, conservação de valores, ausência de estados inválidos).
- **Se Python:** Instale `hypothesis` e crie testes em `tests/properties/` com `@given(...)` validando invariantes de negócio e schemas.
- **Se UI Web Complexa:** Configure testes exploratórios de invariantes de UI (inspirados no *Bombadil*) garantindo que sequências aleatórias de navegação/interação nunca gerem tela branca ou exceções não tratadas.
- Exponha o comando `test:properties` no `package.json` ou `Makefile`.

### Tarefa 4: Criar o `AGENTS.md` Minimalista (< 60 Linhas)
Crie ou substitua o `AGENTS.md` na raiz do repositório. **Restrição estrita: máximo de 60 linhas.** Ele não deve conter explicações teóricas — apenas o contrato operacional apontando para as ferramentas determinísticas criadas pelos Agentes 01, 02 e 03:

```markdown
# AGENTS.md

## Princípios Invioláveis
- Nunca adicione comentários inline no código nem suprima erros de tipo/lint.
- Nunca crie arquivos `.md` não solicitados.
- Use o módulo `<caminho_do_golden_file>` como referência estrutural.

## Pipeline Obrigatório Antes de Abrir PR
Execute todos os comandos abaixo e garanta exit code `0`:
1. `<comando_typecheck>`
2. `<comando_lint>`
3. `<comando_deps_check>`
4. `<comando_test_properties>`
5. `<comando_verify_feature> <feature_afetada>`

## Evidências Obrigatórias na Descrição do PR
- Anexe o screenshot/vídeo ou log gerado em `.artifacts/<feature_afetada>/`.
- Se você criou ou alterou uma máquina de estados ou fluxo complexo, inclua um diagrama Mermaid `stateDiagram-v2` ilustrando os estados do ponto de vista do usuário.
```
*(Substitua os placeholders `<...>` pelos comandos reais deste repositório).*

---

## Critérios de Aceite (Definition of Done)
- [ ] `feature-map.yaml` criado na raiz cobrindo os fluxos principais do sistema.
- [ ] CLI de verificação executa com sucesso para pelo menos uma feature real e gera artefatos em `.artifacts/`.
- [ ] Suíte `test:properties` instalada, escrita e passando no CI.
- [ ] `AGENTS.md` atualizado na raiz com menos de 60 linhas e todos os comandos reais validados.
