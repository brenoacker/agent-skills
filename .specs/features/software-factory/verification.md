# Software Factory verification

**Verdict**: PASS
**Profile**: light
**Diff range**: 1ada6fd..672191d
**Round**: 1 - full
**Verifier**: independent sub-agent (author != verifier)

## Checks

| Check | Claim | Proof run | Evidence | Result |
| --- | --- | --- | --- | --- |
| C1 | `skills/software-factory/SKILL.md` declares frontmatter `name: software-factory` and `skills/tlc-spec-lean/` is removed | `python -m unittest tests/test_software_factory.py -v` exit 0 | `tests/test_software_factory.py:22` - `self.assertFalse(legacy_dir.exists())` · `tests/test_software_factory.py:29` - `self.assertIn("name: software-factory", frontmatter)` | PASS |
| C2 | Zero occurrences of `tlc-spec-lean`, `Tech Leads Club`, `tech-leads-club`, or `Felipe Rodrigues` across `skills/software-factory/`, `registry.json`, `plugin.json`, and `README.md` | `python -m unittest tests/test_software_factory.py -v` exit 0 | `tests/test_software_factory.py:54` - `self.assertNotIn(term.lower(), text.lower())` | PASS |
| C3 | Running `python scripts/validate.py --root .` exits with code 0 and validates `software-factory` in `skills/`, `registry.json`, and `plugin.json` | `python -m unittest tests/test_software_factory.py -v` exit 0 | `tests/test_software_factory.py:68` - `self.assertEqual(res.returncode, 0)` · `tests/test_software_factory.py:73` - `self.assertIn("software-factory", skill_names)` | PASS |
| C4 | `skills/software-factory/references/discovery.md` defines the Scout subagent handoff, the 5-stage flow (`DISCOVER -> PLAN -> CHECKS -> BUILD -> VERIFY`), and structured questioning rules across `Observable` surfaces and the 9 implicit dimensions | `python -m unittest tests/test_software_factory.py -v` exit 0 | `tests/test_software_factory.py:86` - `self.assertIn("DISCOVER -> PLAN -> CHECKS -> BUILD -> VERIFY", text)` · `tests/test_software_factory.py:103` - `self.assertIn(dim, text.lower())` | PASS |
| C5 | Running `validate_plan.py` against a `plan.md` with an assumption row where `Confirmed?` is `n` or blank exits with code 1 and reports an unconfirmed assumption error | `python -m unittest tests/test_software_factory.py -v` exit 0 | `tests/test_software_factory.py:125` - `self.assertEqual(res.returncode, 1)` · `tests/test_software_factory.py:126` - `self.assertIn("unconfirmed", (res.stdout + res.stderr).lower())` | PASS |
| C6 | Running `validate_plan.py` against a structurally valid `plan.md` where all assumption rows have `Confirmed?` set to `y` exits with code 0 | `python -m unittest tests/test_software_factory.py -v` exit 0 | `tests/test_software_factory.py:140` - `self.assertEqual(res.returncode, 0)` · `tests/test_software_factory.py:141` - `self.assertIn("0 error(s)", res.stdout)` | PASS |
| C7 | `skills/software-factory/references/orchestration.md` defines the Thin-Orchestrator rules, context-window budget rules, autonomous post-plan execution loop, and native subagent dispatch mappings for `antigravity`, `claude`, and `codex` across all 6 roles | `python -m unittest tests/test_software_factory.py -v` exit 0 | `tests/test_software_factory.py:155` - `self.assertIn(role, low)` · `tests/test_software_factory.py:158` - `self.assertIn(agent, low)` | PASS |
| C8 | Running `orchestrate.py status <feature> --root <dir>` outputs the current pipeline phase (`discover`, `plan`, `checks`, `build`, `verify`, `fix`, or `done`) and next recommended subagent role, and exits with code 0 | `python -m unittest tests/test_software_factory.py -v` exit 0 | `tests/test_software_factory.py:177` - `self.assertIn("Phase: discover", res.stdout)` · `tests/test_software_factory.py:251` - `self.assertIn("Phase: done", res.stdout)` | PASS |
| C9 | Running `orchestrate.py prompt <feature> --role <role> --root <dir>` generates a self-contained, context-isolated prompt for all 6 roles (`scout`, `planner`, `specifier`, `builder`, `verifier`, `fixer`) and exits with code 0 | `python -m unittest tests/test_software_factory.py -v` exit 0 | `tests/test_software_factory.py:271` - `self.assertEqual(res.returncode, 0)` · `tests/test_software_factory.py:273` - `self.assertIn(".specs/features/billing", res.stdout.replace("\\", "/"))` | PASS |
| C10 | Running `orchestrate.py gate <feature> --phase <phase> --root <dir>` executes the corresponding validator script (`plan`, `checks`, `verify`) and propagates its exit code (`0`, `1`, or `2`) | `python -m unittest tests/test_software_factory.py -v` exit 0 | `tests/test_software_factory.py:287` - `self.assertEqual(res.returncode, 2)` · `tests/test_software_factory.py:301` - `self.assertEqual(res.returncode, 0)` · `tests/test_software_factory.py:314` - `self.assertEqual(res.returncode, 1)` | PASS |
| C11 | Running `orchestrate.py dispatch <feature> --role <role> --dry-run --agent <agent>` prints the exact CLI command and isolated prompt for `antigravity`, `claude`, and `codex` across all 6 roles and exits with code 0 | `python -m unittest tests/test_software_factory.py -v` exit 0 | `tests/test_software_factory.py:351` - `self.assertEqual(res.returncode, 0)` · `tests/test_software_factory.py:354` - `self.assertIn(expected_token.lower(), res.stdout.lower())` | PASS |
| C12 | Running `skills/software-factory/scripts/selftest.py` executes all baseline, fault-injection, negative-control, and tooling checks and exits with code 0 | `python -m unittest tests/test_software_factory.py -v` exit 0 | `tests/test_software_factory.py:365` - `self.assertEqual(res.returncode, 0)` · `tests/test_software_factory.py:366` - `self.assertIn("0 survived", res.stdout)` | PASS |

## Coverage

| Set (size) | Recomputed from | Member -> proof | Unproven |
| --- | --- | --- | --- |
| landing one-way doors (4) | `plan.md` `## Landing` | unified skill directory C1 · confirmed-scope gate C5 · subagent-per-phase architecture C7 · hybrid orchestrator CLI C8 | - |
| subagent roles (6) | `orchestrate.py:32` (`ROLES`) | scout C9 · planner C9 · specifier C9 · builder C9 · verifier C9 · fixer C9 | - |
| orchestrate.py subcommands (4) | `orchestrate.py:280-310` | status C8 · prompt C9 · gate C10 · dispatch C11 | - |
| target agents (3) | `orchestrate.py:33` (`AGENTS`) | antigravity C11 · claude C11 · codex C11 | - |
| Confirmed? assumption states (2) | `validate_plan.py:382-387` | y C6 · n C5 | - |
| orchestrate.py gate phases (3) | `orchestrate.py:34-38` (`GATE_PHASES`) | plan C10 · checks C10 · verify C10 | - |
| pipeline status phases (7) | `orchestrate.py:58-99` (`detect_pipeline_state`) | discover C8 · plan C8 · checks C8 · build C8 · verify C8 · fix C8 · done C8 | - |
| prohibited legacy terms (4) | `plan.md` AC 2 | tlc-spec-lean C2 · Tech Leads Club C2 · tech-leads-club C2 · Felipe Rodrigues C2 | - |

## Gate

`python -m unittest tests/test_software_factory.py -v` - 12 passed, 0 failed
