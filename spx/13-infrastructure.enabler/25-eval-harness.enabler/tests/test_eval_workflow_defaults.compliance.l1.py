"""Compliance evidence: the eval workflow's budget and timeout defaults match Python."""

from __future__ import annotations

from outcomeeng_evals.settings import (
    DEFAULT_MAX_BUDGET_USD_TEXT,
    DEFAULT_TIMEOUT_SECONDS_TEXT,
)
from outcomeeng_testing.harnesses.eval_workflow import observe_eval_workflow_defaults


def test_eval_workflow_uses_global_budget_default() -> None:
    defaults = observe_eval_workflow_defaults()

    assert defaults.dispatch_max_budget_usd == DEFAULT_MAX_BUDGET_USD_TEXT
    assert defaults.runtime_max_budget_usd == (
        "${{ github.event.inputs.max_budget_usd || '"
        f"{DEFAULT_MAX_BUDGET_USD_TEXT}"
        "' }}"
    )
    assert defaults.dispatch_timeout_seconds == DEFAULT_TIMEOUT_SECONDS_TEXT
    assert defaults.runtime_timeout_seconds == (
        "${{ github.event.inputs.timeout_seconds || '"
        f"{DEFAULT_TIMEOUT_SECONDS_TEXT}"
        "' }}"
    )
