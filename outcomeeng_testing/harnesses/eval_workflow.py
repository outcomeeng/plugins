"""Harness for the eval workflow's committed default evidence.

The harness reads the real workflow file on disk, so the observations come
from the declaration the CI provider reads rather than an in-memory stand-in.
It returns observations only; linked tests own every comparison.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

_REPO_ROOT = Path(__file__).resolve().parents[2]
_EVAL_WORKFLOW = _REPO_ROOT / ".github" / "workflows" / "product-tree-evals.yml"


@dataclass(frozen=True)
class EvalWorkflowDefaults:
    """Dispatch-input and runtime defaults the committed workflow declares."""

    dispatch_max_budget_usd: str
    runtime_max_budget_usd: str
    dispatch_timeout_seconds: str
    runtime_timeout_seconds: str


def observe_eval_workflow_defaults() -> EvalWorkflowDefaults:
    """Return the defaults the committed eval workflow declares."""

    workflow = yaml.load(
        _EVAL_WORKFLOW.read_text(encoding="utf-8"),
        Loader=yaml.BaseLoader,
    )
    inputs = workflow["on"]["workflow_dispatch"]["inputs"]
    env = workflow["jobs"]["evals"]["env"]
    return EvalWorkflowDefaults(
        dispatch_max_budget_usd=inputs["max_budget_usd"]["default"],
        runtime_max_budget_usd=env["MAX_BUDGET_USD"],
        dispatch_timeout_seconds=inputs["timeout_seconds"]["default"],
        runtime_timeout_seconds=env["TIMEOUT_SECONDS"],
    )
