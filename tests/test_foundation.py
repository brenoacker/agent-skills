from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def run_installer(target: str, scope: str = "global", dest: str | None = None) -> subprocess.CompletedProcess[str]:
    """Invoke the platform installer script in a subprocess."""
    if sys.platform == "win32":
        cmd = [
            "powershell",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(REPO_ROOT / "scripts" / "install.ps1"),
            "-Target",
            target,
            "-Scope",
            scope,
        ]
        if dest:
            cmd.extend(["-DestinationOverride", dest])
    else:
        cmd = [
            "bash",
            str(REPO_ROOT / "scripts" / "install.sh"),
            "--target",
            target,
            "--scope",
            scope,
        ]
        if dest:
            cmd.extend(["--dest", dest])
    return subprocess.run(cmd, capture_output=True, text=True)


class TestRepositoryFoundation(unittest.TestCase):
    """Integration tests covering repository structure, installers, validation, and CI."""

    def test_skills_directory_structure(self) -> None:
        """C1: skills directory exists and contains flat skill folders with SKILL.md."""
        skills_dir = REPO_ROOT / "skills"
        self.assertTrue(skills_dir.is_dir(), "skills directory must exist")
        entries = [e for e in skills_dir.iterdir() if e.is_dir() and not e.name.startswith(".")]
        for entry in entries:
            skill_md = entry / "SKILL.md"
            self.assertTrue(skill_md.is_file(), f"Skill {entry.name} must contain SKILL.md")

    def test_plugin_json_manifest(self) -> None:
        """C2: root plugin.json specifies name: agent-skills and valid metadata."""
        plugin_file = REPO_ROOT / "plugin.json"
        self.assertTrue(plugin_file.is_file(), "plugin.json must exist at root")
        with open(plugin_file, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        self.assertEqual(data.get("name"), "agent-skills")
        self.assertIn("description", data)

    def test_agents_skills_json(self) -> None:
        """C3: .agents/skills.json defines the skills path entry."""
        skills_json = REPO_ROOT / ".agents" / "skills.json"
        self.assertTrue(skills_json.is_file(), ".agents/skills.json must exist")
        with open(skills_json, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        self.assertIn("entries", data)
        paths = [e.get("path") for e in data["entries"]]
        self.assertTrue(any("skills" in str(p) for p in paths), "Must register skills path in entries")

    def test_registry_json_structure(self) -> None:
        """C4: root registry.json indexes skill entries with required schema."""
        registry_file = REPO_ROOT / "registry.json"
        self.assertTrue(registry_file.is_file(), "registry.json must exist at root")
        with open(registry_file, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        self.assertIn("skills", data)
        self.assertIn("categories", data)
        for skill in data["skills"]:
            self.assertIn("name", skill)
            self.assertIn("description", skill)
            self.assertIn("category", skill)
            self.assertIn("type", skill)
            self.assertIn(skill["type"], ("personal", "curated"))

    def test_skill_template_validity(self) -> None:
        """C5: templates/skill-template/SKILL.md contains required frontmatter and sections."""
        template_file = REPO_ROOT / "templates" / "skill-template" / "SKILL.md"
        self.assertTrue(template_file.is_file(), "Skill template must exist")
        content = template_file.read_text(encoding="utf-8")
        self.assertTrue(content.startswith("---"), "Template must start with frontmatter")
        self.assertIn("name:", content)
        self.assertIn("description:", content)

    def test_install_target_antigravity(self) -> None:
        """C6: installer copies skills to Antigravity path when target is antigravity."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            res = run_installer(target="antigravity", scope="test", dest=tmp_dir)
            self.assertEqual(res.returncode, 0, f"Installer failed: {res.stderr}")
            installed_skills = list(Path(tmp_dir).iterdir())
            self.assertTrue(len(installed_skills) >= 1, "At least one skill directory installed")

    def test_install_target_claude(self) -> None:
        """C7: installer copies skills to Claude Code path when target is claude."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            res = run_installer(target="claude", scope="test", dest=tmp_dir)
            self.assertEqual(res.returncode, 0, f"Installer failed: {res.stderr}")
            installed_skills = list(Path(tmp_dir).iterdir())
            self.assertTrue(len(installed_skills) >= 1, "At least one skill directory installed")

    def test_install_target_codex(self) -> None:
        """C8: installer copies skills to Codex path when target is codex."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            res = run_installer(target="codex", scope="test", dest=tmp_dir)
            self.assertEqual(res.returncode, 0, f"Installer failed: {res.stderr}")
            installed_skills = list(Path(tmp_dir).iterdir())
            self.assertTrue(len(installed_skills) >= 1, "At least one skill directory installed")

    def test_install_target_all(self) -> None:
        """C9: installer copies skills to all targets when target is all."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            res = run_installer(target="all", scope="test", dest=tmp_dir)
            self.assertEqual(res.returncode, 0, f"Installer failed: {res.stderr}")
            for expected_sub in ("antigravity", "claude", "codex"):
                target_path = Path(tmp_dir) / expected_sub
                self.assertTrue(target_path.is_dir(), f"Target dir {expected_sub} must exist")

    def test_install_invalid_target_fails(self) -> None:
        """C10: installer exits with code 1 when target is invalid."""
        res = run_installer(target="unsupported_agent_xyz")
        self.assertEqual(res.returncode, 1, "Installer must fail with code 1 for invalid target")

    def test_validate_script_passes_valid_skills(self) -> None:
        """C11: scripts/validate.py validates skills directory successfully."""
        validate_script = REPO_ROOT / "scripts" / "validate.py"
        self.assertTrue(validate_script.is_file(), "validate.py must exist")
        res = subprocess.run(
            [sys.executable, str(validate_script), "--root", str(REPO_ROOT)],
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 0, f"validate.py failed: {res.stdout} {res.stderr}")

    def test_validate_script_fails_corrupted_skill(self) -> None:
        """C12: scripts/validate.py fails with code 1 when a skill has missing frontmatter."""
        with tempfile.TemporaryDirectory() as tmp_root:
            tmp_skills = Path(tmp_root) / "skills"
            corrupt_skill = tmp_skills / "bad-skill"
            corrupt_skill.mkdir(parents=True)
            (corrupt_skill / "SKILL.md").write_text("# Bad skill with no frontmatter\n", encoding="utf-8")
            validate_script = REPO_ROOT / "scripts" / "validate.py"
            res = subprocess.run(
                [sys.executable, str(validate_script), "--root", tmp_root],
                capture_output=True,
                text=True,
            )
            self.assertEqual(res.returncode, 1, "validate.py must fail when frontmatter is missing")

    def test_validate_script_clean_repo_exit_zero(self) -> None:
        """C13: scripts/validate.py exits with code 0 on clean repository."""
        validate_script = REPO_ROOT / "scripts" / "validate.py"
        res = subprocess.run(
            [sys.executable, str(validate_script), "--root", str(REPO_ROOT)],
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 0)

    def test_github_workflow_configuration(self) -> None:
        """C14: .github/workflows/validate.yml executes validate.py on push and pull_request."""
        workflow_file = REPO_ROOT / ".github" / "workflows" / "validate.yml"
        self.assertTrue(workflow_file.is_file(), "validate.yml workflow must exist")
        content = workflow_file.read_text(encoding="utf-8")
        self.assertIn("push:", content)
        self.assertIn("pull_request:", content)
        self.assertIn("validate.py", content)


if __name__ == "__main__":
    unittest.main()
