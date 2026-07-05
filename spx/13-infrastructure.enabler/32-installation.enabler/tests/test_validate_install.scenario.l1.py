"""Level-1 installation scenario evidence for validate_install."""

from __future__ import annotations

from outcomeeng_testing.harnesses.validate_install import (
    validate_install_scenarios_pass,
)


def test_validate_install_scenarios() -> None:
    assert validate_install_scenarios_pass()
