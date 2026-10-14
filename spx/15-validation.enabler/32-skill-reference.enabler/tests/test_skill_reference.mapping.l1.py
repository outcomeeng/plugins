"""Level 1 mapping evidence for skill-reference validation.

Maps every file of this repository under the validator's scan roots to the
verdict declared in [skill-reference.md](../skill-reference.md).
"""

from __future__ import annotations

from outcomeeng_testing.harnesses.skill_reference import repository_root, run_validator


def test_every_scanned_repository_file_passes_the_validator() -> None:
    run = run_validator(repository_root())

    assert run.lines == ()
    assert run.exit_code == 0
