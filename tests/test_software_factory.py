import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL_DIR = REPO_ROOT / "skills" / "software-factory"
SCRIPTS_DIR = SKILL_DIR / "scripts"
REFS_DIR = SKILL_DIR / "references"
FIXTURES_DIR = SCRIPTS_DIR / "fixtures"


class TestSoftwareFactory(unittest.TestCase):

    def test_skill_directory_and_frontmatter(self):
        """C1: skills/software-factory/SKILL.md declares frontmatter name: software-factory and skills/tlc-spec-lean/ is removed."""
        legacy_dir = REPO_ROOT / "skills" / "tlc-spec-lean"
        self.assertFalse(legacy_dir.exists(), "Legacy skills/tlc-spec-lean/ directory must be removed")

        skill_md = SKILL_DIR / "SKILL.md"
        self.assertTrue(skill_md.is_file(), "skills/software-factory/SKILL.md must exist")
        content = skill_md.read_text(encoding="utf-8")
        self.assertTrue(content.startswith("---"), "SKILL.md must start with YAML frontmatter")
        frontmatter = content.split("---", 2)[1]
        self.assertIn("name: software-factory", frontmatter)

    def test_zero_legacy_branding_references(self):
        """C2: Zero occurrences of prohibited legacy terms exist across skills/software-factory/, registry.json, plugin.json, and README.md."""
        prohibited = (
            "tlc-spec-lean",
            "Tech Leads Club",
            "tech-leads-club",
            "Felipe Rodrigues",
        )
        targets = [
            REPO_ROOT / "registry.json",
            REPO_ROOT / "plugin.json",
            REPO_ROOT / "README.md",
        ]
        if SKILL_DIR.is_dir():
            for root, _dirs, files in os.walk(SKILL_DIR):
                for file in files:
                    if file.endswith((".md", ".py", ".json")):
                        targets.append(Path(root) / file)

        for path in targets:
            self.assertTrue(path.is_file(), f"Expected target file to exist: {path}")
            text = path.read_text(encoding="utf-8")
            for term in prohibited:
                self.assertNotIn(
                    term.lower(),
                    text.lower(),
                    f"Prohibited legacy term '{term}' found in {path.relative_to(REPO_ROOT)}",
                )

    def test_repository_validator_passes_software_factory(self):
        """C3: Running python scripts/validate.py --root . exits with code 0 and validates software-factory in skills/, registry.json, and plugin.json."""
        validate_script = REPO_ROOT / "scripts" / "validate.py"
        res = subprocess.run(
            [sys.executable, str(validate_script), "--root", str(REPO_ROOT)],
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 0, f"validate.py failed: {res.stdout}\n{res.stderr}")
        self.assertIn("Validation PASSED", res.stdout)

        registry = json.loads((REPO_ROOT / "registry.json").read_text(encoding="utf-8"))
        skill_names = [s.get("name") for s in registry.get("skills", [])]
        self.assertIn("software-factory", skill_names)
        self.assertNotIn("tlc-spec-lean", skill_names)

        plugin = json.loads((REPO_ROOT / "plugin.json").read_text(encoding="utf-8"))
        prompts_blob = " ".join(plugin.get("suggestedPrompts", []))
        self.assertIn("software-factory", prompts_blob)

    def test_discovery_reference_completeness(self):
        """C4: skills/software-factory/references/discovery.md defines Scout handoff, 5-stage flow, Observable surfaces, and 9 implicit dimensions."""
        discovery_md = REFS_DIR / "discovery.md"
        self.assertTrue(discovery_md.is_file(), "references/discovery.md must exist")
        text = discovery_md.read_text(encoding="utf-8")

        self.assertIn("DISCOVER -> PLAN -> CHECKS -> BUILD -> VERIFY", text)
        self.assertIn("scout", text.lower())
        self.assertIn("Observable", text)
        self.assertIn("Confirmed?", text)

        dimensions = (
            "validation",
            "failure modes",
            "idempotency",
            "authorization",
            "concurrency",
            "data lifecycle",
            "dependency failure",
            "state transitions",
            "observability",
        )
        for dim in dimensions:
            self.assertIn(dim, text.lower(), f"discovery.md must cover implicit dimension '{dim}'")

    def test_validate_plan_rejects_unconfirmed_assumption(self):
        """C5: validate_plan.py exits with code 1 and reports an unconfirmed assumption error when Confirmed? is n or blank."""
        validate_plan = SCRIPTS_DIR / "validate_plan.py"
        fixture_plan = (FIXTURES_DIR / "plan.md").read_text(encoding="utf-8")

        for bad_val in ("n", ""):
            with tempfile.TemporaryDirectory() as tmp:
                fdir = Path(tmp) / ".specs" / "features" / "billing"
                fdir.mkdir(parents=True)
                mutated = fixture_plan.replace(
                    "| the provider already retried 3 times before it reports a failure | y |",
                    f"| the provider already retried 3 times before it reports a failure | {bad_val} |",
                    1,
                )
                (fdir / "plan.md").write_text(mutated, encoding="utf-8")
                res = subprocess.run(
                    [sys.executable, str(validate_plan), "billing", "--root", tmp],
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(res.returncode, 1, f"Expected exit 1 for Confirmed?='{bad_val}', got {res.returncode}")
                self.assertIn("unconfirmed", (res.stdout + res.stderr).lower())

    def test_validate_plan_accepts_confirmed_assumptions(self):
        """C6: validate_plan.py exits with code 0 when all assumption rows have Confirmed? set to y and structural checks pass."""
        validate_plan = SCRIPTS_DIR / "validate_plan.py"
        with tempfile.TemporaryDirectory() as tmp:
            fdir = Path(tmp) / ".specs" / "features" / "billing"
            fdir.mkdir(parents=True)
            shutil.copyfile(FIXTURES_DIR / "plan.md", fdir / "plan.md")
            res = subprocess.run(
                [sys.executable, str(validate_plan), "billing", "--root", tmp],
                capture_output=True,
                text=True,
            )
            self.assertEqual(res.returncode, 0, f"Expected exit 0, got {res.returncode}: {res.stdout}\n{res.stderr}")
            self.assertIn("0 error(s)", res.stdout)

    def test_orchestration_reference_completeness(self):
        """C7: references/orchestration.md defines Thin-Orchestrator rules, context-window budget rules, autonomous post-plan loop, and native dispatch mappings for antigravity, claude, and codex across all 6 roles."""
        orch_md = REFS_DIR / "orchestration.md"
        self.assertTrue(orch_md.is_file(), "references/orchestration.md must exist")
        text = orch_md.read_text(encoding="utf-8")
        low = text.lower()

        self.assertIn("thin orchestrator", low)
        self.assertIn("invoke_subagent", text)
        self.assertIn("Task", text)

        for role in ("scout", "planner", "specifier", "builder", "verifier", "fixer"):
            self.assertIn(role, low, f"orchestration.md must define role '{role}'")

        for agent in ("antigravity", "claude", "codex"):
            self.assertIn(agent, low, f"orchestration.md must define dispatch mapping for '{agent}'")

    def test_orchestrate_status_phases(self):
        """C8: orchestrate.py status <feature> --root <dir> outputs current pipeline phase (discover, plan, checks, build, verify, fix, done) and next recommended role, exiting 0."""
        orchestrate = SCRIPTS_DIR / "orchestrate.py"
        fixture_plan = (FIXTURES_DIR / "plan.md").read_text(encoding="utf-8")
        fixture_checks = (FIXTURES_DIR / "checks.md").read_text(encoding="utf-8")
        fixture_verif = (FIXTURES_DIR / "verification.md").read_text(encoding="utf-8")

        with tempfile.TemporaryDirectory() as tmp:
            fdir = Path(tmp) / ".specs" / "features" / "billing"

            # 1. discover: feature dir missing or no plan.md yet
            res = subprocess.run(
                [sys.executable, str(orchestrate), "status", "billing", "--root", tmp],
                capture_output=True,
                text=True,
            )
            self.assertEqual(res.returncode, 0)
            self.assertIn("Phase: discover", res.stdout)
            self.assertIn("Next role: scout", res.stdout)

            # 2. plan: plan.md exists but has an unconfirmed assumption (invalid plan)
            fdir.mkdir(parents=True)
            unconfirmed_plan = fixture_plan.replace(
                "| the provider already retried 3 times before it reports a failure | y |",
                "| the provider already retried 3 times before it reports a failure | n |",
                1,
            )
            (fdir / "plan.md").write_text(unconfirmed_plan, encoding="utf-8")
            res = subprocess.run(
                [sys.executable, str(orchestrate), "status", "billing", "--root", tmp],
                capture_output=True,
                text=True,
            )
            self.assertEqual(res.returncode, 0)
            self.assertIn("Phase: plan", res.stdout)
            self.assertIn("Next role: planner", res.stdout)

            # 3. checks: valid plan.md, no checks.md yet
            (fdir / "plan.md").write_text(fixture_plan, encoding="utf-8")
            res = subprocess.run(
                [sys.executable, str(orchestrate), "status", "billing", "--root", tmp],
                capture_output=True,
                text=True,
            )
            self.assertEqual(res.returncode, 0)
            self.assertIn("Phase: checks", res.stdout)
            self.assertIn("Next role: specifier", res.stdout)

            # 4. build: valid plan.md and valid checks.md, no Boundary closed yet and no verification.md
            (fdir / "checks.md").write_text(fixture_checks, encoding="utf-8")
            res = subprocess.run(
                [sys.executable, str(orchestrate), "status", "billing", "--root", tmp],
                capture_output=True,
                text=True,
            )
            self.assertEqual(res.returncode, 0)
            self.assertIn("Phase: build", res.stdout)
            self.assertIn("Next role: builder", res.stdout)

            # 5. verify: checks.md records Boundary closed (all checks built), no verification.md yet
            built_checks = fixture_checks + "\n- **Boundary:** C1-C11 closed at `a1b2c3d`\n"
            (fdir / "checks.md").write_text(built_checks, encoding="utf-8")
            res = subprocess.run(
                [sys.executable, str(orchestrate), "status", "billing", "--root", tmp],
                capture_output=True,
                text=True,
            )
            self.assertEqual(res.returncode, 0)
            self.assertIn("Phase: verify", res.stdout)
            self.assertIn("Next role: verifier", res.stdout)

            # 6. fix: verification.md exists with Verdict: FAIL
            fail_verif = fixture_verif.replace("**Verdict**: PASS", "**Verdict**: FAIL")
            (fdir / "verification.md").write_text(fail_verif, encoding="utf-8")
            res = subprocess.run(
                [sys.executable, str(orchestrate), "status", "billing", "--root", tmp],
                capture_output=True,
                text=True,
            )
            self.assertEqual(res.returncode, 0)
            self.assertIn("Phase: fix", res.stdout)
            self.assertIn("Next role: fixer", res.stdout)

            # 7. done: verification.md exists and passes validate_verification.py
            (fdir / "verification.md").write_text(fixture_verif, encoding="utf-8")
            res = subprocess.run(
                [sys.executable, str(orchestrate), "status", "billing", "--root", tmp],
                capture_output=True,
                text=True,
            )
            self.assertEqual(res.returncode, 0)
            self.assertIn("Phase: done", res.stdout)
            self.assertIn("Next role: none", res.stdout)

    def test_orchestrate_prompt_all_roles(self):
        """C9: orchestrate.py prompt <feature> --role <role> --root <dir> generates a self-contained, context-isolated prompt for all 6 roles and exits 0."""
        orchestrate = SCRIPTS_DIR / "orchestrate.py"
        roles = ("scout", "planner", "specifier", "builder", "verifier", "fixer")

        with tempfile.TemporaryDirectory() as tmp:
            fdir = Path(tmp) / ".specs" / "features" / "billing"
            fdir.mkdir(parents=True)
            for name in ("plan.md", "checks.md", "verification.md"):
                shutil.copyfile(FIXTURES_DIR / name, fdir / name)

            for role in roles:
                res = subprocess.run(
                    [sys.executable, str(orchestrate), "prompt", "billing", "--role", role, "--root", tmp],
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(res.returncode, 0, f"prompt failed for role {role}: {res.stderr}")
                self.assertIn(role.upper(), res.stdout.upper())
                self.assertIn(".specs/features/billing", res.stdout.replace("\\", "/"))

    def test_orchestrate_gate_phases(self):
        """C10: orchestrate.py gate <feature> --phase <plan|checks|verify> --root <dir> runs corresponding validator and propagates exit codes 0, 1, and 2."""
        orchestrate = SCRIPTS_DIR / "orchestrate.py"

        with tempfile.TemporaryDirectory() as tmp:
            # Missing feature -> exit 2 for all 3 phases
            for phase in ("plan", "checks", "verify"):
                res = subprocess.run(
                    [sys.executable, str(orchestrate), "gate", "missing-feat", "--phase", phase, "--root", tmp],
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(res.returncode, 2, f"Expected exit 2 on missing feature for phase {phase}")

            # Valid fixtures -> exit 0 for all 3 phases
            fdir = Path(tmp) / ".specs" / "features" / "billing"
            fdir.mkdir(parents=True)
            for name in ("plan.md", "checks.md", "verification.md"):
                shutil.copyfile(FIXTURES_DIR / name, fdir / name)

            for phase in ("plan", "checks", "verify"):
                res = subprocess.run(
                    [sys.executable, str(orchestrate), "gate", "billing", "--phase", phase, "--root", tmp],
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(res.returncode, 0, f"Expected exit 0 on valid fixture for phase {phase}: {res.stdout}\n{res.stderr}")

            # Broken artifacts -> exit 1 for all 3 phases
            (fdir / "plan.md").write_text("# Broken Plan\n", encoding="utf-8")
            (fdir / "checks.md").write_text("# Broken Checks\n", encoding="utf-8")
            (fdir / "verification.md").write_text("# Broken Verification\n**Verdict**: FAIL\n", encoding="utf-8")

            for phase in ("plan", "checks", "verify"):
                res = subprocess.run(
                    [sys.executable, str(orchestrate), "gate", "billing", "--phase", phase, "--root", tmp],
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(res.returncode, 1, f"Expected exit 1 on invalid artifact for phase {phase}")

    def test_orchestrate_dispatch_dry_run_agents(self):
        """C11: orchestrate.py dispatch <feature> --role <role> --dry-run --agent <antigravity|claude|codex> prints CLI command and isolated prompt and exits 0."""
        orchestrate = SCRIPTS_DIR / "orchestrate.py"
        roles = ("scout", "planner", "specifier", "builder", "verifier", "fixer")
        agents = (
            ("antigravity", "invoke_subagent"),
            ("claude", "claude"),
            ("codex", "codex"),
        )

        with tempfile.TemporaryDirectory() as tmp:
            fdir = Path(tmp) / ".specs" / "features" / "billing"
            fdir.mkdir(parents=True)
            for name in ("plan.md", "checks.md", "verification.md"):
                shutil.copyfile(FIXTURES_DIR / name, fdir / name)

            for agent, expected_token in agents:
                for role in roles:
                    res = subprocess.run(
                        [
                            sys.executable,
                            str(orchestrate),
                            "dispatch",
                            "billing",
                            "--role",
                            role,
                            "--agent",
                            agent,
                            "--dry-run",
                            "--root",
                            tmp,
                        ],
                        capture_output=True,
                        text=True,
                    )
                    self.assertEqual(res.returncode, 0, f"dispatch failed for {agent}/{role}: {res.stderr}")
                    self.assertIn(agent, res.stdout.lower())
                    self.assertIn(role, res.stdout.lower())
                    self.assertIn(expected_token.lower(), res.stdout.lower())

    def test_selftest_script_passes(self):
        """C12: Running skills/software-factory/scripts/selftest.py executes all checks and exits with code 0."""
        selftest = SCRIPTS_DIR / "selftest.py"
        self.assertTrue(selftest.is_file(), "skills/software-factory/scripts/selftest.py must exist")
        res = subprocess.run(
            [sys.executable, str(selftest), "-v"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 0, f"selftest.py failed:\n{res.stdout}\n{res.stderr}")
        self.assertIn("0 survived", res.stdout)
        self.assertIn("tooling ok", res.stdout)
        self.assertIn("baseline clean", res.stdout)


if __name__ == "__main__":
    unittest.main()
