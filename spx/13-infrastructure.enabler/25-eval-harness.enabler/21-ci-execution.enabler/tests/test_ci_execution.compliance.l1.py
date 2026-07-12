"""Compliance evidence for the eval CI CLI command."""

from __future__ import annotations

from outcomeeng_testing.evals.factories import (
    assert_ci_subcommand_builds_plan_and_executes_with_default_ceilings,
    assert_main_group_exposes_ci_subcommand,
)


def test_main_group_exposes_ci_subcommand() -> None:
    assert_main_group_exposes_ci_subcommand()


def test_ci_subcommand_builds_plan_and_executes_with_default_ceilings() -> None:
    assert_ci_subcommand_builds_plan_and_executes_with_default_ceilings()
