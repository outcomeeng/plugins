"""Process boundary for the implementation audit's shipped scope entrypoint.

The entrypoint under test is the rendered copy the build ships under
``dist/claude/``: the resolver reads the artifact registry from a rendered
sibling data file, which only the shipped tree carries as a JSON document.
"""

import contextlib
import io
import json
import pathlib
import subprocess
import sys
from collections.abc import Callable, Iterator, Mapping, Sequence
from dataclasses import dataclass
from types import ModuleType
from typing import Any, Literal, cast

from outcomeeng.distribution.contracts import DIST_DIR_NAME, SKILLS_SUBDIR_NAME, Target
from outcomeeng.distribution.shipped_scripts import load_shipped_module
from outcomeeng.validation.audit_artifacts import (
    IMPLEMENTATION_AUDIT_SCOPE_ENTRYPOINT,
    IMPLEMENTATION_AUDIT_SKILL_NAME,
    SPEC_TREE_PLUGIN_NAME,
)
from outcomeeng.validation.implementation_audit_contract import (
    ImplementationAuditConcern,
    implementation_audit_unit_id,
)
from outcomeeng_testing.harnesses.changeset_scope import (
    StaleBaseRepo,
    commit_file,
    stale_local_base_repo,
)

SCRIPT_PATH = (
    pathlib.Path(__file__)
    .resolve()
    .parents[2]
    .joinpath(
        DIST_DIR_NAME,
        Target.CLAUDE.value,
        SPEC_TREE_PLUGIN_NAME,
        SKILLS_SUBDIR_NAME,
        IMPLEMENTATION_AUDIT_SKILL_NAME,
        IMPLEMENTATION_AUDIT_SCOPE_ENTRYPOINT,
    )
)
_RESOLVE_SCOPE_MODULE_NAME = "implementation_resolve_scope"


def load_resolve_scope_module() -> ModuleType:
    """Load the shipped scope resolver once as a module; every accessor reads that copy."""
    return load_shipped_module(_RESOLVE_SCOPE_MODULE_NAME, SCRIPT_PATH)


_MODULE = vars(load_resolve_scope_module())
ERROR_PREFIX = cast(str, _MODULE["ERROR_PREFIX"])
RECONCILE_PREFIX = cast(str, _MODULE["RECONCILE_PREFIX"])
SCOPE_IDENTITY_OPTION = cast(str, _MODULE["SCOPE_IDENTITY_OPTION"])
SPX_COMMAND = cast(str, _MODULE["SPX_COMMAND"])
RUN_COMMAND_PREFIX = cast(tuple[str, ...], _MODULE["RUN_COMMAND_PREFIX"])
INPUT_COMMAND = cast(str, _MODULE["INPUT_COMMAND"])
RENDER_COMMAND = cast(str, _MODULE["RENDER_COMMAND"])
SCOPE_OPTION = cast(str, _MODULE["SCOPE_OPTION"])
LIVE_PATHS_KEY = cast(str, _MODULE["LIVE_PATHS_KEY"])
# Handles for a run that was never started: any well-formed token no run has,
# and a scope identity no commit can match.
ABSENT_RUN_TOKEN = "1999-01-01_00-00-00-000-000000000000"
SENTINEL_SCOPE_IDENTITY = f"{'0' * 40}..{'1' * 40}"
EXIT_UNRECONCILED = cast(int, _MODULE["EXIT_UNRECONCILED"])
EXIT_COMMAND_FAILURE = cast(int, _MODULE["EXIT_COMMAND_FAILURE"])
REQUIRED_COVERAGE = cast(str, _MODULE["REQUIRED_COVERAGE"])
FINAL_COVERAGE_STATUSES = cast(frozenset[str], _MODULE["FINAL_COVERAGE_STATUSES"])
MISSING_SKILL_STATUS = cast(str, _MODULE["MISSING_SKILL_STATUS"])
# The two StrEnum classes come out of the runpy namespace as plain objects;
# a concrete class annotation cannot name members the checker never sees, so
# the cast admits attribute access and the tests pin each member by value.
AUDIT_FIELD = cast(Any, _MODULE["AuditField"])
RECONCILE_FIELD = cast(Any, _MODULE["ReconcileField"])
reconcile = cast(
    Callable[
        [Sequence[str], Sequence[str], Sequence[Mapping[str, object]]],
        dict[str, object],
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
    # Every launch the injected runner recorded: spx launches for the
    # recorded-run runner, every launch for the record-everything runner.
    recorded_launches: tuple[tuple[str, ...], ...]


def run_implementation_scope_against_recorded_run(
    repo: pathlib.Path,
    selector: str,
    *,
    reconcile_run: str,
    scope_identity: str,
    recorded_input: Mapping[str, object],
    scope_units: object,
) -> InProcessRun:
    """Drive the reconciler with a runner that answers spx reads from given records.

    Interaction protocol at the external-tool boundary: git commands reach the
    real subprocess adapter so the fresh resolution is genuine, while the two
    ``spx verification run`` reads return the supplied start input and recorded
    units verbatim, so the test observes how the reconciler pairs and rejects
    them.
    """
    replies = {
        INPUT_COMMAND: {AUDIT_FIELD.INPUT_CONTENT: json.dumps(dict(recorded_input))},
        RENDER_COMMAND: {AUDIT_FIELD.SCOPE_UNITS: scope_units},
    }
    subcommand_index = 1 + len(RUN_COMMAND_PREFIX)
    invocations: list[tuple[str, ...]] = []

    def runner(
        args: Sequence[str],
        /,
        *,
        cwd: pathlib.Path,
        capture_output: bool,
        text: Literal[True],
        check: bool,
    ) -> subprocess.CompletedProcess[str]:
        if args[0] != SPX_COMMAND:
            return subprocess.run(
                args, cwd=cwd, capture_output=capture_output, text=text, check=check
            )
        invocations.append(tuple(args))
        return subprocess.CompletedProcess(
            list(args),
            0,
            stdout=json.dumps(replies[args[subcommand_index]]) + "\n",
            stderr="",
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


def run_implementation_scope_recording_every_command(
    repo: pathlib.Path, selector: str, *, reconcile_run: str
) -> InProcessRun:
    """Drive a reconcile request that omits the sealed identity, recording every launch.

    The runner delegates nothing and records everything, so the observation is
    the complete list of commands the entrypoint attempted before returning.
    """
    invocations: list[tuple[str, ...]] = []

    def runner(
        args: Sequence[str],
        /,
        *,
        cwd: pathlib.Path,
        capture_output: bool,
        text: Literal[True],
        check: bool,
    ) -> subprocess.CompletedProcess[str]:
        invocations.append(tuple(args))
        return subprocess.CompletedProcess(list(args), 0, stdout="", stderr="")

    return _run_in_process(
        [selector, "--repo", str(repo), "--reconcile-run", reconcile_run],
        runner,
        invocations,
    )


def spx_subcommands(run: InProcessRun) -> tuple[str, ...]:
    """Return the spx subcommand each recorded invocation addressed."""
    return tuple(call[1 + len(RUN_COMMAND_PREFIX)] for call in run.recorded_launches)


def spx_scope_arguments(run: InProcessRun) -> tuple[str, ...]:
    """Return the scope identity each recorded invocation carried."""
    return tuple(call[call.index(SCOPE_OPTION) + 1] for call in run.recorded_launches)


def _run_in_process(
    argv: list[str],
    runner: Callable[..., subprocess.CompletedProcess[str]],
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

    def runner(
        args: Sequence[str],
        /,
        *,
        cwd: pathlib.Path,
        capture_output: bool,
        text: Literal[True],
        check: bool,
    ) -> subprocess.CompletedProcess[str]:
        if args[0] == SPX_COMMAND:
            raise FileNotFoundError(
                f"[Errno 2] No such file or directory: {SPX_COMMAND!r}"
            )
        return subprocess.run(
            args, cwd=cwd, capture_output=capture_output, text=text, check=check
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
        reconcile_argv = (*reconcile_argv, SCOPE_IDENTITY_OPTION, scope_identity)
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


@contextlib.contextmanager
def feature_paths_repo(paths: Sequence[str]) -> Iterator[StaleBaseRepo]:
    """Yield a stale-base repository whose feature branch also changes ``paths``.

    Each path is committed on the feature branch after the generated feature
    file, so the changeset scoped against the remote base carries the generated
    feature file and every supplied path.
    """
    with stale_local_base_repo() as stale:
        for name in paths:
            commit_file(stale.repo, name, name, name)
        yield stale
