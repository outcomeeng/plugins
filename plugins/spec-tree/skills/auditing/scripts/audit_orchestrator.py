"""Git and scope helpers shipped with the spec-tree plugin's auditing skill.

Hosts the deterministic computations the `/auditing` skill cannot reliably
execute in-process from prose: scope hashing, base-ref detection, and the
git plumbing that enumerates a branch's diff against its base.

The module ships outside the ``outcomeeng/`` package so downstream
consumers receive it transitively when they install the ``spec-tree``
plugin; tests load it via ``importlib.util`` from its absolute path (per
the marketplace skill-co-located Python convention).
"""

from __future__ import annotations

import hashlib
import pathlib
import subprocess

NULL_BYTE = b"\x00"
SCOPE_HASH_LENGTH = 12
DEFAULT_BASE_REF = "main"
ORIGIN_HEAD_REF_PREFIX = "refs/remotes/origin/"
ORIGIN_REF_PREFIX = "origin/"
BRANCH_SCOPE_RANGE_TEMPLATE = "{origin_ref}...HEAD"


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

    Raises ``subprocess.CalledProcessError`` when git itself fails — an
    invalid ``range_spec`` (typo, missing ref, unknown SHA), a corrupt
    repository, or a runtime that lacks ``git``. Callers that want a
    domain-specific error (e.g., the ``/auditing`` skill's "scope ref
    not resolvable" halt message) catch and translate; this helper
    propagates the raw subprocess error so the caller decides the
    recovery policy.
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

    The ``origin/`` prefix is composed here rather than required from the
    caller so the orchestrator stays language-agnostic — callers pass
    bare base names like ``main`` or ``develop``.

    ``patterns`` filters the result by pathspec when provided; empty or
    ``None`` returns every file in the range.
    """
    range_spec = BRANCH_SCOPE_RANGE_TEMPLATE.format(
        origin_ref=f"{ORIGIN_REF_PREFIX}{base_ref}"
    )
    return expand_diff_range(range_spec, patterns=patterns, repo=repo)


def detect_base_ref(repo: pathlib.Path) -> str:
    """Return the bare base-branch name configured by ``origin/HEAD``.

    Reads ``refs/remotes/origin/HEAD`` and strips the
    ``refs/remotes/origin/`` prefix so the result is a bare branch name
    (e.g. ``main``). Composing ``origin/<base>..HEAD`` with an unstripped
    ref would produce ``origin/refs/remotes/origin/main..HEAD`` and halt
    git before any audit runs.

    When the symbolic ref is absent (no remote configured, fresh
    bootstrap, solo developer repo), returns ``DEFAULT_BASE_REF`` so
    callers can still compose diff ranges without halting.
    """
    result = subprocess.run(
        ["git", "symbolic-ref", "refs/remotes/origin/HEAD"],  # noqa: S607 — git resolved via PATH by design; portable helper, no fixed install path
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
