"""Process boundary for the implementation audit's shipped scope entrypoint."""

import pathlib
import runpy
import subprocess
import sys
from collections.abc import Callable, Mapping, Sequence
from typing import Any, cast

SCRIPT_PATH = (
    pathlib.Path(__file__)
    .resolve()
    .parents[2]
    .joinpath(
        "src",
        "plugins",
        "spec-tree",
        "skills",
        "audit-implementation",
        "scripts",
        "resolve_scope.py",
    )
)
_MODULE = runpy.run_path(str(SCRIPT_PATH))
ERROR_PREFIX = cast(str, _MODULE["ERROR_PREFIX"])
RECONCILE_PREFIX = cast(str, _MODULE["RECONCILE_PREFIX"])
REQUIRED_COVERAGE = cast(str, _MODULE["REQUIRED_COVERAGE"])
FINAL_COVERAGE_STATUSES = cast(frozenset[str], _MODULE["FINAL_COVERAGE_STATUSES"])
AUDIT_FIELD = cast(Any, _MODULE["AuditField"])
RECONCILE_FIELD = cast(Any, _MODULE["ReconcileField"])
reconcile = cast(
    Callable[
        [Sequence[str], Sequence[str], Sequence[Mapping[str, Any]]], dict[str, Any]
    ],
    _MODULE["reconcile"],
)


def audit_scope_unit(
    subject: str, *, requirement: str, status: str
) -> dict[str, object]:
    """Build one recorded audit scope unit in the shape the reconciler reads."""
    return {
        AUDIT_FIELD.UNIT_ID: f"implementation:typescript:code:{subject}",
        AUDIT_FIELD.SUBJECT: subject,
        AUDIT_FIELD.COVERAGE_REQUIREMENT: requirement,
        AUDIT_FIELD.COVERAGE_STATUS: status,
    }


def run_implementation_scope(
    repo: pathlib.Path,
    selector: str,
    *,
    repo_override: pathlib.Path | None = None,
    audit_input: str | None = None,
    reconcile_run: str | None = None,
) -> subprocess.CompletedProcess[str]:
    """Capture the real CLI result while keeping cwd separate from --repo."""
    audit_input_argv = () if audit_input is None else ("--audit-input", audit_input)
    reconcile_argv = () if reconcile_run is None else ("--reconcile-run", reconcile_run)
    return subprocess.run(
        (
            sys.executable,
            str(SCRIPT_PATH),
            selector,
            "--repo",
            str(repo if repo_override is None else repo_override),
            *audit_input_argv,
            *reconcile_argv,
        ),
        cwd=repo,
        text=True,
        capture_output=True,
        check=False,
    )
