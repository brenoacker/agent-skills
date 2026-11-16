# Discover

**Goal:** eliminate 100% of product, scope, and behavioral ambiguity **before** writing `plan.md`, while keeping the main chat context window clean.

In the 5-stage Software Factory pipeline (`DISCOVER -> PLAN -> CHECKS -> BUILD -> VERIFY`), `DISCOVER` is the interactive front door. Nothing enters `PLAN` with unconfirmed guesses (`Confirmed? n`).

## 1. Scout Subagent Handoff (Protect the Main Chat Context)

The main chat acts as a **Thin Orchestrator** and never reads dozens of repository files directly. Reading the codebase in the main chat pollutes the context window before the feature even starts.

Instead, as soon as the user requests a feature:

1. **Dispatch the `scout` subagent** (read-only explorer) via the host agent's subagent tool (`invoke_subagent` with `research`/`self` in Antigravity, `Task` with `Explore` in Claude Code, or `orchestrate.py dispatch <feature> --role scout`).
2. **What the `scout` reads:**
   - `.specs/STATE.md` (`## Decisions` — active `AD-NNN` constraints and `## Handoff`).
   - Confirmed lessons via `python3 <skill-dir>/scripts/lessons.py --root <project> list --status confirmed`.
   - Relevant modules, routes, schemas, CLI entrypoints, and test runners touched by the request.
3. **What the `scout` returns (~30 lines max):**
   - **Existing reuse candidates**: modules, helpers, validators, and test commands already in the repo.
   - **Active `AD-NNN` constraints & confirmed lessons** that bind this feature.
   - **Candidate one-way doors**: schema changes, external contracts, or new dependencies.
   - **Ranked gray areas**: genuine product/scope decisions that the codebase and conventions do NOT settle.

## 2. Facts vs. Decisions

- **Facts you look up (via `scout`); decisions you ask.** Anything the repository already answers — naming conventions, existing routes, test frameworks, schema shapes — is resolved by the `scout` subagent without bothering the user.
- **Never guess product or scope behavior silently.** A decision is a genuine gray area when:
  1. It belongs to product, scope, UX, or contract behavior,
  2. More than one defensible option exists, and
  3. Existing code and active `AD-NNN` decisions do not settle it.

## 3. Two Systematic Enumerations that Find Every Gray Area

Asking "are there any edge cases?" finds nothing. Walk both fixed enumerations against the `scout` brief to surface what the user's prompt left unsaid:

### Enumeration A: `Observable` Surfaces

Every external surface exposes a fixed set of decisions:

| Surface | Decisions to verify |
| --- | --- |
| **Screen or view** | empty, loading, error, and unauthorized states; density and ordering; confirmation on destructive actions |
| **API or webhook** | request/response signature, error payload shape and status codes, authorization, versioning, rate limits |
| **CLI command or task** | output format and verbosity, flags and defaults, exit codes (`0`, `1`, `2`), partial-failure output |
| **Document or skill** | structure, tone, required sections, and what the reader or agent executes next |
| **Collection** | grouping criterion, naming, ordering, duplicate handling, and exceptions |

### Enumeration B: The 9 Implicit Dimensions

Walk all nine system dimensions before concluding discovery:

| Dimension | What to check during Discovery |
| --- | --- |
| `validation` | input bounds, limits, formats, schema or frontmatter validation rules |
| `failure modes` | timeouts, partial writes, rollbacks, actionable error messages |
| `idempotency` | safe retries, deduplication keys, repeated command runs |
| `authorization` | who may invoke the surface, permission boundaries, blast-radius guards |
| `concurrency` | race conditions, parallel execution safety, locking or ordering |
| `data lifecycle` | migration of existing data, archival, deletion, cleanup of legacy files |
| `dependency failure` | fallback behavior when an external tool, API, or binary is unavailable |
| `state transitions` | valid phase/status transitions, guards against invalid jumps |
| `observability` | structured status output, dry-run inspection, logs, and verification evidence |

Each surface item and each of the 9 dimensions must resolve to:
- a confirmed requirement (`AC <n>`),
- an existing mechanism (`existing - <module/guard>`), or
- an explicit `n/a - <concrete reason>`.

## 4. Structured Questioning Protocol

When the `scout` brief and the two enumerations reveal genuine gray areas, interview the user in the main chat following strict rules:

1. **Concrete options, never open-ended prompts.** Present 2–3 clear choices per question (use the host's structured question tool when available, or concise numbered options).
2. **Lead with `(Recommended)` and one line of rationale.** Ground the recommendation in what the `scout` found in the repo.
3. **Batch at most 1–4 high-leverage questions per turn.** Group independent questions together; ask dependent questions one at a time when the first answer prunes the rest.
4. **"You decide" is a valid confirmation.** If the user delegates a choice, record the recommended default in `## Assumptions` with rationale `user delegated during discovery` and `Confirmed? y`.
5. **Loop until zero doubts remain.** If an answer uncovers a follow-up ambiguity, ask it immediately. Do not proceed to `PLAN` while any scope or product question is unconfirmed.

## 5. The Confirmed-Scope Gate (`Confirmed? y`)

When `DISCOVER` finishes, every row in `plan.md`'s `## Assumptions` table MUST carry `Confirmed?` set to `y`:

```markdown
## Assumptions

| Assumption | Chosen default | Rationale | Confirmed? |
| --- | --- | --- | --- |
| <decision> | <confirmed choice> | <user confirmed / delegated in discovery> | y |
```

`validate_plan.py` enforces this gate deterministically:
- Any assumption row where `Confirmed?` is `n`, `no`, or blank is a **hard gate error** (`exit 1`).
- Once `DISCOVER` is complete, the Thin Orchestrator dispatches the `planner` subagent with the confirmed decisions to write `.specs/features/<feature>/plan.md` and run `validate_plan.py`.
