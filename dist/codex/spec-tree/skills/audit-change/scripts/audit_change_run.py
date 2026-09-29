"""Command boundary for one change-record audit.

The runner reads one JSON request object on stdin, performs the requested file
or ``spx verification run`` operation from the repository root, and writes one
JSON result object on stdout. It writes no file: the SPX run journal is the only
state that persists between requests, and every request names the candidate
path and run token it acts on, so audits of different candidates started from
one worktree share nothing but the journal store SPX keys by run.

Every invocation writes exactly one result, and every result carries
``operation`` and ``status``. ``operation`` is the listed operation the request
names, or ``null`` when it names none. An ``ok`` result carries the operation's
values; a ``blocked`` result carries the reason, a detail line, and a run token:
the token of the run ``start`` created when ``start`` blocks after reading it,
otherwise the ``runToken`` string the request carries, otherwise
``not-started``. A failed command adds its exact command line, payload source,
payload key, exit code, and stderr. A filesystem, encoding, or decoding error
ends the request with a declared ``BlockReason``, never with a traceback.

``validate_request`` checks one parsed request completely before any process
starts: the field set ``REQUIRED_FIELDS`` declares for its operation, then each
field's form in the order ``_REQUEST_CHECKS`` lists. It raises ``Blocked`` with
``invalid-request``, or with ``path-rejected`` for a path that no filesystem
call can accept.

Tested with, each run observed for every file the runner process writes
anywhere and every process it starts:

- every operation of a complete rejected audit over a captured Change record;
- two such audits started at once from one worktree;
- a candidate edited before ``start``, and after it before ``reconcile``;
- an edit landing between the runner's read and SPX's retention;
- a scope payload SPX rejects, which blocks with SPX's exit code and stderr;
- invalid requests part-way through a run, each blocking with its declared
  reason and the run token the request names: a request that is not UTF-8, a
  truncated JSON request, a JSON array, an unknown operation, a missing field,
  an extra field, an absolute, parent-traversing, or unnormalized candidate
  path, a candidate or reference path carrying a NUL character, a run token or
  ``unitId`` carrying a NUL character, a candidate linked outside the
  repository, an absent candidate, an existing candidate the process cannot
  read, a Windows-1252 candidate, a finding ordinal above the maximum, a
  finding rule that is not a lowercase rule ID, a scope payload with no
  ``unitId``, and an undeclared terminal status.

None of these writes a file outside the SPX store, and none starts a process
other than ``git`` and ``spx``.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import re
import shlex
import subprocess
import sys
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from enum import IntEnum, StrEnum
from typing import Final, Protocol, TextIO


class Operation(StrEnum):
    """Requests the runner accepts, one per invocation."""

    READ_CANDIDATE = "read-candidate"
    RESOLVE_REFERENCE = "resolve-reference"
    TOOL_VERSION = "tool-version"
    START = "start"
    ADD_SCOPE = "add-scope"
    ADD_FINDING = "add-finding"
    RECONCILE = "reconcile"
    FINISH = "finish"


class RequestField(StrEnum):
    """Fields of a request object."""

    OPERATION = "operation"
    PATH = "path"
    CANDIDATE_SHA256 = "candidateSha256"
    RUN_TOKEN = "runToken"
    PAYLOAD = "payload"
    ORDINAL = "ordinal"
    TERMINAL_STATUS = "terminalStatus"


class ResultField(StrEnum):
    """Fields of a result object."""

    OPERATION = "operation"
    STATUS = "status"
    REASON = "reason"
    DETAIL = "detail"
    RUN_TOKEN = "runToken"
    PATH = "path"
    CONTENT = "content"
    SHA256 = "sha256"
    RESOLUTION = "resolution"
    TOOL_VERSION = "toolVersion"
    IDEMPOTENCY_KEY = "idempotencyKey"
    SEQUENCE = "sequence"
    IDEMPOTENT = "idempotent"
    RUN_STATUS = "runStatus"
    SCOPE_UNITS = "scopeUnits"
    FINDINGS = "findings"
    RUN = "run"
    RENDER_COMMAND = "renderCommand"
    COMMAND = "command"
    PAYLOAD_SOURCE = "payloadSource"
    PAYLOAD_KEY = "payloadKey"
    EXIT_CODE = "exitCode"
    STDERR = "stderr"
    RETAINED_SHA256 = "retainedSha256"
    LIVE_SHA256 = "liveSha256"


class ResultStatus(StrEnum):
    """Outcome of one request."""

    OK = "ok"
    BLOCKED = "blocked"


class BlockReason(StrEnum):
    """Why a request stopped without its operation's values."""

    INVALID_REQUEST = "invalid-request"
    PATH_REJECTED = "path-rejected"
    CANDIDATE_MISSING = "candidate-missing"
    CANDIDATE_UNREADABLE = "candidate-unreadable"
    CANDIDATE_CHANGED = "candidate-changed"
    RETAINED_INPUT_MISMATCH = "retained-input-mismatch"
    COMMAND_FAILED = "command-failed"
    UNREADABLE_OUTPUT = "unreadable-output"


class Resolution(StrEnum):
    """Where a path a candidate names resolves."""

    RESOLVED = "resolved"
    ABSOLUTE = "absolute"
    OUTSIDE_REPOSITORY = "outside-repository"
    MISSING = "missing"


class TerminalStatus(StrEnum):
    """Terminal statuses the audit may record."""

    APPROVED = "approved"
    REJECTED = "rejected"


class ExitCode(IntEnum):
    """Process exit status for each result status."""

    OK = 0
    BLOCKED = 1
    INVALID_REQUEST = 2


class SpxField(StrEnum):
    """Fields of the ``spx verification run`` output the runner reads."""

    RUN_TOKEN = "runToken"
    LOCATOR = "locator"
    CONTENT = "content"
    SEQUENCE = "sequence"
    IDEMPOTENT = "idempotent"
    AUDIT_SCOPE_UNITS = "auditScopeUnits"
    EVENTS = "events"
    FINDINGS = "findings"
    SEQ = "seq"
    PAYLOAD = "payload"
    UNIT_ID = "unitId"
    PARENT_UNIT_ID = "parentUnitId"
    SUBJECT = "subject"
    COVERAGE_STATUS = "coverageStatus"
    RULE = "rule"
    SEVERITY = "severity"


NOT_STARTED: Final = "not-started"
NOT_APPLICABLE: Final = "none"
NUL: Final = "\x00"
TEXT_ENCODING: Final = "utf-8"
PAYLOAD_FROM_STDIN: Final = "stdin"
IDEMPOTENCY_KEY_SEPARATOR: Final = ":"
RULE_ID_PATTERN: Final = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
MIN_FINDING_ORDINAL: Final = 1
MAX_FINDING_ORDINAL: Final = 999
VERIFICATION_TYPE: Final = "audit"
SCOPE_TYPE: Final = "file"

#: Rendered-projection fields that hold evidence rather than run-level values.
EVIDENCE_FIELDS: Final = frozenset(
    {SpxField.EVENTS, SpxField.AUDIT_SCOPE_UNITS, SpxField.FINDINGS}
)

SPX_EXECUTABLE: Final = "spx"
GIT_EXECUTABLE: Final = "git"
_GIT_TOPLEVEL: Final = (GIT_EXECUTABLE, "rev-parse", "--show-toplevel")
_SPX_VERSION: Final = (SPX_EXECUTABLE, "--version")
_RUN_COMMAND: Final = (SPX_EXECUTABLE, "verification", "run")

#: The fields each operation's request carries besides ``operation``.
REQUIRED_FIELDS: Final[Mapping[Operation, frozenset[RequestField]]] = {
    Operation.READ_CANDIDATE: frozenset({RequestField.PATH}),
    Operation.RESOLVE_REFERENCE: frozenset({RequestField.PATH}),
    Operation.TOOL_VERSION: frozenset(),
    Operation.START: frozenset({RequestField.PATH, RequestField.CANDIDATE_SHA256}),
    Operation.ADD_SCOPE: frozenset(
        {RequestField.PATH, RequestField.RUN_TOKEN, RequestField.PAYLOAD}
    ),
    Operation.ADD_FINDING: frozenset(
        {
            RequestField.PATH,
            RequestField.RUN_TOKEN,
            RequestField.ORDINAL,
            RequestField.PAYLOAD,
        }
    ),
    Operation.RECONCILE: frozenset({RequestField.PATH, RequestField.RUN_TOKEN}),
    Operation.FINISH: frozenset(
        {RequestField.PATH, RequestField.RUN_TOKEN, RequestField.TERMINAL_STATUS}
    ),
}


@dataclass(frozen=True)
class CommandResult:
    """What one external command produced."""

    exit_code: int
    stdout: str
    stderr: str


class CommandRunner(Protocol):
    """Execute one external command through an injectable process boundary."""

    def __call__(
        self, argv: Sequence[str], /, *, cwd: pathlib.Path, stdin: str | None
    ) -> CommandResult: ...


def run_subprocess(
    argv: Sequence[str], /, *, cwd: pathlib.Path, stdin: str | None
) -> CommandResult:
    """Run ``argv`` without a shell and capture its output.

    Standard output must be UTF-8 when the command succeeds; otherwise this
    raises ``UnicodeDecodeError``. Standard error, and the standard output of a
    failed command, decode with every undecodable byte escaped.
    """
    completed = subprocess.run(  # noqa: S603
        list(argv),
        cwd=cwd,
        input=None if stdin is None else stdin.encode(TEXT_ENCODING),
        stdin=subprocess.DEVNULL if stdin is None else None,
        capture_output=True,
        check=False,
    )
    stdout_errors = "strict" if completed.returncode == 0 else "backslashreplace"
    return CommandResult(
        completed.returncode,
        completed.stdout.decode(TEXT_ENCODING, stdout_errors),
        completed.stderr.decode(TEXT_ENCODING, "backslashreplace"),
    )


class Blocked(Exception):
    """A request stops with a reason and the evidence that explains it.

    ``run_token`` names a run the request itself does not name: ``start`` sets
    it once SPX has created the run. A block that leaves it unset carries the
    request's own run token, which ``execute`` supplies.
    """

    def __init__(
        self,
        reason: BlockReason,
        detail: str,
        *,
        run_token: str | None = None,
        evidence: Mapping[str, object] | None = None,
    ) -> None:
        super().__init__(detail)
        self.reason = reason
        self.detail = detail
        self.run_token = run_token
        self.evidence = dict(evidence or {})


@dataclass(frozen=True)
class _Context:
    runner: CommandRunner
    cwd: pathlib.Path


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode(TEXT_ENCODING)).hexdigest()


def _system_text_defect(text: str) -> str | None:
    """Name why ``text`` cannot reach a filesystem call or an argument vector."""
    if NUL in text:
        return "contains a NUL character"
    try:
        text.encode(TEXT_ENCODING)
    except UnicodeEncodeError:
        return "contains text that has no UTF-8 encoding"
    return None


def _command(
    context: _Context,
    argv: Sequence[str],
    *,
    cwd: pathlib.Path,
    run_token: str | None = None,
    stdin: str | None = None,
    payload_key: str = NOT_APPLICABLE,
) -> str:
    """Run one command and return its stdout, or block with its diagnostic."""
    evidence: dict[str, object] = {
        ResultField.COMMAND: shlex.join(argv),
        ResultField.PAYLOAD_SOURCE: NOT_APPLICABLE
        if stdin is None
        else PAYLOAD_FROM_STDIN,
        ResultField.PAYLOAD_KEY: payload_key,
    }
    try:
        result = context.runner(argv, cwd=cwd, stdin=stdin)
    except UnicodeDecodeError as exc:
        evidence[ResultField.EXIT_CODE] = NOT_APPLICABLE
        evidence[ResultField.STDERR] = str(exc)
        raise Blocked(
            BlockReason.UNREADABLE_OUTPUT,
            f"{argv[0]} printed output that is not UTF-8",
            run_token=run_token,
            evidence=evidence,
        ) from exc
    except (OSError, ValueError) as exc:
        evidence[ResultField.EXIT_CODE] = NOT_APPLICABLE
        evidence[ResultField.STDERR] = str(exc)
        raise Blocked(
            BlockReason.COMMAND_FAILED,
            f"{argv[0]} could not be executed",
            run_token=run_token,
            evidence=evidence,
        ) from exc
    if result.exit_code != 0:
        evidence[ResultField.EXIT_CODE] = result.exit_code
        evidence[ResultField.STDERR] = result.stderr
        raise Blocked(
            BlockReason.COMMAND_FAILED,
            f"{argv[0]} exited {result.exit_code}",
            run_token=run_token,
            evidence=evidence,
        )
    return result.stdout


def _json_lines(
    stdout: str, *, run_token: str | None = None
) -> list[dict[str, object]]:
    """Parse every non-empty stdout line as one JSON object."""
    objects: list[dict[str, object]] = []
    for line in stdout.splitlines():
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise Blocked(
                BlockReason.UNREADABLE_OUTPUT,
                f"command output is not JSON: {exc.msg}",
                run_token=run_token,
            ) from exc
        except RecursionError as exc:
            raise Blocked(
                BlockReason.UNREADABLE_OUTPUT,
                "command output nests too deeply to parse",
                run_token=run_token,
            ) from exc
        if not isinstance(value, dict):
            raise Blocked(
                BlockReason.UNREADABLE_OUTPUT,
                "command output line is not a JSON object",
                run_token=run_token,
            )
        objects.append(value)
    if not objects:
        raise Blocked(
            BlockReason.UNREADABLE_OUTPUT,
            "command printed no JSON",
            run_token=run_token,
        )
    return objects


def _repository_root(context: _Context) -> pathlib.Path:
    stdout = _command(context, _GIT_TOPLEVEL, cwd=context.cwd).strip()
    if not stdout:
        raise Blocked(BlockReason.UNREADABLE_OUTPUT, "git printed no repository root")
    return pathlib.Path(stdout)


def _string(request: Mapping[str, object], field: RequestField) -> str:
    value = request.get(field)
    if not isinstance(value, str) or not value:
        raise Blocked(
            BlockReason.INVALID_REQUEST, f"{field} must be a non-empty string"
        )
    return value


def _normalized_path(value: str) -> str:
    """Accept only a normalized repository-relative POSIX path."""
    defect = _system_text_defect(value)
    if defect is not None:
        raise Blocked(BlockReason.PATH_REJECTED, f"path {defect}: {value!r}")
    pure = pathlib.PurePosixPath(value)
    if pure.is_absolute():
        raise Blocked(BlockReason.PATH_REJECTED, f"path is absolute: {value}")
    if ".." in pure.parts:
        raise Blocked(BlockReason.PATH_REJECTED, f"path traverses a parent: {value}")
    if str(pure) != value or pure.parts in ((), (".",)):
        raise Blocked(BlockReason.PATH_REJECTED, f"path is not normalized: {value}")
    return value


def _candidate_path(request: Mapping[str, object]) -> str:
    return _normalized_path(_string(request, RequestField.PATH))


def _reference_path(request: Mapping[str, object]) -> str:
    named = _string(request, RequestField.PATH)
    defect = _system_text_defect(named)
    if defect is not None:
        raise Blocked(BlockReason.PATH_REJECTED, f"path {defect}: {named!r}")
    return named


def _candidate_sha256(request: Mapping[str, object]) -> str:
    return _string(request, RequestField.CANDIDATE_SHA256)


def _run_token(request: Mapping[str, object]) -> str:
    token = _string(request, RequestField.RUN_TOKEN)
    defect = _system_text_defect(token)
    if defect is not None:
        raise Blocked(BlockReason.INVALID_REQUEST, f"{RequestField.RUN_TOKEN} {defect}")
    return token


def _unit_id(request: Mapping[str, object]) -> str:
    payload = request.get(RequestField.PAYLOAD)
    unit_id = payload.get(SpxField.UNIT_ID) if isinstance(payload, dict) else None
    if not isinstance(unit_id, str) or not unit_id:
        raise Blocked(
            BlockReason.INVALID_REQUEST,
            f"payload must be an object with a non-empty {SpxField.UNIT_ID}",
        )
    defect = _system_text_defect(unit_id)
    if defect is not None:
        raise Blocked(
            BlockReason.INVALID_REQUEST, f"payload {SpxField.UNIT_ID} {defect}"
        )
    return unit_id


def _finding_rule(request: Mapping[str, object]) -> str:
    payload = request.get(RequestField.PAYLOAD)
    rule = payload.get(SpxField.RULE) if isinstance(payload, dict) else None
    if not isinstance(rule, str) or not RULE_ID_PATTERN.fullmatch(rule):
        raise Blocked(
            BlockReason.INVALID_REQUEST,
            f"payload {SpxField.RULE} must match {RULE_ID_PATTERN.pattern}",
        )
    return rule


def _ordinal(request: Mapping[str, object]) -> int:
    ordinal = request.get(RequestField.ORDINAL)
    if (
        not isinstance(ordinal, int)
        or isinstance(ordinal, bool)
        or not MIN_FINDING_ORDINAL <= ordinal <= MAX_FINDING_ORDINAL
    ):
        raise Blocked(
            BlockReason.INVALID_REQUEST,
            f"{RequestField.ORDINAL} must be an integer from "
            f"{MIN_FINDING_ORDINAL} to {MAX_FINDING_ORDINAL}",
        )
    return ordinal


def _payload_text(request: Mapping[str, object]) -> str:
    try:
        return json.dumps(request.get(RequestField.PAYLOAD), separators=(",", ":"))
    except RecursionError as exc:
        raise Blocked(
            BlockReason.INVALID_REQUEST, "payload nests too deeply to serialize"
        ) from exc


def _terminal_status(request: Mapping[str, object]) -> TerminalStatus:
    terminal = _string(request, RequestField.TERMINAL_STATUS)
    if terminal not in {status.value for status in TerminalStatus}:
        raise Blocked(
            BlockReason.INVALID_REQUEST,
            f"terminal status must be one of {', '.join(TerminalStatus)}: {terminal}",
        )
    return TerminalStatus(terminal)


#: The field checks ``validate_request`` applies to each operation, in order.
_REQUEST_CHECKS: Final[
    Mapping[Operation, tuple[Callable[[Mapping[str, object]], object], ...]]
] = {
    Operation.READ_CANDIDATE: (_candidate_path,),
    Operation.RESOLVE_REFERENCE: (_reference_path,),
    Operation.TOOL_VERSION: (),
    Operation.START: (_candidate_path, _candidate_sha256),
    Operation.ADD_SCOPE: (_candidate_path, _run_token, _unit_id, _payload_text),
    Operation.ADD_FINDING: (
        _candidate_path,
        _run_token,
        _unit_id,
        _finding_rule,
        _ordinal,
        _payload_text,
    ),
    Operation.RECONCILE: (_candidate_path, _run_token),
    Operation.FINISH: (_candidate_path, _run_token, _terminal_status),
}


def _named_operation(request: Mapping[str, object]) -> Operation | None:
    name = request.get(RequestField.OPERATION)
    if isinstance(name, str) and name in {operation.value for operation in Operation}:
        return Operation(name)
    return None


def validate_request(request: Mapping[str, object]) -> Operation:
    """Return the operation of a well-formed request, or raise ``Blocked``.

    A request is well-formed when it names one listed operation, carries
    exactly that operation's ``REQUIRED_FIELDS`` besides ``operation``, and
    every field passes its check. The first failing check decides the reason:
    ``path-rejected`` for a path no filesystem call accepts, ``invalid-request``
    for every other defect. No check starts a process or reads a file.
    """
    operation = _named_operation(request)
    if operation is None:
        raise Blocked(
            BlockReason.INVALID_REQUEST,
            f"{RequestField.OPERATION} must be one of {', '.join(Operation)}",
        )
    allowed = REQUIRED_FIELDS[operation] | {RequestField.OPERATION}
    missing = sorted(field.value for field in allowed if field not in request)
    unexpected = sorted(str(field) for field in request if field not in allowed)
    if missing or unexpected:
        raise Blocked(
            BlockReason.INVALID_REQUEST,
            f"{operation} request fields: missing {missing}, unexpected {unexpected}",
        )
    for check in _REQUEST_CHECKS[operation]:
        check(request)
    return operation


def _within(root: pathlib.Path, path: pathlib.Path, named: str) -> bool:
    """Report whether ``path`` resolves inside ``root``, blocking when it cannot resolve."""
    try:
        return path.resolve().is_relative_to(root.resolve())
    except (OSError, ValueError) as exc:
        raise Blocked(
            BlockReason.PATH_REJECTED, f"path cannot be resolved: {named!r}: {exc}"
        ) from exc


def _live_content(root: pathlib.Path, relative: str) -> str:
    """Read the candidate exactly as stored, refusing a path that escapes the root."""
    candidate = root / relative
    if not _within(root, candidate, relative):
        raise Blocked(
            BlockReason.PATH_REJECTED,
            f"path resolves outside the repository: {relative}",
        )
    if not candidate.exists():
        raise Blocked(BlockReason.CANDIDATE_MISSING, f"candidate is absent: {relative}")
    if not candidate.is_file():
        raise Blocked(
            BlockReason.PATH_REJECTED,
            f"candidate is not a regular file: {relative}",
        )
    try:
        stored = candidate.read_bytes()
    except FileNotFoundError as exc:
        raise Blocked(
            BlockReason.CANDIDATE_MISSING, f"candidate is absent: {relative}"
        ) from exc
    except OSError as exc:
        raise Blocked(
            BlockReason.CANDIDATE_UNREADABLE,
            f"candidate cannot be read: {relative}: {exc.strerror or exc}",
        ) from exc
    try:
        return stored.decode(TEXT_ENCODING)
    except UnicodeDecodeError as exc:
        raise Blocked(
            BlockReason.PATH_REJECTED, f"candidate is not UTF-8 text: {relative}"
        ) from exc


def _run_argv(verb: Sequence[str], relative: str, run_token: str) -> list[str]:
    return [
        *_RUN_COMMAND,
        *verb,
        "--verification-type",
        VERIFICATION_TYPE,
        "--scope-type",
        SCOPE_TYPE,
        "--scope",
        relative,
        "--run",
        run_token,
    ]


def render_argv(relative: str, run_token: str) -> list[str]:
    """Return the command that reproduces the complete rendered projection."""
    return _run_argv(("render",), relative, run_token)


def _run_json(
    context: _Context,
    root: pathlib.Path,
    verb: Sequence[str],
    relative: str,
    run_token: str,
) -> dict[str, object]:
    stdout = _command(
        context, _run_argv(verb, relative, run_token), cwd=root, run_token=run_token
    )
    return _json_lines(stdout, run_token=run_token)[-1]


def _retained_content(
    context: _Context, root: pathlib.Path, relative: str, run_token: str
) -> str:
    replay = _run_json(context, root, ("input",), relative, run_token)
    content = replay.get(SpxField.CONTENT)
    if not isinstance(content, str):
        raise Blocked(
            BlockReason.UNREADABLE_OUTPUT,
            "retained input carries no content string",
            run_token=run_token,
        )
    return content


def _read_candidate(
    context: _Context, request: Mapping[str, object]
) -> dict[str, object]:
    relative = _candidate_path(request)
    content = _live_content(_repository_root(context), relative)
    return {
        ResultField.PATH: relative,
        ResultField.SHA256: _sha256(content),
        ResultField.CONTENT: content,
    }


def _resolve_reference(
    context: _Context, request: Mapping[str, object]
) -> dict[str, object]:
    named = _reference_path(request)
    root = _repository_root(context)
    if pathlib.PurePosixPath(named).is_absolute():
        resolution = Resolution.ABSOLUTE
    elif not _within(root, root / named, named):
        resolution = Resolution.OUTSIDE_REPOSITORY
    elif not (root / named).exists():
        resolution = Resolution.MISSING
    else:
        resolution = Resolution.RESOLVED
    return {ResultField.PATH: named, ResultField.RESOLUTION: resolution}


def _tool_version(
    context: _Context, request: Mapping[str, object]
) -> dict[str, object]:
    del request
    version = _command(context, _SPX_VERSION, cwd=context.cwd).strip()
    if not version:
        raise Blocked(BlockReason.UNREADABLE_OUTPUT, "spx printed no version")
    return {ResultField.TOOL_VERSION: version}


def _start(context: _Context, request: Mapping[str, object]) -> dict[str, object]:
    relative = _candidate_path(request)
    expected = _candidate_sha256(request)
    root = _repository_root(context)
    content = _live_content(root, relative)
    if _sha256(content) != expected:
        raise Blocked(
            BlockReason.CANDIDATE_CHANGED,
            "candidate differs from the content read before the run",
            evidence={
                ResultField.LIVE_SHA256: _sha256(content),
                ResultField.SHA256: expected,
            },
        )
    argv = [
        *_RUN_COMMAND,
        "start",
        "--verification-type",
        VERIFICATION_TYPE,
        "--scope-type",
        SCOPE_TYPE,
        "--scope",
        relative,
        "--input",
        relative,
    ]
    lines = _json_lines(_command(context, argv, cwd=root))
    run_token = next(
        (
            token
            for line in lines
            if SpxField.LOCATOR in line
            and isinstance(token := line.get(SpxField.RUN_TOKEN), str)
            and token
        ),
        None,
    )
    if run_token is None:
        raise Blocked(BlockReason.UNREADABLE_OUTPUT, "start printed no run locator")
    retained = _retained_content(context, root, relative, run_token)
    if retained != content:
        raise Blocked(
            BlockReason.RETAINED_INPUT_MISMATCH,
            "retained input differs from the candidate the runner read",
            run_token=run_token,
            evidence={
                ResultField.RETAINED_SHA256: _sha256(retained),
                ResultField.LIVE_SHA256: _sha256(content),
            },
        )
    return {
        ResultField.RUN_TOKEN: run_token,
        ResultField.PATH: relative,
        ResultField.SHA256: _sha256(content),
    }


def _append(
    context: _Context,
    request: Mapping[str, object],
    *,
    noun: str,
    idempotency_key: str,
) -> dict[str, object]:
    relative = _candidate_path(request)
    run_token = _run_token(request)
    argv = [
        *_run_argv((noun, "add"), relative, run_token),
        "--idempotency-key",
        idempotency_key,
        "--payload",
        PAYLOAD_FROM_STDIN,
    ]
    stdout = _command(
        context,
        argv,
        cwd=_repository_root(context),
        stdin=_payload_text(request),
        payload_key=idempotency_key,
    )
    accepted = _json_lines(stdout)[-1]
    return {
        ResultField.RUN_TOKEN: run_token,
        ResultField.IDEMPOTENCY_KEY: idempotency_key,
        ResultField.SEQUENCE: accepted.get(SpxField.SEQUENCE),
        ResultField.IDEMPOTENT: accepted.get(SpxField.IDEMPOTENT),
    }


def _add_scope(context: _Context, request: Mapping[str, object]) -> dict[str, object]:
    return _append(context, request, noun="scope", idempotency_key=_unit_id(request))


def finding_key(unit_id: str, ordinal: int, rule: str) -> str:
    """Return the idempotency key of one finding on one unit."""
    return f"{unit_id}{IDEMPOTENCY_KEY_SEPARATOR}finding-{ordinal:03d}-{rule}"


def _add_finding(context: _Context, request: Mapping[str, object]) -> dict[str, object]:
    key = finding_key(_unit_id(request), _ordinal(request), _finding_rule(request))
    return _append(context, request, noun="finding", idempotency_key=key)


def _finding_entries(
    projection: Mapping[str, object],
) -> list[tuple[int, dict[str, object]]]:
    """Return every rendered finding as ``(seq, payload)`` once, in journal order."""
    groups = projection.get(SpxField.FINDINGS)
    if not isinstance(groups, dict):
        raise Blocked(
            BlockReason.UNREADABLE_OUTPUT,
            "rendered projection carries no findings object",
        )
    entries: dict[int, dict[str, object]] = {}
    for group in groups.values():
        for entry in group if isinstance(group, list) else []:
            seq = entry.get(SpxField.SEQ) if isinstance(entry, dict) else None
            payload = entry.get(SpxField.PAYLOAD) if isinstance(entry, dict) else None
            if not isinstance(seq, int) or not isinstance(payload, dict):
                raise Blocked(
                    BlockReason.UNREADABLE_OUTPUT,
                    "rendered finding lacks an integer seq and a payload object",
                )
            entries.setdefault(seq, payload)
    return sorted(entries.items())


def _reconcile(context: _Context, request: Mapping[str, object]) -> dict[str, object]:
    relative = _candidate_path(request)
    run_token = _run_token(request)
    root = _repository_root(context)
    retained = _retained_content(context, root, relative, run_token)
    live = _live_content(root, relative)
    if live != retained:
        raise Blocked(
            BlockReason.CANDIDATE_CHANGED,
            "candidate differs from the retained input",
            evidence={
                ResultField.RETAINED_SHA256: _sha256(retained),
                ResultField.LIVE_SHA256: _sha256(live),
            },
        )
    run_status = _run_json(context, root, ("status",), relative, run_token)
    projection = _run_json(context, root, ("render",), relative, run_token)
    units = projection.get(SpxField.AUDIT_SCOPE_UNITS)
    scope_units = [
        {
            field: unit.get(field)
            for field in (
                SpxField.UNIT_ID,
                SpxField.PARENT_UNIT_ID,
                SpxField.SUBJECT,
                SpxField.COVERAGE_STATUS,
            )
        }
        for unit in (units if isinstance(units, list) else [])
        if isinstance(unit, dict)
    ]
    findings = [
        {
            SpxField.SEQ: seq,
            SpxField.UNIT_ID: payload.get(SpxField.UNIT_ID),
            SpxField.RULE: payload.get(SpxField.RULE),
            SpxField.SEVERITY: payload.get(SpxField.SEVERITY),
        }
        for seq, payload in _finding_entries(projection)
    ]
    return {
        ResultField.RUN_TOKEN: run_token,
        ResultField.RUN_STATUS: run_status,
        ResultField.SCOPE_UNITS: scope_units,
        ResultField.FINDINGS: findings,
    }


def _finish(context: _Context, request: Mapping[str, object]) -> dict[str, object]:
    relative = _candidate_path(request)
    run_token = _run_token(request)
    terminal = _terminal_status(request)
    root = _repository_root(context)
    finish_argv = [
        *_run_argv(("finish",), relative, run_token),
        "--terminal-status",
        terminal,
    ]
    _command(context, finish_argv, cwd=root)
    projection = _run_json(context, root, ("render",), relative, run_token)
    return {
        ResultField.RUN_TOKEN: run_token,
        ResultField.RUN: {
            field: value
            for field, value in projection.items()
            if field not in EVIDENCE_FIELDS
        },
        ResultField.FINDINGS: [
            payload for _seq, payload in _finding_entries(projection)
        ],
        ResultField.RENDER_COMMAND: shlex.join(render_argv(relative, run_token)),
    }


_HANDLERS: Final[
    Mapping[Operation, Callable[[_Context, Mapping[str, object]], dict[str, object]]]
] = {
    Operation.READ_CANDIDATE: _read_candidate,
    Operation.RESOLVE_REFERENCE: _resolve_reference,
    Operation.TOOL_VERSION: _tool_version,
    Operation.START: _start,
    Operation.ADD_SCOPE: _add_scope,
    Operation.ADD_FINDING: _add_finding,
    Operation.RECONCILE: _reconcile,
    Operation.FINISH: _finish,
}


def _request_token(request: Mapping[str, object]) -> str:
    """Return the run token a request names, or ``not-started`` when it names none."""
    token = request.get(RequestField.RUN_TOKEN)
    return token if isinstance(token, str) and token else NOT_STARTED


def _parse_request(text: str) -> dict[str, object]:
    try:
        request = json.loads(text)
    except json.JSONDecodeError as exc:
        raise Blocked(
            BlockReason.INVALID_REQUEST, f"request is not JSON: {exc.msg}"
        ) from exc
    except RecursionError as exc:
        raise Blocked(
            BlockReason.INVALID_REQUEST, "request nests too deeply to parse"
        ) from exc
    if not isinstance(request, dict):
        raise Blocked(BlockReason.INVALID_REQUEST, "request must be a JSON object")
    return request


def _blocked_result(
    operation: Operation | None, blocked: Blocked, request_token: str
) -> tuple[ExitCode, dict[str, object]]:
    code = (
        ExitCode.INVALID_REQUEST
        if blocked.reason is BlockReason.INVALID_REQUEST
        else ExitCode.BLOCKED
    )
    return code, {
        ResultField.OPERATION: operation,
        ResultField.STATUS: ResultStatus.BLOCKED,
        ResultField.REASON: blocked.reason,
        ResultField.DETAIL: blocked.detail,
        ResultField.RUN_TOKEN: blocked.run_token or request_token,
        **blocked.evidence,
    }


def execute(
    request_text: str, *, cwd: pathlib.Path, runner: CommandRunner
) -> tuple[ExitCode, dict[str, object]]:
    """Perform one request and return its exit code and result object.

    A blocked result carries the token of the run ``start`` created when
    ``start`` blocks after reading it, otherwise the ``runToken`` string the
    request carries, otherwise ``not-started``.
    """
    operation: Operation | None = None
    request_token = NOT_STARTED
    try:
        request = _parse_request(request_text)
        request_token = _request_token(request)
        operation = _named_operation(request)
        validated = validate_request(request)
        values = _HANDLERS[validated](_Context(runner=runner, cwd=cwd), request)
    except Blocked as blocked:
        return _blocked_result(operation, blocked, request_token)
    return ExitCode.OK, {
        ResultField.OPERATION: operation,
        ResultField.STATUS: ResultStatus.OK,
        **values,
    }


def _read_request(stdin: TextIO | None) -> str:
    if stdin is None:
        return sys.stdin.buffer.read().decode(TEXT_ENCODING)
    return stdin.read()


def _serialized(code: ExitCode, result: Mapping[str, object]) -> tuple[ExitCode, str]:
    """Serialize one result, blocking when the output it carries nests too deeply."""
    try:
        return code, json.dumps(result, sort_keys=True)
    except RecursionError:
        named = result.get(ResultField.OPERATION)
        token = result.get(ResultField.RUN_TOKEN)
        code, blocked = _blocked_result(
            Operation(named) if isinstance(named, str) else None,
            Blocked(
                BlockReason.UNREADABLE_OUTPUT, "result nests too deeply to serialize"
            ),
            token if isinstance(token, str) else NOT_STARTED,
        )
        return code, json.dumps(blocked, sort_keys=True)


def main(
    *,
    stdin: TextIO | None = None,
    stdout: TextIO | None = None,
    runner: CommandRunner = run_subprocess,
) -> int:
    """Read one request on stdin, write one result on stdout."""
    sink = sys.stdout if stdout is None else stdout
    try:
        request_text = _read_request(stdin)
    except UnicodeDecodeError:
        code, result = _blocked_result(
            None,
            Blocked(BlockReason.INVALID_REQUEST, "request is not UTF-8 text"),
            NOT_STARTED,
        )
    except OSError as exc:
        code, result = _blocked_result(
            None,
            Blocked(BlockReason.INVALID_REQUEST, f"request could not be read: {exc}"),
            NOT_STARTED,
        )
    else:
        code, result = execute(request_text, cwd=pathlib.Path(), runner=runner)
    code, text = _serialized(code, result)
    sink.write(text)
    sink.write("\n")
    return int(code)


if __name__ == "__main__":
    raise SystemExit(main())
