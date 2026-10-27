"""Real-Git harness for the audit-change runner's ``resolve-reference`` operation.

Backs the ``[test]`` evidence that the operation reports in ``defaultBranch``
whether a named path is a file on origin's default branch, and blocks with a
declared reason when Git cannot answer. Each situation is a real Git
repository under a temporary directory with a real bare origin, so the runner's
own ``git`` calls answer from real refs and objects: the checkout, a work
branch that origin does not hold, an untracked file, and a file origin holds
that the checkout has deleted are constructed with Git commands, not simulated.

A ``Situation`` states what its construction made true about the named path:
whether the spelling names a file on origin's default branch and whether it
names an existing path of any kind, file or directory, inside the checkout. Those two facts come from the
construction, never from the runner, and the linked test derives the expected
``defaultBranch`` from them.

Two failure cases use a controlled process boundary under the failure-simulation
exception of the test methodology: the runner's command seam answers the
default-branch read with success and no output, or cannot start the path
lookup, and every other command runs for real. The boundary records every
command it receives and exposes observations only.

The harness decides nothing: every predicate belongs to the linked test.
"""

from __future__ import annotations

import errno
import io
import json
import os
import shutil
import subprocess
from collections.abc import Callable, Iterator, Sequence
from contextlib import chdir, contextmanager
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Final

from outcomeeng_testing.harnesses.audit_change_run import load_runner

_runner = load_runner()

_DEFAULT_BRANCH: Final = "main"
_WORK_BRANCH: Final = "work"
_REMOTE: Final = "origin"
_BASELINE_FILE: Final = "baseline.txt"
_NAMED_FILE: Final = "records/named.md"
_NAMED_DIRECTORY: Final = "records"
_NAMED_FILE_WITH_DOT_SEGMENT: Final = "records/./named.md"
_OUTSIDE_FILE: Final = "outside.txt"
_OUTSIDE_SPELLING: Final = f"../{_OUTSIDE_FILE}"
_FILE_TEXT: Final = "named by a candidate\n"
_GIT_CONFIGURATION: Final = (
    "-c",
    "user.name=Example Author",
    "-c",
    "user.email=author@example.invalid",
    "-c",
    "commit.gpgsign=false",
)
# Git subcommands the controlled boundary recognizes; Git owns these words.
_READ_DEFAULT_BRANCH_SUBCOMMAND: Final = "symbolic-ref"
LOOK_UP_PATH_SUBCOMMAND: Final = "cat-file"


class PathCondition(StrEnum):
    """The finite conditions a named path takes against origin and the checkout."""

    COMMITTED_TO_ORIGIN_DEFAULT = "committed-to-origin-default"
    COMMITTED_ON_WORK_BRANCH_ONLY = "committed-on-work-branch-only"
    UNTRACKED_IN_CHECKOUT = "untracked-in-checkout"
    NOWHERE = "nowhere"
    DELETED_FROM_CHECKOUT = "deleted-from-checkout"
    SPELLED_WITH_DOT_SEGMENT = "spelled-with-dot-segment"
    SPELLED_ABSOLUTE = "spelled-absolute"
    OUTSIDE_REPOSITORY = "outside-repository"
    DIRECTORY_ON_ORIGIN_DEFAULT_ONLY = "directory-on-origin-default-only"
    DIRECTORY_IN_CHECKOUT_ONLY = "directory-in-checkout-only"
    DIRECTORY_IN_CHECKOUT_AND_ORIGIN_DEFAULT = (
        "directory-in-checkout-and-origin-default"
    )


@dataclass(frozen=True)
class Situation:
    """A repository built for one condition, and what that condition made true."""

    condition: PathCondition
    root: Path
    #: The path text the request names.
    named: str
    #: The spelling names a file that origin's default branch holds.
    names_file_on_origin_default: bool
    #: The spelling names an existing path, file or directory, inside the checkout.
    names_existing_path_in_checkout: bool


@dataclass(frozen=True)
class ResolveObservation:
    """What one ``resolve-reference`` request did."""

    exit_code: int
    stdout: str
    #: The argument vector of every command the runner issued, in order.
    commands: tuple[tuple[str, ...], ...]

    @property
    def stdout_lines(self) -> tuple[str, ...]:
        """The lines the call printed on stdout."""
        return tuple(self.stdout.splitlines())

    @property
    def result(self) -> dict[str, object]:
        """The result object of the call's one stdout line."""
        (line,) = self.stdout_lines
        parsed = json.loads(line)
        if not isinstance(parsed, dict):
            raise TypeError(f"runner printed a result that is not an object: {line}")
        return parsed


def _git(cwd: Path, *arguments: str) -> None:
    subprocess.run(  # noqa: S603
        ["git", *_GIT_CONFIGURATION, *arguments],  # noqa: S607
        cwd=cwd,
        check=True,
        capture_output=True,
    )


def _write(root: Path, relative: str) -> None:
    target = root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(_FILE_TEXT, encoding="utf-8")


def _commit(root: Path, relative: str, message: str) -> None:
    _write(root, relative)
    _git(root, "add", "--", relative)
    _git(root, "commit", "--quiet", "-m", message)


def _build_repository(base: Path, *, origin_head: bool) -> Path:
    origin = base / "origin.git"
    root = base / "repository"
    origin.mkdir()
    root.mkdir()
    _git(origin, "init", "--quiet", "--bare", f"--initial-branch={_DEFAULT_BRANCH}")
    _git(root, "init", "--quiet", f"--initial-branch={_DEFAULT_BRANCH}")
    _git(root, "remote", "add", _REMOTE, str(origin))
    _commit(root, _BASELINE_FILE, "baseline")
    _git(root, "push", "--quiet", _REMOTE, _DEFAULT_BRANCH)
    if origin_head:
        _git(root, "remote", "set-head", _REMOTE, _DEFAULT_BRANCH)
    return root


def _publish(root: Path) -> None:
    _commit(root, _NAMED_FILE, "named file")
    _git(root, "push", "--quiet", _REMOTE, _DEFAULT_BRANCH)


@contextmanager
def default_branch_situation(
    condition: PathCondition, *, origin_head: bool = True
) -> Iterator[Situation]:
    """Yield a real repository built for ``condition``.

    With ``origin_head`` false the remote carries no ``HEAD`` reference, which
    is what a clone made without a default-branch reference holds.
    """
    with TemporaryDirectory() as temporary:
        base = Path(temporary)
        root = _build_repository(base, origin_head=origin_head)
        named = _NAMED_FILE
        on_origin = False
        in_checkout = False
        if condition is PathCondition.COMMITTED_TO_ORIGIN_DEFAULT:
            _publish(root)
            on_origin = in_checkout = True
        elif condition is PathCondition.COMMITTED_ON_WORK_BRANCH_ONLY:
            _git(root, "checkout", "--quiet", "-b", _WORK_BRANCH)
            _commit(root, _NAMED_FILE, "named file on the work branch")
            in_checkout = True
        elif condition is PathCondition.UNTRACKED_IN_CHECKOUT:
            _write(root, _NAMED_FILE)
            in_checkout = True
        elif condition is PathCondition.NOWHERE:
            pass
        elif condition is PathCondition.DELETED_FROM_CHECKOUT:
            _publish(root)
            (root / _NAMED_FILE).unlink()
            on_origin = True
        elif condition is PathCondition.SPELLED_WITH_DOT_SEGMENT:
            _publish(root)
            named = _NAMED_FILE_WITH_DOT_SEGMENT
            on_origin = in_checkout = True
        elif condition is PathCondition.SPELLED_ABSOLUTE:
            _publish(root)
            named = str(root / _NAMED_FILE)
        elif condition is PathCondition.OUTSIDE_REPOSITORY:
            (base / _OUTSIDE_FILE).write_text(_FILE_TEXT, encoding="utf-8")
            named = _OUTSIDE_SPELLING
        elif condition is PathCondition.DIRECTORY_ON_ORIGIN_DEFAULT_ONLY:
            _publish(root)
            shutil.rmtree(root / _NAMED_DIRECTORY)
            named = _NAMED_DIRECTORY
        elif condition is PathCondition.DIRECTORY_IN_CHECKOUT_ONLY:
            _write(root, _NAMED_FILE)
            named = _NAMED_DIRECTORY
            in_checkout = True
        elif condition is PathCondition.DIRECTORY_IN_CHECKOUT_AND_ORIGIN_DEFAULT:
            _publish(root)
            named = _NAMED_DIRECTORY
            in_checkout = True
        else:
            raise ValueError(f"no construction for condition {condition!r}")
        yield Situation(
            condition=condition,
            root=root,
            named=named,
            names_file_on_origin_default=on_origin,
            names_existing_path_in_checkout=in_checkout,
        )


class _Boundary:
    """Record each command; answer through ``interpose`` or run it for real."""

    def __init__(self, interpose: Callable[[Sequence[str]], object | None]) -> None:
        self._interpose = interpose
        self.commands: list[tuple[str, ...]] = []

    def __call__(
        self, argv: Sequence[str], /, *, cwd: Path, stdin: str | None
    ) -> object:
        self.commands.append(tuple(argv))
        answer = self._interpose(argv)
        if answer is not None:
            return answer
        return _runner.run_subprocess(argv, cwd=cwd, stdin=stdin)


def _interpose_nothing(argv: Sequence[str]) -> object | None:
    del argv
    return None


def _answer_default_branch_with_no_output(argv: Sequence[str]) -> object | None:
    if _READ_DEFAULT_BRANCH_SUBCOMMAND in argv:
        return _runner.CommandResult(0, "\n", "")
    return None


def _fail_to_start_path_lookup(argv: Sequence[str]) -> object | None:
    if LOOK_UP_PATH_SUBCOMMAND in argv:
        # What the process boundary raises when no ``git`` executable is found.
        raise FileNotFoundError(
            errno.ENOENT, os.strerror(errno.ENOENT), _runner.GIT_EXECUTABLE
        )
    return None


def _resolve(
    situation: Situation, interpose: Callable[[Sequence[str]], object | None]
) -> ResolveObservation:
    request = json.dumps(
        {
            _runner.RequestField.OPERATION: _runner.Operation.RESOLVE_REFERENCE,
            _runner.RequestField.PATH: situation.named,
        }
    )
    boundary = _Boundary(interpose)
    sink = io.StringIO()
    with chdir(situation.root):
        exit_code = int(
            _runner.main(stdin=io.StringIO(request), stdout=sink, runner=boundary)
        )
    return ResolveObservation(
        exit_code=exit_code,
        stdout=sink.getvalue(),
        commands=tuple(boundary.commands),
    )


def resolve_reference(situation: Situation) -> ResolveObservation:
    """Request ``resolve-reference`` for the situation's named path, with real Git."""
    return _resolve(situation, _interpose_nothing)


def resolve_reference_with_empty_default_branch(
    situation: Situation,
) -> ResolveObservation:
    """Request ``resolve-reference`` while the default-branch read prints nothing."""
    return _resolve(situation, _answer_default_branch_with_no_output)


def resolve_reference_with_unstartable_path_lookup(
    situation: Situation,
) -> ResolveObservation:
    """Request ``resolve-reference`` while the path lookup cannot start ``git``."""
    return _resolve(situation, _fail_to_start_path_lookup)
