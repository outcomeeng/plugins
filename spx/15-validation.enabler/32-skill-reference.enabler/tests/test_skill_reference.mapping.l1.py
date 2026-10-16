"""Level 1 mapping evidence for skill-reference validation.

Maps every file of this repository under the validator's scan roots to the
verdict declared in [skill-reference.md](../skill-reference.md), and every
exempted reference to the Change that removes it.
"""

from __future__ import annotations

import re

from outcomeeng.validation.skill_reference import EXEMPTED_REFERENCES
from outcomeeng_testing.harnesses.skill_reference import (
    repository_root,
    run_validator,
    scan_repository_references,
    scan_text_references,
)

CHANGE_IDENTITY = re.compile(r"outcomeeng/changes#[0-9]+")


def test_every_scanned_repository_file_passes_the_validator() -> None:
    run = run_validator(repository_root())

    assert run.lines == ()
    assert run.exit_code == 0


def test_every_exempted_reference_names_the_change_that_removes_it() -> None:
    for reference, change in EXEMPTED_REFERENCES.items():
        assert CHANGE_IDENTITY.fullmatch(change), reference


def test_every_exempted_reference_names_a_skill_no_plugin_ships() -> None:
    root = repository_root()

    for reference in EXEMPTED_REFERENCES:
        assert scan_text_references(root, f"Run {reference} now.\n", {}) == (reference,)
        assert (
            scan_text_references(root, f"Run {reference} now.\n", EXEMPTED_REFERENCES)
            == ()
        )


def test_repository_passes_only_through_references_the_mapping_names() -> None:
    root = repository_root()

    unexempted = scan_repository_references(root, {})
    exempted = set(unexempted) - set(EXEMPTED_REFERENCES)

    assert exempted == set()
    assert set(EXEMPTED_REFERENCES) <= set(unexempted)
