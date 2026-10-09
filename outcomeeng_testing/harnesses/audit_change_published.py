"""Replay harness for the audit-change runner's ``read-published`` operation.

Backs the ``[test]`` evidence that the operation reads a Change's published
body through one ``gh`` query, writes nothing, and blocks with a declared
reason on a malformed request, a failed or unrunnable ``gh`` call, and a store
answer without a body string. The runner reaches the store only through its
injected command seam, so the harness passes the runner's entry point a
collaborator in place of the real process boundary, under two ``/test`` Stage 5
exceptions: as an interaction-protocol recording collaborator it records every
command the runner starts and answers each store query with a replayed answer;
as a failure-simulation controlled runner it answers with the failure a ``gh``
call returns, or raises the ``OSError`` the process boundary raises when ``gh``
cannot be started. No call reaches the network.

Every replayed answer is an inert fixture file under
``outcomeeng_testing/fixtures/audit_change_published``, written with an
invented body because the Change store is private and this repository is
public. The files at the directory's top level hold an issue body string —
one with content, one empty, which is what the store answers for an issue
whose body holds nothing — and the files under ``bodyless/`` are answers that
carry no body string. ``gh-failure.json`` holds the exit status and standard
error of a failed ``gh api graphql`` call.

Each request enters the runner's entry point in this process under one
observer ``Recorder``, so an observation also carries every file the call
wrote and every process it started. The harness owns the generated malformed
requests' seed, example count, and replay command.

The harness decides nothing: every predicate belongs to the linked test.
"""

from __future__ import annotations

import errno
import functools
import io
import json
import os
import sys
import threading
from collections.abc import Callable, Mapping, Sequence
from contextlib import chdir
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Final

from hypothesis import given, seed, settings

from outcomeeng_testing.generators.audit_change_published import (
    malformed_published_requests,
)
from outcomeeng_testing.harnesses import audit_change_run_observer as observer
from outcomeeng_testing.harnesses.audit_change_authority import REPLAYED_ISSUE
from outcomeeng_testing.harnesses.audit_change_run import REPO_ROOT, load_runner
from outcomeeng_testing.harnesses.property_evidence import run_replayable_property

_FIXTURES_DIR: Final = (
    REPO_ROOT / "outcomeeng_testing" / "fixtures" / "audit_change_published"
)
#: A replayed answer whose issue body holds a published record.
PUBLISHED_BODY_ANSWER: Final = _FIXTURES_DIR / "published-body.json"
#: A replayed answer whose issue body holds nothing.
EMPTY_BODY_ANSWER: Final = _FIXTURES_DIR / "empty-body.json"
_BODYLESS_DIR: Final = _FIXTURES_DIR / "bodyless"
_GH_FAILURE: Final = _FIXTURES_DIR / "gh-failure.json"
# Members of the recorded ``gh`` failure fixture.
_FAILURE_EXIT_CODE: Final = "exitCode"
_FAILURE_STDERR: Final = "stderr"
_ANSWER_SUFFIX: Final = ".json"

#: The invented Change identity every request names.
PUBLISHED_ISSUE: Final = REPLAYED_ISSUE

#: Property run configuration for generated malformed requests.
MALFORMED_PUBLISHED_PROPERTY_SEED: Final = 20261009
MALFORMED_PUBLISHED_PROPERTY_EXAMPLES: Final = settings().max_examples
MALFORMED_PUBLISHED_PROPERTY_REPLAY: Final = (
    "just test spx/31-outcomeeng.enabler/32-changes.enabler/tests/"
    "test_audit_change_published.compliance.l1.py"
)

_runner = load_runner()


@dataclass(frozen=True)
class RecordedFailure:
    """What the recorded failed ``gh`` call returned."""

    exit_code: int
    stderr: str


@dataclass(frozen=True)
class PublishedObservation:
    """What one ``read-published`` request did."""

    exit_code: int
    stdout: str
    #: The argument vector of every command the runner issued to the store.
    store_calls: tuple[tuple[str, ...], ...]
    #: Every filesystem mutation the call performed, as ``(event, path)``.
    runner_writes: tuple[tuple[str, ...], ...]
    #: The argument vector of every process the call started.
    spawned_commands: tuple[tuple[str, ...], ...]

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


def bodyless_answers() -> tuple[Path, ...]:
    """Every replayed answer that carries no issue body string."""
    return tuple(sorted(_BODYLESS_DIR.glob(f"*{_ANSWER_SUFFIX}")))


def stored_body(answer: Path) -> str:
    """The issue body a replayed answer holds."""
    recorded = json.loads(answer.read_text(encoding="utf-8"))
    body = recorded["data"]["repository"]["issue"]["body"]
    if not isinstance(body, str):
        raise TypeError(f"replayed answer holds no body string: {answer}")
    return body


def recorded_failure() -> RecordedFailure:
    """The exit status and standard error of the recorded failed ``gh`` call."""
    recorded = json.loads(_GH_FAILURE.read_text(encoding="utf-8"))
    return RecordedFailure(
        exit_code=recorded[_FAILURE_EXIT_CODE], stderr=recorded[_FAILURE_STDERR]
    )


def published_request(issue: str = PUBLISHED_ISSUE) -> str:
    """The request text naming ``read-published`` for ``issue``."""
    return json.dumps(
        {
            _runner.RequestField.OPERATION: _runner.Operation.READ_PUBLISHED,
            _runner.RequestField.ISSUE: issue,
        }
    )


class _Store:
    """Record each store command and answer it through ``respond``."""

    def __init__(self, respond: Callable[[], object]) -> None:
        self._respond = respond
        self.calls: list[tuple[str, ...]] = []

    def __call__(
        self, argv: Sequence[str], /, *, cwd: Path, stdin: str | None
    ) -> object:
        del cwd, stdin
        self.calls.append(tuple(argv))
        return self._respond()


def _replaying(answer: Path) -> Callable[[], object]:
    # The CLI prints an answer as one line of JSON; the fixture file is indented
    # by the repository formatter, so the replay serves it as one line again.
    text = json.dumps(json.loads(answer.read_text(encoding="utf-8")))
    return lambda: _runner.CommandResult(0, text, "")


def _failing() -> object:
    failure = recorded_failure()
    return _runner.CommandResult(failure.exit_code, "", failure.stderr)


def _unrunnable() -> object:
    # What the process boundary raises when no ``gh`` executable is found.
    raise FileNotFoundError(
        errno.ENOENT, os.strerror(errno.ENOENT), _runner.GH_EXECUTABLE
    )


@functools.cache
def _entry_point_recorder() -> observer.Recorder:
    """Install one audit hook in this process for entry-point observation."""
    recorder = observer.Recorder()
    sys.addaudithook(recorder)
    return recorder


def _call(request_text: str, respond: Callable[[], object]) -> PublishedObservation:
    store = _Store(respond)
    recorder = _entry_point_recorder()
    sink = io.StringIO()
    recorder.start(thread=threading.get_ident())
    try:
        exit_code = int(
            _runner.main(stdin=io.StringIO(request_text), stdout=sink, runner=store)
        )
    finally:
        writes, spawns = recorder.stop()
    return PublishedObservation(
        exit_code=exit_code,
        stdout=sink.getvalue(),
        store_calls=tuple(store.calls),
        runner_writes=tuple(tuple(write) for write in writes),
        spawned_commands=tuple(tuple(command) for command in spawns),
    )


def read_published(answer: Path) -> PublishedObservation:
    """Request ``read-published`` while the store answers with ``answer``."""
    return _call(published_request(), _replaying(answer))


def read_published_with_failed_gh() -> PublishedObservation:
    """Request ``read-published`` while ``gh`` exits with the recorded failure."""
    return _call(published_request(), _failing)


def read_published_without_gh() -> PublishedObservation:
    """Request ``read-published`` while no ``gh`` executable can be started."""
    return _call(published_request(), _unrunnable)


def exercise_malformed_published_requests(
    assert_case: Callable[[Mapping[str, object], PublishedObservation], None],
) -> None:
    """Send every generated malformed ``read-published`` request to the entry point.

    The store would answer with the published body, so a request that reached
    it would return that body. ``assert_case`` receives the request and what
    the entry point did with its JSON text.
    """
    respond = _replaying(PUBLISHED_BODY_ANSWER)

    @seed(MALFORMED_PUBLISHED_PROPERTY_SEED)
    @settings(max_examples=MALFORMED_PUBLISHED_PROPERTY_EXAMPLES, print_blob=True)
    @given(request=malformed_published_requests(_runner))
    def run_cases(request: dict[str, object]) -> None:
        assert_case(request, _call(json.dumps(request), respond))

    with TemporaryDirectory() as temporary, chdir(temporary):
        run_replayable_property(
            run_cases,
            seed_value=MALFORMED_PUBLISHED_PROPERTY_SEED,
            replay_path=MALFORMED_PUBLISHED_PROPERTY_REPLAY,
        )
