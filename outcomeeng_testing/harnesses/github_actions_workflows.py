"""Harnesses for asserting repository GitHub Actions workflow policy."""

from __future__ import annotations

import re
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final, cast

# PyYAML ships without inline types; callers cast parsed workflow structure.
import yaml  # type: ignore[import-untyped]

REPO_ROOT: Final = Path(__file__).resolve().parents[2]
WORKFLOWS_DIR: Final = REPO_ROOT / ".github" / "workflows"
FULL_SHA_RE: Final = re.compile(r"^[0-9a-f]{40}$")
OUTCOMEENG_GH_ACTIONS_PREFIX: Final = "outcomeeng/gh-actions/"
BETA_TESTER_MARKER: Final = "# BETA TESTER:"
GENERIC_CLAUDE_WORKFLOW_NAMES: Final = frozenset(
    {
        "claude.yml",
        "claude.yaml",
        "claude-code-review.yml",
        "claude-code-review.yaml",
    }
)


@dataclass(frozen=True)
class ExternalWorkflowUse:
    workflow: Path
    value: str
    ref: str
    marked_beta: bool


def active_generic_claude_callers() -> tuple[str, ...]:
    """Return generic Claude caller workflows active in this repository."""
    return tuple(
        workflow.name
        for workflow in _workflow_paths()
        if workflow.name in GENERIC_CLAUDE_WORKFLOW_NAMES
    )


def external_workflow_pin_violations() -> tuple[str, ...]:
    """Return external `uses:` refs that violate the workflow pin policy."""
    return tuple(
        external_use.value
        for external_use in _external_workflow_uses()
        if not _allowed_external_workflow_use(external_use)
    )


def _allowed_external_workflow_use(external_use: ExternalWorkflowUse) -> bool:
    if FULL_SHA_RE.fullmatch(external_use.ref):
        return True

    return (
        external_use.value.startswith(OUTCOMEENG_GH_ACTIONS_PREFIX)
        and external_use.ref == "main"
        and external_use.marked_beta
    )


def _external_workflow_uses() -> Iterator[ExternalWorkflowUse]:
    for workflow in _workflow_paths():
        marked_beta = BETA_TESTER_MARKER in workflow.read_text()
        for uses in _walk_uses(_workflow_document(workflow)):
            if uses.startswith("./"):
                continue
            _, _, ref = uses.partition("@")
            yield ExternalWorkflowUse(
                workflow=workflow,
                value=uses,
                ref=ref,
                marked_beta=marked_beta,
            )


def _workflow_document(workflow: Path) -> dict[str, Any]:
    return cast(
        "dict[str, Any]", yaml.load(workflow.read_text(), Loader=yaml.BaseLoader)
    )


def _workflow_paths() -> tuple[Path, ...]:
    return tuple(sorted([*WORKFLOWS_DIR.glob("*.yml"), *WORKFLOWS_DIR.glob("*.yaml")]))


def _walk_uses(value: object) -> Iterator[str]:
    if isinstance(value, dict):
        for key, nested in cast("dict[str, object]", value).items():
            if key == "uses" and isinstance(nested, str):
                yield nested
            else:
                yield from _walk_uses(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from _walk_uses(nested)
