from __future__ import annotations

import json
import re
from dataclasses import dataclass

SKILL_NAME_PATTERN = re.compile(r"^[a-z0-9\-_.]+$")
RELATIVE_LINK_PATTERN = re.compile(r"\[.*?\]\((\./[^)]+)\)")
MIN_DESCRIPTION_LENGTH = 10


@dataclass(frozen=True)
class SkillFileData:
    """Immutable domain representation of a single skill directory snapshot."""

    dir_name: str
    has_skill_md: bool
    skill_md_content: str | None
    read_error: str | None
    existing_links: frozenset[str]


@dataclass(frozen=True)
class RepoSnapshot:
    """Immutable domain representation of the repository validation surface."""

    has_skills_dir: bool
    skills_dir_label: str
    skills: tuple[SkillFileData, ...]
    plugin_json_raw: str | None
    plugin_json_error: str | None
    registry_json_raw: str | None
    registry_json_error: str | None


def parse_frontmatter(content: str) -> tuple[dict[str, str] | None, str | None]:
    """Parse leading YAML frontmatter key-value pairs without external dependencies."""
    if not content.startswith("---"):
        return None, "File does not start with '---' YAML frontmatter"

    parts = content.split("---", 2)
    if len(parts) < 3:
        return None, "Malformed YAML frontmatter (missing closing '---')"

    fm_text = parts[1]
    data: dict[str, str] = {}
    for raw_line in fm_text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" in line:
            key, val = line.split(":", 1)
            data[key.strip()] = val.strip().strip("'\"")
    return data, None


def extract_relative_links(content: str) -> list[str]:
    """Extract relative markdown links anchored at './' from skill documentation."""
    return RELATIVE_LINK_PATTERN.findall(content)


def validate_skill_data(skill: SkillFileData) -> list[str]:
    """Validate frontmatter metadata and relative links for a single skill snapshot."""
    errors: list[str] = []
    if not skill.has_skill_md:
        errors.append(f"{skill.dir_name}: missing mandatory SKILL.md file")
        return errors

    if skill.read_error is not None:
        errors.append(f"{skill.dir_name}/SKILL.md: failed to read file: {skill.read_error}")
        return errors

    content = skill.skill_md_content if skill.skill_md_content is not None else ""
    frontmatter, err = parse_frontmatter(content)
    if err is not None or frontmatter is None:
        errors.append(f"{skill.dir_name}/SKILL.md: {err}")
        return errors

    name = frontmatter.get("name", "")
    if not name:
        errors.append(f"{skill.dir_name}/SKILL.md: frontmatter missing required 'name' field")
    elif not SKILL_NAME_PATTERN.match(name):
        errors.append(f"{skill.dir_name}/SKILL.md: 'name' must be lowercase alphanumeric with hyphens ({name})")

    description = frontmatter.get("description", "")
    if not description:
        errors.append(f"{skill.dir_name}/SKILL.md: frontmatter missing required 'description' field")
    elif len(description) < MIN_DESCRIPTION_LENGTH:
        errors.append(f"{skill.dir_name}/SKILL.md: 'description' is too short ({len(description)} chars)")

    for link in extract_relative_links(content):
        if link not in skill.existing_links:
            errors.append(f"{skill.dir_name}/SKILL.md: broken relative link '{link}'")

    return errors


def validate_plugin_manifest(raw_json: str) -> list[str]:
    """Validate root plugin.json content against required manifest schema."""
    try:
        parsed = json.loads(raw_json)
    except Exception as exc:
        return [f"plugin.json is invalid JSON: {exc}"]

    if not isinstance(parsed, dict) or not parsed.get("name"):
        return ["plugin.json missing required 'name' field"]
    return []


def validate_registry_manifest(raw_json: str) -> list[str]:
    """Validate root registry.json content against required catalog schema."""
    try:
        parsed = json.loads(raw_json)
    except Exception as exc:
        return [f"registry.json is invalid JSON: {exc}"]

    if not isinstance(parsed, dict) or "skills" not in parsed:
        return ["registry.json missing 'skills' list"]
    return []


def validate_repo_snapshot(snapshot: RepoSnapshot) -> list[str]:
    """Validate all skills and manifests contained in a repository snapshot."""
    if not snapshot.has_skills_dir:
        return [f"Skills directory does not exist: {snapshot.skills_dir_label}"]

    errors: list[str] = []
    if not snapshot.skills:
        errors.append("No skills found under skills/ directory")

    for skill in snapshot.skills:
        errors.extend(validate_skill_data(skill))

    if snapshot.plugin_json_error is not None:
        errors.append(f"plugin.json is invalid JSON: {snapshot.plugin_json_error}")
    elif snapshot.plugin_json_raw is not None:
        errors.extend(validate_plugin_manifest(snapshot.plugin_json_raw))

    if snapshot.registry_json_error is not None:
        errors.append(f"registry.json is invalid JSON: {snapshot.registry_json_error}")
    elif snapshot.registry_json_raw is not None:
        errors.extend(validate_registry_manifest(snapshot.registry_json_raw))

    return errors
