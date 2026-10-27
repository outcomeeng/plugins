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


_DEFAULT_FIXTURES = (
    Path(__file__).resolve().parents[1] / "fixtures" / "eval_workflow_defaults"
)


def violating_default_workflow_paths() -> tuple[Path, ...]:
    """Return the inert workflow files that each declare a drifted default."""

    return tuple(sorted(_DEFAULT_FIXTURES.glob("*.yml")))


def observe_eval_workflow_defaults(
    workflow_path: Path | None = None,
) -> EvalWorkflowDefaults:
    """Return the defaults a workflow file declares.

    Without an argument the committed eval workflow is read.
    """

    path = _EVAL_WORKFLOW if workflow_path is None else workflow_path
    workflow = yaml.load(path.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
    inputs = workflow["on"]["workflow_dispatch"]["inputs"]
    env = workflow["jobs"]["evals"]["env"]
    return EvalWorkflowDefaults(
        dispatch_max_budget_usd=inputs["max_budget_usd"]["default"],
        runtime_max_budget_usd=env["MAX_BUDGET_USD"],
        dispatch_timeout_seconds=inputs["timeout_seconds"]["default"],
        runtime_timeout_seconds=env["TIMEOUT_SECONDS"],
    )


_TRIGGER_FIXTURES = (
    Path(__file__).resolve().parents[1] / "fixtures" / "eval_workflow_triggers"
)


def violating_trigger_workflow_paths() -> tuple[Path, ...]:
    """Return the inert workflow files that each declare a forbidden trigger."""

    return tuple(sorted(_TRIGGER_FIXTURES.glob("*.yml")))


def observe_workflow_triggers(workflow_path: Path | None = None) -> frozenset[str]:
    """Return the event names a workflow file declares under `on`.

    Without an argument the committed eval workflow is read.
    """

    path = _EVAL_WORKFLOW if workflow_path is None else workflow_path
    workflow = yaml.load(path.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
    declared = workflow["on"]
    if isinstance(declared, str):
        return frozenset({declared})
    if isinstance(declared, list):
        return frozenset(declared)
    return frozenset(declared)
