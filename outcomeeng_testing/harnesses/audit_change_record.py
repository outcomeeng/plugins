"""Replay harness for the audit-change runner's ``retain-record`` operation.

Backs the ``[test]`` evidence that the operation composes a Change Draft from
the store, creates the Draft's one file through one ``spx draft create --kind
change`` command run from the Product's checkout root, writes the composed
Draft to the absolute path that command returns, and blocks with a declared
reason when the retained Draft differs or a command fails.

The runner reaches the store and SPX only through its injected command seam,
and writes the Draft only through its injected writer seam, so the harness
passes the runner's entry point a collaborator in place of each, under two
``/test`` Stage 5 exceptions. As an interaction-protocol recording
collaborator it records every command the runner starts with its working
directory and stdin, answers each store query with a replayed answer, and
plays the SPX draft store: it creates one empty Draft file under the checkout
root and reports the Draft's identifier and absolute path, as the store does;
the writer writes the bytes it receives to the path it is given. As a
failure-simulation controlled runner the writer writes other content than it
received, or the command seam answers with the failure a command returned or
raises the ``OSError`` the process boundary raises when a command cannot be
started. ``git`` commands run for real against a fresh repository in a
temporary directory. No call reaches the network.

Every replayed store answer is an inert fixture file under
``outcomeeng_testing/fixtures/audit_change_record``, written with an invented
record because the Change store is private and this repository is public.
``spx-failure.json`` holds the exit status and standard error ``spx draft
create --kind change`` returned for a repository whose draft store git does
not ignore, captured from spx 0.10.0 with the repository path replaced by
``<ROOT>``; recapture it when the spx version the gate pins prints other text
for that failure.

The harness decides nothing: every predicate belongs to the linked test.
"""

from __future__ import annotations

import errno
import io
import json
import os
import uuid
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Final

from outcomeeng.hygiene.clean import SPX_STORE_DIR
from outcomeeng_testing.harnesses.audit_change_authority import REPLAYED_ISSUE
from outcomeeng_testing.harnesses.audit_change_published import (
    RecordedFailure,
    recorded_failure,
)
from outcomeeng_testing.harnesses.audit_change_run import (
    CANDIDATE_EDIT,
    REPO_ROOT,
    audit_workspace,
    load_runner,
)

_FIXTURES_DIR: Final = (
    REPO_ROOT / "outcomeeng_testing" / "fixtures" / "audit_change_record"
)
#: The replayed answer to the record query.
RECORD_ANSWER: Final = _FIXTURES_DIR / "record.json"
#: The replayed answer to the blockers query.
BLOCKERS_ANSWER: Final = _FIXTURES_DIR / "blockers.json"
_SPX_FAILURE: Final = _FIXTURES_DIR / "spx-failure.json"
_DRAFT_SUFFIX: Final = ".md"
#: Where the played draft store creates a Change Draft under the checkout root.
_DRAFT_STORE_DIR: Final = Path(SPX_STORE_DIR) / "drafts" / "change"

#: The invented Change identity every request names.
RECORD_ISSUE: Final = REPLAYED_ISSUE

_runner = load_runner()


class StoreCondition(StrEnum):
    """How the Change store answers the runner's ``gh`` commands."""

    ANSWERING = "answering"
    FAILING = "failing"
    UNRUNNABLE = "unrunnable"


class DraftStoreCondition(StrEnum):
    """How the SPX draft store answers ``spx draft create --kind change``."""

    RETAINING = "retaining"
    ALTERING = "altering"
    FAILING = "failing"
    UNRUNNABLE = "unrunnable"


@dataclass(frozen=True)
class StoredRecord:
    """The parts of the record the replayed store answer holds."""

    title: str
    body: str
    #: The value of each organization issue field, keyed by the field's name.
    field_values: Mapping[str, object]


@dataclass(frozen=True)
class CommandCall:
    """One command the runner started through its command seam."""

    argv: tuple[str, ...]
    cwd: Path
    stdin: str | None


@dataclass(frozen=True)
class CreatedDraft:
    """The Draft file the played draft store created and reported."""

    draft_id: str
    path: Path


@dataclass(frozen=True)
class RecordObservation:
    """What one ``retain-record`` request did."""

    exit_code: int
    stdout: str
    #: The checkout root the request named.
    root: Path
    #: Every command the runner started, in order.
    calls: tuple[CommandCall, ...]
    #: Every Draft file the played draft store created, in order.
    created_drafts: tuple[CreatedDraft, ...]
    #: The bytes the runner handed its writer, keyed by the absolute path.
    written: Mapping[str, bytes]
    #: The content of every file in the draft store, keyed by its absolute path.
    retained_drafts: Mapping[str, str]

    @property
    def result(self) -> dict[str, object]:
        """The result object of the call's one stdout line."""
        (line,) = self.stdout.splitlines()
        parsed = json.loads(line)
        if not isinstance(parsed, dict):
            raise TypeError(f"runner printed a result that is not an object: {line}")
        return parsed

    def calls_of(self, executable: str) -> tuple[CommandCall, ...]:
        """Every command the runner started with ``executable``."""
        return tuple(call for call in self.calls if call.argv[0] == executable)


def stored_record() -> StoredRecord:
    """The record the replayed store answer holds."""
    node = json.loads(RECORD_ANSWER.read_text(encoding="utf-8"))
    for key in (
        _runner.StoreField.DATA,
        _runner.StoreField.REPOSITORY,
        _runner.StoreField.ISSUE,
    ):
        node = node[key]
    entries = node[_runner.StoreField.ISSUE_FIELD_VALUES][_runner.StoreField.NODES]
    return StoredRecord(
        title=node[_runner.StoreField.TITLE],
        body=node[_runner.StoreField.BODY],
        field_values={
            entry[_runner.StoreField.FIELD][_runner.StoreField.NAME]: entry.get(
                _runner.StoreField.NAME, entry.get(_runner.StoreField.VALUE)
            )
            for entry in entries
        },
    )


def recorded_spx_failure() -> RecordedFailure:
    """The exit status and standard error of the recorded failed ``spx`` call."""
    recorded = json.loads(_SPX_FAILURE.read_text(encoding="utf-8"))
    return RecordedFailure(
        exit_code=recorded[_runner.ResultField.EXIT_CODE],
        stderr=recorded[_runner.ResultField.STDERR],
    )


def _one_line(answer: Path) -> str:
    # The CLI prints an answer as one line of JSON; the fixture file is indented
    # by the repository formatter, so the replay serves it as one line again.
    return json.dumps(json.loads(answer.read_text(encoding="utf-8")))


def _unrunnable(executable: str) -> FileNotFoundError:
    # What the process boundary raises when no such executable is found.
    return FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), executable)


class _Boundary:
    """Record each command and answer it as the configured stores do."""

    def __init__(
        self, *, store: StoreCondition, draft_store: DraftStoreCondition
    ) -> None:
        self._store = store
        self._draft_store = draft_store
        self._store_answers = [_one_line(RECORD_ANSWER), _one_line(BLOCKERS_ANSWER)]
        self.calls: list[CommandCall] = []
        self.created: list[CreatedDraft] = []
        self.written: dict[str, bytes] = {}

    def __call__(
        self, argv: Sequence[str], /, *, cwd: Path, stdin: str | None
    ) -> object:
        self.calls.append(CommandCall(argv=tuple(argv), cwd=cwd, stdin=stdin))
        if argv[0] == _runner.GH_EXECUTABLE:
            return self._store_answer()
        if tuple(argv) == _runner.DRAFT_CREATE_COMMAND:
            return self._draft_answer(cwd)
        return _runner.run_subprocess(argv, cwd=cwd, stdin=stdin)

    def write(self, path: Path, data: bytes, /) -> None:
        """Write the Draft as the filesystem does, or altered under ``ALTERING``."""
        self.written[str(path)] = data
        if self._draft_store is DraftStoreCondition.ALTERING:
            data += CANDIDATE_EDIT.encode(_runner.TEXT_ENCODING)
        path.write_bytes(data)

    def _store_answer(self) -> object:
        if self._store is StoreCondition.UNRUNNABLE:
            raise _unrunnable(_runner.GH_EXECUTABLE)
        if self._store is StoreCondition.FAILING:
            failure = recorded_failure()
            return _runner.CommandResult(failure.exit_code, "", failure.stderr)
        return _runner.CommandResult(0, self._store_answers.pop(0), "")

    def _draft_answer(self, cwd: Path) -> object:
        if self._draft_store is DraftStoreCondition.UNRUNNABLE:
            raise _unrunnable(_runner.SPX_EXECUTABLE)
        if self._draft_store is DraftStoreCondition.FAILING:
            failure = recorded_spx_failure()
            return _runner.CommandResult(failure.exit_code, "", failure.stderr)
        draft_id = str(uuid.uuid4())
        target = (cwd / _DRAFT_STORE_DIR / f"{draft_id}{_DRAFT_SUFFIX}").resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.touch()
        self.created.append(CreatedDraft(draft_id=draft_id, path=target))
        answer = json.dumps(
            {
                "kind": _runner.CHANGE_DRAFT_KIND,
                _runner.SpxField.DRAFT_ID: draft_id,
                _runner.SpxField.PATH: str(target),
            }
        )
        return _runner.CommandResult(0, answer, "")


def _retained_drafts(root: Path) -> dict[str, str]:
    store = root / _DRAFT_STORE_DIR
    return {
        str(path.resolve()): path.read_bytes().decode(_runner.TEXT_ENCODING)
        for path in sorted(store.rglob(f"*{_DRAFT_SUFFIX}"))
    }


def retain_record(
    *,
    store: StoreCondition = StoreCondition.ANSWERING,
    draft_store: DraftStoreCondition = DraftStoreCondition.RETAINING,
) -> RecordObservation:
    """Request ``retain-record`` in a fresh checkout under the given conditions."""
    with audit_workspace() as workspace:
        boundary = _Boundary(store=store, draft_store=draft_store)
        request = json.dumps(
            {
                _runner.RequestField.OPERATION: _runner.Operation.RETAIN_RECORD,
                _runner.RequestField.ISSUE: RECORD_ISSUE,
                _runner.RequestField.ROOT: str(workspace.root),
            }
        )
        sink = io.StringIO()
        exit_code = int(
            _runner.main(
                stdin=io.StringIO(request),
                stdout=sink,
                runner=boundary,
                writer=boundary.write,
            )
        )
        return RecordObservation(
            exit_code=exit_code,
            stdout=sink.getvalue(),
            root=workspace.root,
            calls=tuple(boundary.calls),
            created_drafts=tuple(boundary.created),
            written=dict(boundary.written),
            retained_drafts=_retained_drafts(workspace.root),
        )
