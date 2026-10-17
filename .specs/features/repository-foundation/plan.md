# Repository Foundation

## Problem

Developers using AI coding agents (Antigravity, Claude Code, Codex) currently lack a single, unified repository to consume both author-curated personal workflows and high-quality market-standard agent skills. Today, setting up agent skills requires manual directory hunting, manually copying files into disparate tool-specific directories (`.agents/`, `.claude/`, `~/.gemini/`), and risking broken frontmatter formatting that causes silent discovery failures.

When this foundation ships, developers will be able to clone or install the `agent-skills` package with a single command for their tool of choice, while authors will have a standardized directory structure, automated validation tooling, and unified registry indexing for publishing personal and curated skills.

## Flow

This foundation reuses the native Antigravity plugin and discovery conventions (`plugin.json` and `.agents/skills.json`) and standard shell execution environments instead of building an external package manager.

1. `<User installer command>` -> `scripts/install.sh` / `scripts/install.ps1` (door 3) - parses target agent (`--target [antigravity|claude|codex|all]`) and scope
2. `scripts/install.sh` / `scripts/install.ps1` (door 3) - validates target directory and copies skills from `skills/<skill_name>/` (door 1)
3. `scripts/validate.py` (door 4) - validates frontmatter schemas and file integrity across all skills
4. out: skills installed cleanly into target agent directories, and `.github/workflows/validate.yml` enforces quality on PRs

## Impact

| Front | What changes |
| --- | --- |
| domain | new term: `Agent Skill Package` - standardized bundle distributing skills across Antigravity, Claude Code, and Codex, lives at repository root |
| domain | new term: `Skill Origin Tag` - metadata flag (`personal` vs `curated`) indicating authorship and licensing provenance, lives in `registry.json` and SKILL.md frontmatter |
| stored data | nothing to migrate - initial repository structure creation |

## Relations

None - no stored-data shape change

## Surface

None - nothing consumed outside

## Landing

| One-way door | Literal shape | Alternative rejected |
| --- | --- | --- |
| Skills directory layout | `skills/<skill_name>/SKILL.md` flat structure (door 1) | Nested subdirectories `skills/personal/` and `skills/curated/`, which breaks Antigravity 1-level deep plugin discovery scan |
| Antigravity Plugin manifest | `plugin.json` at root with `"name": "agent-skills"` (door 2) | Nested plugin configurations, requiring users to install individual sub-plugins separately |
| Universal installer interface | `scripts/install.sh` and `scripts/install.ps1` with `--target [antigravity\|claude\|codex\|all]` (door 3) | Separate scripts per agent, which duplicates path resolution and copying logic |
| Skill quality validation gate | `scripts/validate.py` checking YAML frontmatter schema and link integrity (door 4) | Relying solely on manual pull request reviews, allowing malformed frontmatter to reach consumers |

- Nothing else in this change is hard to reverse

## Criteria

Grouped by slice - one observable outcome each, never a layer.

### S1: Repository Structure and Manifest Foundation (P1)

A standardized, discovery-ready repository architecture for Antigravity, Claude Code, and Codex.

**Acceptance Criteria**

1. The system SHALL organize all individual skills as flat directories under `skills/<skill_name>/` containing a mandatory `SKILL.md`.
2. The system SHALL provide a root `plugin.json` declaring `"name": "agent-skills"` and valid Antigravity plugin manifest metadata.
3. The system SHALL provide `.agents/skills.json` registering the workspace skills path for immediate discovery in Antigravity.
4. The system SHALL provide `registry.json` indexing all skills with `name`, `description`, `category`, `author`, and `type` (`personal` or `curated`).
5. The system SHALL provide a `templates/skill-template/SKILL.md` with standard YAML frontmatter and progressive disclosure sections.

**Independent test:** Verify file paths existence and parse `plugin.json` and `registry.json` as valid JSON.

### S2: Multi-Agent Installer Scripts (P1)

Cross-platform installation scripts allowing users to install the package into their agent of choice.

**Acceptance Criteria**

6. WHEN executed with `--target antigravity` THEN the installer script SHALL copy skills into the Antigravity discovery path.
7. WHEN executed with `--target claude` THEN the installer script SHALL copy skills into the Claude Code discovery path.
8. WHEN executed with `--target codex` THEN the installer script SHALL copy skills into the Codex agent discovery path.
9. WHEN executed with `--target all` THEN the installer script SHALL copy skills into all supported agent paths.
10. IF an unrecognized target argument is passed THEN the installer script SHALL exit with code 1 and output usage instructions.

**Independent test:** Execute `install.ps1` with dry-run/test destination parameters and verify exit codes and created files.

### S3: Skill Quality Validation and CI Automation (P2)

Automated linting and CI verification preventing broken skills from entering the package.

**Acceptance Criteria**

11. WHEN executed against `skills/` THEN `scripts/validate.py` SHALL verify that every `SKILL.md` contains valid YAML frontmatter with `name` and `description`.
12. IF any `SKILL.md` contains missing required frontmatter fields or malformed YAML THEN `scripts/validate.py` SHALL exit with code 1 and print the failing file and error message.
13. WHEN all skills pass frontmatter and file structure checks THEN `scripts/validate.py` SHALL exit with code 0.
14. The system SHALL provide `.github/workflows/validate.yml` configured to execute `scripts/validate.py` on push and pull_request events.

**Independent test:** Run `scripts/validate.py` against valid skills and assert exit 0, then against a corrupted dummy skill and assert exit 1.

## Out of scope

Product capabilities only.

| Excluded | Why |
| --- | --- |
| Direct publishing to npm, pip, or homebrew package managers | Initial release focuses on Git repository distribution and native shell installer scripts |
| Porting external market skills into `skills/` during foundation | Foundation architecture and validation must be established and verified before migrating content |

## Assumptions

| Assumption | Chosen default | Rationale | Confirmed? |
| --- | --- | --- | --- |
| Skill layout format | Flat `skills/<skill_name>/` structure with origin tags in metadata | User explicitly chose flat layout for native plugin compatibility | y |
| Target agent support | Multi-agent support (Antigravity, Claude Code, Codex) | User explicitly requested support for all three ecosystems | y |
| Default installation scope | Global user configuration (`~`) when `--local` is not passed | Users typically want curated agent skills available across all projects | n |

**Open questions:** none - all resolved or logged above.

## Observable

Worksheet of surface decisions.

| Surface | Decision | Landing |
| --- | --- | --- |
| CLI `install.sh` / `install.ps1` | invalid parameter error message and non-zero exit | AC 10 |
| CLI `install.sh` / `install.ps1` | target routing and destination paths | AC 6, AC 7, AC 8, AC 9 |
| CLI `scripts/validate.py` | exit codes and validation output reporting | AC 11, AC 12, AC 13 |
| all interactive screens | UI states | n/a - repository is a code and CLI package with no graphical user interface |

## Sources

- `User prompt and decisions` - settles flat directory layout and cross-agent targets (Antigravity, Claude, Codex)
- `Antigravity Customization System Guide` - defines `plugin.json` and 1-level deep `skills/` discovery
