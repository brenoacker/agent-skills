#!/usr/bin/env python3
"""
orchestrate.py - deterministic subagent-per-phase orchestrator for software-factory.

Keeps the main chat context window minimal (<15k tokens) by inspecting pipeline state
from on-disk `.specs/features/<feature>/` artifacts, generating self-contained prompts
for isolated phase subagents (`scout`, `planner`, `specifier`, `builder`, `verifier`,
`fixer`), running deterministic phase gates (`plan`, `checks`, `verify`), and
formatting or dispatching subagent invocations across Antigravity, Claude Code, and Codex.

Pure Python standard library, zero external dependencies.

Usage:
  python3 <skill-dir>/scripts/orchestrate.py status <feature> [--root DIR]
  python3 <skill-dir>/scripts/orchestrate.py prompt <feature> --role <role> [--root DIR] [--batch S1] [--base SHA] [--request TEXT]
  python3 <skill-dir>/scripts/orchestrate.py gate <feature> --phase <plan|checks|verify> [--root DIR] [--strict]
  python3 <skill-dir>/scripts/orchestrate.py dispatch <feature> --role <role> --agent <antigravity|claude|codex> [--dry-run] [--root DIR]

Exit codes: 0 ok, 1 gate failure / subagent failure, 2 usage error.
"""

import argparse
import json
import os
import re
import shlex
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(HERE)
ROLES = ("scout", "planner", "specifier", "builder", "verifier", "fixer")
AGENTS = ("antigravity", "claude", "codex")
GATE_PHASES = {
    "plan": "validate_plan.py",
    "checks": "validate_checks.py",
    "verify": "validate_verification.py",
}
BOUNDARY_CLOSED_RE = re.compile(r"\*\*Boundary\s*:\*\*.*closed", re.IGNORECASE)


def _run_validator(script_name, feature, root, strict=False):
    cmd = [sys.executable, os.path.join(HERE, script_name), feature, "--root", root]
    if strict:
        cmd.append("--strict")
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return proc.returncode, proc.stdout + proc.stderr


def _build_completed(checks_path):
    if not os.path.isfile(checks_path):
        return False
    with open(checks_path, "r", encoding="utf-8", errors="replace") as f:
        text = f.read()
    return bool(BOUNDARY_CLOSED_RE.search(text))


def detect_pipeline_state(feature, root):
    """Return (phase, next_role, details_dict) from on-disk .specs/features/<feature>/."""
    fdir = os.path.join(root, ".specs", "features", feature)
    plan_path = os.path.join(fdir, "plan.md")
    checks_path = os.path.join(fdir, "checks.md")
    verif_path = os.path.join(fdir, "verification.md")

    details = {
        "feature": feature,
        "feature_dir": fdir,
        "plan_exists": os.path.isfile(plan_path),
        "checks_exists": os.path.isfile(checks_path),
        "verification_exists": os.path.isfile(verif_path),
    }

    if not details["plan_exists"]:
        return "discover", "scout", details

    plan_code, _ = _run_validator("validate_plan.py", feature, root)
    details["plan_valid"] = plan_code == 0
    if plan_code != 0:
        return "plan", "planner", details

    if not details["checks_exists"]:
        return "checks", "specifier", details

    checks_code, _ = _run_validator("validate_checks.py", feature, root)
    details["checks_valid"] = checks_code == 0
    if checks_code != 0:
        return "checks", "specifier", details

    if details["verification_exists"]:
        verif_code, _ = _run_validator("validate_verification.py", feature, root)
        details["verification_valid"] = verif_code == 0
        if verif_code == 0:
            return "done", "none", details
        return "fix", "fixer", details

    if _build_completed(checks_path):
        return "verify", "verifier", details

    return "build", "builder", details


def build_isolated_prompt(feature, role, root, batch=None, base_sha=None, request_text=None):
    """Build a self-contained, zero-chat-history prompt for a specific phase subagent."""
    rel_fdir = f".specs/features/{feature}"
    plan_ref = f"{rel_fdir}/plan.md"
    checks_ref = f"{rel_fdir}/checks.md"
    verif_ref = f"{rel_fdir}/verification.md"
    diff_range = f"{base_sha}..HEAD" if base_sha else "<feature-base>..HEAD"

    header = [
        f"# Software Factory Subagent Brief — Role: {role.upper()}",
        f"Feature: `{feature}`",
        f"Artifacts directory: `{rel_fdir}`",
        "Context-isolation rule: Do NOT rely on prior chat history. Everything you need is on disk.",
        "",
    ]

    if role == "scout":
        body = [
            "## Mission (DISCOVER — Read-Only Scout)",
            f"1. Read `skills/software-factory/references/discovery.md` and `.specs/STATE.md`.",
            "2. Load confirmed lessons via `python skills/software-factory/scripts/lessons.py --root . list --status confirmed`.",
            f"3. Scan the repository modules, schemas, routes, and tests relevant to feature `{feature}`"
            + (f" (Request: {request_text})" if request_text else "."),
            "4. Return a compact (~30 lines max) ambiguity brief listing:",
            "   - Existing modules/helpers/tests to reuse",
            "   - Active `AD-NNN` decisions and confirmed lessons",
            "   - Candidate one-way doors",
            "   - Genuine product/scope gray areas across `Observable` surfaces and the 9 implicit dimensions.",
            "5. Do NOT modify any files.",
        ]
    elif role == "planner":
        body = [
            "## Mission (PLAN — Specification & Shape Author)",
            "1. Read `skills/software-factory/references/discovery.md`, `skills/software-factory/references/plan.md`, and `.specs/STATE.md`.",
            f"2. Write `{plan_ref}` with all required sections (`Problem`, `Flow`, `Impact`, `Relations`, `Surface`, `Landing`, `Criteria`, `Out of scope`, `Assumptions`, `Observable`, `Sources`).",
            "3. Ensure every row in `## Assumptions` has `Confirmed?` set to `y` (zero unconfirmed assumptions).",
            f"4. Run `python skills/software-factory/scripts/validate_plan.py {feature} --root .` and fix any errors until it exits 0.",
            "5. Stop after `validate_plan.py` exits 0 and report the summary to the Thin Orchestrator.",
        ]
    elif role == "specifier":
        body = [
            "## Mission (CHECKS — Obligation & Proof Specifier)",
            f"1. Read `{plan_ref}` and `skills/software-factory/references/checks.md`.",
            f"2. Derive `{checks_ref}` from `{plan_ref}`: numbered checks (`C1..CN`) with concrete claims and exact `Proof:` test selectors, the `## Coverage` join table, `## Swept` (all 9 dimensions), and `## Handoff` batch sizing.",
            f"3. Run `python skills/software-factory/scripts/validate_checks.py {feature} --root .` and fix any errors until it exits 0.",
            "4. Stop after `validate_checks.py` exits 0 and report the check count and batch plan to the Thin Orchestrator.",
        ]
    elif role == "builder":
        batch_label = batch or "all assigned slices"
        body = [
            f"## Mission (BUILD — Batch/Slice Builder: {batch_label})",
            f"1. Read `{plan_ref}`, `{checks_ref}`, and `skills/software-factory/references/build.md`.",
            f"2. Inspect git state (`git status --porcelain` and `git log -n 5`) to see prior batch commits.",
            f"3. For `{batch_label}`: write tests strictly from the claims and proofs in `{checks_ref}` (never from the implementation), implement the code, and run every proof command until exit 0.",
            f"4. Append `- **Boundary:** <checks> closed at <sha>` under `## Handoff` in `{checks_ref}`.",
            "5. Validate commit messages with `python skills/software-factory/scripts/check_commit.py --message \"<msg>\"` and commit your changes (no Co-Authored-By trailers).",
            f"6. Do NOT create `{verif_ref}` and do NOT launch the Verifier. Report closed checks and commit hashes back to the Thin Orchestrator.",
        ]
    elif role == "verifier":
        body = [
            "## Mission (VERIFY — Independent Verifier, author != verifier)",
            f"1. Read `{plan_ref}`, `{checks_ref}`, and `skills/software-factory/references/verify.md`.",
            f"2. Audit the diff range `{diff_range}` read-only against every check in `{checks_ref}`.",
            "3. Run every proof at `HEAD`, confirm each named test exists and ran, locate `file:line` assertion evidence per check, and perform profile-required steps (`Coverage` recompute and fault injection under `standard`/`ui`).",
            f"4. Write `{verif_ref}` and run `python skills/software-factory/scripts/validate_verification.py {feature} --root .`.",
            "5. Report the final PASS/FAIL verdict and ranked gaps (if any) back to the Thin Orchestrator.",
        ]
    elif role == "fixer":
        body = [
            "## Mission (FIX — Scoped Verification Gap Fixer)",
            f"1. Read `{verif_ref}`, `{checks_ref}`, `{plan_ref}`, and `skills/software-factory/references/build.md`.",
            f"2. Address every failed check, surviving mutant, or unproven coverage member listed in `{verif_ref}` without weakening any existing assertion or check.",
            "3. Run the covering proofs at `HEAD` and confirm they exit 0.",
            "4. Validate your commit message via `python skills/software-factory/scripts/check_commit.py --message \"<msg>\"` and commit the fix.",
            f"5. Do NOT overwrite `{verif_ref}` — stop and let the Thin Orchestrator dispatch a fresh `verifier` for the next scoped round.",
        ]
    else:
        raise ValueError(f"Unsupported role: {role}")

    return "\n".join(header + body) + "\n"


def format_agent_dispatch(agent, role, feature, prompt):
    """Return (cli_cmd_list, native_tool_hint) for the requested agent."""
    if agent == "antigravity":
        subagent_type = "research" if role == "scout" else "self"
        native = (
            f'invoke_subagent(Subagents=[{{"TypeName": "{subagent_type}", '
            f'"Role": "Software Factory {role.title()}", "Model": "inherit", '
            f'"Workspace": "inherit", "Prompt": <isolated_prompt>}}])'
        )
        cli = ["agy", "chat", "--prompt", prompt]
        return cli, native
    if agent == "claude":
        subagent_type = "Explore" if role == "scout" else "general-purpose"
        native = (
            f'Task(subagent_type="{subagent_type}", '
            f'description="Software Factory {role} ({feature})", prompt=<isolated_prompt>)'
        )
        cli = ["claude", "-p", prompt]
        return cli, native
    if agent == "codex":
        native = f'codex exec <isolated_prompt> (role={role}, feature={feature})'
        cli = ["codex", "exec", prompt]
        return cli, native
    raise ValueError(f"Unsupported agent: {agent}")


def cmd_status(args):
    root = os.path.abspath(args.root)
    phase, next_role, details = detect_pipeline_state(args.feature, root)
    print(f"Feature: {args.feature}")
    print(f"Phase: {phase}")
    print(f"Next role: {next_role}")
    print(
        f"Artifacts: plan={'yes' if details['plan_exists'] else 'no'}, "
        f"checks={'yes' if details['checks_exists'] else 'no'}, "
        f"verification={'yes' if details['verification_exists'] else 'no'}"
    )
    return 0


def cmd_prompt(args):
    root = os.path.abspath(args.root)
    prompt = build_isolated_prompt(
        feature=args.feature,
        role=args.role,
        root=root,
        batch=args.batch,
        base_sha=args.base,
        request_text=args.request,
    )
    print(prompt, end="")
    return 0


def cmd_gate(args):
    root = os.path.abspath(args.root)
    script_name = GATE_PHASES[args.phase]
    code, out = _run_validator(script_name, args.feature, root, strict=args.strict)
    if out:
        sys.stdout.write(out)
    return code


def cmd_dispatch(args):
    root = os.path.abspath(args.root)
    prompt = build_isolated_prompt(
        feature=args.feature,
        role=args.role,
        root=root,
        batch=args.batch,
        base_sha=args.base,
        request_text=args.request,
    )
    cli_cmd, native_hint = format_agent_dispatch(args.agent, args.role, args.feature, prompt)
    printable_cmd = " ".join(shlex.quote(part) for part in cli_cmd[:2]) + " <isolated-prompt>"

    if args.dry_run:
        print(f"Target agent: {args.agent}")
        print(f"Role: {args.role}")
        print(f"Native tool: {native_hint}")
        print(f"CLI command: {printable_cmd}")
        print("\n--- Isolated Prompt ---")
        print(prompt, end="")
        return 0

    proc = subprocess.run(cli_cmd, cwd=root)
    return proc.returncode


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="orchestrate.py",
        description="Deterministic subagent-per-phase orchestrator for software-factory.",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    sp_status = sub.add_parser("status", help="Inspect current pipeline phase and next recommended subagent role")
    sp_status.add_argument("feature", help="Feature name under .specs/features/<feature>")
    sp_status.add_argument("--root", default=".", help="Project root containing .specs/")
    sp_status.set_defaults(fn=cmd_status)

    sp_prompt = sub.add_parser("prompt", help="Generate a context-isolated prompt for a phase subagent")
    sp_prompt.add_argument("feature", help="Feature name under .specs/features/<feature>")
    sp_prompt.add_argument("--role", required=True, choices=ROLES, help="Subagent role")
    sp_prompt.add_argument("--batch", default=None, help="Optional slice/batch label for builder (e.g. S1)")
    sp_prompt.add_argument("--base", default=None, help="Optional base git SHA for verifier diff range")
    sp_prompt.add_argument("--request", default=None, help="Optional raw user feature request for scout")
    sp_prompt.add_argument("--root", default=".", help="Project root containing .specs/")
    sp_prompt.set_defaults(fn=cmd_prompt)

    sp_gate = sub.add_parser("gate", help="Run the deterministic validator gate for a phase")
    sp_gate.add_argument("feature", help="Feature name under .specs/features/<feature>")
    sp_gate.add_argument("--phase", required=True, choices=tuple(GATE_PHASES.keys()), help="Gate phase")
    sp_gate.add_argument("--root", default=".", help="Project root containing .specs/")
    sp_gate.add_argument("--strict", action="store_true", help="Treat warnings as errors")
    sp_gate.set_defaults(fn=cmd_gate)

    sp_dispatch = sub.add_parser("dispatch", help="Dispatch a phase subagent for antigravity, claude, or codex")
    sp_dispatch.add_argument("feature", help="Feature name under .specs/features/<feature>")
    sp_dispatch.add_argument("--role", required=True, choices=ROLES, help="Subagent role")
    sp_dispatch.add_argument("--agent", required=True, choices=AGENTS, help="Target coding agent")
    sp_dispatch.add_argument("--dry-run", action="store_true", help="Print CLI command and isolated prompt without executing")
    sp_dispatch.add_argument("--batch", default=None, help="Optional slice/batch label for builder")
    sp_dispatch.add_argument("--base", default=None, help="Optional base git SHA for verifier")
    sp_dispatch.add_argument("--request", default=None, help="Optional raw user feature request for scout")
    sp_dispatch.add_argument("--root", default=".", help="Project root containing .specs/")
    sp_dispatch.set_defaults(fn=cmd_dispatch)

    args = parser.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
