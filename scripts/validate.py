#!/usr/bin/env python3
"""
validate.py - Automated linter and validation gate for agent skills.

Verifies:
1. Every skill under `skills/` is in a dedicated folder containing `SKILL.md`.
2. Every `SKILL.md` contains valid YAML frontmatter with `name` and `description`.
3. If `registry.json` or `plugin.json` exists, verifies valid JSON schema.
4. Relative links inside `SKILL.md` point to existing files.

Exit codes: 0 pass, 1 error found.
"""

import os
import sys
import json
import re
import argparse
from pathlib import Path

def parse_frontmatter(content):
    """Simple parser for YAML frontmatter without external dependencies."""
    if not content.startswith("---"):
        return None, "File does not start with '---' YAML frontmatter"
    
    parts = content.split("---", 2)
    if len(parts) < 3:
        return None, "Malformed YAML frontmatter (missing closing '---')"
    
    fm_text = parts[1]
    data = {}
    for line in fm_text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" in line:
            key, val = line.split(":", 1)
            key = key.strip()
            val = val.strip().strip("'\"")
            data[key] = val
    return data, None

def validate_skill(skill_dir):
    errors = []
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        errors.append(f"{skill_dir.name}: missing mandatory SKILL.md file")
        return errors
    
    try:
        content = skill_md.read_text(encoding="utf-8")
    except Exception as e:
        errors.append(f"{skill_dir.name}/SKILL.md: failed to read file: {e}")
        return errors

    fm, err = parse_frontmatter(content)
    if err:
        errors.append(f"{skill_dir.name}/SKILL.md: {err}")
        return errors

    if not fm.get("name"):
        errors.append(f"{skill_dir.name}/SKILL.md: frontmatter missing required 'name' field")
    elif not re.match(r"^[a-z0-9\-_.]+$", fm["name"]):
        errors.append(f"{skill_dir.name}/SKILL.md: 'name' must be lowercase alphanumeric with hyphens ({fm['name']})")

    if not fm.get("description"):
        errors.append(f"{skill_dir.name}/SKILL.md: frontmatter missing required 'description' field")
    elif len(fm["description"]) < 10:
        errors.append(f"{skill_dir.name}/SKILL.md: 'description' is too short ({len(fm['description'])} chars)")

    # Check relative links
    links = re.findall(r"\[.*?\]\((\./[^)]+)\)", content)
    for link in links:
        target = (skill_dir / link).resolve()
        if not target.exists():
            errors.append(f"{skill_dir.name}/SKILL.md: broken relative link '{link}'")

    return errors

def validate_repository(root_dir):
    root = Path(root_dir)
    errors = []

    skills_dir = root / "skills"
    if not skills_dir.is_dir():
        errors.append(f"Skills directory does not exist: {skills_dir}")
        return errors

    skill_folders = [d for d in skills_dir.iterdir() if d.is_dir() and not d.name.startswith(".")]
    if not skill_folders:
        errors.append("No skills found under skills/ directory")

    for sf in skill_folders:
        sf_errors = validate_skill(sf)
        errors.extend(sf_errors)

    # Validate plugin.json if present
    plugin_path = root / "plugin.json"
    if plugin_path.is_file():
        try:
            with open(plugin_path, "r", encoding="utf-8") as f:
                p_data = json.load(f)
            if not p_data.get("name"):
                errors.append("plugin.json missing required 'name' field")
        except Exception as e:
            errors.append(f"plugin.json is invalid JSON: {e}")

    # Validate registry.json if present
    registry_path = root / "registry.json"
    if registry_path.is_file():
        try:
            with open(registry_path, "r", encoding="utf-8") as f:
                r_data = json.load(f)
            if "skills" not in r_data:
                errors.append("registry.json missing 'skills' list")
        except Exception as e:
            errors.append(f"registry.json is invalid JSON: {e}")

    return errors

def main():
    parser = argparse.ArgumentParser(description="Validate agent skills repository")
    parser.add_argument("--root", default=".", help="Root directory of the repository")
    args = parser.parse_args()

    errors = validate_repository(args.root)
    if errors:
        print(f"Validation FAILED with {len(errors)} error(s):")
        for err in errors:
            print(f"  - ERROR: {err}")
        sys.exit(1)
    else:
        print("Validation PASSED: All skills, manifests, and links are valid.")
        sys.exit(0)

if __name__ == "__main__":
    main()
