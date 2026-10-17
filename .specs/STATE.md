# Project state

## Decisions

| ID | Decision | Rationale | Status | Date |
| --- | --- | --- | --- | --- |
| AD-001 | Skills maintain a flat layout under `skills/<skill_name>/` with origin/type tracked in metadata | Complies with Antigravity 1-level deep plugin discovery while keeping all skills addressable uniformly | active | 2026-10-17 |
| AD-002 | Package installation targets Antigravity, Claude Code, and Codex | Allows maximum reach across developers using different AI coding tools from a single curated repository | active | 2026-10-17 |
| AD-003 | Unify spec-driven workflow into `skills/software-factory/` with active `DISCOVER` phase and mandatory `Confirmed? y` plan gate | Eliminates third-party branding and forbids unconfirmed product guesses (`Confirmed? n`) from entering `CHECKS` or `BUILD` | active | 2026-10-17 |
| AD-004 | Enforce Thin-Orchestrator subagent-per-phase execution (`scout`, `planner`, `specifier`, `builder`, `verifier`, `fixer`) via native subagent tools and `scripts/orchestrate.py` | Keeps the main chat context window under ~15k tokens and prevents lossy context compaction across multi-slice features | active | 2026-10-17 |

## Handoff

**Feature**: software-factory
**Where**: C1-C12 built, awaiting independent Verifier
**In progress**: none
**Next step**: Dispatch independent Verifier over `software-factory` to produce `.specs/features/software-factory/verification.md`
**Blockers**: none
**Uncommitted**: none
**Branch**: main
