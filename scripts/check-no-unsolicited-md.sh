#!/usr/bin/env bash
set -e

BASE_REF="${GITHUB_BASE_REF:-HEAD}"
if [ "$BASE_REF" != "HEAD" ]; then
  git fetch origin "$BASE_REF" --depth=1 >/dev/null 2>&1 || true
  NEW_MD=$(git diff --name-only --diff-filter=A "origin/$BASE_REF"...HEAD | grep -E '\.md$' | grep -vE '^(docs/|README\.md|AGENTS\.md|skills/|templates/|\.specs/)' || true)
else
  NEW_MD=$(git diff --cached --name-only --diff-filter=A | grep -E '\.md$' | grep -vE '^(docs/|README\.md|AGENTS\.md|skills/|templates/|\.specs/)' || true)
fi

if [ -n "$NEW_MD" ]; then
  echo "AGENTE: Criação de arquivos Markdown não solicitados bloqueada:"
  echo "$NEW_MD"
  echo "Não crie arquivos .md para documentar tarefas. A evidência deve estar no código e nos testes."
  exit 1
fi
