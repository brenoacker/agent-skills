#!/usr/bin/env bash
# install.sh - Universal installer for agent skills across Antigravity, Claude Code, and Codex.

set -euo pipefail

TARGET=""
SCOPE="global"
DESTINATION_OVERRIDE=""

usage() {
  echo "Usage: $0 --target [antigravity|claude|codex|all] [--scope global|project] [--dest <path>]"
  exit 1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --target|-t)
      TARGET="$2"
      shift 2
      ;;
    --scope|-s)
      SCOPE="$2"
      shift 2
      ;;
    --dest|-d)
      DESTINATION_OVERRIDE="$2"
      shift 2
      ;;
    --help|-h)
      usage
      ;;
    *)
      echo "Unknown option: $1"
      usage
      ;;
  esac
done

if [[ -z "$TARGET" ]]; then
  echo "Error: --target is required."
  usage
fi

TARGET=$(echo "$TARGET" | tr '[:upper:]' '[:lower:]')

case "$TARGET" in
  antigravity|claude|codex|all)
    ;;
  *)
    echo "Error: Invalid target '$TARGET'. Expected antigravity, claude, codex, or all."
    exit 1
    ;;
esac

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
SOURCE_SKILLS_DIR="$REPO_ROOT/skills"

if [[ ! -d "$SOURCE_SKILLS_DIR" ]]; then
  echo "Error: Source skills directory not found at $SOURCE_SKILLS_DIR"
  exit 1
fi

get_target_dir() {
  local agent="$1"
  if [[ -n "$DESTINATION_OVERRIDE" ]]; then
    if [[ "$TARGET" == "all" ]]; then
      echo "$DESTINATION_OVERRIDE/$agent"
    else
      echo "$DESTINATION_OVERRIDE"
    fi
    return
  fi

  local home_dir="${HOME:-}"
  case "$agent" in
    antigravity)
      if [[ "$SCOPE" == "project" ]]; then echo "$(pwd)/.agents/skills"; else echo "$home_dir/.gemini/antigravity/skills"; fi
      ;;
    claude)
      if [[ "$SCOPE" == "project" ]]; then echo "$(pwd)/.claude/skills"; else echo "$home_dir/.claude/skills"; fi
      ;;
    codex)
      if [[ "$SCOPE" == "project" ]]; then echo "$(pwd)/.codex/skills"; else echo "$home_dir/.codex/skills"; fi
      ;;
  esac
}

copy_skills() {
  local dest="$1"
  mkdir -p "$dest"
  for skill_path in "$SOURCE_SKILLS_DIR"/*; do
    if [[ -d "$skill_path" ]]; then
      local skill_name="$(basename "$skill_path")"
      cp -R "$skill_path" "$dest/"
      echo "Installed skill '$skill_name' -> $dest/$skill_name"
    fi
  done
}

if [[ "$TARGET" == "all" ]]; then
  for t in antigravity claude codex; do
    dest=$(get_target_dir "$t")
    echo "Installing skills for target: $t into $dest..."
    copy_skills "$dest"
  done
else
  dest=$(get_target_dir "$TARGET")
  echo "Installing skills for target: $TARGET into $dest..."
  copy_skills "$dest"
fi

echo "Skills installation completed successfully."
exit 0
