"""Compliance evidence: the eval workflow's budget and timeout defaults match Python."""

from __future__ import annotations

from outcomeeng_evals.settings import (
    DEFAULT_MAX_BUDGET_USD_TEXT,
    DEFAULT_TIMEOUT_SECONDS_TEXT,
)
from outcomeeng_testing.harnesses.eval_workflow import (
    EvalWorkflowDefaults,
    observe_eval_workflow_defaults,
    violating_default_workflow_paths,
)

EXPECTED_DEFAULTS = EvalWorkflowDefaults(
    dispatch_max_budget_usd=DEFAULT_MAX_BUDGET_USD_TEXT,
    runtime_max_budget_usd=(
        "${{ github.event.inputs.max_budget_usd || '"
        f"{DEFAULT_MAX_BUDGET_USD_TEXT}"
        "' }}"
    ),
    dispatch_timeout_seconds=DEFAULT_TIMEOUT_SECONDS_TEXT,
    runtime_timeout_seconds=(
        "${{ github.event.inputs.timeout_seconds || '"
        f"{DEFAULT_TIMEOUT_SECONDS_TEXT}"
        "' }}"
    ),
)


def test_eval_workflow_uses_global_budget_default() -> None:
    assert observe_eval_workflow_defaults() == EXPECTED_DEFAULTS


def test_default_drift_is_flagged_in_every_violating_workflow() -> None:
    violating_paths = violating_default_workflow_paths()

    assert violating_paths
    for path in violating_paths:
        assert observe_eval_workflow_defaults(path) != EXPECTED_DEFAULTS, path.name
