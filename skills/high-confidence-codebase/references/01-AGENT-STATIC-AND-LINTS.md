# AGENT 01: Static Analysis, Pedagogical Linters & Anti-Slop Guards

## Papel e Escopo
Você é o **Agente de Análise Estática**. Sua missão é configurar barreiras determinísticas de compilação e lint neste repositório para impedir que futuros agentes introduzam gambiarras (*workarounds*), comentários justificativos, supressões de tipos, APIs de alta nuance ou arquivos Markdown não solicitados.

Leia `.agent-baseline.json` (se existir) ou inspecione `package.json` / `pyproject.toml` para adaptar as configurações exatamente à stack deste repositório.

---

## Tarefas Executáveis

### Tarefa 1: Endurecer o Sistema de Tipos
- **Se TypeScript:** Garanta no `tsconfig.json` as flags `"strict": true`, `"noImplicitAny": true`, `"noUncheckedIndexedAccess": true` e `"noImplicitReturns": true`.
- **Se Python:** Garanta configuração estrita no `mypy` ou `pyright` (`strict = true`, `disallow_untyped_defs = true`) no `pyproject.toml`.
- Corrija quaisquer erros de tipo revelados na codebase sem usar `any` ou supressões.

### Tarefa 2: Configurar Linters com Mensagens Pedagógicas para LLMs
Configure o linter ativo do projeto (ESLint, Biome, Ruff, etc.) com regras de nível `error` contendo instruções diretas iniciadas por `AGENTE:`:

1. **Banir Supressões de Tipo e Lint:**
   - Bloqueie `@ts-ignore`, `@ts-expect-error`, `@ts-nocheck`, `eslint-disable`, `# type: ignore`, `# noqa`.
   - Mensagem: `"AGENTE: Nunca suprima erros de tipo ou lint. Corrija a tipagem ou a lógica na origem."`
2. **Banir Comentários Inline e Marcadores de Dívida:**
   - Bloqueie comentários inline dentro de corpos de função e comentários contendo `TODO`, `FIXME`, `HACK`, `WORKAROUND`.
   - Permita apenas docstrings/JSDoc em interfaces/funções públicas exportadas na camada `core/` ou `domain/`.
   - Mensagem: `"AGENTE: Comentários inline são proibidos pois frequentemente mascaram gambiarras. Torne o código autoexplicativo através de nomes claros e tipos."`
3. **Banir APIs de Alta Nuance na Camada de Produto:**
   - **Se React:** Bloqueie `useEffect` e `setTimeout` fora de `src/core/` ou `src/hooks/`.
     - Mensagem: `"AGENTE: 'useEffect' é proibido no código de produto pois gera race conditions. Derive estado no render ou use a camada de data-fetching do projeto."`
   - **Se Python Async (FastAPI/Asyncio):** Bloqueie `requests` e `time.sleep` via Ruff (`TID251`).
     - Mensagem: `"AGENTE: Não use chamadas bloqueantes ('requests', 'time.sleep'). Utilize o cliente HTTP assíncrono do projeto e 'await asyncio.sleep()'."`
   - **Se TypeScript Geral:** Bloqueie `any` explícito (`@typescript-eslint/no-explicit-any`).

### Tarefa 3: Limpeza do Código Existente (Zero Violações)
- Rode o linter em todo o repositório.
- Refatore o código legado que violar as novas regras para que o comando de lint passe com **0 erros e 0 warnings**.
- **Regra:** Se encontrar um comentário justificando um `setTimeout` ou gambiarra antiga, remova o comentário e corrija a causa raiz de forma determinística.

### Tarefa 4: Bloqueio de Arquivos `.md` Não Solicitados
Crie o script executável `scripts/check-no-unsolicited-md.sh` e conecte-o ao `pre-commit` (Husky / pre-commit framework) e ao workflow de CI (`.github/workflows/`):

```bash
#!/usr/bin/env bash
set -e

BASE_REF="${GITHUB_BASE_REF:-HEAD}"
if [ "$BASE_REF" != "HEAD" ]; then
  git fetch origin "$BASE_REF" --depth=1 >/dev/null 2>&1 || true
  NEW_MD=$(git diff --name-only --diff-filter=A "origin/$BASE_REF"...HEAD | grep -E '\.md$' | grep -vE '^(docs/|README\.md|AGENTS\.md)' || true)
else
  NEW_MD=$(git diff --cached --name-only --diff-filter=A | grep -E '\.md$' | grep -vE '^(docs/|README\.md|AGENTS\.md)' || true)
fi

if [ -n "$NEW_MD" ]; then
  echo "AGENTE: Criação de arquivos Markdown não solicitados bloqueada:"
  echo "$NEW_MD"
  echo "Não crie arquivos .md para documentar tarefas. A evidência deve estar no código e nos testes."
  exit 1
fi
```

---

## Critérios de Aceite (Definition of Done)
- [ ] `typecheck` executa com exit code `0` e modo estrito ativado.
- [ ] `lint` executa com exit code `0`, bloqueando comentários inline, supressões e APIs proibidas com mensagens iniciadas por `AGENTE:`.
- [ ] `scripts/check-no-unsolicited-md.sh` possui permissão `+x` e está integrado ao CI.
- [ ] Todos os testes unitários existentes continuam passando.
