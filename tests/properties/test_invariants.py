from __future__ import annotations

import string
import tempfile
import unittest
from pathlib import Path

from hypothesis import given
from hypothesis import strategies as st

from scripts.check_deps import check_dependencies
from scripts.domain.skill_validator import (
    SkillFileData,
    parse_frontmatter,
    validate_skill_data,
)
from scripts.pedagogical_lint import lint_source

SAFE_DESCRIPTION_ALPHABET = string.ascii_letters + string.digits + " .,;:!?()/_"


@st.composite
def valid_skill_metadata(draw: st.DrawFn) -> tuple[str, str]:
    """Generate valid lowercase skill names and non-trivial descriptions."""
    name = draw(st.from_regex(r"\A[a-z0-9][a-z0-9\-_.]{0,30}\Z", fullmatch=True))
    raw_desc = draw(
        st.text(alphabet=SAFE_DESCRIPTION_ALPHABET, min_size=12, max_size=80).filter(
            lambda text: "---" not in text and len(text.strip()) >= 10
        )
    )
    return name, raw_desc.strip()


class TestPropertyInvariants(unittest.TestCase):
    """Property-based invariants for skill validation, pedagogical linting, and layer isolation."""

    @given(metadata=valid_skill_metadata())
    def test_frontmatter_round_trip_invariant(self, metadata: tuple[str, str]) -> None:
        """Any valid skill name and description round-trips through YAML frontmatter with zero errors."""
        name, description = metadata
        markdown = f"---\nname: {name}\ndescription: {description}\n---\n\n# Heading\n"

        parsed, err = parse_frontmatter(markdown)
        self.assertIsNone(err)
        self.assertIsNotNone(parsed)
        assert parsed is not None
        self.assertEqual(parsed.get("name"), name)
        self.assertEqual(parsed.get("description"), description)

        skill = SkillFileData(
            dir_name=name,
            has_skill_md=True,
            skill_md_content=markdown,
            read_error=None,
            existing_links=frozenset(),
        )
        self.assertEqual(validate_skill_data(skill), [])

    @given(
        bad_name=st.text(
            alphabet=string.ascii_letters + string.digits + " -_",
            min_size=1,
            max_size=24,
        ).filter(lambda text: text.strip() != "" and any(ch.isupper() or ch.isspace() for ch in text.strip()))
    )
    def test_invalid_skill_name_always_rejected(self, bad_name: str) -> None:
        """Any skill name containing uppercase characters or whitespace is deterministically rejected."""
        normalized_input = bad_name.strip()
        markdown = f"---\nname: {normalized_input}\ndescription: Valid description over ten chars.\n---\n"
        skill = SkillFileData(
            dir_name="invalid-skill",
            has_skill_md=True,
            skill_md_content=markdown,
            read_error=None,
            existing_links=frozenset(),
        )
        errors = validate_skill_data(skill)
        self.assertTrue(len(errors) >= 1)
        self.assertTrue(any("lowercase alphanumeric with hyphens" in msg for msg in errors))

    @given(
        forbidden_snippet=st.sampled_from(
            [
                "x: int = 'bad'  # type: ignore\n",
                "import os  # noqa\n",
                "def fn() -> int:\n    # TODO: refactor\n    return 1\n",
                "import requests\n",
                "import time\n\ndef wait() -> None:\n    time.sleep(1)\n",
            ]
        )
    )
    def test_pedagogical_linter_emits_agente_prefix(self, forbidden_snippet: str) -> None:
        """Suppressions, inline comments, and blocking APIs always fail with an AGENTE: message."""
        violations = lint_source(forbidden_snippet, "synthetic.py")
        self.assertTrue(len(violations) >= 1)
        self.assertTrue(all(v.message.startswith("AGENTE:") for v in violations))

    @given(
        forbidden_import=st.sampled_from(
            [
                "scripts.infrastructure.fs_loader",
                "scripts.validate",
                "subprocess",
                "os",
            ]
        )
    )
    def test_domain_boundary_violation_emits_agente_prefix(self, forbidden_import: str) -> None:
        """A simulated domain module importing infrastructure, CLI, or side-effect APIs fails deps check."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_root = Path(tmp_dir)
            domain_dir = tmp_root / "scripts" / "domain"
            domain_dir.mkdir(parents=True)
            (tmp_root / "scripts" / "__init__.py").write_text("", encoding="utf-8")
            (domain_dir / "__init__.py").write_text("", encoding="utf-8")
            (domain_dir / "leaky_domain.py").write_text(f"import {forbidden_import}\n", encoding="utf-8")

            violations = check_dependencies(tmp_root)
            self.assertTrue(len(violations) >= 1)
            self.assertTrue(any(v.message.startswith("AGENTE:") for v in violations))


if __name__ == "__main__":
    unittest.main()
