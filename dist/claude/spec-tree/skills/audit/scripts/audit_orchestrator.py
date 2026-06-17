"""Audit-orchestration helpers shipped with the spec-tree plugin.

Hosts the deterministic computations that the ``/audit`` skill and the
``audit-orchestrator`` agent cannot reliably execute in-process from prose:
scope hashing, branch slug derivation, base-ref detection, git plumbing,
lock acquisition, and the content-based identity used for regression
detection across audit runs.

Exposes a stdlib ``argparse`` CLI so the ``/audit`` skill can drive
each helper from shell. Subcommands: ``base-ref``, ``current-branch``,
``branch-slug``, ``scope-hash``, ``branch-scope``, ``modified-since``,
``sha-reachable``, ``acquire-lock``, ``release-lock``,
``state-transition``. Library callers continue to import the functions
directly via ``importlib.util`` (per the marketplace skill-co-located
Python convention); the CLI is a thin wrapper around the same surface.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import pathlib
import re
import subprocess
import sys
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from types import ModuleType
from typing import Any

NULL_BYTE = b"\x00"
SCOPE_HASH_LENGTH = 12
DEFAULT_LOCK_TTL_SECONDS = 600
LOCK_FILE_MODE = 0o644
MODIFIED_SINCE_RANGE_TEMPLATE = "{prior_sha}..HEAD"
COMMIT_PEEL_SUFFIX = "^{commit}"

STATE_FRONTMATTER_DELIMITER = "---"
FINDING_ID_FORMAT = "f-{:03d}"
STATE_SCHEMA_VERSION = 1
STATE_TITLE_TEMPLATE = "# Audit State — {branch}"
STATE_OPEN_HEADING = "## Open findings"
STATE_RESOLVED_HEADING = "## Resolved findings"
STATE_OPEN_TABLE_HEADER = (
    "| ID | File:line | Concern | Root cause | Required fix | First seen |"
)
STATE_OPEN_TABLE_SEPARATOR = "| --- | --- | --- | --- | --- | --- |"
STATE_RESOLVED_TABLE_HEADER = (
    "| ID | File:line | Concern | Root cause | First seen | Resolved at |"
)
STATE_RESOLVED_TABLE_SEPARATOR = "| --- | --- | --- | --- | --- | --- |"

# Cell escape uses backslash as the lead-in character so the three escape
# sequences (\\, \|, \n) compose without ambiguity. Escape order: backslash
# first (otherwise it would corrupt the subsequent escape introductions);
# pipe and newline order is interchangeable after that.
CELL_ESCAPE_BACKSLASH = "\\\\"
CELL_ESCAPE_PIPE = r"\|"
CELL_ESCAPE_NEWLINE = r"\n"


def _load_changeset_scope() -> ModuleType:
    """Load the shared ``changeset_scope`` module via ``importlib``.

    The git-derivation primitives — base-ref detection, current-branch
    detection, branch-scope, diff-range expansion, slug — live in the
    changeset-scope skill; this module imports them rather than redefining
    them.
    """
    cached = sys.modules.get("changeset_scope")
    if cached is not None:
        return cached
    path = (
        pathlib.Path(__file__).resolve().parent.parent.parent
        / "scope-changeset"
        / "scripts"
        / "changeset_scope.py"
    )
    spec = importlib.util.spec_from_file_location("changeset_scope", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load changeset_scope from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["changeset_scope"] = module
    spec.loader.exec_module(module)
    return module


_changeset_scope = _load_changeset_scope()

# Shared git-derivation primitives — defined once in changeset_scope, imported
# here. ``is`` identity holds, so the auditing CLI and the thread-store slug /
# base-ref re-export resolve the same objects.
BaseRefNotConfiguredError = _changeset_scope.BaseRefNotConfiguredError
DetachedHeadError = _changeset_scope.DetachedHeadError
expand_diff_range = _changeset_scope.expand_diff_range
branch_scope = _changeset_scope.branch_scope
detect_base_ref = _changeset_scope.detect_base_ref
detect_current_branch = _changeset_scope.detect_current_branch
branch_slug = _changeset_scope.branch_slug


class RunLockError(RuntimeError):
    """Raised when a fresh lock file already exists at the target path.

    Indicates another audit run is in progress (or recently crashed within
    the TTL window). Distinguishes the fresh-lock case (refuse) from the
    stale-lock case (overwrite — handled silently by ``RunLock``).
    """


class StateFileCorruptError(RuntimeError):
    """Raised by :func:`load_state` when an existing state file fails to parse.

    Distinguishes "corrupt file" from "no file" (``None`` return) and
    "valid file" (populated ``AuditState`` return) so callers can choose
    a recovery policy. With atomic ``save_state`` (write-to-temp +
    ``os.replace``), in-process corruption is unreachable; this error
    therefore signals out-of-band tampering, partial writes from an
    earlier non-atomic implementation, or a schema-version mismatch
    that the parser cannot accommodate.
    """


def compute_scope_hash(files: list[tuple[str, str]]) -> str:
    """Return a deterministic, collision-resistant hex digest of the file list.

    Each ``(path, content)`` pair is encoded as
    ``path\\0<byte_count>\\0<content>`` before being fed to SHA-256. Without
    the byte-count prefix, distinct file lists can serialize to the same
    byte stream because the path-terminator nullbyte alone does not
    delimit the content/next-path boundary; for example
    ``[("a.ts", ""), ("a.tsb", "x")]`` and
    ``[("a.ts", "a.ts"), ("b", "x")]`` both produce
    ``a.ts\\0a.tsb\\0x`` under the unprefixed framing.

    Returns the first ``SCOPE_HASH_LENGTH = 12`` characters (48 bits) of
    the SHA-256 hex digest. The truncation is collision-resistant for the
    scope-identity use case — a single branch's diff history typically
    contains at most thousands of distinct scopes, well below the 48-bit
    birthday bound (~16M distinct scopes before a collision becomes
    plausible). The framing — not the truncation — is what prevents two
    distinct file lists with the same serialized bytes from colliding;
    see the worked example above. The caller is responsible for sorting
    ``files`` deterministically before calling this function; the hash
    is sensitive to order.
    """
    digest = hashlib.sha256()
    for path, content in files:
        content_bytes = content.encode("utf-8")
        digest.update(path.encode("utf-8"))
        digest.update(NULL_BYTE)
        digest.update(str(len(content_bytes)).encode("ascii"))
        digest.update(NULL_BYTE)
        digest.update(content_bytes)
    return digest.hexdigest()[:SCOPE_HASH_LENGTH]


def uncommitted_scope(
    *,
    patterns: list[str] | None = None,
    repo: pathlib.Path,
) -> list[str]:
    """Return uncommitted, staged, and untracked file paths relative to HEAD.

    ``git diff --name-only HEAD`` enumerates modified-and-staged files
    only — it never lists untracked files (those that have not yet been
    ``git add``-ed). A developer who creates a new file and runs the
    audit before staging it would see an empty scope under
    ``expand_diff_range("HEAD")``. This helper closes that gap by
    unioning ``git diff --name-only HEAD`` with
    ``git ls-files --others --exclude-standard`` and de-duplicating
    while preserving git's order: modified/staged paths first (as git
    diff returns them), then untracked paths (as ``ls-files`` returns
    them, alphabetised by git). Paths matched by ``.gitignore`` are
    excluded by ``--exclude-standard`` so build artefacts do not
    pollute the scope.

    ``patterns`` filters both halves: each pathspec is applied to the
    ``git diff`` call and to the ``ls-files`` call so a new ``foo.ts``
    file and an existing modified ``bar.ts`` are both retained under
    ``patterns=["*.ts"]``.
    """
    modified = expand_diff_range("HEAD", patterns=patterns, repo=repo)
    untracked_cmd = ["git", "ls-files", "--others", "--exclude-standard"]
    if patterns:
        untracked_cmd.append("--")
        untracked_cmd.extend(patterns)
    untracked_result = subprocess.run(  # noqa: S603 — fixed argv, no shell, patterns caller-controlled
        untracked_cmd,
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )
    untracked = [line for line in untracked_result.stdout.splitlines() if line]
    # ``modified`` and ``untracked`` are disjoint by construction
    # (untracked files cannot appear in ``git diff HEAD``), but a defensive
    # ``dict.fromkeys`` round-trip is cheap insurance against future git
    # behaviour changes and keeps the order ``modified, untracked``.
    return list(dict.fromkeys([*modified, *untracked]))


def modified_since(
    prior_sha: str,
    *,
    patterns: list[str] | None = None,
    repo: pathlib.Path,
) -> list[str]:
    """Return files changed between ``prior_sha`` and HEAD.

    Composes the diff range ``<prior_sha>..HEAD`` (two-dot tree-diff)
    and delegates to :func:`expand_diff_range`. The two-dot form is
    deliberate and contrasts with :func:`branch_scope`'s three-dot
    form: re-run scope must include any file currently differing
    between the prior state and HEAD's tree, including deletions of
    files that existed only on a divergent prior history. Three-dot
    would mask those by routing through the merge-base.

    The caller is responsible for confirming ``prior_sha`` is reachable
    in the local clone before invoking this helper; an unreachable
    SHA raises :class:`subprocess.CalledProcessError` from the
    underlying git invocation.

    ``patterns`` filters the result by pathspec when provided; empty
    or ``None`` returns every file in the range.
    """
    range_spec = MODIFIED_SINCE_RANGE_TEMPLATE.format(prior_sha=prior_sha)
    return expand_diff_range(range_spec, patterns=patterns, repo=repo)


def is_sha_reachable(sha: str, *, repo: pathlib.Path) -> bool:
    """Return ``True`` iff ``sha`` resolves to a commit object in ``repo``.

    Runs ``git rev-parse --verify --quiet <sha>^{commit}``. The
    ``^{commit}`` peel restricts the resolution to commit objects so a
    tree SHA, blob SHA, or tag-pointing-at-non-commit returns ``False``
    even though bare ``git rev-parse <sha>`` would succeed on those.
    The caller composes ``<sha>..HEAD`` ranges downstream; a tree SHA
    would compose to a syntactically valid range and produce garbage
    file lists without this commit-type guard.

    Detects the "prior-run SHA unreachable" failure mode where a state
    file's SHA was force-pushed away or never fetched into the local
    clone. The caller's re-run protocol falls back to a full
    branch-scope scan when this returns ``False``.

    Any non-zero exit from git (unknown SHA, malformed input, non-commit
    object) maps to ``False``; the helper does not propagate
    :class:`subprocess.CalledProcessError` because every error path
    means the same thing to the caller — the SHA cannot be used.
    """
    try:
        subprocess.run(  # noqa: S603 — fixed argv, no shell, sha is caller-controlled
            [
                "git",
                "rev-parse",
                "--verify",
                "--quiet",
                f"{sha}{COMMIT_PEEL_SUFFIX}",
            ],
            cwd=repo,
            capture_output=True,
            check=True,
        )
    except subprocess.CalledProcessError:
        return False
    return True


def _acquire_lock_once(
    path: pathlib.Path,
    *,
    max_age_seconds: float,
    now: Callable[[], float],
) -> int:
    """Atomically acquire the file lock at ``path``; return its open fd.

    Encapsulates the shared retry-on-stale loop used by both
    :class:`RunLock` and the CLI ``acquire-lock`` subcommand so the
    acquisition contract — ``O_CREAT | O_EXCL`` create with TTL-bounded
    stale-lock handling — lives in exactly one place. Both call sites
    handle their own post-acquisition work (timestamp write, mtime
    normalisation) so the helper stays minimal.

    ``O_CREAT | O_EXCL`` fails when the file already exists, which lets
    two concurrent acquirers distinguish "I got the lock" from "someone
    else holds it" without a TOCTOU window between an existence check
    and a write.

    Raises :class:`RunLockError` when an existing lock has mtime within
    ``max_age_seconds`` of ``now()`` (fresh — another holder is active).
    Overwrites a lock older than ``max_age_seconds`` (stale — left by a
    crashed run) by unlinking and retrying. ``stat`` after the failed
    ``O_EXCL`` open itself races against another holder's release; if
    the file disappears between create and stat, the outcome is
    equivalent to observing no lock at all — retry.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    while True:
        try:
            return os.open(
                path,
                os.O_CREAT | os.O_EXCL | os.O_WRONLY,
                LOCK_FILE_MODE,
            )
        except FileExistsError:
            try:
                age = now() - path.stat().st_mtime
            except FileNotFoundError:
                continue
            if age < max_age_seconds:
                raise RunLockError(
                    f"lock held: {path} (age {age:.0f}s, ttl {max_age_seconds:.0f}s)"
                ) from None
            try:
                path.unlink()
            except FileNotFoundError:
                pass
            continue


class RunLock:
    """File-based exclusive lock with a TTL-based stale-lock policy.

    Used by the ``audit-orchestrator`` agent to prevent concurrent runs on
    the same branch state file. Acquiring writes a lock file at ``path``
    whose mtime records the acquisition time (from the injected clock).
    On context exit (normal or exception), the lock file is removed.

    Acquisition rules:
      - No existing lock → acquire.
      - Existing lock with mtime within ``max_age_seconds`` → raise
        ``RunLockError`` (fresh; another run is in progress).
      - Existing lock with mtime older than ``max_age_seconds`` →
        acquire by overwriting (stale; previous run crashed).

    The ``now`` callable is injectable to keep TTL tests deterministic
    without sleeping; defaults to ``time.time``.
    """

    def __init__(
        self,
        path: pathlib.Path,
        *,
        max_age_seconds: float = DEFAULT_LOCK_TTL_SECONDS,
        now: Callable[[], float] = time.time,
    ) -> None:
        self._path = path
        self._max_age = max_age_seconds
        self._now = now

    def __enter__(self) -> RunLock:
        fd = _acquire_lock_once(
            self._path, max_age_seconds=self._max_age, now=self._now
        )
        timestamp = self._now()
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(str(timestamp))
        # Set mtime to the injected clock value so age comparisons
        # across acquisitions stay in the same time frame as
        # ``now``. Production default (``now=time.time``) sees this
        # as a no-op redundant write.
        os.utime(self._path, (timestamp, timestamp))
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        try:
            self._path.unlink()
        except FileNotFoundError:
            pass


@dataclass(frozen=True)
class Finding:
    """An open audit finding pinned to a specific file:line and root cause.

    Persisted as one row of the ``## Open findings`` table in the state
    file. Fields are plain strings so the table representation is
    lossless under the escaping policy in :func:`_escape_cell`.
    """

    id: str
    file_line: str
    concern: str
    root_cause: str
    required_fix: str
    first_seen: str


@dataclass(frozen=True)
class ResolvedFinding:
    """A finding that was open in a prior run and is no longer present.

    Persisted as one row of the ``## Resolved findings`` table. The
    ``resolved_at`` field carries the SHA of the run that flipped the
    finding from open to resolved so the re-run protocol can detect a
    regression (root cause returns at the same file:line) and reopen
    the original ID rather than allocating a new one.
    """

    id: str
    file_line: str
    concern: str
    root_cause: str
    first_seen: str
    resolved_at: str


@dataclass
class AuditState:
    """In-memory representation of a branch's audit state file.

    Frontmatter fields plus two findings tables. ``next_finding_id`` is
    an integer counter that strictly exceeds every ID ever assigned on
    this branch — open or resolved — so monotonic IDs survive across
    runs. The counter drives :func:`assign_finding_id`; the ID lists
    are read by callers that need to look up findings by identity but
    are not the source of truth for the next ID.

    ``schema_version`` defaults to :data:`STATE_SCHEMA_VERSION`. A
    future schema bump goes here and the parser routes by value.
    """

    branch: str
    first_run_sha: str
    first_run_at: str
    last_run_sha: str
    last_run_at: str
    last_verdict: str
    run_count: int
    next_finding_id: int
    open_findings: list[Finding] = field(default_factory=list)
    resolved_findings: list[ResolvedFinding] = field(default_factory=list)
    schema_version: int = STATE_SCHEMA_VERSION


_FRONTMATTER_FIELD_PATTERN = re.compile(r"^([a-z_]+):\s*(.+)$")
# Split markdown table cells on ``|`` only when not preceded by a backslash.
# Escaped pipes (``\|`` per ``_escape_cell``) stay inside their cell.
#
# Correctness invariant: ``_serialize_state`` joins cells with ``" | "``
# (space-pipe-space). A cell-boundary ``|`` is therefore always preceded by
# a space, never by a backslash from cell content — so a literal escaped
# backslash at a cell's tail (``\\``) followed by the cell boundary
# (``\\ | next``) parses correctly. Removing the space padding from the
# serializer would break this splitter for inputs ending in ``\\``.
_UNESCAPED_PIPE_PATTERN = re.compile(r"(?<!\\)\|")


def load_state(path: pathlib.Path) -> AuditState | None:
    """Return the parsed :class:`AuditState` at ``path``, or ``None`` if absent.

    Distinguishes three cases so the caller's branching is total:

    - ``path`` absent → ``None`` (first run).
    - ``path`` present and parseable → populated ``AuditState``.
    - ``path`` present and unparseable → :class:`StateFileCorruptError`
      (with atomic ``save_state`` this is unreachable in-process; it
      remains as a signal for out-of-band tampering or partial writes
      from an earlier non-atomic implementation).

    The on-disk format is YAML-ish frontmatter (one ``key: value`` pair
    per line between ``---`` delimiters) followed by two markdown
    tables under ``## Open findings`` and ``## Resolved findings``.
    """
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8")
    try:
        frontmatter, body = _split_frontmatter(text)
        fields = _parse_frontmatter(frontmatter)
        open_findings = _parse_open_table(body)
        resolved_findings = _parse_resolved_table(body)
        return AuditState(
            branch=fields["branch"],
            schema_version=int(fields["schema_version"]),
            first_run_sha=fields["first_run_sha"],
            first_run_at=fields["first_run_at"],
            last_run_sha=fields["last_run_sha"],
            last_run_at=fields["last_run_at"],
            last_verdict=fields["last_verdict"],
            run_count=int(fields["run_count"]),
            next_finding_id=int(fields["next_finding_id"]),
            open_findings=open_findings,
            resolved_findings=resolved_findings,
        )
    except (ValueError, KeyError, IndexError) as exc:
        # ``IndexError`` surfaces when ``_parse_open_table`` /
        # ``_parse_resolved_table`` index ``row[0]..row[5]`` against a
        # truncated row (out-of-band editing, a partial write from a
        # non-atomic predecessor). Callers branching on
        # :class:`StateFileCorruptError` must see those rows as corrupt
        # state, not as an uncaught exception.
        raise StateFileCorruptError(
            f"state file at {path} failed to parse: {exc}"
        ) from exc


def save_state(state: AuditState, path: pathlib.Path) -> None:
    """Write ``state`` to ``path`` atomically in the on-disk state-file format.

    Writes to ``<path>.tmp`` first, then calls :func:`os.replace` to
    rename it over ``path``. POSIX guarantees the rename is atomic on
    the same filesystem, so a crash between truncate-and-write and the
    rename leaves the prior state file intact rather than corrupted.
    The non-atomic alternative — writing directly with
    :meth:`pathlib.Path.write_text` — opens the destination in write
    mode (truncating it) before writing, leaving a partial file when
    interrupted.

    Creates ``path.parent`` if absent so callers do not need to
    pre-create ``.spx/audits/<lang>/`` for first runs.

    On ``write_text`` failure (disk full, permission denied) the
    partially-written ``.tmp`` is cleaned up so repeated failures do
    not accumulate orphans alongside the state file. The
    ``os.replace`` failure path is left alone — there the ``.tmp``
    holds the intended new content and the prior state file is
    intact, so preserving the ``.tmp`` makes the post-failure state
    recoverable.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    try:
        tmp.write_text(_serialize_state(state), encoding="utf-8")
    except OSError:
        try:
            tmp.unlink(missing_ok=True)
        except OSError:
            pass
        raise
    os.replace(tmp, path)


def assign_finding_id(state: AuditState) -> str:
    """Return the next monotonic finding ID and increment the counter.

    The ID is formatted as ``f-NNN`` with zero-padding to at least
    three digits. The counter strictly exceeds every ID ever assigned
    on this branch — open or resolved — so a finding resolved in a
    prior run never sees its ID reissued to a new finding. State
    persists ``next_finding_id`` through :func:`save_state` so the
    invariant survives across runs.
    """
    assigned = FINDING_ID_FORMAT.format(state.next_finding_id)
    state.next_finding_id += 1
    return assigned


def find_resolved_by_identity(
    state: AuditState,
    *,
    file_line: str,
    root_cause: str,
) -> ResolvedFinding | None:
    """Return the resolved finding matching (file_line, root_cause), or None.

    Identity for regression detection is the pair (file_line,
    root_cause): the same defect at the same code location. Absence
    (``None``) signals "no regression for this finding" so the caller
    allocates a fresh ID via :func:`assign_finding_id` instead.
    """
    for resolved in state.resolved_findings:
        if resolved.file_line == file_line and resolved.root_cause == root_cause:
            return resolved
    return None


def find_open_by_identity(
    state: AuditState,
    *,
    file_line: str,
    root_cause: str,
) -> Finding | None:
    """Return the open finding matching (file_line, root_cause), or None.

    Carry-over lookup: a finding that was open in the prior run and is
    still present in the current run keeps its ID. The caller updates
    the required-fix text from the current audit but never reissues
    the ID.
    """
    for open_finding in state.open_findings:
        if (
            open_finding.file_line == file_line
            and open_finding.root_cause == root_cause
        ):
            return open_finding
    return None


def reopen_finding(
    state: AuditState,
    resolved: ResolvedFinding,
    *,
    required_fix: str,
    concern: str | None = None,
) -> Finding:
    """Move ``resolved`` from resolved back to open, preserving its ID.

    Regression invariant: a root cause returning at the same file:line
    reopens the original finding by moving its row from Resolved to
    Open and clearing ``resolved_at``. Never create a new ID for a
    regression. ``next_finding_id`` is not advanced.

    ``required_fix`` is supplied by the caller because the suggested
    remediation is regenerated from the current audit per run rather
    than carried across resolution. ``concern`` is an optional override
    so callers (e.g. :func:`state_transition`) can refresh the concern
    label from the current run — symmetric with the carry-forward path
    that refreshes ``concern`` from the incoming finding. Omitting it
    keeps the prior resolved row's label.
    """
    reopened = Finding(
        id=resolved.id,
        file_line=resolved.file_line,
        concern=resolved.concern if concern is None else concern,
        root_cause=resolved.root_cause,
        required_fix=required_fix,
        first_seen=resolved.first_seen,
    )
    state.resolved_findings.remove(resolved)
    state.open_findings.append(reopened)
    return reopened


def resolve_finding(
    state: AuditState,
    finding: Finding,
    *,
    resolved_at: str,
) -> ResolvedFinding:
    """Move ``finding`` from open to resolved, preserving its ID.

    Symmetric counterpart to :func:`reopen_finding`. Records
    ``resolved_at`` (the SHA of the run that flipped the finding) so
    a later regression can be distinguished from a fresh occurrence.
    ``next_finding_id`` is not advanced: resolution is not allocation.
    """
    resolved = ResolvedFinding(
        id=finding.id,
        file_line=finding.file_line,
        concern=finding.concern,
        root_cause=finding.root_cause,
        first_seen=finding.first_seen,
        resolved_at=resolved_at,
    )
    state.open_findings.remove(finding)
    state.resolved_findings.append(resolved)
    return resolved


def _escape_cell(text: str) -> str:
    """Encode ``|`` and ``\\n`` in ``text`` for safe markdown-table storage.

    Forward order: backslash first (so subsequent escape sequences
    don't get re-escaped), then pipe, then newline. The reverse
    operation :func:`_unescape_cell` walks the text char-by-char to
    avoid the ambiguity inherent in naive substitution.
    """
    return (
        text.replace("\\", CELL_ESCAPE_BACKSLASH)
        .replace("|", CELL_ESCAPE_PIPE)
        .replace("\n", CELL_ESCAPE_NEWLINE)
    )


def _unescape_cell(text: str) -> str:
    """Decode a cell value previously encoded by :func:`_escape_cell`.

    Walks ``text`` char-by-char so a literal backslash that precedes
    an escape character is not accidentally re-interpreted as an
    escape sequence by string-replace ordering.
    """
    out: list[str] = []
    cursor = 0
    length = len(text)
    while cursor < length:
        char = text[cursor]
        if char == "\\" and cursor + 1 < length:
            nxt = text[cursor + 1]
            if nxt == "\\":
                out.append("\\")
                cursor += 2
                continue
            if nxt == "|":
                out.append("|")
                cursor += 2
                continue
            if nxt == "n":
                out.append("\n")
                cursor += 2
                continue
        out.append(char)
        cursor += 1
    return "".join(out)


def _split_frontmatter(text: str) -> tuple[str, str]:
    """Split ``text`` into (frontmatter, body) at the YAML-ish delimiters."""
    lines = text.splitlines()
    if not lines or lines[0] != STATE_FRONTMATTER_DELIMITER:
        raise ValueError("state file missing leading frontmatter delimiter")
    try:
        end_index = lines.index(STATE_FRONTMATTER_DELIMITER, 1)
    except ValueError as exc:
        raise ValueError("state file missing trailing frontmatter delimiter") from exc
    frontmatter = "\n".join(lines[1:end_index])
    body = "\n".join(lines[end_index + 1 :])
    return frontmatter, body


def _parse_frontmatter(text: str) -> dict[str, str]:
    """Parse ``key: value`` lines into a dict, stripping whitespace."""
    fields: dict[str, str] = {}
    for line in text.splitlines():
        match = _FRONTMATTER_FIELD_PATTERN.match(line)
        if match is None:
            continue
        fields[match.group(1)] = match.group(2).strip()
    return fields


def _parse_open_table(body: str) -> list[Finding]:
    """Parse rows from the ``## Open findings`` section of ``body``."""
    rows = _extract_table_rows(body, STATE_OPEN_HEADING)
    return [
        Finding(
            id=row[0],
            file_line=row[1],
            concern=_unescape_cell(row[2]),
            root_cause=_unescape_cell(row[3]),
            required_fix=_unescape_cell(row[4]),
            first_seen=row[5],
        )
        for row in rows
    ]


def _parse_resolved_table(body: str) -> list[ResolvedFinding]:
    """Parse rows from the ``## Resolved findings`` section of ``body``."""
    rows = _extract_table_rows(body, STATE_RESOLVED_HEADING)
    return [
        ResolvedFinding(
            id=row[0],
            file_line=row[1],
            concern=_unescape_cell(row[2]),
            root_cause=_unescape_cell(row[3]),
            first_seen=row[4],
            resolved_at=row[5],
        )
        for row in rows
    ]


def _extract_table_rows(body: str, heading: str) -> list[list[str]]:
    """Return the data rows under ``heading`` (header + separator stripped).

    Returns an empty list when the heading is absent or when the
    section under it contains only the header and separator rows
    (first-run with no findings). Stops collecting rows at the next
    ``##``-level heading or at end-of-text.
    """
    lines = body.splitlines()
    try:
        start = lines.index(heading)
    except ValueError:
        return []
    rows: list[list[str]] = []
    cursor = start + 1
    seen_table_lines = 0
    while cursor < len(lines):
        line = lines[cursor]
        if line.startswith("## "):
            break
        if line.startswith("|"):
            seen_table_lines += 1
            if seen_table_lines > 2:
                cells = [
                    cell.strip()
                    for cell in _UNESCAPED_PIPE_PATTERN.split(line.strip("|"))
                ]
                rows.append(cells)
        cursor += 1
    return rows


def _serialize_state(state: AuditState) -> str:
    """Render an :class:`AuditState` as the on-disk state-file text.

    ``file_line`` and ``first_seen`` / ``resolved_at`` are written
    without cell escaping. ``file_line`` is constrained to
    ``<repo-relative-path>:<line>`` (no pipe, no newline in any
    sensibly-named path); ``first_seen`` / ``resolved_at`` are git
    SHAs (lowercase hex). Both columns also avoid the backslash that
    drives the escape encoding, so unescaped round-trip is lossless
    for every input the orchestrator emits. ``concern``,
    ``root_cause``, and ``required_fix`` carry free-form prose from
    the dispatched audit skills and so go through the escape /
    unescape path on both directions.
    """
    lines: list[str] = [STATE_FRONTMATTER_DELIMITER]
    lines.extend(
        [
            f"branch: {state.branch}",
            f"schema_version: {state.schema_version}",
            f"first_run_sha: {state.first_run_sha}",
            f"first_run_at: {state.first_run_at}",
            f"last_run_sha: {state.last_run_sha}",
            f"last_run_at: {state.last_run_at}",
            f"last_verdict: {state.last_verdict}",
            f"run_count: {state.run_count}",
            f"next_finding_id: {state.next_finding_id}",
        ]
    )
    lines.append(STATE_FRONTMATTER_DELIMITER)
    lines.append("")
    lines.append(STATE_TITLE_TEMPLATE.format(branch=state.branch))
    lines.append("")
    lines.append(STATE_OPEN_HEADING)
    lines.append("")
    lines.append(STATE_OPEN_TABLE_HEADER)
    lines.append(STATE_OPEN_TABLE_SEPARATOR)
    for finding in state.open_findings:
        lines.append(
            f"| {finding.id} | {finding.file_line} "
            f"| {_escape_cell(finding.concern)} "
            f"| {_escape_cell(finding.root_cause)} "
            f"| {_escape_cell(finding.required_fix)} "
            f"| {finding.first_seen} |"
        )
    lines.append("")
    lines.append(STATE_RESOLVED_HEADING)
    lines.append("")
    lines.append(STATE_RESOLVED_TABLE_HEADER)
    lines.append(STATE_RESOLVED_TABLE_SEPARATOR)
    for resolved in state.resolved_findings:
        lines.append(
            f"| {resolved.id} | {resolved.file_line} "
            f"| {_escape_cell(resolved.concern)} "
            f"| {_escape_cell(resolved.root_cause)} | {resolved.first_seen} "
            f"| {resolved.resolved_at} |"
        )
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# state-transition: the one composed operation the CLI exposes beyond the
# individual helpers. Given a state file and the current run's findings,
# carry forward identities, reopen regressions, and resolve absences.
# ---------------------------------------------------------------------------


def state_transition(
    *,
    state_path: pathlib.Path,
    branch: str,
    current_sha: str,
    now: str,
    verdict: str,
    new_findings: list[dict[str, str]],
) -> dict[str, list[dict[str, Any]]]:
    """Apply ``new_findings`` to the state at ``state_path`` and persist it.

    Identity is the (file_line, root_cause) pair. For each finding:

    - If the identity matches a prior resolved finding, reopen it
      (preserves the original ID, clears ``resolved_at``).
    - If the identity matches a currently open finding, carry the ID
      forward and refresh ``required_fix`` from the current run.
    - Otherwise allocate a fresh ID via :func:`assign_finding_id`.

    Open findings whose identity does not appear in ``new_findings``
    are resolved with ``resolved_at = current_sha``. Returns the
    classification dict the caller renders or relays:

    ``{"open": [...], "resolved": [...], "reopened": [...]}``

    Each entry carries the full finding fields. The new state file is
    written atomically via :func:`save_state` before the dict is
    returned, so a caller crash after this returns leaves the state
    coherent.
    """
    state = load_state(state_path)
    if state is None:
        state = AuditState(
            branch=branch,
            first_run_sha=current_sha,
            first_run_at=now,
            last_run_sha=current_sha,
            last_run_at=now,
            last_verdict=verdict,
            run_count=1,
            next_finding_id=1,
        )
    else:
        state.last_run_sha = current_sha
        state.last_run_at = now
        state.last_verdict = verdict
        state.run_count += 1

    new_open: list[Finding] = []
    reopened: list[Finding] = []
    new_identities: set[tuple[str, str]] = set()
    for incoming in new_findings:
        identity = (incoming["file_line"], incoming["root_cause"])
        new_identities.add(identity)
        existing_open = find_open_by_identity(
            state, file_line=identity[0], root_cause=identity[1]
        )
        if existing_open is not None:
            # Carry forward: same ID and first_seen, refresh required_fix.
            refreshed = Finding(
                id=existing_open.id,
                file_line=existing_open.file_line,
                concern=incoming.get("concern", existing_open.concern),
                root_cause=existing_open.root_cause,
                required_fix=incoming["required_fix"],
                first_seen=existing_open.first_seen,
            )
            state.open_findings.remove(existing_open)
            state.open_findings.append(refreshed)
            new_open.append(refreshed)
            continue
        resolved_match = find_resolved_by_identity(
            state, file_line=identity[0], root_cause=identity[1]
        )
        if resolved_match is not None:
            reopened_finding = reopen_finding(
                state,
                resolved_match,
                required_fix=incoming["required_fix"],
                concern=incoming.get("concern", resolved_match.concern),
            )
            reopened.append(reopened_finding)
            new_open.append(reopened_finding)
            continue
        finding = Finding(
            id=assign_finding_id(state),
            file_line=identity[0],
            concern=incoming.get("concern", ""),
            root_cause=identity[1],
            required_fix=incoming["required_fix"],
            first_seen=current_sha,
        )
        state.open_findings.append(finding)
        new_open.append(finding)

    # Resolve open findings whose identity is not in the new run.
    just_resolved: list[ResolvedFinding] = []
    for open_finding in list(state.open_findings):
        identity = (open_finding.file_line, open_finding.root_cause)
        if identity not in new_identities:
            just_resolved.append(
                resolve_finding(state, open_finding, resolved_at=current_sha)
            )

    save_state(state, state_path)

    return {
        "open": [asdict(f) for f in new_open],
        "resolved": [asdict(r) for r in just_resolved],
        "reopened": [asdict(f) for f in reopened],
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _add_repo_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--repo",
        default=".",
        type=pathlib.Path,
        help="Git repository root (default: current directory).",
    )


def _add_pattern_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--pattern",
        action="append",
        default=[],
        help="Pathspec pattern to filter the result. May be repeated.",
    )


def _cmd_base_ref(args: argparse.Namespace) -> int:
    sys.stdout.write(detect_base_ref(args.repo) + "\n")
    return 0


def _cmd_current_branch(args: argparse.Namespace) -> int:
    try:
        branch = detect_current_branch(args.repo)
    except DetachedHeadError as exc:
        sys.stderr.write(f"{exc}\n")
        return 2
    sys.stdout.write(branch + "\n")
    return 0


def _cmd_branch_slug(args: argparse.Namespace) -> int:
    sys.stdout.write(branch_slug(args.branch, args.state_dir) + "\n")
    return 0


def _cmd_scope_hash(args: argparse.Namespace) -> int:
    paths = [line for line in sys.stdin.read().splitlines() if line]
    pairs: list[tuple[str, str]] = []
    for path in paths:
        absolute = args.repo / path
        content = absolute.read_text(encoding="utf-8") if absolute.is_file() else ""
        pairs.append((path, content))
    sys.stdout.write(compute_scope_hash(pairs) + "\n")
    return 0


def _cmd_branch_scope(args: argparse.Namespace) -> int:
    files = branch_scope(args.base, patterns=args.pattern or None, repo=args.repo)
    sys.stdout.write("\n".join(files) + ("\n" if files else ""))
    return 0


def _cmd_modified_since(args: argparse.Namespace) -> int:
    files = modified_since(args.since, patterns=args.pattern or None, repo=args.repo)
    sys.stdout.write("\n".join(files) + ("\n" if files else ""))
    return 0


def _cmd_sha_reachable(args: argparse.Namespace) -> int:
    return 0 if is_sha_reachable(args.sha, repo=args.repo) else 1


def _cmd_acquire_lock(args: argparse.Namespace) -> int:
    # Unlike :class:`RunLock`, the CLI runs in its own process and exits
    # before the lock is released — there is no injectable clock to thread
    # through, and mtime defaults to the kernel's wall-clock time at write.
    # Production reads (the next ``acquire-lock`` invocation) compute age
    # against ``time.time()`` in the same wall-clock frame, so the omission
    # of an explicit ``os.utime`` is intentional. Tests that need a faked
    # clock exercise :class:`RunLock` directly rather than the CLI.
    try:
        fd = _acquire_lock_once(
            args.path, max_age_seconds=args.max_age_seconds, now=time.time
        )
    except RunLockError as exc:
        sys.stderr.write(f"{exc}\n")
        return 1
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(str(time.time()))
    return 0


def _cmd_release_lock(args: argparse.Namespace) -> int:
    try:
        args.path.unlink()
    except FileNotFoundError:
        pass
    return 0


REQUIRED_FINDING_KEYS = ("file_line", "root_cause", "required_fix")


def _cmd_state_transition(args: argparse.Namespace) -> int:
    payload = json.loads(sys.stdin.read())
    findings = payload.get("findings", [])
    for index, finding in enumerate(findings):
        missing = [key for key in REQUIRED_FINDING_KEYS if key not in finding]
        if missing:
            sys.stderr.write(
                f"finding[{index}] missing required keys: {sorted(missing)}\n"
            )
            return 3
    try:
        result = state_transition(
            state_path=args.state_file,
            branch=args.branch,
            current_sha=args.current_sha,
            now=args.now,
            verdict=args.verdict,
            new_findings=findings,
        )
    except StateFileCorruptError as exc:
        sys.stderr.write(f"corrupt state file: {exc}\n")
        return 2
    json.dump(result, sys.stdout)
    sys.stdout.write("\n")
    return 0


def _collect_open_findings(verdict_dict: dict[str, object]) -> list[dict[str, object]]:
    """Walk a verdict's rows and children recursively and return every open finding.

    Open findings are those carried in row arrays of the wrapper and any
    child verdict. The verdict-level ``resolved`` and ``reopened`` arrays
    on a prior verdict are NOT open findings — they are state markers
    used by the diff caller, not currently-failing concerns.

    Identity-collision note: callers that index the result by
    ``_finding_identity`` (file, line, rule, message) into a dict will
    silently keep only the last finding of any colliding tuple. Distinct
    findings sharing the same identity tuple in one verdict indicates a
    producer bug, not a consumer concern.
    """
    collected: list[dict[str, object]] = []
    for row in verdict_dict.get("rows", []) or []:
        if isinstance(row, dict):
            for finding in row.get("findings", []) or []:
                if isinstance(finding, dict):
                    collected.append(finding)
    for child in verdict_dict.get("children", []) or []:
        if isinstance(child, dict):
            collected.extend(_collect_open_findings(child))
    return collected


def _finding_identity(
    finding: dict[str, object],
) -> tuple[str, int | None, str, str]:
    """Return the content-identity tuple for a finding.

    Identity is ``(file, line, rule, message)`` — the producer-stable
    description of *what* the finding flags. ``id`` and ``severity`` are
    deliberately excluded: ``id`` is producer-assigned and varies across
    runs; ``severity`` may legitimately upgrade or downgrade across runs
    without being a different finding. Two findings with the same
    identity tuple are the same concern across runs.
    """
    raw_line = finding.get("line")
    line = (
        raw_line
        if isinstance(raw_line, int) and not isinstance(raw_line, bool)
        else None
    )
    return (
        str(finding.get("file", "")),
        line,
        str(finding.get("rule", "")),
        str(finding.get("message", "")),
    )


def compute_verdict_diff(
    *,
    prior: dict[str, object] | None,
    current: dict[str, object],
) -> dict[str, object]:
    """Return the current verdict enriched with ``resolved`` and ``reopened``.

    The diff carries forward state across runs by content-identity:

    - ``resolved`` = (prior.resolved ∪ {findings present in prior.open
      and absent from current.open}) − {findings present in current.open}.
      The set grows monotonically across runs except for findings that
      are reopened.
    - ``reopened`` = current.open ∩ prior.resolved. A finding that was
      previously resolved and is now open again surfaces in this set.

    When ``prior`` is ``None`` (first run on a new PR), both arrays are
    empty and the current verdict is returned with empty ``resolved`` and
    ``reopened`` lists.

    The function does not mutate ``current``; it returns a new dict that
    is the same shape as ``current`` with the two arrays populated.
    """
    enriched = dict(current)
    enriched["resolved"] = []
    enriched["reopened"] = []
    if prior is None:
        return enriched
    prior_open = _collect_open_findings(prior)
    current_open = _collect_open_findings(current)
    prior_resolved_raw = prior.get("resolved", []) or []
    prior_resolved: list[dict[str, object]] = [
        f for f in prior_resolved_raw if isinstance(f, dict)
    ]
    prior_open_by_identity = {_finding_identity(f): f for f in prior_open}
    current_open_by_identity = {_finding_identity(f): f for f in current_open}
    prior_resolved_by_identity = {_finding_identity(f): f for f in prior_resolved}
    newly_resolved_keys = sorted(
        set(prior_open_by_identity) - set(current_open_by_identity),
        key=_identity_sort_key,
    )
    newly_resolved = [prior_open_by_identity[k] for k in newly_resolved_keys]
    carried_resolved_keys = sorted(
        set(prior_resolved_by_identity) - set(current_open_by_identity),
        key=_identity_sort_key,
    )
    carried_resolved = [prior_resolved_by_identity[k] for k in carried_resolved_keys]
    enriched["resolved"] = carried_resolved + newly_resolved
    reopened_keys = sorted(
        set(current_open_by_identity) & set(prior_resolved_by_identity),
        key=_identity_sort_key,
    )
    enriched["reopened"] = [current_open_by_identity[k] for k in reopened_keys]
    return enriched


def _identity_sort_key(
    identity: tuple[str, int | None, str, str],
) -> tuple[str, int, int, str, str]:
    """Return a None-safe sort key for finding identity tuples.

    Python 3 cannot compare ``None`` to ``int`` directly, so the line
    component is split into a presence bit (0 for None, 1 for int) and a
    numeric value (0 when None). Findings with no line sort before
    findings with a line within the same file, then by numeric line.
    """
    file_, line, rule, message = identity
    has_line = 0 if line is None else 1
    line_value = 0 if line is None else line
    return (file_, has_line, line_value, rule, message)


def _cmd_verdict_diff(args: argparse.Namespace) -> int:
    """CLI: enrich a current verdict with resolved/reopened computed from a prior.

    Reads the current verdict on stdin (JSON), reads the optional prior
    verdict from ``--prior`` (a path; absent means first-run), writes
    the enriched verdict JSON to stdout. Exit codes: 0 on success,
    1 on JSON parse failure, 2 on missing required structure.
    """
    try:
        current = json.loads(sys.stdin.read())
    except json.JSONDecodeError as exc:
        sys.stderr.write(f"verdict-diff: invalid current JSON on stdin: {exc}\n")
        return 1
    if not isinstance(current, dict):
        sys.stderr.write("verdict-diff: current verdict must be a JSON object\n")
        return 2
    prior: dict[str, object] | None = None
    if args.prior is not None:
        try:
            prior_text = args.prior.read_text(encoding="utf-8")
        except OSError as exc:
            sys.stderr.write(f"verdict-diff: cannot read prior verdict: {exc}\n")
            return 1
        try:
            prior_loaded = json.loads(prior_text)
        except json.JSONDecodeError as exc:
            sys.stderr.write(f"verdict-diff: invalid prior JSON: {exc}\n")
            return 1
        if not isinstance(prior_loaded, dict):
            sys.stderr.write("verdict-diff: prior verdict must be a JSON object\n")
            return 2
        prior = prior_loaded
    enriched = compute_verdict_diff(prior=prior, current=current)
    json.dump(enriched, sys.stdout)
    sys.stdout.write("\n")
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Return the argparse parser exposing every CLI subcommand."""
    parser = argparse.ArgumentParser(
        prog="audit_orchestrator",
        description=(
            "Git, scope-hashing, locking, and state-transition helpers for the "
            "/audit skill."
        ),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    base_ref = subparsers.add_parser(
        "base-ref", help="Print the bare base-branch name (default 'main')."
    )
    _add_repo_arg(base_ref)
    base_ref.set_defaults(func=_cmd_base_ref)

    current_branch = subparsers.add_parser(
        "current-branch", help="Print the current branch (exit 2 on detached HEAD)."
    )
    _add_repo_arg(current_branch)
    current_branch.set_defaults(func=_cmd_current_branch)

    branch_slug_cmd = subparsers.add_parser(
        "branch-slug",
        help="Derive the on-disk state-file slug for the given branch.",
    )
    branch_slug_cmd.add_argument("--branch", required=True)
    branch_slug_cmd.add_argument("--state-dir", required=True, type=pathlib.Path)
    branch_slug_cmd.set_defaults(func=_cmd_branch_slug)

    scope_hash = subparsers.add_parser(
        "scope-hash",
        help=(
            "Read newline-separated file paths from stdin, hash them with "
            "their on-disk content, print the 12-char scope hash."
        ),
    )
    _add_repo_arg(scope_hash)
    scope_hash.set_defaults(func=_cmd_scope_hash)

    branch_scope_cmd = subparsers.add_parser(
        "branch-scope",
        help="Print files changed on this branch vs origin/<base> (three-dot).",
    )
    branch_scope_cmd.add_argument("--base", required=True)
    _add_repo_arg(branch_scope_cmd)
    _add_pattern_arg(branch_scope_cmd)
    branch_scope_cmd.set_defaults(func=_cmd_branch_scope)

    modified_since_cmd = subparsers.add_parser(
        "modified-since",
        help="Print files changed between --since SHA and HEAD (two-dot).",
    )
    modified_since_cmd.add_argument("--since", required=True)
    _add_repo_arg(modified_since_cmd)
    _add_pattern_arg(modified_since_cmd)
    modified_since_cmd.set_defaults(func=_cmd_modified_since)

    sha_reachable_cmd = subparsers.add_parser(
        "sha-reachable",
        help="Exit 0 if SHA resolves to a commit object; 1 otherwise.",
    )
    sha_reachable_cmd.add_argument("--sha", required=True)
    _add_repo_arg(sha_reachable_cmd)
    sha_reachable_cmd.set_defaults(func=_cmd_sha_reachable)

    acquire_lock = subparsers.add_parser(
        "acquire-lock",
        help="Acquire a TTL-bounded file lock; exit 1 if held within TTL.",
    )
    acquire_lock.add_argument("--path", required=True, type=pathlib.Path)
    acquire_lock.add_argument(
        "--max-age-seconds",
        type=float,
        default=DEFAULT_LOCK_TTL_SECONDS,
    )
    acquire_lock.set_defaults(func=_cmd_acquire_lock)

    release_lock = subparsers.add_parser(
        "release-lock", help="Release a previously acquired lock (idempotent)."
    )
    release_lock.add_argument("--path", required=True, type=pathlib.Path)
    release_lock.set_defaults(func=_cmd_release_lock)

    state_transition_cmd = subparsers.add_parser(
        "state-transition",
        help=(
            "Apply a JSON findings list from stdin to the branch state file: "
            "carry forward IDs, reopen regressions, resolve absences. Emit "
            "the classification {open, resolved, reopened} as JSON on stdout."
        ),
    )
    state_transition_cmd.add_argument("--state-file", required=True, type=pathlib.Path)
    state_transition_cmd.add_argument("--branch", required=True)
    state_transition_cmd.add_argument("--current-sha", required=True)
    state_transition_cmd.add_argument("--now", required=True)
    state_transition_cmd.add_argument("--verdict", required=True)
    state_transition_cmd.set_defaults(func=_cmd_state_transition)

    verdict_diff_cmd = subparsers.add_parser(
        "verdict-diff",
        help=(
            "Read a current verdict on stdin and an optional prior verdict "
            "from --prior; print the current verdict enriched with "
            "resolved/reopened arrays computed by content identity."
        ),
    )
    verdict_diff_cmd.add_argument(
        "--prior",
        type=pathlib.Path,
        default=None,
        help="Path to prior verdict JSON. Omit for first-run (no prior).",
    )
    verdict_diff_cmd.set_defaults(func=_cmd_verdict_diff)

    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entry point. Returns the process exit code."""
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
