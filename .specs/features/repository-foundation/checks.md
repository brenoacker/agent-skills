# Repository Foundation checks

Profile: light
Plan: `.specs/features/repository-foundation/plan.md`

14 checks in 3 slices · 4 one-way doors · 0 open

## Checks

Grouped by the spec's slices; numbering runs across the whole feature.

### S1 - Repository Structure and Manifest Foundation · 5 files · 15 KB · ~4k

**C1** - All skills are stored in flat folders under `skills/<skill_name>/` containing a `SKILL.md` file (AC 1)
Proof: `python -m unittest tests/test_foundation.py -k test_skills_directory_structure`

**C2** - The root `plugin.json` specifies `"name": "agent-skills"` and valid Antigravity plugin manifest fields (AC 2)
Proof: `python -m unittest tests/test_foundation.py -k test_plugin_json_manifest`

**C3** - The file `.agents/skills.json` defines the `skills` path entry for Antigravity discovery (AC 3)
Proof: `python -m unittest tests/test_foundation.py -k test_agents_skills_json`

**C4** - The root `registry.json` indexes skill entries containing `name`, `description`, `category`, `author`, and `type` (AC 4)
Proof: `python -m unittest tests/test_foundation.py -k test_registry_json_structure`

**C5** - The file `templates/skill-template/SKILL.md` contains required YAML frontmatter and progressive disclosure sections (AC 5)
Proof: `python -m unittest tests/test_foundation.py -k test_skill_template_validity`

### S2 - Multi-Agent Installer Scripts · 2 files · 20 KB · ~5k

**C6** - Invoking installer with target antigravity copies skills to the Antigravity discovery path (AC 6)
Proof: `python -m unittest tests/test_foundation.py -k test_install_target_antigravity`

**C7** - Invoking installer with target claude copies skills to the Claude Code discovery path (AC 7)
Proof: `python -m unittest tests/test_foundation.py -k test_install_target_claude`

**C8** - Invoking installer with target codex copies skills to the Codex discovery path (AC 8)
Proof: `python -m unittest tests/test_foundation.py -k test_install_target_codex`

**C9** - Invoking installer with target all copies skills to all supported agent target paths (AC 9)
Proof: `python -m unittest tests/test_foundation.py -k test_install_target_all`

**C10** - Invoking installer with an invalid target argument exits with code 1 and prints usage (AC 10)
Proof: `python -m unittest tests/test_foundation.py -k test_install_invalid_target_fails`

### S3 - Skill Quality Validation and CI Automation · 2 files · 18 KB · ~5k

**C11** - Running `scripts/validate.py` on valid skills verifies YAML frontmatter schema without errors (AC 11)
Proof: `python -m unittest tests/test_foundation.py -k test_validate_script_passes_valid_skills`

**C12** - Running `scripts/validate.py` against a malformed skill outputs error details and exits with code 1 (AC 12)
Proof: `python -m unittest tests/test_foundation.py -k test_validate_script_fails_corrupted_skill`

**C13** - Running `scripts/validate.py` exits with code 0 when all skills in repository are compliant (AC 13)
Proof: `python -m unittest tests/test_foundation.py -k test_validate_script_clean_repo_exit_zero`

**C14** - The GitHub Actions workflow `.github/workflows/validate.yml` is configured to run `scripts/validate.py` on push and pull_request (AC 14)
Proof: `python -m unittest tests/test_foundation.py -k test_github_workflow_configuration`

## Coverage

| Set (size) | Member -> proof | Unproven |
| --- | --- | --- |
| target agents supported (3) | antigravity C6 · claude C7 · codex C8 | - |
| manifest configurations (3) | plugin.json C2 · skills.json C3 · registry.json C4 | - |
| validation exit outcomes (2) | valid exit 0 C13 · invalid exit 1 C12 | - |
| installer target options (4) | antigravity C6 · claude C7 · codex C8 · all C9 | - |
| landing one-way doors (4) | flat layout C1 · root plugin manifest C2 · universal installer C6 · validation gate C11 | - |

- Claims naming a configuration format, exit code, or copy path have proofs exercising exact conditions.
- No other check claims more than the single case its proof exercises.

## Swept

Where each unwritten requirement landed. All nine, one line each, every time.

- validation: C11, C12
- failure modes: C10, C12
- idempotency: C6, C7
- authorization: n/a - local filesystem scripts with no authentication requirement
- concurrency: n/a - single user CLI operations
- data lifecycle: n/a - static file structure and scripts with no persistent database
- dependency failure: n/a - relies solely on Python standard library and standard shell capabilities
- state transitions: n/a - single-shot deterministic scripts
- observability: C12, C13

## Handoff

- S1 = 4k; S2 = 5k; S3 = 5k -> 14k total, under the 150k budget - one builder
- Mechanism: one builder
