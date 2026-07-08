"""Harnesses for asserting repository GitHub Actions workflow policy."""

from __future__ import annotations

import re
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Final

REPO_ROOT: Final = Path(__file__).resolve().parents[2]
WORKFLOWS_DIR: Final = REPO_ROOT / ".github" / "workflows"
FULL_SHA_RE: Final = re.compile(r"^[0-9a-f]{40}$")
USES_LINE_RE: Final = re.compile(r"^\s*(?:-\s*)?uses:\s*(?P<value>[^#]+)")
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
        lines = workflow.read_text().splitlines()
        for line_number, line in enumerate(lines):
            match = USES_LINE_RE.match(line)
            if match is None:
                continue
            uses = match.group("value").strip().strip("'\"")
            if uses.startswith("./"):
                continue

            _, _, ref = uses.partition("@")
            yield ExternalWorkflowUse(
                workflow=workflow,
                value=uses,
                ref=ref,
                marked_beta=_marked_beta(lines, line_number),
            )


def _marked_beta(lines: list[str], line_number: int) -> bool:
    if BETA_TESTER_MARKER in lines[line_number]:
        return True

    for comment_line in reversed(lines[:line_number]):
        stripped = comment_line.strip()
        if not stripped.startswith("#"):
            return False
        if BETA_TESTER_MARKER in stripped:
            return True
    return False


def _workflow_paths() -> tuple[Path, ...]:
    return tuple(sorted([*WORKFLOWS_DIR.glob("*.yml"), *WORKFLOWS_DIR.glob("*.yaml")]))
