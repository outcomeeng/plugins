"""Scenario evidence that absent include fragments fail loudly."""

from pytest import raises

from outcomeeng.distribution.build import (
    IncludeResolutionError,
    plan_emissions,
    render_text,
)
from outcomeeng_testing.harnesses.source_and_templating import (
    implementation_is_ready,
    missing_fragment_case,
)


def test_module_is_implemented() -> None:
    assert implementation_is_ready()


def test_missing_fragment_raises_include_resolution_error() -> None:
    with missing_fragment_case() as case:
        with raises(IncludeResolutionError):
            render_text(case.template, shared_root=case.shared_root)


def test_missing_fragment_planning_raises_include_resolution_error() -> None:
    with missing_fragment_case() as case:
        with raises(IncludeResolutionError):
            plan_emissions(case.src_root)
