"""Scenario evidence that absent include fragments fail loudly."""

from outcomeeng_testing.harnesses.source_and_templating import (
    implementation_is_ready,
    missing_fragment_raises,
)


def test_module_is_implemented() -> None:
    assert implementation_is_ready()


def test_missing_fragment_raises_include_resolution_error() -> None:
    assert missing_fragment_raises()
