# Orchestration (Thin Orchestrator & Subagent-per-Phase)

**Goal:** run the 5-stage Software Factory (`DISCOVER -> PLAN -> CHECKS -> BUILD -> VERIFY`) without ever bloating the main chat context window.

## 1. Thin Orchestrator Rule & Context-Window Budget

Single-session coding agents degrade on multi-slice features because codebase exploration, requirements interviews, plan drafting, check derivation, test authoring, implementation, and verification all accumulate in one context window until lossy compaction fires.

To prevent context bloat, the main chat operates strictly as a **Thin Orchestrator**:

- **Main chat budget (<15k tokens):** The main chat never reads large source files, never writes `plan.md` or `checks.md` inline, and never writes implementation or test code directly.
- **Zero-chat-history handoff:** Every heavy phase runs inside a fresh, ephemeral subagent whose context starts clean. Subagents communicate exclusively through on-disk `.specs/features/<feature>/` artifacts (`plan.md`, `checks.md`, `verification.md`), `.specs/STATE.md`, and git commits (`<base>..HEAD`).
- **Deterministic state & prompt generation:** Use `python3 <skill-dir>/scripts/orchestrate.py` to inspect pipeline state (`status`), generate context-isolated subagent prompts (`prompt`), run phase gates (`gate`), or dispatch subagents across CLI environments (`dispatch`).

## 2. The 6 Ephemeral Subagent Roles

| Role | Phase | Mode | Reads from disk | Writes / Returns | Gate script |
| --- | --- | --- | --- | --- | --- |
| `scout` | `DISCOVER` | Read-only | `.specs/STATE.md`, `.specs/LESSONS.md`, target repo files | Returns a ~30-line ambiguity brief to the Thin Orchestrator | - |
| `planner` | `PLAN` | Write `.specs/` | Confirmed Discovery decisions, `.specs/STATE.md`, target files | Writes `.specs/features/<feature>/plan.md` (with all `Confirmed? y`) | `validate_plan.py` |
| `specifier` | `CHECKS` | Write `.specs/` | `.specs/features/<feature>/plan.md`, test runner configs | Writes `.specs/features/<feature>/checks.md` + `## Handoff` batches | `validate_checks.py` |
| `builder` | `BUILD` | Write repo + commit | `plan.md`, `checks.md`, git diff of prior batches | Writes tests from checks, implements slice/batch, updates `checks.md`, commits | `check_commit.py` + proof exit 0 |
| `verifier` | `VERIFY` | Read-only repo, write report | `plan.md`, `checks.md`, diff `<base>..HEAD` | Runs proofs, checks `file:line` evidence, injects faults (`standard`/`ui`), writes `verification.md` | `validate_verification.py` |
| `fixer` | `FIX` | Write repo + commit | `verification.md` ranked gaps, `checks.md`, `plan.md` | Fixes only the failing checks/mutants and commits with `check_commit.py` | `check_commit.py` |

## 3. Human Approval Boundary & Autonomous Post-Plan Loop

1. **Interactive Front-Load (`DISCOVER` -> `PLAN`):**
   - Dispatch `scout` -> receive compact ambiguity brief.
   - Interview the user in the main chat until 0 unconfirmed assumptions remain ([discovery.md](discovery.md)).
   - Dispatch `planner` -> writes `plan.md` and passes `validate_plan.py`.
   - **Quick Human Sign-off:** Present a concise summary of `plan.md` (`Flow`, `Impact`, `Landing` doors, and slice criteria) and ask the user for quick sign-off.
2. **100% Autonomous Execution Loop (`CHECKS -> BUILD -> VERIFY -> FIX`):**
   - Once the user approves `plan.md`, **do not stop for manual phase prompts**.
   - **Step A (`specifier`):** Dispatch `specifier` to write `checks.md` and run `validate_checks.py`.
   - **Step B (`builder` per batch/slice):** Read `## Handoff` in `checks.md`. Dispatch one `builder` subagent per batch/slice sequentially. Wait for each builder to report green proofs and commit hashes before launching the next batch.
   - **Step C (`verifier`):** Immediately after the final builder batch commits, dispatch a fresh `verifier` subagent over `<feature base>..HEAD`. Never let a `builder` write `verification.md`.
   - **Step D (`fixer` loop, up to 3 rounds):** If `verification.md` reports `FAIL` or `validate_verification.py` exits 1, automatically dispatch a `fixer` subagent with the ranked gaps from `verification.md`, then dispatch a fresh `verifier` for a scoped re-verification round (`Round: 2 - scoped`, up to 3 rounds max before escalating to the user).

## 4. Native Multi-Agent Dispatch Mapping (`antigravity`, `claude`, `codex`)

Generate the role's self-contained prompt via:

```bash
python3 <skill-dir>/scripts/orchestrate.py prompt <feature> --role <role> --root <project>
```

Then dispatch using the active agent environment's native subagent mechanism:

### Antigravity (`antigravity`)

Use the native `invoke_subagent` tool so each phase runs in its own isolated subagent conversation:

- For `scout`:
  - `invoke_subagent` with `TypeName: "research"` (or `"self"`), `Role: "Discovery Scout"`, `Model: "inherit"`, `Workspace: "inherit"`, `Prompt: <output of orchestrate.py prompt --role scout>`.
- For `planner`, `specifier`, `builder`, `verifier`, `fixer`:
  - `invoke_subagent` with `TypeName: "self"`, `Role: "<Phase Role>"`, `Model: "inherit"`, `Workspace: "inherit"`, `Prompt: <output of orchestrate.py prompt --role <role>>`.
- Headless / CLI fallback:
  - `agy chat --prompt "<isolated prompt>"` (previewable via `orchestrate.py dispatch <feature> --role <role> --agent antigravity --dry-run`).

### Claude Code (`claude`)

Use Claude Code's native `Task` tool (`subagent_type`) to spawn an isolated subagent context:

- For `scout`:
  - `Task(subagent_type="Explore", description="Scout <feature>", prompt="<isolated prompt>")`
- For `planner`, `specifier`, `builder`, `verifier`, `fixer`:
  - `Task(subagent_type="general-purpose", description="<Role> <feature>", prompt="<isolated prompt>")`
- Headless / CLI dispatch:
  - `claude -p "<isolated prompt>"` (via `orchestrate.py dispatch <feature> --role <role> --agent claude`).

### Codex (`codex`)

Use Codex subagent delegation or the `codex exec` CLI runner:

- Native / CLI dispatch:
  - `codex exec "<isolated prompt>"` (via `orchestrate.py dispatch <feature> --role <role> --agent codex`).

## 5. Orchestrator CLI Reference (`scripts/orchestrate.py`)

```bash
# 1. Inspect current pipeline phase (discover, plan, checks, build, verify, fix, done) and next role
python3 <skill-dir>/scripts/orchestrate.py status <feature> --root .

# 2. Generate context-isolated subagent prompt for any of the 6 roles
python3 <skill-dir>/scripts/orchestrate.py prompt <feature> --role <scout|planner|specifier|builder|verifier|fixer> --root .

# 3. Run deterministic phase gate (plan, checks, verify)
python3 <skill-dir>/scripts/orchestrate.py gate <feature> --phase <plan|checks|verify> --root .

# 4. Preview or execute CLI dispatch for antigravity, claude, or codex
python3 <skill-dir>/scripts/orchestrate.py dispatch <feature> --role builder --agent claude --dry-run --root .
```
