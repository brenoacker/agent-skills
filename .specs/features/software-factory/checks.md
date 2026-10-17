# Software Factory checks

Profile: light
Plan: `.specs/features/software-factory/plan.md`

12 checks in 3 slices · 4 one-way doors · 0 open

## Checks

Grouped by the spec's slices; numbering runs across the whole feature.

### S1 - Rebrand and Unify into `software-factory` · 4 files · 25 KB · ~7k

**C1** - `skills/software-factory/SKILL.md` declares frontmatter `name: software-factory` and `skills/tlc-spec-lean/` is removed (AC 1)
Proof: `python -m unittest tests/test_software_factory.py -k test_skill_directory_and_frontmatter`

**C2** - Zero occurrences of `tlc-spec-lean`, `Tech Leads Club`, `tech-leads-club`, or `Felipe Rodrigues` exist across `skills/software-factory/`, `registry.json`, `plugin.json`, and `README.md` (AC 2)
Proof: `python -m unittest tests/test_software_factory.py -k test_zero_legacy_branding_references`

**C3** - Running `python scripts/validate.py --root .` exits with code 0 and validates `software-factory` in `skills/`, `registry.json`, and `plugin.json` (AC 3)
Proof: `python -m unittest tests/test_software_factory.py -k test_repository_validator_passes_software_factory`

### S2 - Active Discovery Phase and Confirmed-Scope Gate · 2 files · 18 KB · ~5k

**C4** - `skills/software-factory/references/discovery.md` defines the Scout subagent handoff, the 5-stage flow (`DISCOVER -> PLAN -> CHECKS -> BUILD -> VERIFY`), and structured questioning rules across `Observable` surfaces and the 9 implicit dimensions (AC 4)
Proof: `python -m unittest tests/test_software_factory.py -k test_discovery_reference_completeness`

**C5** - Running `validate_plan.py` against a `plan.md` with an assumption row where `Confirmed?` is `n` or blank exits with code 1 and reports an unconfirmed assumption error (AC 5)
Proof: `python -m unittest tests/test_software_factory.py -k test_validate_plan_rejects_unconfirmed_assumption`

**C6** - Running `validate_plan.py` against a structurally valid `plan.md` where all assumption rows have `Confirmed?` set to `y` exits with code 0 (AC 6)
Proof: `python -m unittest tests/test_software_factory.py -k test_validate_plan_accepts_confirmed_assumptions`

### S3 - Subagent-per-Phase Hybrid Orchestration (`orchestrate.py` + `orchestration.md`) · 3 files · 42 KB · ~12k

**C7** - `skills/software-factory/references/orchestration.md` defines the Thin-Orchestrator rules, context-window budget rules, autonomous post-plan execution loop, and native subagent dispatch mappings for `antigravity`, `claude`, and `codex` across all 6 roles (`scout`, `planner`, `specifier`, `builder`, `verifier`, `fixer`) (AC 7)
Proof: `python -m unittest tests/test_software_factory.py -k test_orchestration_reference_completeness`

**C8** - Running `orchestrate.py status <feature> --root <dir>` outputs the current pipeline phase (`discover`, `plan`, `checks`, `build`, `verify`, `fix`, or `done`) and next recommended subagent role, and exits with code 0 (AC 8)
Proof: `python -m unittest tests/test_software_factory.py -k test_orchestrate_status_phases`

**C9** - Running `orchestrate.py prompt <feature> --role <scout|planner|specifier|builder|verifier|fixer> --root <dir>` generates a self-contained, context-isolated prompt referencing only on-disk `.specs/features/<feature>/` artifacts and git state, and exits with code 0 (AC 9)
Proof: `python -m unittest tests/test_software_factory.py -k test_orchestrate_prompt_all_roles`

**C10** - Running `orchestrate.py gate <feature> --phase <plan|checks|verify> --root <dir>` executes the corresponding validator script and propagates its exit code (`0`, `1`, or `2`) (AC 10)
Proof: `python -m unittest tests/test_software_factory.py -k test_orchestrate_gate_phases`

**C11** - Running `orchestrate.py dispatch <feature> --role <scout|planner|specifier|builder|verifier|fixer> --dry-run --agent <antigravity|claude|codex>` prints the exact CLI command and isolated prompt for that target agent and exits with code 0 (AC 11)
Proof: `python -m unittest tests/test_software_factory.py -k test_orchestrate_dispatch_dry_run_agents`

**C12** - Running `skills/software-factory/scripts/selftest.py` executes all baseline, fault-injection, negative-control, and tooling checks (including `orchestrate.py` over all 6 subagent roles and the unconfirmed-assumption mutant) and exits with code 0 (AC 12)
Proof: `python -m unittest tests/test_software_factory.py -k test_selftest_script_passes`

## Coverage

| Set (size) | Member -> proof | Unproven |
| --- | --- | --- |
| landing one-way doors (4) | unified skill directory C1 · confirmed-scope gate C5 · subagent-per-phase architecture C7 · hybrid orchestrator CLI C8 | - |
| subagent roles (6) | scout C9 · planner C9 · specifier C9 · builder C9 · verifier C9 · fixer C9 | - |
| orchestrate.py subcommands (4) | status C8 · prompt C9 · gate C10 · dispatch C11 | - |
| target agents (3) | antigravity C11 · claude C11 · codex C11 | - |
| Confirmed? assumption states (2) | y C6 · n C5 | - |
| orchestrate.py gate phases (3) | plan C10 · checks C10 · verify C10 | - |
| pipeline status phases (7) | discover C8 · plan C8 · checks C8 · build C8 · verify C8 · fix C8 · done C8 | - |
| prohibited legacy terms (4) | tlc-spec-lean C2 · Tech Leads Club C2 · tech-leads-club C2 · Felipe Rodrigues C2 | - |

- Claims naming a CLI subcommand, exit code, role, or target agent have proofs exercising exact conditions.
- No other check claims more than the single case its proof exercises.

## Swept

Where each unwritten requirement landed. All nine, one line each, every time.

- validation: C3, C5, C6, C10
- failure modes: C5, C10, C12
- idempotency: C8, C9, C11
- authorization: n/a - local CLI scripts and markdown skill files with no authentication or user roles
- concurrency: n/a - sequential phase-by-phase subagent orchestration over local filesystem artifacts
- data lifecycle: C1, C2
- dependency failure: n/a - pure Python standard library scripts with zero external runtime dependencies
- state transitions: C8, C10
- observability: C8, C11, C12

## Handoff

- S1 = 7k; S2 = 5k; S3 = 12k -> 24k total, under the 150k budget - one builder
- Mechanism: one builder
- **Boundary:** C1-C12 closed at `HEAD`
- **Settled mid-build:** none — all scope decisions were confirmed in `plan.md` prior to build
- **Abandoned:** none
