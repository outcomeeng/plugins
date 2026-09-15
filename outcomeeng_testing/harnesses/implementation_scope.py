"""Process boundary for the implementation audit's shipped scope entrypoint."""

import contextlib
import io
import json
import pathlib
import runpy
import subprocess
import sys
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any, cast

from outcomeeng.validation.implementation_audit_contract import (
    ImplementationAuditConcern,
    implementation_audit_unit_id,
)
from outcomeeng_testing.harnesses.changeset_scope import CHANGESET_SCOPE

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
SCOPE_IDENTITY_OPTION = cast(str, _MODULE["SCOPE_IDENTITY_OPTION"])
SPX_COMMAND = cast(str, _MODULE["SPX_COMMAND"])
EXIT_UNRECONCILED = cast(int, _MODULE["EXIT_UNRECONCILED"])
EXIT_COMMAND_FAILURE = cast(int, _MODULE["EXIT_COMMAND_FAILURE"])
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
_main = cast(Callable[..., int], _MODULE["main"])


@dataclass(frozen=True)
class InProcessRun:
    """Exit code, captured streams, and spx invocations of one in-process run."""

    returncode: int
    stdout: str
    stderr: str
    spx_invocations: tuple[tuple[str, ...], ...]


def run_implementation_scope_against_recorded_run(
    repo: pathlib.Path,
    selector: str,
    *,
    reconcile_run: str,
    scope_identity: str,
    recorded_changed_paths: Sequence[str],
    scope_units: Sequence[Mapping[str, Any]],
) -> InProcessRun:
    """Drive the reconciler with a runner that answers spx reads from given records.

    Interaction protocol at the external-tool boundary: git commands reach the
    real subprocess adapter so the fresh resolution is genuine, while the two
    ``spx verification run`` reads return the supplied sealed inventory and
    recorded units, so the test observes how the reconciler pairs them.
    """
    replies = {
        "input": {
            AUDIT_FIELD.INPUT_CONTENT: json.dumps(
                {CHANGESET_SCOPE.ScopeField.CHANGED_PATHS: list(recorded_changed_paths)}
            )
        },
        "render": {AUDIT_FIELD.SCOPE_UNITS: list(scope_units)},
    }

    invocations: list[tuple[str, ...]] = []

    def runner(args: Sequence[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        if args[0] != SPX_COMMAND:
            return subprocess.run(args, **kwargs)
        invocations.append(tuple(args))
        return subprocess.CompletedProcess(
            list(args), 0, stdout=json.dumps(replies[args[3]]) + "\n", stderr=""
        )

    return _run_in_process(
        [
            selector,
            "--repo",
            str(repo),
            "--reconcile-run",
            reconcile_run,
            SCOPE_IDENTITY_OPTION,
            scope_identity,
        ],
        runner,
        invocations,
    )


def _run_in_process(
    argv: list[str],
    runner: Callable[..., Any],
    invocations: Sequence[tuple[str, ...]] = (),
) -> InProcessRun:
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = _main(argv, runner=runner)
    return InProcessRun(code, out.getvalue(), err.getvalue(), tuple(invocations))


def run_implementation_scope_with_unlaunchable_spx(
    repo: pathlib.Path, selector: str, *, reconcile_run: str, scope_identity: str
) -> InProcessRun:
    """Drive the entrypoint with a runner whose spx launch fails before spx runs.

    Failure simulation at the external-tool boundary: git commands reach the
    real subprocess adapter so scope resolution is genuine, while every spx
    launch raises the ``OSError`` a missing or non-executable CLI produces.
    """

    def runner(args: Sequence[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        if args[0] == SPX_COMMAND:
            raise FileNotFoundError(
                f"[Errno 2] No such file or directory: {SPX_COMMAND!r}"
            )
        return subprocess.run(args, **kwargs)

    return _run_in_process(
        [
            selector,
            "--repo",
            str(repo),
            "--reconcile-run",
            reconcile_run,
            SCOPE_IDENTITY_OPTION,
            scope_identity,
        ],
        runner,
    )


def audit_scope_unit(
    subject: str,
    *,
    language: str,
    concern: ImplementationAuditConcern,
    requirement: str,
    status: str,
) -> dict[str, object]:
    """Build one recorded audit scope unit in the shape the reconciler reads."""
    return {
        AUDIT_FIELD.UNIT_ID: implementation_audit_unit_id(
            language, concern, subject_path=subject
        ),
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
    scope_identity: str | None = None,
) -> subprocess.CompletedProcess[str]:
    """Capture the real CLI result while keeping cwd separate from --repo."""
    audit_input_argv = () if audit_input is None else ("--audit-input", audit_input)
    reconcile_argv = () if reconcile_run is None else ("--reconcile-run", reconcile_run)
    if scope_identity is not None:
        reconcile_argv = (*reconcile_argv, "--scope-identity", scope_identity)
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
