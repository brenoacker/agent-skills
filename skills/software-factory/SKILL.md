---
name: software-factory
description: 'End-to-end multi-agent Software Factory (DISCOVER -> PLAN -> CHECKS -> BUILD -> VERIFY) with a Thin-Orchestrator subagent-per-phase architecture across Antigravity, Claude Code, and Codex. Freezes obligations with EARS criteria and proof-backed checks, delegates every heavy phase to fresh isolated subagents to protect the main context window, and gates completion with an independent Verifier. Use when the user says "software-factory", "discover feature", "plan feature", "specify feature", "write the checks", "build this plan", or "verify work".'
license: MIT
metadata:
  author: brenoacker
  version: '2.0.0'
---

# Software Factory

Close every scope doubt first. Freeze the obligations. Delegate every heavy phase to a fresh subagent. Prove completion with an independent Verifier who did not write the code.

```
┌──────────┐   ┌──────┐   ┌────────┐   ┌───────┐   ┌────────┐
│ DISCOVER │ → │ PLAN │ → │ CHECKS │ → │ BUILD │ → │ VERIFY │
└──────────┘   └──────┘   └────────┘   └───────┘   └────────┘
 0 doubts       confirm    obligations   batches     author != verifier
```

Five moves, three durable artifacts under `.specs/features/<feature>/`, and a **Thin Orchestrator** in the main chat that never bloats its context window.

1. **DISCOVER**: A read-only `scout` subagent scans the codebase and returns a compact (~30-line) ambiguity brief. The main chat interviews the user with concrete options and recommended defaults until **zero unconfirmed assumptions** remain (`Confirmed? y` for every row). See [discovery.md](./references/discovery.md).
2. **PLAN**: A `planner` subagent writes `.specs/features/<feature>/plan.md` (Problem, Flow, Impact, Relations, Surface, Landing, Criteria, Out of scope, Assumptions, Observable, Sources) and runs `validate_plan.py`. The user gives a quick sign-off on `plan.md`. See [plan.md](./references/plan.md).
3. **CHECKS**: After `plan.md` sign-off, the autonomous post-plan loop begins. A `specifier` subagent derives `.specs/features/<feature>/checks.md` (claims + proofs, Coverage join, Test policy, Swept, Handoff arithmetic) and runs `validate_checks.py`. See [checks.md](./references/checks.md).
4. **BUILD**: One `builder` subagent per slice/batch writes tests strictly from the checks, implements the code, runs proofs, updates `checks.md`, and commits using `check_commit.py`. See [build.md](./references/build.md).
5. **VERIFY (and FIX loop)**: An independent `verifier` subagent (never the builder) audits `<feature base>..HEAD` against every check, writes `.specs/features/<feature>/verification.md`, and runs `validate_verification.py`. If any check fails, a `fixer` subagent resolves the ranked gaps and a fresh `verifier` re-verifies (up to 3 rounds). See [verify.md](./references/verify.md) and [orchestration.md](./references/orchestration.md).

## Why this shape

Coding agents fail on complex features for two predictable reasons:
1. **Context window bloat**: When a single chat session explores the repo, interviews the user, writes the plan, derives checks, writes tests and code, and verifies its own work, the context window fills up and triggers lossy compaction.
2. **Unconfirmed requirements & self-review blind spots**: Silently guessing product behavior (`Confirmed? n`) or letting the author self-certify completion ships the author's own blind spots.

`software-factory` solves both:
- **Thin Orchestrator (<15k tokens in main chat)**: The main chat acts strictly as coordinator and user interviewer. All codebase reading, artifact authoring, coding, testing, and verification run inside isolated ephemeral subagents (`scout`, `planner`, `specifier`, `builder`, `verifier`, `fixer`) that communicate exclusively via `.specs/features/<feature>/` files on disk and git commits. Full dispatch protocol: [orchestration.md](./references/orchestration.md).
- **Small, frozen obligation set + independent Verifier**: There is no granular task checklist or component catalogue (`Purpose`/`Location`/`Interfaces` per class) to go stale. One-way doors get a literal shape in `Landing`; reversible placement is decided in the diff.

## Critical rules

The pinned set. These hold at every profile:

1. **Zero unconfirmed assumptions (`Confirmed? y`).** Never guess product or scope behavior silently. Every gray area surfaced during `DISCOVER` must be asked with concrete options and a recommended default, or explicitly delegated by the user (`Confirmed? y`). `validate_plan.py` rejects any row where `Confirmed?` is `n` or blank.
2. **Thin Orchestrator isolation.** Keep the main chat under ~15k tokens. Delegate repo exploration (`scout`), plan drafting (`planner`), check derivation (`specifier`), coding (`builder`), auditing (`verifier`), and gap repair (`fixer`) to fresh subagents via native agent tools (`invoke_subagent` in Antigravity, `Task` in Claude Code) or `scripts/orchestrate.py`.
3. **Every check is one observable claim with a concrete value plus the proof** — the exact test selector or command whose exit code settles it. No proof, no check.
4. **Tests assert what the checks say, never what the code happens to do.** Never write a test by reading the implementation.
5. **Never weaken an assertion, delete a test, or skip one to make a suite pass.** A genuinely wrong check is a stop-and-ask, not an edit.
6. **Checks and `Test policy` rows are fixed once approved.** In `plan.md`, `Landing`, `Relations`, and `Surface` are additive — a door discovered while building gets a row before the code that closes it, and a row the user approved is never rewritten. `Flow` and `Impact` are **kept true** in the commit that changes the path.
7. **The Verifier is a fresh subagent**, never the author, never optional, never waiting to be asked. The Orchestrator dispatches it immediately after the last commit of the feature lands over `<feature base>..HEAD` with every check.
8. **The profile is a floor and is enforced by `validate_verification.py`.**
9. **The completion gate is a script, not a feeling:** `validate_verification.py` must exit 0.
10. **Blast radius:** an approved spec authorizes local edits and local commits. `git push`, deploy, and production data changes need an explicit go-ahead for that action.

## Profile

The project declares how much runs, in `AGENTS.md` or equivalent. Absent a declaration: `light`.

```markdown
## software-factory

profile: light
budget: 150k
```

| Profile | Adds | Cannot catch |
| --- | --- | --- |
| `light` (default) | proofs run at `HEAD` with each named test shown to exist and run, one located assertion per check, level and sampling gaps, `Swept existing` re-read | a set member with no proof; a test that would pass under a wrong implementation |
| `standard` | the `Coverage` join recomputed, `Test policy` rows with a verdict each, one fault per assertion surface | a check that contradicts a binding source; a screen nobody built |
| `ui` | binding sources opened and compared, per-screen enumeration of copy **and** arrangement | only spacing, colour and type weight, enumerated per screen |

`validate_verification.py` fails a report whose profile differs from the one `checks.md` was approved under, fails a `standard` report with no fault rows or no recomputed coverage, and fails a `ui` report with no binding-sources section.

## Artifacts

```
.specs/
├── STATE.md                    # Decisions log (AD-NNN) + Handoff snapshot
├── LESSONS.md                  # rendered by scripts/lessons.py - never hand-edit
├── lessons.json                # machine-owned
└── features/<feature>/
    ├── plan.md                 # problem, flow, impact, relations, surface, landing, criteria, assumptions (all y), observable
    ├── checks.md               # claims + proofs, coverage join, test policy, swept, handoff batches
    └── verification.md         # the independent Verifier's report
```

Create each file when its phase produces content. For a change under roughly three files with no one-way door and zero scope ambiguity, write only `checks.md` with an `## Intent` paragraph and skip `plan.md`.

## Fivebounded design sections in `plan.md`

| Section | Reviews | Kept out |
| --- | --- | --- |
| `Flow` | the path, one line per hop | any module that neither exists nor is created by a door - that is placement |
| `Impact` | what changes underneath: terms, and existing data | risk registers |
| `Relations` | entities, cardinality, one-way constraints | columns and types |
| `Surface` | route, in, out, statuses | request-body specification, and check ids - those do not exist yet |
| `Landing` | the one-way doors, with the literal shape and the rejected alternative | anything a refactor reverses |

## Flow

- **Discover** — Dispatch the read-only `scout` subagent to inspect the repo, `.specs/STATE.md`, and `.specs/LESSONS.md` and return a ~30-line ambiguity brief. Walk the user through genuine product and scope gray areas (at most 2 questions per turn, concrete options with recommended default) across `Observable` surfaces and the 9 implicit dimensions until 0 doubts remain: [discovery.md](./references/discovery.md).
- **Plan** — Dispatch the `planner` subagent with the confirmed discovery decisions to write `.specs/features/<feature>/plan.md` and pass `validate_plan.py`. Present `plan.md` to the user for quick sign-off: [plan.md](./references/plan.md).
- **Checks** — Once `plan.md` is approved, run autonomously. Dispatch the `specifier` subagent to derive `.specs/features/<feature>/checks.md` (claims + proofs, `Coverage` join, `Swept`, and `## Handoff` batch sizing) and pass `validate_checks.py`: [checks.md](./references/checks.md).
- **Build** — Dispatch one `builder` subagent per batch/slice sequentially. Each builder writes tests from the checks, implements, runs proofs, records `Boundary` in `checks.md`, and commits with `check_commit.py`: [build.md](./references/build.md).
- **Verify & Fix** — Dispatch a fresh `verifier` subagent over `<feature base>..HEAD` to write `verification.md` and run `validate_verification.py`. If FAIL, dispatch a `fixer` subagent and re-verify (up to 3 rounds): [verify.md](./references/verify.md).
- **Orchestration & Subagent Dispatch** — Thin-Orchestrator rules, context-window budgets, and multi-agent mappings (`antigravity`, `claude`, `codex`): [orchestration.md](./references/orchestration.md).
- **Durable Memory** — Project decisions (`STATE.md`), session handoff, and verification-grounded lessons (`lessons.py`): [memory.md](./references/memory.md).

## Scripts

Resolve `<skill-dir>` as the directory containing this `SKILL.md` and invoke `python3 <skill-dir>/scripts/<name>.py`. Pass `--root` when cwd differs from the project root. A non-zero exit means STOP and fix.

| When | Command |
| --- | --- |
| Inspect pipeline phase & next subagent role | `orchestrate.py status <feature> --root <dir>` |
| Generate isolated subagent prompt | `orchestrate.py prompt <feature> --role <scout\|planner\|specifier\|builder\|verifier\|fixer> --root <dir>` |
| Run phase gate via orchestrator | `orchestrate.py gate <feature> --phase <plan\|checks\|verify> --root <dir>` |
| Dispatch subagent via CLI (or `--dry-run`) | `orchestrate.py dispatch <feature> --role <role> --agent <antigravity\|claude\|codex> [--dry-run]` |
| Before presenting `plan.md` | `validate_plan.py <feature>` |
| Before starting `BUILD` | `validate_checks.py <feature>` |
| Before each commit | `check_commit.py --message "<msg>"` |
| Before declaring done | `validate_verification.py <feature>` |
| At distillation | `lessons.py add ...` |
| After editing a validator, script, or template | `selftest.py` |

## Subagents and handoff

Every phase is isolated in its own subagent context (`scout`, `planner`, `specifier`, `builder`, `verifier`, `fixer`). During `BUILD`, pack whole slices into batches under the declared `budget` (default 150k tokens) or dispatch one `builder` per slice (`S1`, `S2`, ...) so each builder starts with a clean context window and reads only `plan.md`, `checks.md`, and the git diff of prior batches.

When the final builder batch returns green, the Orchestrator immediately dispatches the independent `verifier` subagent in the same turn without asking the user.

## Knowledge chain

In strict order: existing code and conventions, project docs, library documentation (Context7 where available), web search, then flag as uncertain. Never invent an API, a flag, a command, or a behaviour.

## Output behaviour

Produce the artifact; do not narrate the phase. Lead with the verdict. State decisions definitively. Cut filler and mechanical hedging. Keep section headings in English (they are a schema verified by the gates).
