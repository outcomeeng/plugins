"""Harness for the eval workflow's committed trigger and default evidence.

The harness reads the real workflow file on disk, so the assertions exercise
the declaration the CI provider reads rather than an in-memory stand-in.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from outcomeeng_evals.settings import (
    DEFAULT_MAX_BUDGET_USD_TEXT,
    DEFAULT_TIMEOUT_SECONDS_TEXT,
)

_REPO_ROOT = Path(__file__).resolve().parents[2]
_EVAL_WORKFLOW = _REPO_ROOT / ".github" / "workflows" / "product-tree-evals.yml"


def assert_eval_workflow_uses_global_budget_default() -> None:
    """Assert the workflow's dispatch and runtime defaults match Python."""

    workflow = yaml.load(
        _EVAL_WORKFLOW.read_text(encoding="utf-8"),
        Loader=yaml.BaseLoader,
    )
    dispatch_default = workflow["on"]["workflow_dispatch"]["inputs"]["max_budget_usd"][
        "default"
    ]
    runtime_default = workflow["jobs"]["evals"]["env"]["MAX_BUDGET_USD"]
    dispatch_timeout = workflow["on"]["workflow_dispatch"]["inputs"]["timeout_seconds"][
        "default"
    ]
    runtime_timeout = workflow["jobs"]["evals"]["env"]["TIMEOUT_SECONDS"]
    expected_runtime_default = (
        "${{ github.event.inputs.max_budget_usd || '"
        f"{DEFAULT_MAX_BUDGET_USD_TEXT}"
        "' }}"
    )
    expected_runtime_timeout = (
        "${{ github.event.inputs.timeout_seconds || '"
        f"{DEFAULT_TIMEOUT_SECONDS_TEXT}"
        "' }}"
    )

    assert dispatch_default == DEFAULT_MAX_BUDGET_USD_TEXT
    assert runtime_default == expected_runtime_default
    assert dispatch_timeout == DEFAULT_TIMEOUT_SECONDS_TEXT
    assert runtime_timeout == expected_runtime_timeout


def eval_workflow_trigger_events() -> tuple[str, ...]:
    """Return the event names the committed eval workflow declares under `on`.

    The harness observes the real workflow file and returns the sorted event
    names; the linked test decides which events the workflow may declare.
    """

    workflow = yaml.load(
        _EVAL_WORKFLOW.read_text(encoding="utf-8"),
        Loader=yaml.BaseLoader,
    )
    return tuple(sorted(workflow["on"]))
