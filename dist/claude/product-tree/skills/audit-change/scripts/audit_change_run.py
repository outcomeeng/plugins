"""Command boundary for one change-record audit.

The runner reads one JSON request object on stdin, performs the requested file
or ``spx verification run`` operation from the Product's checkout root, and writes one
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
- a scope payload SPX rejects, which blocks with SPX's exit code and stderr;
- a request that is not UTF-8 text;
- a candidate that is absent, a directory, unreadable, linked outside the
  repository, or Windows-1252 text;
- for each operation that takes a ``runToken``, a request naming a started
  run with fields its operation does not take, which blocks with that
  operation and run token;
- generated request texts the runner cannot parse as one JSON object: a
  truncated request object, a JSON value of another type, or an object
  carrying an integer literal longer than the interpreter converts;
- generated request objects outside the request contract: an absent or
  unlisted operation; a missing field or one the operation does not take; a
  ``path``, ``candidateSha256``, ``runToken``, or ``terminalStatus`` that is
  not a non-empty string; a path, ``runToken``, or payload ``unitId`` carrying
  a NUL character or text with no UTF-8 encoding; an absolute,
  parent-traversing, or unnormalized candidate path; a payload that is not an
  object with a non-empty ``unitId``; a finding rule that is not a lowercase
  hyphenated ID; and an unlisted terminal status. Each blocks on stdout.

None of these writes a file outside the SPX store, and none starts a process
other than ``git`` and ``spx``; the generated requests start none.

``read-authority`` starts ``gh`` and is tested apart from those runs, in this
process over replayed store pages: it reads the issue's field-change events and
no comment, a read that ends before the bound returns every event, and a connection that keeps reporting a further page blocks after
the bound with ``page-bound-reached`` naming it.

Every operation that names a candidate or a record path takes the Product's
checkout root as ``root``, an absolute path: ``read-candidate``, ``start``,
``add-scope``, ``add-finding``, ``reconcile``, ``finish``, and ``count-limits``
resolve the candidate path under that root and run their ``git`` and ``spx``
commands with that root as the working directory, and ``resolve-reference``
resolves the path a record names under it, whatever checkout holds the draft
or runs the audit. A request without ``root``, or one whose ``root`` is no
repository checkout root, blocks naming it, and the containment check of the
path stays against that root.

``read-published`` starts ``gh`` once and returns the issue's published body,
the empty string when the store holds none.

``read-relations`` starts ``gh`` once per page of the store's issues and returns
the named issue's Product and Parent, its Parent's Product, and the issues whose
Parent is the named issue, and the issues whose Predecessors value names it,
within the same page bound as ``read-authority``.

``count-limits`` reads the candidate under ``root`` and starts no process beyond
the repository-root lookup of that root; it returns the title's word count and the Intent
section's word count, labels included, with the limit of each, and lists those
over their limit.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import re
import shlex
import string
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
    READ_AUTHORITY = "read-authority"
    READ_PUBLISHED = "read-published"
    READ_RELATIONS = "read-relations"
    COUNT_LIMITS = "count-limits"


class RequestField(StrEnum):
    """Fields of a request object."""

    OPERATION = "operation"
    PATH = "path"
    CANDIDATE_SHA256 = "candidateSha256"
    RUN_TOKEN = "runToken"
    PAYLOAD = "payload"
    TERMINAL_STATUS = "terminalStatus"
    ISSUE = "issue"
    ROOT = "root"


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
    ISSUE = "issue"
    EVENTS = "events"
    BOUND = "bound"
    CREATED_AT = "createdAt"
    ACTOR = "actor"
    FIELD = "field"
    PREVIOUS_VALUE = "previousValue"
    NEW_VALUE = "newValue"
    BODY = "body"
    PRODUCT = "product"
    PARENT = "parent"
    PARENT_PRODUCT = "parentProduct"
    CHILDREN = "children"
    ABSORBERS = "absorbers"
    NUMBER = "number"
    LIMITS = "limits"
    VIOLATIONS = "violations"
    SECTION = "section"
    LIMIT = "limit"
    COUNT = "count"


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
    PAGE_BOUND_REACHED = "page-bound-reached"


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


class AuthorityRead(StrEnum):
    """The store connection ``read-authority`` reads."""

    EVENTS = "events"


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


class StoreField(StrEnum):
    """Fields of the store's GraphQL answer that ``read-authority`` reads."""

    DATA = "data"
    REPOSITORY = "repository"
    ISSUE = "issue"
    TIMELINE_ITEMS = "timelineItems"
    PAGE_INFO = "pageInfo"
    HAS_NEXT_PAGE = "hasNextPage"
    END_CURSOR = "endCursor"
    NODES = "nodes"
    CREATED_AT = "createdAt"
    ACTOR = "actor"
    LOGIN = "login"
    PREVIOUS_VALUE = "previousValue"
    NEW_VALUE = "newValue"
    ISSUE_FIELD = "issueField"
    NAME = "name"
    BODY = "body"
    ISSUES = "issues"
    NUMBER = "number"
    VALUE = "value"
    ISSUE_FIELD_VALUES = "issueFieldValues"


NOT_STARTED: Final = "not-started"
NOT_APPLICABLE: Final = "none"
NUL: Final = "\x00"
TEXT_ENCODING: Final = "utf-8"
PAYLOAD_FROM_STDIN: Final = "stdin"
IDEMPOTENCY_KEY_SEPARATOR: Final = ":"
RULE_ID_ALPHABET: Final = string.ascii_lowercase + string.digits
RULE_ID_SEPARATOR: Final = "-"
_RULE_ID_RUN: Final = f"[{re.escape(RULE_ID_ALPHABET)}]+"
RULE_ID_PATTERN: Final = re.compile(
    f"{_RULE_ID_RUN}(?:{re.escape(RULE_ID_SEPARATOR)}{_RULE_ID_RUN})*"
)
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
GH_EXECUTABLE: Final = "gh"
_GRAPHQL: Final = (GH_EXECUTABLE, "api", "graphql")

#: One store read takes pages of this many entries, at most this many pages.
AUTHORITY_PAGE_SIZE: Final = 100
AUTHORITY_MAX_PAGES: Final = 10

_QUERY_HEAD: Final = (
    "query($o:String!,$r:String!,$n:Int!,$after:String)"
    "{repository(owner:$o,name:$r){issue(number:$n){"
)
_AUTHORITY_QUERIES: Final[Mapping[AuthorityRead, str]] = {
    AuthorityRead.EVENTS: (
        f"{_QUERY_HEAD}{StoreField.TIMELINE_ITEMS}"
        f"(first:{AUTHORITY_PAGE_SIZE},after:$after,"
        "itemTypes:[ISSUE_FIELD_CHANGED_EVENT])"
        "{pageInfo{hasNextPage endCursor} nodes{... on IssueFieldChangedEvent"
        "{createdAt actor{login} previousValue newValue issueField"
        "{... on IssueFieldSingleSelect{name} ... on IssueFieldText{name}}}}}}}}"
    ),
}
_AUTHORITY_CONNECTIONS: Final[Mapping[AuthorityRead, StoreField]] = {
    AuthorityRead.EVENTS: StoreField.TIMELINE_ITEMS,
}
_PUBLISHED_QUERY: Final = (
    "query($o:String!,$r:String!,$n:Int!)"
    f"{{repository(owner:$o,name:$r){{issue(number:$n){{{StoreField.BODY}}}}}}}"
)
ISSUE_FIELD_VALUES_PAGE_SIZE: Final = 50
_RELATIONS_QUERY: Final = (
    "query($o:String!,$r:String!,$after:String)"
    f"{{repository(owner:$o,name:$r){{{StoreField.ISSUES}"
    f"(first:{AUTHORITY_PAGE_SIZE},after:$after)"
    "{pageInfo{hasNextPage endCursor} nodes{number "
    f"issueFieldValues(first:{ISSUE_FIELD_VALUES_PAGE_SIZE})"
    "{pageInfo{hasNextPage} nodes{... on IssueFieldNumberValue{value field{... on IssueFieldNumber{name}}}"
    " ... on IssueFieldTextValue{value field{... on IssueFieldText{name}}}"
    " ... on IssueFieldSingleSelectValue{name field{... on IssueFieldSingleSelect"
    "{name}}}}}}}}}"
)
PRODUCT_FIELD: Final = "Product"
PARENT_FIELD: Final = "Parent"
PREDECESSORS_FIELD: Final = "Predecessors"
PREDECESSOR_SEPARATOR: Final = ", "
ISSUE_IDENTITY_PATTERN: Final = re.compile(
    r"([A-Za-z0-9][A-Za-z0-9-]*)/([A-Za-z0-9._-]+)#([1-9][0-9]*)"
)

#: The fields each operation's request carries besides ``operation``.
REQUIRED_FIELDS: Final[Mapping[Operation, frozenset[RequestField]]] = {
    Operation.READ_CANDIDATE: frozenset({RequestField.PATH, RequestField.ROOT}),
    Operation.RESOLVE_REFERENCE: frozenset({RequestField.PATH, RequestField.ROOT}),
    Operation.TOOL_VERSION: frozenset(),
    Operation.START: frozenset(
        {RequestField.PATH, RequestField.ROOT, RequestField.CANDIDATE_SHA256}
    ),
    Operation.ADD_SCOPE: frozenset(
        {
            RequestField.PATH,
            RequestField.ROOT,
            RequestField.RUN_TOKEN,
            RequestField.PAYLOAD,
        }
    ),
    Operation.ADD_FINDING: frozenset(
        {
            RequestField.PATH,
            RequestField.ROOT,
            RequestField.RUN_TOKEN,
            RequestField.PAYLOAD,
        }
    ),
    Operation.RECONCILE: frozenset(
        {RequestField.PATH, RequestField.ROOT, RequestField.RUN_TOKEN}
    ),
    Operation.FINISH: frozenset(
        {
            RequestField.PATH,
            RequestField.ROOT,
            RequestField.RUN_TOKEN,
            RequestField.TERMINAL_STATUS,
        }
    ),
    Operation.READ_AUTHORITY: frozenset({RequestField.ISSUE}),
    Operation.READ_PUBLISHED: frozenset({RequestField.ISSUE}),
    Operation.READ_RELATIONS: frozenset({RequestField.ISSUE}),
    Operation.COUNT_LIMITS: frozenset({RequestField.PATH, RequestField.ROOT}),
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


_RENDER_HINT: Final = (
    "; rerun the run's render command by hand and confirm the installed spx "
    "version prints the rendered projection"
)
_STORE_HINT: Final = (
    "; rerun the store query by hand and confirm gh is authenticated for the "
    "store's repository"
)
_BOUND_HINT: Final = (
    "; the runner reads no further, so report this block rather than judge the "
    "unread part"
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
            f"{argv[0]} printed output that is not UTF-8; rerun the command in this result's command field by hand and confirm the installed tool prints UTF-8 text",
            run_token=run_token,
            evidence=evidence,
        ) from exc
    except (OSError, ValueError) as exc:
        evidence[ResultField.EXIT_CODE] = NOT_APPLICABLE
        evidence[ResultField.STDERR] = str(exc)
        raise Blocked(
            BlockReason.COMMAND_FAILED,
            f"{argv[0]} could not be executed; confirm {argv[0]} is installed and on PATH, then repeat the request",
            run_token=run_token,
            evidence=evidence,
        ) from exc
    if result.exit_code != 0:
        evidence[ResultField.EXIT_CODE] = result.exit_code
        evidence[ResultField.STDERR] = result.stderr
        raise Blocked(
            BlockReason.COMMAND_FAILED,
            f"{argv[0]} exited {result.exit_code}; the stderr and command fields of this result show the failure, so rerun that command by hand to reproduce it before repeating the request",
            run_token=run_token,
            evidence=evidence,
        )
    return result.stdout


def _json_lines(
    stdout: str, *, argv: Sequence[str], run_token: str | None = None
) -> list[dict[str, object]]:
    """Parse every non-empty stdout line as one JSON object.

    ``argv`` names the command that printed ``stdout`` so a block can say which
    command to rerun by hand.
    """
    command = " ".join(argv)
    objects: list[dict[str, object]] = []
    for line in stdout.splitlines():
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise Blocked(
                BlockReason.UNREADABLE_OUTPUT,
                f"`{command}` printed a line that is not JSON ({exc.msg}); "
                "run it by hand and confirm the installed tool prints one JSON "
                "object per line",
                run_token=run_token,
            ) from exc
        except ValueError as exc:
            raise Blocked(
                BlockReason.UNREADABLE_OUTPUT,
                f"`{command}` printed output that cannot be parsed ({exc}); "
                "run it by hand and confirm it prints one JSON object per line",
                run_token=run_token,
            ) from exc
        except RecursionError as exc:
            raise Blocked(
                BlockReason.UNREADABLE_OUTPUT,
                f"`{command}` printed JSON nested too deeply to parse; "
                "run it by hand and confirm the installed tool version",
                run_token=run_token,
            ) from exc
        if not isinstance(value, dict):
            raise Blocked(
                BlockReason.UNREADABLE_OUTPUT,
                f"`{command}` printed a JSON {type(value).__name__} line "
                "where an object is required; run it by hand and confirm "
                "the installed tool version",
                run_token=run_token,
            )
        objects.append(value)
    if not objects:
        raise Blocked(
            BlockReason.UNREADABLE_OUTPUT,
            f"`{command}` printed no JSON; run it by hand and confirm it "
            "exits with output on stdout",
            run_token=run_token,
        )
    return objects


def _repository_root(context: _Context) -> pathlib.Path:
    stdout = _command(context, _GIT_TOPLEVEL, cwd=context.cwd).strip()
    if not stdout:
        raise Blocked(
            BlockReason.UNREADABLE_OUTPUT,
            f"`{' '.join(_GIT_TOPLEVEL)}` printed no repository root in "
            f"{context.cwd}; run the request from inside a git worktree",
        )
    return pathlib.Path(stdout)


def _received(request: Mapping[str, object], field: RequestField) -> str:
    """Describe the value a request carries for ``field``."""
    if field not in request:
        return "no value"
    return f"a {type(request[field]).__name__}"


def _string(request: Mapping[str, object], field: RequestField) -> str:
    value = request.get(field)
    if not isinstance(value, str) or not value:
        raise Blocked(
            BlockReason.INVALID_REQUEST,
            f"request field {field.value} must be a non-empty JSON string, "
            f"received {_received(request, field)}; set it to a non-empty string",
        )
    return value


def _normalized_path(value: str) -> str:
    """Accept only a normalized repository-relative POSIX path."""
    defect = _system_text_defect(value)
    if defect is not None:
        raise Blocked(
            BlockReason.PATH_REJECTED,
            f"path {defect}: {value!r}; pass a repository-relative path of printable UTF-8 text",
        )
    pure = pathlib.PurePosixPath(value)
    if pure.is_absolute():
        raise Blocked(
            BlockReason.PATH_REJECTED,
            f"path is absolute: {value}; pass the repository-relative form, "
            f"such as {value.lstrip('/')!r}",
        )
    if ".." in pure.parts:
        raise Blocked(
            BlockReason.PATH_REJECTED,
            f"path traverses a parent: {value}; pass a path that stays "
            "inside the repository, with no `..` segment",
        )
    if str(pure) != value or pure.parts in ((), (".",)):
        raise Blocked(
            BlockReason.PATH_REJECTED,
            f"path is not normalized: {value}; pass the normalized form "
            f"{str(pure)!r}, with no empty, `.`, or repeated-slash segment",
        )
    return value


def _candidate_path(request: Mapping[str, object]) -> str:
    return _normalized_path(_string(request, RequestField.PATH))


def _reference_path(request: Mapping[str, object]) -> str:
    named = _string(request, RequestField.PATH)
    defect = _system_text_defect(named)
    if defect is not None:
        raise Blocked(
            BlockReason.PATH_REJECTED,
            f"path {defect}: {named!r}; pass a path of printable UTF-8 text",
        )
    return named


def _checkout_root(request: Mapping[str, object]) -> pathlib.Path:
    """Return the Product's checkout root a request names, an absolute path."""
    named = _string(request, RequestField.ROOT)
    defect = _system_text_defect(named)
    if defect is not None:
        raise Blocked(
            BlockReason.PATH_REJECTED,
            f"root {defect}: {named!r}; pass the absolute path of the Product's checkout root",
        )
    root = pathlib.PurePosixPath(named)
    if not root.is_absolute():
        raise Blocked(
            BlockReason.INVALID_REQUEST,
            f"request field {RequestField.ROOT.value} must be an absolute path, received {named!r}; pass the absolute path of the Product's checkout root",
        )
    return pathlib.Path(named)


def _candidate_sha256(request: Mapping[str, object]) -> str:
    return _string(request, RequestField.CANDIDATE_SHA256)


def _run_token(request: Mapping[str, object]) -> str:
    token = _string(request, RequestField.RUN_TOKEN)
    defect = _system_text_defect(token)
    if defect is not None:
        raise Blocked(
            BlockReason.INVALID_REQUEST,
            f"{RequestField.RUN_TOKEN} {defect}; pass the runToken string that start returned",
        )
    return token


def _unit_id(request: Mapping[str, object]) -> str:
    payload = request.get(RequestField.PAYLOAD)
    unit_id = payload.get(SpxField.UNIT_ID) if isinstance(payload, dict) else None
    if not isinstance(unit_id, str) or not unit_id:
        raise Blocked(
            BlockReason.INVALID_REQUEST,
            f"payload must be an object with a non-empty {SpxField.UNIT_ID}; set payload.{SpxField.UNIT_ID} to the scope unit's id string",
        )
    defect = _system_text_defect(unit_id)
    if defect is not None:
        raise Blocked(
            BlockReason.INVALID_REQUEST,
            f"payload {SpxField.UNIT_ID} {defect}; pass the unit id as printable UTF-8 text",
        )
    return unit_id


def _finding_rule(request: Mapping[str, object]) -> str:
    payload = request.get(RequestField.PAYLOAD)
    rule = payload.get(SpxField.RULE) if isinstance(payload, dict) else None
    if not isinstance(rule, str) or not RULE_ID_PATTERN.fullmatch(rule):
        raise Blocked(
            BlockReason.INVALID_REQUEST,
            f"payload {SpxField.RULE} must match {RULE_ID_PATTERN.pattern}, received {rule!r}; pass the finding's catalog rule identifier",
        )
    return rule


def _payload_text(request: Mapping[str, object]) -> str:
    try:
        return json.dumps(request.get(RequestField.PAYLOAD), separators=(",", ":"))
    except RecursionError as exc:
        raise Blocked(
            BlockReason.INVALID_REQUEST,
            "payload nests too deeply to serialize; flatten it to the fields its record declares",
        ) from exc


def _terminal_status(request: Mapping[str, object]) -> TerminalStatus:
    terminal = _string(request, RequestField.TERMINAL_STATUS)
    if terminal not in {status.value for status in TerminalStatus}:
        raise Blocked(
            BlockReason.INVALID_REQUEST,
            f"{RequestField.TERMINAL_STATUS} must be one of {', '.join(TerminalStatus)}, received {terminal!r}; pass one of those values",
        )
    return TerminalStatus(terminal)


def _issue_identity(request: Mapping[str, object]) -> tuple[str, str, str]:
    """Return ``(owner, repository, number)`` of the canonical issue identity."""
    named = request.get(RequestField.ISSUE)
    found = ISSUE_IDENTITY_PATTERN.fullmatch(named) if isinstance(named, str) else None
    if found is None:
        raise Blocked(
            BlockReason.INVALID_REQUEST,
            f"{RequestField.ISSUE} must match {ISSUE_IDENTITY_PATTERN.pattern}, received {named!r}; write the issue as owner/repository#number, such as acme/changes#12",
        )
    owner, repository, number = found.groups()
    return owner, repository, number


#: The field checks ``validate_request`` applies to each operation, in order.
_REQUEST_CHECKS: Final[
    Mapping[Operation, tuple[Callable[[Mapping[str, object]], object], ...]]
] = {
    Operation.READ_CANDIDATE: (_candidate_path, _checkout_root),
    Operation.RESOLVE_REFERENCE: (_reference_path, _checkout_root),
    Operation.TOOL_VERSION: (),
    Operation.START: (_candidate_path, _checkout_root, _candidate_sha256),
    Operation.ADD_SCOPE: (
        _candidate_path,
        _checkout_root,
        _run_token,
        _unit_id,
        _payload_text,
    ),
    Operation.ADD_FINDING: (
        _candidate_path,
        _checkout_root,
        _run_token,
        _unit_id,
        _finding_rule,
        _payload_text,
    ),
    Operation.RECONCILE: (_candidate_path, _checkout_root, _run_token),
    Operation.FINISH: (_candidate_path, _checkout_root, _run_token, _terminal_status),
    Operation.READ_AUTHORITY: (_issue_identity,),
    Operation.READ_PUBLISHED: (_issue_identity,),
    Operation.READ_RELATIONS: (_issue_identity,),
    Operation.COUNT_LIMITS: (_candidate_path, _checkout_root),
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
            f"{RequestField.OPERATION} must be one of {', '.join(Operation)}, received {request.get(RequestField.OPERATION)!r}; name one of those operations",
        )
    allowed = REQUIRED_FIELDS[operation] | {RequestField.OPERATION}
    missing = sorted(field.value for field in allowed if field not in request)
    unexpected = sorted(str(field) for field in request if field not in allowed)
    if missing or unexpected:
        raise Blocked(
            BlockReason.INVALID_REQUEST,
            f"{operation} request fields: missing {missing}, unexpected {unexpected}; send exactly {sorted(str(field) for field in allowed)}",
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
            BlockReason.PATH_REJECTED,
            f"path cannot be resolved: {named!r}: {exc}; pass a path whose parent directories exist and are readable",
        ) from exc


def _live_content(root: pathlib.Path, relative: str) -> str:
    """Read the candidate exactly as stored, refusing a path that escapes the root."""
    candidate = root / relative
    if not _within(root, candidate, relative):
        raise Blocked(
            BlockReason.PATH_REJECTED,
            f"path resolves outside the repository: {relative}; pass a path that stays inside the repository and is not a link leaving it",
        )
    if not candidate.exists():
        raise Blocked(
            BlockReason.CANDIDATE_MISSING,
            f"candidate is absent: {relative}; pass the repository-relative path of an existing file",
        )
    if not candidate.is_file():
        raise Blocked(
            BlockReason.PATH_REJECTED,
            f"candidate is not a regular file: {relative}; pass the path of a file, not a directory or special file",
        )
    try:
        stored = candidate.read_bytes()
    except FileNotFoundError as exc:
        raise Blocked(
            BlockReason.CANDIDATE_MISSING,
            f"candidate is absent: {relative}; pass the repository-relative path of an existing file",
        ) from exc
    except OSError as exc:
        raise Blocked(
            BlockReason.CANDIDATE_UNREADABLE,
            f"candidate cannot be read: {relative}: {exc.strerror or exc}; fix the file's read permission and repeat the request",
        ) from exc
    try:
        return stored.decode(TEXT_ENCODING)
    except UnicodeDecodeError as exc:
        raise Blocked(
            BlockReason.PATH_REJECTED,
            f"candidate is not UTF-8 text: {relative}; save the file as UTF-8 text and repeat the request",
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
    return _json_lines(
        stdout, argv=_run_argv(verb, relative, run_token), run_token=run_token
    )[-1]


def _retained_content(
    context: _Context, root: pathlib.Path, relative: str, run_token: str
) -> str:
    replay = _run_json(context, root, ("input",), relative, run_token)
    content = replay.get(SpxField.CONTENT)
    if not isinstance(content, str):
        raise Blocked(
            BlockReason.UNREADABLE_OUTPUT,
            f"retained input carries no content string{_RENDER_HINT}",
            run_token=run_token,
        )
    return content


def _read_candidate(
    context: _Context, request: Mapping[str, object]
) -> dict[str, object]:
    relative = _candidate_path(request)
    content = _live_content(_product_root(context, _checkout_root(request)), relative)
    return {
        ResultField.PATH: relative,
        ResultField.SHA256: _sha256(content),
        ResultField.CONTENT: content,
    }


def _product_root(context: _Context, named: pathlib.Path) -> pathlib.Path:
    """Return the repository checkout root ``named`` names, or block naming it."""
    if not named.is_dir():
        raise Blocked(
            BlockReason.PATH_REJECTED,
            f"root is not a directory: {named}; pass the absolute path of the Product's checkout root",
        )
    try:
        top = _repository_root(_Context(runner=context.runner, cwd=named))
    except Blocked as exc:
        raise Blocked(
            BlockReason.PATH_REJECTED,
            f"root is no repository checkout: {named}; pass the absolute path of the directory that holds the Product's checkout",
        ) from exc
    if top.resolve() != named.resolve():
        raise Blocked(
            BlockReason.PATH_REJECTED,
            f"root is no repository checkout root: {named}; pass the absolute path of the directory that holds the Product's checkout",
        )
    return top


def _resolve_reference(
    context: _Context, request: Mapping[str, object]
) -> dict[str, object]:
    named = _reference_path(request)
    root = _product_root(context, _checkout_root(request))
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
        raise Blocked(
            BlockReason.UNREADABLE_OUTPUT,
            f"`{' '.join(_SPX_VERSION)}` printed no version; confirm spx is "
            "installed and on PATH",
        )
    return {ResultField.TOOL_VERSION: version}


def _start(context: _Context, request: Mapping[str, object]) -> dict[str, object]:
    relative = _candidate_path(request)
    expected = _candidate_sha256(request)
    root = _product_root(context, _checkout_root(request))
    content = _live_content(root, relative)
    if _sha256(content) != expected:
        raise Blocked(
            BlockReason.CANDIDATE_CHANGED,
            "candidate differs from the content read before the run; call read-candidate again and restart with the new candidateSha256",
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
    lines = _json_lines(_command(context, argv, cwd=root), argv=argv)
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
        raise Blocked(
            BlockReason.UNREADABLE_OUTPUT,
            f"`{' '.join(argv)}` printed no line carrying a run locator and "
            "run token; confirm the installed spx version supports the run "
            "`start` verb",
        )
    retained = _retained_content(context, root, relative, run_token)
    if retained != content:
        raise Blocked(
            BlockReason.RETAINED_INPUT_MISMATCH,
            "retained input differs from the candidate the runner read; the candidate changed during start, so repeat read-candidate and start",
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
        cwd=_product_root(context, _checkout_root(request)),
        stdin=_payload_text(request),
        payload_key=idempotency_key,
    )
    accepted = _json_lines(stdout, argv=argv)[-1]
    return {
        ResultField.RUN_TOKEN: run_token,
        ResultField.IDEMPOTENCY_KEY: idempotency_key,
        ResultField.SEQUENCE: accepted.get(SpxField.SEQUENCE),
        ResultField.IDEMPOTENT: accepted.get(SpxField.IDEMPOTENT),
    }


def _add_scope(context: _Context, request: Mapping[str, object]) -> dict[str, object]:
    return _append(context, request, noun="scope", idempotency_key=_unit_id(request))


def finding_key(unit_id: str, rule: str) -> str:
    """Return the idempotency key of the one finding of a rule on one unit."""
    return f"{unit_id}{IDEMPOTENCY_KEY_SEPARATOR}{rule}"


def _add_finding(context: _Context, request: Mapping[str, object]) -> dict[str, object]:
    key = finding_key(_unit_id(request), _finding_rule(request))
    return _append(context, request, noun="finding", idempotency_key=key)


def _finding_entries(
    projection: Mapping[str, object],
) -> list[tuple[int, dict[str, object]]]:
    """Return every rendered finding as ``(seq, payload)`` once, in journal order."""
    groups = projection.get(SpxField.FINDINGS)
    if not isinstance(groups, dict):
        raise Blocked(
            BlockReason.UNREADABLE_OUTPUT,
            f"rendered projection carries no findings object{_RENDER_HINT}",
        )
    entries: dict[int, dict[str, object]] = {}
    for group in groups.values():
        if not isinstance(group, list):
            raise Blocked(
                BlockReason.UNREADABLE_OUTPUT,
                f"rendered findings group is not an array{_RENDER_HINT}",
            )
        for entry in group:
            seq = entry.get(SpxField.SEQ) if isinstance(entry, dict) else None
            payload = entry.get(SpxField.PAYLOAD) if isinstance(entry, dict) else None
            if not isinstance(seq, int) or not isinstance(payload, dict):
                raise Blocked(
                    BlockReason.UNREADABLE_OUTPUT,
                    f"rendered finding lacks an integer seq and a payload object{_RENDER_HINT}",
                )
            entries.setdefault(seq, payload)
    return sorted(entries.items())


def _reconcile(context: _Context, request: Mapping[str, object]) -> dict[str, object]:
    relative = _candidate_path(request)
    run_token = _run_token(request)
    root = _product_root(context, _checkout_root(request))
    retained = _retained_content(context, root, relative, run_token)
    live = _live_content(root, relative)
    if live != retained:
        raise Blocked(
            BlockReason.CANDIDATE_CHANGED,
            "candidate differs from the retained input; the candidate changed after start, so call read-candidate again and start a new run for the changed content",
            evidence={
                ResultField.RETAINED_SHA256: _sha256(retained),
                ResultField.LIVE_SHA256: _sha256(live),
            },
        )
    run_status = _run_json(context, root, ("status",), relative, run_token)
    projection = _run_json(context, root, ("render",), relative, run_token)
    units = projection.get(SpxField.AUDIT_SCOPE_UNITS)
    if not isinstance(units, list) or not all(isinstance(unit, dict) for unit in units):
        raise Blocked(
            BlockReason.UNREADABLE_OUTPUT,
            f"rendered projection lacks a {SpxField.AUDIT_SCOPE_UNITS} array of objects{_RENDER_HINT}",
        )
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
        for unit in units
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
    root = _product_root(context, _checkout_root(request))
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


def _connection(
    answer: Mapping[str, object], kind: AuthorityRead
) -> Mapping[str, object]:
    """Return the connection of ``kind`` from one store answer, or block."""
    node: object = answer
    for key in (StoreField.DATA, StoreField.REPOSITORY, StoreField.ISSUE):
        node = node.get(key) if isinstance(node, dict) else None
    connection = (
        node.get(_AUTHORITY_CONNECTIONS[kind]) if isinstance(node, dict) else None
    )
    if not isinstance(connection, dict):
        raise Blocked(
            BlockReason.UNREADABLE_OUTPUT,
            f"store answer carries no {_AUTHORITY_CONNECTIONS[kind]} connection{_STORE_HINT}",
        )
    return connection


def _login(person: object) -> object:
    return person.get(StoreField.LOGIN) if isinstance(person, dict) else None


def _event(node: Mapping[str, object]) -> dict[str, object]:
    field = node.get(StoreField.ISSUE_FIELD)
    return {
        ResultField.CREATED_AT: node.get(StoreField.CREATED_AT),
        ResultField.ACTOR: _login(node.get(StoreField.ACTOR)),
        ResultField.FIELD: field.get(StoreField.NAME)
        if isinstance(field, dict)
        else None,
        ResultField.PREVIOUS_VALUE: node.get(StoreField.PREVIOUS_VALUE),
        ResultField.NEW_VALUE: node.get(StoreField.NEW_VALUE),
    }


def _read_connection(
    context: _Context, kind: AuthorityRead, identity: tuple[str, str, str]
) -> list[dict[str, object]]:
    """Read every entry of one connection within the page bound, or block."""
    owner, repository, number = identity
    entries: list[dict[str, object]] = []
    cursor: str | None = None
    for _page in range(AUTHORITY_MAX_PAGES):
        argv = [
            *_GRAPHQL,
            "-f",
            f"query={_AUTHORITY_QUERIES[kind]}",
            "-f",
            f"o={owner}",
            "-f",
            f"r={repository}",
            "-F",
            f"n={number}",
        ]
        if cursor is not None:
            argv += ["-f", f"after={cursor}"]
        connection = _connection(
            _json_lines(_command(context, argv, cwd=context.cwd), argv=argv)[-1],
            kind,
        )
        nodes = connection.get(StoreField.NODES)
        info = connection.get(StoreField.PAGE_INFO)
        if not isinstance(nodes, list) or not isinstance(info, dict):
            raise Blocked(
                BlockReason.UNREADABLE_OUTPUT,
                f"{kind} page carries no nodes array and pageInfo object{_STORE_HINT}",
            )
        if not all(isinstance(node, dict) for node in nodes):
            raise Blocked(
                BlockReason.UNREADABLE_OUTPUT,
                f"{kind} page holds an entry that is not an object{_STORE_HINT}",
            )
        entries.extend(_event(node) for node in nodes)
        if info.get(StoreField.HAS_NEXT_PAGE) is not True:
            return entries
        cursor = info.get(StoreField.END_CURSOR)
        if not isinstance(cursor, str) or not cursor:
            raise Blocked(
                BlockReason.UNREADABLE_OUTPUT,
                f"{kind} page reports a further page and no end cursor{_STORE_HINT}",
            )
    bound = f"{AUTHORITY_PAGE_SIZE} {kind} per page, {AUTHORITY_MAX_PAGES} pages"
    raise Blocked(
        BlockReason.PAGE_BOUND_REACHED,
        f"the {kind} read is not complete at {bound}{_BOUND_HINT}",
        evidence={ResultField.BOUND: bound},
    )


def _read_authority(
    context: _Context, request: Mapping[str, object]
) -> dict[str, object]:
    identity = _issue_identity(request)
    return {
        ResultField.ISSUE: request[RequestField.ISSUE],
        ResultField.EVENTS: _read_connection(context, AuthorityRead.EVENTS, identity),
    }


def _read_published(
    context: _Context, request: Mapping[str, object]
) -> dict[str, object]:
    """Return the store's published body of the named issue, or block."""
    owner, repository, number = _issue_identity(request)
    argv = [
        *_GRAPHQL,
        "-f",
        f"query={_PUBLISHED_QUERY}",
        "-f",
        f"o={owner}",
        "-f",
        f"r={repository}",
        "-F",
        f"n={number}",
    ]
    node: object = _json_lines(_command(context, argv, cwd=context.cwd), argv=argv)[-1]
    for key in (StoreField.DATA, StoreField.REPOSITORY, StoreField.ISSUE):
        node = node.get(key) if isinstance(node, dict) else None
    body = node.get(StoreField.BODY) if isinstance(node, dict) else None
    if not isinstance(body, str):
        raise Blocked(
            BlockReason.UNREADABLE_OUTPUT,
            f"store answer carries no issue {StoreField.BODY} string{_STORE_HINT}",
        )
    return {ResultField.ISSUE: request[RequestField.ISSUE], ResultField.BODY: body}


def _field_values(node: Mapping[str, object]) -> dict[str, object]:
    """Return the Product, Parent, and Predecessors values one store issue node carries."""
    values: dict[str, object] = {}
    container = node.get(StoreField.ISSUE_FIELD_VALUES)
    entries = container.get(StoreField.NODES) if isinstance(container, dict) else None
    info = container.get(StoreField.PAGE_INFO) if isinstance(container, dict) else None
    if isinstance(info, dict) and info.get(StoreField.HAS_NEXT_PAGE) is True:
        bound = f"{ISSUE_FIELD_VALUES_PAGE_SIZE} issue field values per issue"
        raise Blocked(
            BlockReason.PAGE_BOUND_REACHED,
            f"the issue field values read is not complete at {bound}{_BOUND_HINT}",
            evidence={ResultField.BOUND: bound},
        )
    for entry in entries if isinstance(entries, list) else []:
        field = entry.get("field") if isinstance(entry, dict) else None
        name = field.get(StoreField.NAME) if isinstance(field, dict) else None
        if name == PRODUCT_FIELD:
            values[PRODUCT_FIELD] = entry.get(StoreField.NAME)
        elif (
            name == PARENT_FIELD
            and isinstance(entry.get(StoreField.VALUE), int | float)
            and not isinstance(entry.get(StoreField.VALUE), bool)
        ):
            values[PARENT_FIELD] = int(entry[StoreField.VALUE])
        elif name == PREDECESSORS_FIELD and isinstance(
            entry.get(StoreField.VALUE), str
        ):
            values[PREDECESSORS_FIELD] = entry[StoreField.VALUE]
    return values


def _read_relations(
    context: _Context, request: Mapping[str, object]
) -> dict[str, object]:
    """Return the issue's Product and Parent, its Parent's Product, and its children.

    Reads every issue of the store's repository within the page bound; a child
    is an issue whose ``Parent`` number field equals the named issue's number,
    and an absorber is an issue whose ``Predecessors`` text field, split at
    every comma followed by one space, holds the named issue's identity.
    """
    owner, repository, number = _issue_identity(request)
    target = int(number)
    by_number: dict[int, dict[str, object]] = {}
    cursor: str | None = None
    for _page in range(AUTHORITY_MAX_PAGES):
        argv = [
            *_GRAPHQL,
            "-f",
            f"query={_RELATIONS_QUERY}",
            "-f",
            f"o={owner}",
            "-f",
            f"r={repository}",
        ]
        if cursor is not None:
            argv += ["-f", f"after={cursor}"]
        node: object = _json_lines(_command(context, argv, cwd=context.cwd), argv=argv)[
            -1
        ]
        for key in (StoreField.DATA, StoreField.REPOSITORY, StoreField.ISSUES):
            node = node.get(key) if isinstance(node, dict) else None
        nodes = node.get(StoreField.NODES) if isinstance(node, dict) else None
        info = node.get(StoreField.PAGE_INFO) if isinstance(node, dict) else None
        if not isinstance(nodes, list) or not isinstance(info, dict):
            raise Blocked(
                BlockReason.UNREADABLE_OUTPUT,
                f"relations page carries no nodes array and pageInfo object{_STORE_HINT}",
            )
        for entry in nodes:
            numbered = entry.get(StoreField.NUMBER) if isinstance(entry, dict) else None
            if not isinstance(numbered, int):
                raise Blocked(
                    BlockReason.UNREADABLE_OUTPUT,
                    f"relations page holds an entry with no issue number{_STORE_HINT}",
                )
            by_number[numbered] = _field_values(entry)
        if info.get(StoreField.HAS_NEXT_PAGE) is not True:
            own = by_number.get(target, {})
            parent = own.get(PARENT_FIELD)
            return {
                ResultField.ISSUE: request[RequestField.ISSUE],
                ResultField.PRODUCT: own.get(PRODUCT_FIELD),
                ResultField.PARENT: parent,
                ResultField.PARENT_PRODUCT: (
                    by_number.get(parent, {}).get(PRODUCT_FIELD)
                    if isinstance(parent, int)
                    else None
                ),
                ResultField.CHILDREN: [
                    {
                        ResultField.NUMBER: child,
                        ResultField.PRODUCT: values.get(PRODUCT_FIELD),
                    }
                    for child, values in sorted(by_number.items())
                    if values.get(PARENT_FIELD) == target
                ],
                ResultField.ABSORBERS: [
                    absorber
                    for absorber, values in sorted(by_number.items())
                    if request[RequestField.ISSUE]
                    in str(values.get(PREDECESSORS_FIELD, "")).split(
                        PREDECESSOR_SEPARATOR
                    )
                    and f"{owner}/{repository}#{absorber}"
                    not in str(own.get(PREDECESSORS_FIELD, "")).split(
                        PREDECESSOR_SEPARATOR
                    )
                ],
            }
        cursor = info.get(StoreField.END_CURSOR)
        if not isinstance(cursor, str) or not cursor:
            raise Blocked(
                BlockReason.UNREADABLE_OUTPUT,
                f"relations page reports a further page and no end cursor{_STORE_HINT}",
            )
    bound = f"{AUTHORITY_PAGE_SIZE} issues per page, {AUTHORITY_MAX_PAGES} pages"
    raise Blocked(
        BlockReason.PAGE_BOUND_REACHED,
        f"the issues read is not complete at {bound}{_BOUND_HINT}",
        evidence={ResultField.BOUND: bound},
    )


TITLE_WORD_LIMIT: Final = 15
INTENT_WORD_LIMIT: Final = 60
_FRONT_MATTER_PATTERN: Final = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
_TITLE_PATTERN: Final = re.compile(r"^title:[ \t]*(.*)$", re.MULTILINE)
_LINK_PATTERN: Final = re.compile(r"\[([^\]]*)\]\([^)]*\)")
_LIST_MARKER_PATTERN: Final = re.compile(r"^[ \t]*(?:[-*]|\d+\.)[ \t]+", re.MULTILINE)
_EMPHASIS_PATTERN: Final = re.compile(r"\*+|_{2,}")
_HEADING_PATTERN: Final = re.compile(r"##[ \t]+(.+?)[ \t]*$")


def count_words(text: str) -> int:
    """Count words: whitespace-separated tokens that hold a letter or a digit.

    A list marker and emphasis markup carry no word, a link counts its text, and
    a label such as ``What:`` counts as one word.
    """
    plain = _LINK_PATTERN.sub(r"\1", text)
    plain = _LIST_MARKER_PATTERN.sub("", plain)
    plain = _EMPHASIS_PATTERN.sub("", plain)
    return len([token for token in plain.split() if any(c.isalnum() for c in token)])


def _body_sections(body: str) -> dict[str, str]:
    """Map each level-two heading outside a code fence to its text."""
    sections: dict[str, list[str]] = {}
    current: list[str] | None = None
    fenced = False
    for line in body.splitlines():
        if line.lstrip().startswith("```"):
            fenced = not fenced
        heading = None if fenced else _HEADING_PATTERN.match(line)
        if heading:
            current = sections.setdefault(heading.group(1), [])
        elif current is not None:
            current.append(line)
    return {name: "\n".join(lines) for name, lines in sections.items()}


def _count_limits(
    context: _Context, request: Mapping[str, object]
) -> dict[str, object]:
    """Count the title's words and the Intent section's words, labels included."""
    relative = _candidate_path(request)
    content = _live_content(_product_root(context, _checkout_root(request)), relative)
    front = _FRONT_MATTER_PATTERN.match(content)
    body = content[front.end() :] if front else content
    title_match = _TITLE_PATTERN.search(front.group(1)) if front else None
    title = title_match.group(1).strip().strip("\"'") if title_match else ""
    measured: list[dict[str, object]] = [
        {
            ResultField.SECTION: "title",
            ResultField.LIMIT: TITLE_WORD_LIMIT,
            ResultField.COUNT: len(title.split()),
        }
    ]
    sections = _body_sections(body)
    if "Intent" in sections:
        measured.append(
            {
                ResultField.SECTION: "Intent",
                ResultField.LIMIT: INTENT_WORD_LIMIT,
                ResultField.COUNT: count_words(sections["Intent"]),
            }
        )
    return {
        ResultField.PATH: relative,
        ResultField.SHA256: _sha256(content),
        ResultField.LIMITS: measured,
        ResultField.VIOLATIONS: [
            item
            for item in measured
            if int(str(item[ResultField.COUNT])) > int(str(item[ResultField.LIMIT]))
        ],
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
    Operation.READ_AUTHORITY: _read_authority,
    Operation.READ_PUBLISHED: _read_published,
    Operation.READ_RELATIONS: _read_relations,
    Operation.COUNT_LIMITS: _count_limits,
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
            BlockReason.INVALID_REQUEST,
            f"request is not JSON: {exc.msg} at line {exc.lineno} column {exc.colno}; write the request as one JSON object and pass it again",
        ) from exc
    except ValueError as exc:
        raise Blocked(
            BlockReason.INVALID_REQUEST,
            f"request cannot be parsed: {exc}; write the request as one JSON object and pass it again",
        ) from exc
    except RecursionError as exc:
        raise Blocked(
            BlockReason.INVALID_REQUEST,
            "request nests too deeply to parse; flatten the request to the fields its operation takes",
        ) from exc
    if not isinstance(request, dict):
        raise Blocked(
            BlockReason.INVALID_REQUEST,
            f"request must be a JSON object, received a JSON "
            f"{type(request).__name__}; write the request file as "
            '`{"operation": ...}` and pass its path',
        )
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
                BlockReason.UNREADABLE_OUTPUT,
                "result nests too deeply to serialize; report this block, since the operation's result cannot be printed",
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
            Blocked(
                BlockReason.INVALID_REQUEST,
                "request is not UTF-8 text; write the request file as UTF-8 and pass it again",
            ),
            NOT_STARTED,
        )
    except OSError as exc:
        code, result = _blocked_result(
            None,
            Blocked(
                BlockReason.INVALID_REQUEST,
                f"request could not be read: {exc}; confirm stdin is open and readable, then repeat the request",
            ),
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
