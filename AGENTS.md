# AGENTS.md

## Princípios Invioláveis
- Nunca adicione comentários inline no código nem suprima erros de tipo/lint.
- Nunca crie arquivos `.md` não solicitados.
- Use o módulo `scripts/domain/skill_validator.py` como referência estrutural (*Golden File*).

## Pipeline Obrigatório Antes de Abrir PR
Execute todos os comandos abaixo e garanta exit code `0`:
1. `python -m mypy scripts tests`
2. `python scripts/pedagogical_lint.py && python -m ruff check scripts tests`
3. `python scripts/check_deps.py`
4. `python -m unittest discover -s tests && python -m unittest discover -s tests/properties`
5. `python -m scripts.verify_feature --all`

## Evidências Obrigatórias na Descrição do PR
- Anexe o log estruturado gerado em `.artifacts/<feature_afetada>/execution-proof.json`.
- Se você criou ou alterou uma máquina de estados ou fluxo complexo, inclua um diagrama Mermaid `stateDiagram-v2` ilustrando os estados do ponto de vista do usuário.
