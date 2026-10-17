# agent-skills

Personal and open-source curated skills package for AI coding agents (**Antigravity**, **Claude Code**, and **Codex**).

## Overview

`agent-skills` is a modular, discovery-ready repository designed to house both personal agent workflows and high-quality curated market skills. It provides:
- **Native Antigravity Plugin Support**: Clone or link directly into `~/.gemini/config/plugins/agent-skills` or `.agents/skills/`.
- **Universal Multi-Agent Installer**: Install seamlessly into Antigravity, Claude Code, or Codex via unified shell scripts.
- **Continuous Validation Gate**: Automated linter ensuring YAML frontmatter integrity and link consistency across all skills.
- **Progressive Disclosure**: Skills follow the standard `SKILL.md` format with lightweight instructions and dedicated `references/` and `scripts/`.

---

## Quick Installation

### 1. Via Universal CLI (`npx skills`) — Recommended

The easiest way for anyone to install skills from this repository directly into their AI agent (Antigravity, Claude Code, Cursor, Codex, etc.) without cloning manually:

```bash
# Interactive skill and agent selection
npx skills add brenoacker/agent-skills

# Install all skills globally
npx skills add brenoacker/agent-skills -g --all

# List available skills without installing
npx skills add brenoacker/agent-skills --list

# Install a specific skill (e.g. tlc-spec-lean)
npx skills add brenoacker/agent-skills --skill tlc-spec-lean
```

---

### 2. Via Standalone Shell Scripts (No Node.js Required)

```powershell
# Install into Antigravity (~/.gemini/antigravity/skills)
.\scripts\install.ps1 -Target antigravity

# Install into Claude Code (~/.claude/skills)
.\scripts\install.ps1 -Target claude

# Install into Codex (~/.codex/skills)
.\scripts\install.ps1 -Target codex

# Install across all supported agents
.\scripts\install.ps1 -Target all
```

To install into the current project workspace instead of globally, add `-Scope project`:
```powershell
.\scripts\install.ps1 -Target antigravity -Scope project
```

### Linux / macOS (Bash)

```bash
# Make executable
chmod +x scripts/install.sh

# Install into Antigravity
./scripts/install.sh --target antigravity

# Install into Claude Code
./scripts/install.sh --target claude

# Install into Codex
./scripts/install.sh --target codex

# Install across all supported agents
./scripts/install.sh --target all
```

---

## Repository Structure

```text
agent-skills/
├── .agents/
│   └── skills.json             # Workspace discovery configuration
├── .github/
│   └── workflows/
│       └── validate.yml        # CI linting and automated tests
├── plugin.json                 # Antigravity plugin manifest
├── registry.json               # Indexed catalog of all skills with metadata
├── skills/                     # Flat directory of all installed skills
│   └── tlc-spec-lean/          # Spec-driven development skill
│       ├── SKILL.md
│       ├── references/
│       └── scripts/
├── templates/
│   └── skill-template/         # Boilerplate template for new skills
│       └── SKILL.md
├── scripts/
│   ├── install.ps1             # PowerShell installer
│   ├── install.sh              # Bash installer
│   └── validate.py             # Validation gate linter
├── tests/
│   └── test_foundation.py      # Automated foundation test suite
└── README.md
```

---

## Authoring a New Skill

1. Copy the template from `templates/skill-template/` into `skills/<your-skill-name>/`:
   ```bash
   cp -r templates/skill-template skills/my-new-skill
   ```
2. Update the YAML frontmatter in `SKILL.md` (`name`, `description`, and metadata).
3. Add the skill entry to `registry.json`.
4. Validate compliance with the linter:
   ```bash
   python scripts/validate.py --root .
   ```

---

## License

MIT License. See [LICENSE](LICENSE) for details.
