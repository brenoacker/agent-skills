#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _ensure_repo_root_on_path() -> None:
    repo_root = str(Path(__file__).resolve().parent.parent)
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)


def parse_frontmatter(content: str) -> tuple[dict[str, str] | None, str | None]:
    """Parse leading YAML frontmatter from skill markdown content."""
    _ensure_repo_root_on_path()
    from scripts.domain.skill_validator import parse_frontmatter as domain_parse_frontmatter

    return domain_parse_frontmatter(content)


def validate_skill(skill_dir: Path | str) -> list[str]:
    """Validate a skill directory on disk and return a list of errors."""
    _ensure_repo_root_on_path()
    from scripts.infrastructure.fs_loader import validate_skill_on_disk

    return validate_skill_on_disk(Path(skill_dir))


def validate_repository(root_dir: Path | str) -> list[str]:
    """Validate all skills and manifests under root_dir and return a list of errors."""
    _ensure_repo_root_on_path()
    from scripts.infrastructure.fs_loader import validate_repository_on_disk

    return validate_repository_on_disk(Path(root_dir))


def main() -> None:
    """CLI entry point for validating the agent-skills repository."""
    parser = argparse.ArgumentParser(description="Validate agent skills repository")
    parser.add_argument("--root", default=".", help="Root directory of the repository")
    args = parser.parse_args()

    errors = validate_repository(args.root)
    if errors:
        print(f"Validation FAILED with {len(errors)} error(s):")
        for err in errors:
            print(f"  - ERROR: {err}")
        sys.exit(1)

    print("Validation PASSED: All skills, manifests, and links are valid.")
    sys.exit(0)


if __name__ == "__main__":
    main()
