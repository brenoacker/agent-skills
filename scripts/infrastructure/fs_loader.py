from __future__ import annotations

from pathlib import Path

from scripts.domain.skill_validator import (
    RepoSnapshot,
    SkillFileData,
    extract_relative_links,
    validate_repo_snapshot,
    validate_skill_data,
)


def load_skill_data(skill_dir: Path) -> SkillFileData:
    """Read a skill directory from disk into an immutable SkillFileData object."""
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        return SkillFileData(
            dir_name=skill_dir.name,
            has_skill_md=False,
            skill_md_content=None,
            read_error=None,
            existing_links=frozenset(),
        )

    try:
        content = skill_md.read_text(encoding="utf-8")
    except Exception as exc:
        return SkillFileData(
            dir_name=skill_dir.name,
            has_skill_md=True,
            skill_md_content=None,
            read_error=str(exc),
            existing_links=frozenset(),
        )

    existing_links = frozenset(
        link for link in extract_relative_links(content) if (skill_dir / link).resolve().exists()
    )
    return SkillFileData(
        dir_name=skill_dir.name,
        has_skill_md=True,
        skill_md_content=content,
        read_error=None,
        existing_links=existing_links,
    )


def _read_optional_manifest(manifest_path: Path) -> tuple[str | None, str | None]:
    if not manifest_path.is_file():
        return None, None
    try:
        return manifest_path.read_text(encoding="utf-8"), None
    except Exception as exc:
        return None, str(exc)


def load_repo_snapshot(root_dir: Path) -> RepoSnapshot:
    """Read repository skill folders and manifests from disk into a RepoSnapshot."""
    skills_dir = root_dir / "skills"
    if not skills_dir.is_dir():
        return RepoSnapshot(
            has_skills_dir=False,
            skills_dir_label=str(skills_dir),
            skills=(),
            plugin_json_raw=None,
            plugin_json_error=None,
            registry_json_raw=None,
            registry_json_error=None,
        )

    skill_folders = sorted(
        (d for d in skills_dir.iterdir() if d.is_dir() and not d.name.startswith(".")),
        key=lambda path: path.name,
    )
    skills = tuple(load_skill_data(folder) for folder in skill_folders)
    plugin_raw, plugin_err = _read_optional_manifest(root_dir / "plugin.json")
    registry_raw, registry_err = _read_optional_manifest(root_dir / "registry.json")

    return RepoSnapshot(
        has_skills_dir=True,
        skills_dir_label=str(skills_dir),
        skills=skills,
        plugin_json_raw=plugin_raw,
        plugin_json_error=plugin_err,
        registry_json_raw=registry_raw,
        registry_json_error=registry_err,
    )


def validate_skill_on_disk(skill_dir: Path) -> list[str]:
    """Load and validate a single skill directory from disk."""
    return validate_skill_data(load_skill_data(skill_dir))


def validate_repository_on_disk(root_dir: Path) -> list[str]:
    """Load and validate the full repository from disk."""
    return validate_repo_snapshot(load_repo_snapshot(root_dir))
