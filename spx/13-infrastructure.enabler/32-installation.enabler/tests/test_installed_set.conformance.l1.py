"""Level 1 conformance for the Codex installed-set query and its parser."""

from __future__ import annotations

from outcomeeng_testing.harnesses.installed_set import (
    installed_set_conformance_passes,
)


def test_installed_set_conformance() -> None:
    assert installed_set_conformance_passes()
