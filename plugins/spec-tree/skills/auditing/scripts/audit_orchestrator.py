"""Audit-orchestration helpers shipped with the spec-tree plugin.

Hosts the deterministic computations that the `/auditing` skill and the
`auditor` agent cannot reliably execute in-process from prose: scope
hashing, branch slug derivation, base-ref detection, git plumbing, lock
acquisition, and the content-based identity used for regression detection.

The module is loaded by tests via ``importlib.util`` from its absolute
path (per the marketplace skill-co-located Python convention). It ships
outside the ``outcomeeng/`` package so downstream consumers receive it
transitively when they install the ``spec-tree`` plugin.
"""

from __future__ import annotations

import hashlib
import os
import pathlib
import re
import subprocess
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import StrEnum

NULL_BYTE = b"\x00"
SCOPE_HASH_LENGTH = 12
DEFAULT_BASE_REF = "main"
DEFAULT_LOCK_TTL_SECONDS = 600
LOCK_FILE_MODE = 0o644
BRANCH_SLUG_COLLISION_SUFFIX_LENGTH = 8
ORIGIN_HEAD_REF_PREFIX = "refs/remotes/origin/"
ORIGIN_REF_PREFIX = "origin/"
BRANCH_SCOPE_RANGE_TEMPLATE = "{origin_ref}...HEAD"
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


class DetachedHeadError(RuntimeError):
    """Raised when current-branch detection runs against a detached HEAD.

    State-file naming requires a stable branch label; the orchestrator
    refuses to create state under the placeholder ``HEAD`` reference.
    """


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


class Verdict(StrEnum):
    """The two overall outcomes an audit run can emit.

    Marketplace convention (per the ``/auditing`` skill's
    ``<verdict_format>`` block): ``APPROVED`` is the overall verdict
    when every concern row is PASS or N/A; ``REJECTED`` is the overall
    verdict when at least one row is REJECT. Per-row status uses the
    different word ``REJECT`` (singular) to distinguish row outcomes
    from the run-level verdict — this enum covers only the run-level
    spelling stored in :attr:`AuditState.last_verdict`.

    StrEnum members compare equal to their string values, so callers
    that already work with the literal strings ``"APPROVED"`` /
    ``"REJECTED"`` (existing state files, audit prose) keep working
    without code changes.
    """

    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


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


def expand_diff_range(
    range_spec: str,
    *,
    patterns: list[str] | None = None,
    repo: pathlib.Path,
) -> list[str]:
    """Return the file paths changed in the given git diff range.

    Equivalent to ``git diff --name-only <range_spec> [-- <pat1> <pat2> ...]``
    run inside ``repo``. The ``patterns`` argument is a list of pathspec
    patterns (e.g. ``["*.ts", "*.tsx"]``); when omitted or empty, no
    pathspec filter is applied and every file changed in the range is
    returned. The result preserves the order produced by git and is
    de-duplicated implicitly by git (each path appears at most once).

    Empty output means the range produced no matching paths — not an
    error. The ``/auditing`` skill's Phase 0 distinguishes this from a
    git failure by treating it as the no-scope-detected case (halt with
    a deliberate message) rather than re-raising.
    """
    cmd = ["git", "diff", "--name-only", range_spec]
    if patterns:
        cmd.append("--")
        cmd.extend(patterns)
    result = subprocess.run(  # noqa: S603 — fixed argv, no shell, range_spec and patterns caller-controlled
        cmd,
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )
    return [line for line in result.stdout.splitlines() if line]


def branch_scope(
    base_ref: str,
    *,
    patterns: list[str] | None = None,
    repo: pathlib.Path,
) -> list[str]:
    """Return the files this branch changed relative to ``origin/<base_ref>``.

    Composes the diff range ``origin/<base_ref>...HEAD`` (three-dot
    semantics: ``git diff`` between the merge-base of HEAD and
    ``origin/<base_ref>`` and HEAD itself) and delegates to
    :func:`expand_diff_range`. The three-dot form is deliberate: commits
    that landed on the base branch after this feature branch was cut are
    not part of the feature scope. Using the two-dot form would include
    those files as deletions in the diff, polluting the scope.

    Closes the interim agent's Phase 0 step 6 inline shell line, which
    used two-dot syntax. The three-dot form is the safer default for
    "what files does this branch propose". The ``origin/`` prefix is
    composed here rather than required from the caller so the
    orchestrator stays language-agnostic — callers pass bare base names
    like ``main`` or ``develop``.

    ``patterns`` filters the result by pathspec when provided; empty or
    ``None`` returns every file in the range.
    """
    range_spec = BRANCH_SCOPE_RANGE_TEMPLATE.format(
        origin_ref=f"{ORIGIN_REF_PREFIX}{base_ref}"
    )
    return expand_diff_range(range_spec, patterns=patterns, repo=repo)


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

    Closes the interim agent's Phase R step 5 inline shell line
    ``git diff --name-only <last_run_sha>..HEAD -- <patterns>``. The
    caller is responsible for confirming ``prior_sha`` is reachable
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

    Detects the interim agent's "Last_run_sha unreachable" failure mode
    where a state file's SHA was force-pushed away or never fetched
    into the local clone. The caller's re-run protocol falls back to a
    full branch-scope scan when this returns ``False``.

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


def detect_base_ref(repo: pathlib.Path) -> str:
    """Return the bare base-branch name configured by ``origin/HEAD``.

    Reads ``refs/remotes/origin/HEAD`` and strips the
    ``refs/remotes/origin/`` prefix so the result is a bare branch name
    (e.g. ``main``). The interim agent's Phase 0 failure mode showed that
    composing ``origin/<base>..HEAD`` with an unstripped ref produces
    ``origin/refs/remotes/origin/main..HEAD`` and halts git before any
    audit runs.

    When the symbolic ref is absent (no remote configured, fresh
    bootstrap, solo developer repo), returns ``DEFAULT_BASE_REF`` so
    callers can still compose diff ranges without halting.
    """
    result = subprocess.run(
        ["git", "symbolic-ref", "refs/remotes/origin/HEAD"],  # noqa: S607
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return DEFAULT_BASE_REF
    line = result.stdout.strip()
    if line.startswith(ORIGIN_HEAD_REF_PREFIX):
        return line[len(ORIGIN_HEAD_REF_PREFIX) :]
    return DEFAULT_BASE_REF


def detect_current_branch(repo: pathlib.Path) -> str:
    """Return the current branch name; raise ``DetachedHeadError`` on detached HEAD.

    The orchestrator names state files by the current branch; running on
    detached HEAD would produce a file named ``HEAD.md`` that collides
    across every detached-checkout invocation. Raising forces the caller
    to switch to a named branch before audit state is created.
    """
    result = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],  # noqa: S607
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )
    branch = result.stdout.strip()
    if branch == "HEAD":
        raise DetachedHeadError(f"detached HEAD at {repo}")
    return branch


def _read_frontmatter_branch(path: pathlib.Path) -> str | None:
    """Extract the ``branch:`` value from a markdown file's YAML frontmatter.

    Returns ``None`` if the file is unreadable, has no frontmatter, or has
    no ``branch:`` key. Used by ``branch_slug`` to detect whether an
    existing state file at the base-slug path belongs to a different
    branch (collision case) or the same branch (reuse case).
    """
    try:
        content = path.read_text(encoding="utf-8")
    except OSError:
        return None
    if not content.startswith("---"):
        return None
    in_frontmatter = False
    for line in content.splitlines():
        if line.strip() == "---":
            if in_frontmatter:
                return None
            in_frontmatter = True
            continue
        if in_frontmatter and line.startswith("branch:"):
            return line.partition(":")[2].strip()
    return None


def branch_slug(branch_name: str, state_dir: pathlib.Path) -> str:
    """Derive the on-disk state-file slug for ``branch_name``.

    Replaces every ``/`` in the branch name with ``__`` to produce a
    flat-filesystem-safe slug. If an existing state file at
    ``state_dir/<base-slug>.md`` records a *different* branch in its
    frontmatter, appends ``--<sha8>`` where ``sha8`` is the first eight
    hex characters of SHA-256(branch_name). The suffix is deterministic
    so re-runs land on the same state file across invocations.

    Same-branch state files (frontmatter ``branch:`` matches
    ``branch_name``) reuse the base slug — no suffix.
    """
    base_slug = branch_name.replace("/", "__")
    existing = state_dir / f"{base_slug}.md"
    if existing.is_file():
        existing_branch = _read_frontmatter_branch(existing)
        if existing_branch is not None and existing_branch != branch_name:
            digest = hashlib.sha256(branch_name.encode("utf-8")).hexdigest()
            suffix = digest[:BRANCH_SLUG_COLLISION_SUFFIX_LENGTH]
            return f"{base_slug}--{suffix}"
    return base_slug


class RunLock:
    """File-based exclusive lock with a TTL-based stale-lock policy.

    Used by the ``auditor`` agent to prevent concurrent runs on the same
    branch state file. Acquiring writes a lock file at ``path`` whose
    mtime records the acquisition time (from the injected clock). On
    context exit (normal or exception), the lock file is removed.

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
        self._path.parent.mkdir(parents=True, exist_ok=True)
        while True:
            # Atomic acquisition: O_CREAT | O_EXCL fails if the file
            # already exists, which lets two concurrent acquirers
            # distinguish "I got the lock" from "someone else holds it"
            # without a TOCTOU window between an existence check and a
            # write. The prior exists-then-write sequence let both
            # racers see no lock and both proceed.
            try:
                fd = os.open(
                    self._path,
                    os.O_CREAT | os.O_EXCL | os.O_WRONLY,
                    LOCK_FILE_MODE,
                )
            except FileExistsError:
                age = self._now() - self._path.stat().st_mtime
                if age < self._max_age:
                    raise RunLockError(
                        f"lock held: {self._path} "
                        f"(age {age:.0f}s, ttl {self._max_age:.0f}s)"
                    ) from None
                # Stale (older than max_age): remove and retry the
                # atomic create. The unlink may itself race, which is
                # benign — whoever creates the file next holds the lock.
                try:
                    self._path.unlink()
                except FileNotFoundError:
                    pass
                continue
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
    lossless under the PRIORITY 1 escaping policy (plain text only;
    cell escaping for ``|`` and newlines is PRIORITY 2).
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

    Mirrors the interim agent's ``<state_file_format>`` block: nine
    frontmatter fields plus two tables. ``next_finding_id`` is an
    integer counter that strictly exceeds every ID ever assigned on
    this branch — open or resolved — so monotonic IDs survive across
    runs. The counter is what drives :func:`assign_finding_id`; the
    ID lists are read by callers that need to look up findings by
    identity but are not the source of truth for the next ID.

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

    - ``path`` absent → ``None`` (first run; Phase F).
    - ``path`` present and parseable → populated ``AuditState`` (Phase R).
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
    except (ValueError, KeyError) as exc:
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
    pre-create ``.spx/audits/<lang>/`` for first runs. The frontmatter
    field order matches the ``<state_file_format>`` block in the
    ``auditor`` agent prose; field order in the file is stable for
    diff readability, not load-bearing for parsing.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(_serialize_state(state), encoding="utf-8")
    os.replace(tmp, path)


def assign_finding_id(state: AuditState) -> str:
    """Return the next monotonic finding ID and increment the counter.

    The ID is formatted as ``f-NNN`` with zero-padding to at least
    three digits (per :data:`FINDING_ID_FORMAT`). The counter strictly
    exceeds every ID ever assigned on this branch — open or resolved —
    so a finding resolved in a prior run never sees its ID reissued to
    a new finding. State persists ``next_finding_id`` through
    :func:`save_state` so the invariant survives across runs.
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
    root_cause): the same defect at the same code location. The
    interim agent's Phase R step 4 walks resolved findings and reopens
    any whose root cause has returned at the same file:line. This
    helper is the lookup step of that protocol — absence (``None``)
    signals "no regression for this finding" so the caller allocates
    a fresh ID via :func:`assign_finding_id` instead.
    """
    for resolved in state.resolved_findings:
        if resolved.file_line == file_line and resolved.root_cause == root_cause:
            return resolved
    return None


def reopen_finding(
    state: AuditState,
    resolved: ResolvedFinding,
    *,
    required_fix: str,
) -> Finding:
    """Move ``resolved`` from resolved back to open, preserving its ID.

    The interim agent's invariant: "A regression — the same root cause
    returning at the same file:line — reopens the original finding by
    moving its row from Resolved to Open and clearing resolved_at.
    Never create a new ID for a regression." This helper enforces the
    invariant: the returned :class:`Finding` carries the same ``id``
    and ``first_seen`` as ``resolved``, ``next_finding_id`` is not
    advanced, and ``resolved_at`` is dropped (it lives only on
    resolved rows).

    ``required_fix`` is supplied by the caller because the suggested
    remediation is regenerated from the current audit per run rather
    than carried across resolution.
    """
    reopened = Finding(
        id=resolved.id,
        file_line=resolved.file_line,
        concern=resolved.concern,
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
    escape sequence by string-replace ordering. The forward direction
    introduces backslash escapes before pipe and newline escapes;
    the reverse must consume those backslash escapes in lockstep.
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
            concern=row[2],
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
            concern=row[2],
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
    # Skip the heading itself, then the header line and the separator line.
    # The first two table lines (header + separator) carry no data and are
    # already known structurally; advance past them before reading rows.
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
    """Render an :class:`AuditState` as the on-disk state-file text."""
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
            f"| {finding.id} | {finding.file_line} | {finding.concern} "
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
            f"| {resolved.id} | {resolved.file_line} | {resolved.concern} "
            f"| {_escape_cell(resolved.root_cause)} | {resolved.first_seen} "
            f"| {resolved.resolved_at} |"
        )
    lines.append("")
    return "\n".join(lines)
