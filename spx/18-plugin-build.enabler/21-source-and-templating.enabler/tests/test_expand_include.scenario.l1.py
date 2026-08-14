"""Scenario evidence that absent include fragments fail loudly."""

from pytest import raises

from outcomeeng.distribution.build import IncludeResolutionError
from outcomeeng_testing.harnesses.source_and_templating import (
    implementation_is_ready,
    project_missing_fragment,
    render_missing_fragment,
)


def test_module_is_implemented() -> None:
    assert implementation_is_ready()


def test_missing_fragment_raises_include_resolution_error() -> None:
    with raises(IncludeResolutionError):
        render_missing_fragment()


def test_missing_fragment_planning_raises_include_resolution_error() -> None:
    with raises(IncludeResolutionError):
        project_missing_fragment()
