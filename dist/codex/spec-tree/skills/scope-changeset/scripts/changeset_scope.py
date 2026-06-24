"""Canonical git-derived changeset primitives shipped with the spec-tree plugin.

Single home for the deterministic git derivation shared by the audit,
review-changes, and thread-store skills: branch identity, the on-disk
addressing slug, base-ref resolution, the remote-tracking ref form, and
merge-base diff scope. Consumers import these symbols (directly or through
``thread-store/scripts/branch_slug.py``'s re-export); none re-implements them.

Every changeset diff range over a git-derived base is composed against the
remote-tracking ref ``origin/<base>`` through :func:`remote_tracking_ref`, so a
stale local branch ref in a multi-worktree checkout cannot widen the scope.

Stdlib-only, ``python3`` — no third-party packages, no ``uv``, no
``outcomeeng_*`` imports, per the Plugin Portability Constraints in ``AGENTS.md``.
"""

from __future__ import annotations

import hashlib
import pathlib
import subprocess

DEFAULT_BASE_REF = "main"
BRANCH_SLUG_COLLISION_SUFFIX_LENGTH = 8
BRANCH_SLUG_MAX_LENGTH = 64
BRANCH_SLUG_DOT_SUBSTITUTE = "__dot__"
BRANCH_SLUG_DOTDOT_SUBSTITUTE = "__dotdot__"
ORIGIN_HEAD_REF_PREFIX = "refs/remotes/origin/"
ORIGIN_REF_PREFIX = "origin/"
BRANCH_SCOPE_RANGE_TEMPLATE = "{origin_ref}...HEAD"
FRONTMATTER_DELIMITER = "---"
COMMIT_PEEL_SUFFIX = "^{commit}"


class BaseRefNotConfiguredError(RuntimeError):
    """Raised by ``detect_base_ref(strict=True)`` when origin/HEAD is absent.

    The default ``detect_base_ref(strict=False)`` falls back to
    ``DEFAULT_BASE_REF`` because the audit skill tolerates a missing
    remote (single-developer repos, fresh bootstraps). The strict
    variant exists for the review-changes skill, which refuses to
    pick a fallback because the operator needs a definitive answer
    about which ref the diff was computed against.
    """


class DetachedHeadError(RuntimeError):
    """Raised when current-branch detection runs against a detached HEAD.

    State-file naming requires a stable branch label; the orchestrator
    refuses to create state under the placeholder ``HEAD`` reference.
    """


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
    error. Callers distinguish this from a git failure by treating empty
    output as the no-scope case rather than re-raising.

    Raises ``subprocess.CalledProcessError`` when git itself fails — an
    invalid ``range_spec`` (typo, missing ref, unknown SHA), a corrupt
    repository, or a runtime that lacks ``git``. Callers that want a
    domain-specific error catch and translate; this helper propagates the
    raw subprocess error so the caller decides the recovery policy.
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


def remote_tracking_ref(base_ref: str) -> str:
    """Compose the remote-tracking ref ``origin/<base_ref>`` from a bare base.

    The single source of the ``origin/`` composition. Both the audit
    surface (:func:`branch_scope`) and the review surface
    (``compute_diff``) route their git-derived base through this helper so
    every changeset diff range is taken against the fetched remote-tracking
    ref rather than a bare local branch. A bare local ref such as ``main``
    can lag ``origin/<base>`` in a multi-worktree checkout where the local
    branch is left unattached; the three-dot diff then recomputes its merge
    base from the stale ref and re-includes already-merged commits.
    """
    return f"{ORIGIN_REF_PREFIX}{base_ref}"


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

    The ``origin/`` prefix is composed here through
    :func:`remote_tracking_ref` rather than required from the caller, so
    callers pass bare base names like ``main`` or ``develop``.

    ``patterns`` filters the result by pathspec when provided; empty or
    ``None`` returns every file in the range.
    """
    range_spec = BRANCH_SCOPE_RANGE_TEMPLATE.format(
        origin_ref=remote_tracking_ref(base_ref)
    )
    return expand_diff_range(range_spec, patterns=patterns, repo=repo)


def detect_base_ref(repo: pathlib.Path, *, strict: bool = False) -> str:
    """Return the bare base-branch name configured by ``origin/HEAD``.

    Reads ``refs/remotes/origin/HEAD`` and strips the
    ``refs/remotes/origin/`` prefix so the result is a bare branch name
    (e.g. ``main``). Callers compose the remote-tracking ref through
    :func:`remote_tracking_ref`; returning the bare name keeps the slug
    derivation and the diff-range composition independent.

    When the symbolic ref is absent (no remote configured, fresh
    bootstrap, solo developer repo):

    - ``strict=False`` (default): returns ``DEFAULT_BASE_REF`` so callers
      can still compose diff ranges without halting. The audit skill
      relies on this fallback.
    - ``strict=True``: raises ``BaseRefNotConfiguredError``. The
      review-changes skill uses this variant so the operator gets a
      definitive answer rather than a silently-chosen literal.
    """
    result = subprocess.run(
        ["git", "symbolic-ref", "refs/remotes/origin/HEAD"],  # noqa: S607 — git resolved via PATH by design; portable helper, no fixed install path
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        if strict:
            raise BaseRefNotConfiguredError(f"refs/remotes/origin/HEAD unset at {repo}")
        return DEFAULT_BASE_REF
    line = result.stdout.strip()
    if line.startswith(ORIGIN_HEAD_REF_PREFIX):
        return line[len(ORIGIN_HEAD_REF_PREFIX) :]
    if strict:
        raise BaseRefNotConfiguredError(
            f"refs/remotes/origin/HEAD has unexpected shape: {line!r}"
        )
    return DEFAULT_BASE_REF


def detect_current_branch(repo: pathlib.Path) -> str:
    """Return the current branch name; raise ``DetachedHeadError`` on detached HEAD.

    Callers name records by the current branch; running on detached HEAD
    would produce a label of ``HEAD`` that collides across every
    detached-checkout invocation. Raising forces the caller to switch to a
    named branch before a branch-scoped record is created.
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


def commit_oid(ref: str, *, repo: pathlib.Path) -> str:
    """Resolve ``ref`` to the full object ID of a commit.

    The journal run-state identity records concrete head/base commit IDs, not
    symbolic refs. Peeling through ``^{commit}`` rejects blobs and trees while
    accepting commits and tags that point at commits.
    """
    # Fixed argv, no shell, ref is caller-controlled.
    result = subprocess.run(  # noqa: S603
        ["git", "rev-parse", "--verify", "--quiet", f"{ref}{COMMIT_PEEL_SUFFIX}"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def _read_frontmatter_branch(path: pathlib.Path) -> str | None:
    """Extract the ``branch:`` value from a markdown file's YAML frontmatter.

    Returns ``None`` if the file is unreadable, has no frontmatter, or has
    no ``branch:`` key. Used by :func:`branch_slug` to detect whether an
    existing state file at the base-slug path belongs to a different
    branch (collision case) or the same branch (reuse case).
    """
    try:
        content = path.read_text(encoding="utf-8")
    except OSError:
        return None
    if not content.startswith(FRONTMATTER_DELIMITER):
        return None
    in_frontmatter = False
    for line in content.splitlines():
        if line.strip() == FRONTMATTER_DELIMITER:
            if in_frontmatter:
                return None
            in_frontmatter = True
            continue
        if in_frontmatter and line.startswith("branch:"):
            return line.partition(":")[2].strip()
    return None


def branch_slug(branch_name: str, state_dir: pathlib.Path | None = None) -> str:
    """Derive the on-disk slug for ``branch_name``.

    Constructs the slug in three stages:

    1. Replace every ``/`` in the branch name with ``__`` so the result
       fits in a single filesystem path component.
    2. Replace a whole-segment ``.`` or ``..`` value with a distinct
       token so the slug never resolves to the current or parent
       directory. Internal ``.`` characters survive (they cannot
       resolve a parent segment by themselves).
    3. Bound the slug at ``BRANCH_SLUG_MAX_LENGTH`` characters. When
       the base slug exceeds the bound, truncate and append
       ``--<sha8>`` where ``sha8`` is the first eight hex characters of
       SHA-256(branch_name) so distinct branches with a long common
       prefix remain distinguishable.

    When ``state_dir`` is provided and an existing state file at
    ``state_dir/<base-slug>.md`` records a *different* branch in its
    frontmatter, the same ``--<sha8>`` suffix disambiguates. The
    suffix is deterministic so re-runs land on the same slug across
    invocations.

    The ``state_dir`` argument is optional — passing ``None`` disables
    the state-file collision check, which is the calling convention
    callers use when they do not maintain audit-state files (the
    thread-store helper consumes this contract via re-export).
    """
    # Stage 1: replace slashes.
    slashed = branch_name.replace("/", "__")

    # Stage 2: defuse whole-segment ``.`` / ``..`` values.
    if slashed == ".":
        base_slug = BRANCH_SLUG_DOT_SUBSTITUTE
    elif slashed == "..":
        base_slug = BRANCH_SLUG_DOTDOT_SUBSTITUTE
    else:
        base_slug = slashed

    digest = hashlib.sha256(branch_name.encode("utf-8")).hexdigest()
    suffix = digest[:BRANCH_SLUG_COLLISION_SUFFIX_LENGTH]
    suffix_with_separator = f"--{suffix}"

    # Stage 3: bound the length.
    if len(base_slug) > BRANCH_SLUG_MAX_LENGTH:
        truncated_prefix_length = BRANCH_SLUG_MAX_LENGTH - len(suffix_with_separator)
        return f"{base_slug[:truncated_prefix_length]}{suffix_with_separator}"

    # Stage 4 (optional): state-collision disambiguation.
    if state_dir is not None:
        existing = state_dir / f"{base_slug}.md"
        if existing.is_file():
            existing_branch = _read_frontmatter_branch(existing)
            if existing_branch is not None and existing_branch != branch_name:
                collided = f"{base_slug}{suffix_with_separator}"
                # Collision suffix also obeys the length bound.
                if len(collided) > BRANCH_SLUG_MAX_LENGTH:
                    truncated_prefix_length = BRANCH_SLUG_MAX_LENGTH - len(
                        suffix_with_separator
                    )
                    return (
                        f"{base_slug[:truncated_prefix_length]}{suffix_with_separator}"
                    )
                return collided
    return base_slug
