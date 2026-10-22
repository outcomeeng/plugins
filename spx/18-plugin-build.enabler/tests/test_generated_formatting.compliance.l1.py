"""Compliance evidence that the build formats generated files under any enclosing ignore rule."""

from __future__ import annotations

import pytest

from outcomeeng_testing.harnesses.generated_formatting import (
    VIOLATING_ENCLOSURES,
    Enclosure,
    build_inside_enclosure,
)


@pytest.mark.parametrize("enclosure", VIOLATING_ENCLOSURES)
def test_enclosing_ignore_rules_leave_formatting_unchanged(
    enclosure: Enclosure,
) -> None:
    unenclosed = build_inside_enclosure(Enclosure.NONE)
    enclosed = build_inside_enclosure(enclosure)

    assert unenclosed.after_formatting != unenclosed.before_formatting
    assert enclosed.before_formatting == unenclosed.before_formatting
    assert enclosed.after_formatting == unenclosed.after_formatting
