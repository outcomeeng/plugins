"""Canonical git-derived changeset primitives shipped with the spec-tree plugin.

Single home for the deterministic git derivation every scope consumer
shares: branch identity, the on-disk addressing slug, base-ref resolution,
the remote-tracking ref form, and merge-base diff scope. Consumers import
these symbols (directly or through consumer imports); none re-implements
them.

Every changeset diff range over a git-derived base is composed against the
remote-tracking ref ``origin/<base>`` through :func:`remote_tracking_ref`, so a
stale local branch ref in a multi-worktree checkout cannot widen the scope.

Portability: stdlib only — no third-party packages, no ``uv``, no
``outcomeeng_*`` imports. This script ships into consumer plugin trees where
only the standard library is available.

Tested inputs and error cases: changeset-scope and dependent
verification-run suites exercise origin/HEAD base detection, missing-origin
rejection, named-branch detection, detached-HEAD refusal, branch slug collision
suffixes, diff-range expansion with and without pathspec filters, empty diff
matches, staged and unstaged changes, remote-tracking three-dot branch scope,
arbitrary base refs, base-advanced-after-branch-off exclusion, git failure
propagation, and the stale-base refusal — a head behind the fetched base tip,
a lagging local remote-tracking ref the fetch corrects, and a current head —
before this script is bundled.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import runpy
import subprocess
import sys
from collections.abc import Sequence
from enum import StrEnum
from typing import Literal, Protocol, cast

_CONTRACT = runpy.run_path(
    str(pathlib.Path(__file__).with_name("changeset_scope_contract.py"))
)
BRANCH_SLUG_COLLISION_SUFFIX_LENGTH = cast(
    int, _CONTRACT["BRANCH_SLUG_COLLISION_SUFFIX_LENGTH"]
)
BRANCH_SLUG_MAX_LENGTH = cast(int, _CONTRACT["BRANCH_SLUG_MAX_LENGTH"])
BRANCH_REF_PATH_SEPARATOR = cast(str, _CONTRACT["BRANCH_REF_PATH_SEPARATOR"])
BRANCH_SLUG_PATH_SUBSTITUTE = cast(str, _CONTRACT["BRANCH_SLUG_PATH_SUBSTITUTE"])
BRANCH_SLUG_DOT_SUBSTITUTE = cast(str, _CONTRACT["BRANCH_SLUG_DOT_SUBSTITUTE"])
BRANCH_SLUG_DOTDOT_SUBSTITUTE = cast(str, _CONTRACT["BRANCH_SLUG_DOTDOT_SUBSTITUTE"])
ORIGIN_REMOTE_NAME = cast(str, _CONTRACT["ORIGIN_REMOTE_NAME"])
ORIGIN_HEAD_REF_PREFIX = cast(str, _CONTRACT["ORIGIN_HEAD_REF_PREFIX"])
ORIGIN_HEAD_REF = cast(str, _CONTRACT["ORIGIN_HEAD_REF"])
ORIGIN_REF_PREFIX = cast(str, _CONTRACT["ORIGIN_REF_PREFIX"])
HEAD_REF = cast(str, _CONTRACT["HEAD_REF"])
BRANCH_SCOPE_RANGE_TEMPLATE = cast(str, _CONTRACT["BRANCH_SCOPE_RANGE_TEMPLATE"])
FRONTMATTER_DELIMITER = cast(str, _CONTRACT["FRONTMATTER_DELIMITER"])
STATE_FILE_BRANCH_KEY = cast(str, _CONTRACT["STATE_FILE_BRANCH_KEY"])
STATE_FILE_SUFFIX = cast(str, _CONTRACT["STATE_FILE_SUFFIX"])
COMMIT_PEEL_SUFFIX = cast(str, _CONTRACT["COMMIT_PEEL_SUFFIX"])
BRANCH_SLUG_SUFFIX_SEPARATOR = cast(str, _CONTRACT["BRANCH_SLUG_SUFFIX_SEPARATOR"])
RANGE_SEPARATOR = "..."
# A head behind the fetched base is refused with its own exit code so a caller
# never mistakes it for a selector the resolver could not read (argparse's 2).
EXIT_STALE_BASE = 3
STALE_BASE_STATUS = "stale-base"


class ScopeField(StrEnum):
    """Public fields in a resolved committed changeset."""

    BASE = "base"
    HEAD = "head"
    CHANGED_PATHS = "changed_paths"


class StaleBaseField(StrEnum):
    """Fields of the diagnostic a stale-base refusal emits in place of a scope."""

    STATUS = "status"
    TIP = "tip"
    MERGE_BASE = "merge_base"
    BEHIND = "behind"


class Runner(Protocol):
    """Execute one git command through an injectable process boundary."""

    def __call__(
        self,
        argv: Sequence[str],
        /,
        *,
        cwd: pathlib.Path,
        capture_output: bool,
        text: Literal[True],
        check: bool,
    ) -> subprocess.CompletedProcess[str]: ...


class BaseRefNotConfiguredError(RuntimeError):
    """Raised by ``detect_base_ref`` when origin/HEAD is absent.

    Base-ref derivation has no portable fallback when the remote default is
    absent. Callers must supply authoritative scope rather than guessing a
    consumer repository's branch name.
    """


class DetachedHeadError(RuntimeError):
    """Raised when current-branch detection runs against a detached HEAD.

    State-file naming requires a stable branch label; the orchestrator
    refuses to create state under the placeholder ``HEAD`` reference.
    """


class ScopeResolutionError(RuntimeError):
    """A selector cannot resolve to an exact committed changeset."""


class StaleBaseError(RuntimeError):
    """The head is behind the fetched base tip, so no verification may start.

    Distinct from :class:`ScopeResolutionError`: the selector resolved, and the
    refusal is the verdict — the tree is not the one that would merge.
    """

    def __init__(self, *, tip: str, merge_base: str, behind: int) -> None:
        super().__init__(
            f"head is {behind} commit(s) behind the fetched base tip {tip} "
            f"(merge base {merge_base}); bring the branch current first"
        )
        self.tip = tip
        self.merge_base = merge_base
        self.behind = behind

    def diagnostic(self) -> dict[str, object]:
        """Return the machine-readable refusal a caller relays verbatim."""
        return {
            StaleBaseField.STATUS: STALE_BASE_STATUS,
            StaleBaseField.TIP: self.tip,
            StaleBaseField.MERGE_BASE: self.merge_base,
            StaleBaseField.BEHIND: self.behind,
        }


def resolve_committed_scope(
    selector: str,
    *,
    repo: pathlib.Path,
    runner: Runner = subprocess.run,
) -> dict[str, object]:
    """Resolve HEAD, a branch, or an explicit three-dot range against a fetched base.

    Preserve explicit endpoints. A single ref uses the configured remote base.
    A remote-tracking base is fetched first, which updates that ref and never
    the working tree, and a head behind the fetched tip is refused. The base
    identity is the fetched tip, not the merge-base commit; the changed paths
    always follow Git's merge-base diff semantics.
    """
    try:
        if RANGE_SEPARATOR in selector:
            base_ref, _, head_ref = selector.partition(RANGE_SEPARATOR)
            if not base_ref or not head_ref:
                raise ScopeResolutionError(
                    f"malformed commit range: {selector!r} — expected "
                    "'<base>...<head>', for example 'origin/main...HEAD'"
                )
        else:
            base_ref = remote_tracking_ref(detect_base_ref(repo, runner=runner))
            head_ref = selector
        require_current_base(base_ref, head_ref, repo=repo, runner=runner)
        return {
            ScopeField.BASE: commit_oid(base_ref, repo=repo, runner=runner),
            ScopeField.HEAD: commit_oid(head_ref, repo=repo, runner=runner),
            ScopeField.CHANGED_PATHS: expand_diff_range(
                f"{base_ref}{RANGE_SEPARATOR}{head_ref}", repo=repo, runner=runner
            ),
        }
    except subprocess.CalledProcessError as exc:
        raise ScopeResolutionError(
            f"git could not resolve {selector}: {(exc.stderr or '').strip()}"
        ) from exc
    except BaseRefNotConfiguredError as exc:
        raise ScopeResolutionError(str(exc)) from exc
    except OSError as exc:
        raise ScopeResolutionError(
            f"cannot execute git for {selector!r} at {repo}: {exc}"
        ) from exc


def require_current_base(
    base_ref: str,
    head_ref: str,
    *,
    repo: pathlib.Path,
    runner: Runner = subprocess.run,
) -> None:
    """Refuse a head that does not descend from the fetched remote base tip.

    Only a remote-tracking base is checked: a local ref or commit named as the
    base of an explicit range is the caller's exact endpoint, compared as
    given with no fetch and no refusal. A remote-tracking base is fetched
    first with an explicit refspec, so the comparison reads the ref the fetch
    just wrote rather than whatever the local remote-tracking ref last saw;
    the symbolic ``origin/HEAD`` resolves to its configured branch first,
    because a bare ``git fetch origin HEAD`` writes only ``FETCH_HEAD``. The
    head is current when its merge base with that tip is the tip itself;
    otherwise :class:`StaleBaseError` names the tip, the merge base, and the
    base commits the head lacks. Git failures propagate as
    ``subprocess.CalledProcessError`` for the caller to translate.
    """
    if not base_ref.startswith(ORIGIN_REF_PREFIX):
        return
    bare_base = base_ref[len(ORIGIN_REF_PREFIX) :]
    if bare_base == HEAD_REF:
        bare_base = detect_base_ref(repo, runner=runner)
        base_ref = remote_tracking_ref(bare_base)
    runner(
        [
            "git",
            "fetch",
            "--quiet",
            ORIGIN_REMOTE_NAME,
            f"+refs/heads/{bare_base}:{ORIGIN_HEAD_REF_PREFIX}{bare_base}",
        ],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )
    tip = commit_oid(base_ref, repo=repo, runner=runner)
    merge_base = runner(
        ["git", "merge-base", tip, head_ref],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    if merge_base == tip:
        return
    behind = runner(
        ["git", "rev-list", "--count", f"{merge_base}..{tip}"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    raise StaleBaseError(tip=tip, merge_base=merge_base, behind=int(behind))


def expand_diff_range(
    range_spec: str,
    *,
    patterns: list[str] | None = None,
    repo: pathlib.Path,
    runner: Runner = subprocess.run,
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
    result = runner(
        cmd,
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )
    return [line for line in result.stdout.splitlines() if line]


def remote_tracking_ref(base_ref: str) -> str:
    """Compose the remote-tracking ref ``origin/<base_ref>`` from a bare base.

    The single source of the ``origin/`` composition. :func:`branch_scope`
    and every consumer with its own diff operation route their git-derived
    base through this helper, so every changeset diff range is taken against
    the fetched remote-tracking ref rather than a bare local branch. A bare
    local ref such as ``main`` can lag ``origin/<base>`` in a multi-worktree
    checkout where the local branch is left unattached; the three-dot diff
    then recomputes its merge base from the stale ref and re-includes
    already-merged commits.
    """
    return f"{ORIGIN_REF_PREFIX}{base_ref}"


def branch_scope(
    base_ref: str,
    *,
    patterns: list[str] | None = None,
    repo: pathlib.Path,
    runner: Runner = subprocess.run,
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
    return expand_diff_range(range_spec, patterns=patterns, repo=repo, runner=runner)


def detect_base_ref(
    repo: pathlib.Path,
    *,
    runner: Runner = subprocess.run,
) -> str:
    """Return the bare base-branch name configured by ``origin/HEAD``.

    Reads ``refs/remotes/origin/HEAD`` and strips the
    ``refs/remotes/origin/`` prefix so the result is a bare branch name
    (e.g. ``main``). Callers compose the remote-tracking ref through
    :func:`remote_tracking_ref`; returning the bare name keeps the slug
    derivation and the diff-range composition independent.

    When the symbolic ref is absent, raises ``BaseRefNotConfiguredError``.
    No mode guesses a consumer repository's default branch.
    """
    result = runner(
        ["git", "symbolic-ref", ORIGIN_HEAD_REF],  # noqa: S607  # Git is intentionally resolved through PATH.
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise BaseRefNotConfiguredError(f"{ORIGIN_HEAD_REF} unset at {repo}")
    line = result.stdout.strip()
    if line.startswith(ORIGIN_HEAD_REF_PREFIX):
        return line[len(ORIGIN_HEAD_REF_PREFIX) :]
    raise BaseRefNotConfiguredError(f"{ORIGIN_HEAD_REF} has unexpected shape: {line!r}")


def detect_current_branch(
    repo: pathlib.Path,
    *,
    runner: Runner = subprocess.run,
) -> str:
    """Return the current branch name; raise ``DetachedHeadError`` on detached HEAD.

    Callers name records by the current branch; running on detached HEAD
    would produce a label of ``HEAD`` that collides across every
    detached-checkout invocation. Raising forces the caller to switch to a
    named branch before a branch-scoped record is created.
    """
    result = runner(
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


def commit_oid(
    ref: str,
    *,
    repo: pathlib.Path,
    runner: Runner = subprocess.run,
) -> str:
    """Resolve ``ref`` to the full object ID of a commit.

    The journal run-state identity records concrete head/base commit IDs, not
    symbolic refs. Peeling through ``^{commit}`` rejects blobs and trees while
    accepting commits and tags that point at commits.
    """
    # Fixed argv, no shell, ref is caller-controlled.
    result = runner(
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
        if in_frontmatter and line.startswith(f"{STATE_FILE_BRANCH_KEY}:"):
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
    consumers import this contract directly).
    """
    # Stage 1: replace slashes.
    slashed = branch_name.replace(
        BRANCH_REF_PATH_SEPARATOR,
        BRANCH_SLUG_PATH_SUBSTITUTE,
    )

    # Stage 2: defuse whole-segment ``.`` / ``..`` values.
    if slashed == ".":
        base_slug = BRANCH_SLUG_DOT_SUBSTITUTE
    elif slashed == "..":
        base_slug = BRANCH_SLUG_DOTDOT_SUBSTITUTE
    else:
        base_slug = slashed

    digest = hashlib.sha256(branch_name.encode("utf-8")).hexdigest()
    suffix = digest[:BRANCH_SLUG_COLLISION_SUFFIX_LENGTH]
    suffix_with_separator = f"{BRANCH_SLUG_SUFFIX_SEPARATOR}{suffix}"

    # Stage 3: bound the length.
    if len(base_slug) > BRANCH_SLUG_MAX_LENGTH:
        truncated_prefix_length = BRANCH_SLUG_MAX_LENGTH - len(suffix_with_separator)
        return f"{base_slug[:truncated_prefix_length]}{suffix_with_separator}"

    # Stage 4 (optional): state-collision disambiguation.
    if state_dir is not None:
        existing = state_dir / f"{base_slug}{STATE_FILE_SUFFIX}"
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


def main(argv: Sequence[str] | None = None) -> int:
    """Resolve a committed selector through the provider's command boundary."""
    parser = argparse.ArgumentParser(description="Resolve a committed changeset")
    parser.add_argument("selector", help="HEAD, a branch, or a three-dot range")
    parser.add_argument("--repo", type=pathlib.Path, default=pathlib.Path.cwd())
    args = parser.parse_args(argv)
    try:
        resolved = resolve_committed_scope(
            args.selector, repo=args.repo, runner=subprocess.run
        )
    except StaleBaseError as exc:
        print(json.dumps(exc.diagnostic(), sort_keys=True), file=sys.stderr)
        return EXIT_STALE_BASE
    except ScopeResolutionError as exc:
        parser.error(str(exc))
    print(json.dumps(resolved, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
