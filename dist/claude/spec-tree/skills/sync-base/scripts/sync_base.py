"""Bring a branch behind its fetched base current by rebasing.

Synchronization fetches the branch's base, detects whether the branch is
behind the remote-tracking base ref ``origin/<base>``, and rebases the
branch's own commits onto that ref. The mechanism is rebase, never
``git reset``: rebase replays the branch's commits onto the advanced base,
preserving the branch's work, where ``reset`` would repoint the branch while
leaving the working tree at the old base and silently revert merged changes.

A clean rebase runs without operator interaction. A rebase conflict leaves the
rebase state active so the caller can inspect and reconcile the conflicted
stages. When autonomous reconciliation cannot resolve it, the human-facing
report names the conflicted paths, the attempted sync, and the operator's
manual options, including continuing or aborting the rebase.

A working tree with uncommitted changes to tracked files blocks the rebase
before it starts. This is reported as the distinct ``dirty_tree`` outcome with
no rebase attempted and the working tree left untouched: a dirty tree is a
precondition the caller clears by committing through the commit workflow, not a
rebase conflict, and synchronization never commits or stashes on the caller's
behalf. Untracked files do not block a rebase and are not a dirty tree.

A detached HEAD — a worktree with no branch checked out, the normal parked state
of a bare-repository worktree pool — is brought current by fetch-and-compare
rather than waved through. When the detached commit is an ancestor of the
fetched ``origin/<base>`` (behind it or equal to it) and the working tree is
clean, the worktree is advanced to the base tip and reported ``rebased`` (it
moved) or ``already_current`` (it was already there); a behind detached commit
with uncommitted tracked changes reports ``dirty_tree``. When the detached
commit has diverged — it carries commits the base lacks — advancing it would
orphan those commits, so the outcome is ``git_failure``; a detached HEAD has no
branch to rebase its own commits onto. A detached HEAD with no resolvable remote
base also reports ``git_failure``. Advancing a clean, strictly-behind detached
worktree is a fast-forward to commits it does not yet have, never the reset the
mechanism rejects.

On a clean outcome (``rebased`` or ``already_current``) the result carries a
readiness-preservation proof: full before/after base and branch OIDs, the base
delta, the branch's changed paths against the old and new base, their overlap,
and whether the branch patch identity changed. A caller reads it to decide
which pre-push readiness predicates survive the base movement. The proof is git
facts only — validation-lane mapping and the governance-surface list are the
project overlay's — and it never satisfies a merge gate.

The base ref and its remote-tracking form are resolved through the shared
changeset-scope primitives, never re-derived here. The primitives ship under a
runtime-substituted plugin skill directory and are not importable by package
name, so they are loaded through ``importlib`` and re-exported with object
identity preserved.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import pathlib
import subprocess
import sys
from dataclasses import dataclass
from enum import Enum
from types import ModuleType

_CHANGESET_SCOPE_PATH = (
    pathlib.Path(__file__).resolve().parent.parent.parent
    / "scope-changeset"
    / "scripts"
    / "changeset_scope.py"
)

CONFLICT_SUMMARY = "Base sync stopped: rebase conflict requires reconciliation"
CONFLICT_INSPECT_STATUS = "git status"
CONFLICT_INSPECT_DIFF = "git diff"
CONFLICT_INSPECT_STAGES = "git ls-files -u"
CONFLICT_CONTINUE = "git add <resolved-paths> && git rebase --continue"
CONFLICT_ABORT = "git rebase --abort"

#: Schema version of the readiness-preservation proof embedded in the result.
READINESS_SCHEMA_VERSION = 1


def _load_changeset_scope() -> ModuleType:
    """Load the canonical ``changeset_scope`` module via importlib and cache it."""
    resolved_path = _CHANGESET_SCOPE_PATH.resolve()
    cached = sys.modules.get("changeset_scope")
    if cached is not None and _module_origin(cached) == resolved_path:
        return cached
    module_name = (
        "changeset_scope"
        if cached is None
        else "changeset_scope_"
        + hashlib.sha256(str(resolved_path).encode()).hexdigest()
    )
    path_cached = sys.modules.get(module_name)
    if path_cached is not None and _module_origin(path_cached) == resolved_path:
        return path_cached
    spec = importlib.util.spec_from_file_location(
        module_name,
        resolved_path,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load changeset_scope from {_CHANGESET_SCOPE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _module_origin(module: ModuleType) -> pathlib.Path | None:
    module_file = getattr(module, "__file__", None)
    if not isinstance(module_file, str):
        return None
    return pathlib.Path(module_file).resolve()


_changeset_scope = _load_changeset_scope()

# Re-export the canonical primitives. ``is`` identity holds — these are the same
# function/class objects the changeset-scope module defines, so sync-base never
# re-implements base, remote-tracking, or branch derivation.
detect_base_ref = _changeset_scope.detect_base_ref
remote_tracking_ref = _changeset_scope.remote_tracking_ref
detect_current_branch = _changeset_scope.detect_current_branch
BaseRefNotConfiguredError = _changeset_scope.BaseRefNotConfiguredError
DetachedHeadError = _changeset_scope.DetachedHeadError


class SyncStatus(str, Enum):
    """Terminal outcome of a base-synchronization run."""

    ALREADY_CURRENT = "already_current"
    REBASED = "rebased"
    CONFLICT = "conflict"
    DIRTY_TREE = "dirty_tree"
    GIT_FAILURE = "git_failure"


#: Process exit code per terminal status.
_EXIT_CODES = {
    SyncStatus.ALREADY_CURRENT: 0,
    SyncStatus.REBASED: 0,
    SyncStatus.CONFLICT: 3,
    SyncStatus.DIRTY_TREE: 4,
    SyncStatus.GIT_FAILURE: 1,
}


@dataclass(frozen=True)
class Preservation:
    """Git facts a caller reads to decide which pre-push readiness survives a sync.

    Emitted only on a clean outcome (``rebased`` or ``already_current``). All
    OIDs are full, unabbreviated hashes. ``old_base_oid`` is the branch's fork
    point from the base — the merge-base of the pre-rebase HEAD and the current
    base — so ``base_delta_paths`` reports the files the base advanced over since
    the branch diverged, accurate whether or not the caller pre-fetched.
    ``branch_paths_before``/``branch_paths_after`` are the branch's own changed
    paths against the fork point and the new base. ``path_overlap`` is the base
    delta's intersection with the branch's paths. ``branch_patch_changed`` is
    whether the branch's patch identity differs across the sync.
    ``branch_diff_unchanged`` is the git-only reuse signal: the branch patch is
    unchanged and nothing in the base delta overlaps the branch — a caller still
    ANDs its own governance-surface check before reusing a prior local review. A
    field is ``None`` when a required OID could not be resolved, in which case
    ``branch_diff_unchanged`` is ``False``.

    This proof scopes pre-push local verification only; it never satisfies a
    merge gate. Validation-lane mapping over ``base_delta_paths`` and the
    governance-surface list are the project overlay's, not this primitive's.
    """

    old_base_oid: str | None
    new_base_oid: str | None
    old_head_oid: str | None
    new_head_oid: str | None
    base_delta_paths: list[str] | None
    branch_paths_before: list[str] | None
    branch_paths_after: list[str] | None
    path_overlap: list[str] | None
    branch_patch_changed: bool
    branch_diff_unchanged: bool

    def to_json_dict(self) -> dict[str, object]:
        """Serialize the proof with the schema version and stable keys."""
        return {
            "schema_version": READINESS_SCHEMA_VERSION,
            "old_base_oid": self.old_base_oid,
            "new_base_oid": self.new_base_oid,
            "old_head_oid": self.old_head_oid,
            "new_head_oid": self.new_head_oid,
            "base_delta_paths": self.base_delta_paths,
            "branch_paths_before": self.branch_paths_before,
            "branch_paths_after": self.branch_paths_after,
            "path_overlap": self.path_overlap,
            "branch_patch_changed": self.branch_patch_changed,
            "branch_diff_unchanged": self.branch_diff_unchanged,
        }


@dataclass(frozen=True)
class ConflictDetails:
    """Inspectable conflict state left active for reconciliation.

    ``summary`` is the human-facing headline; it is deliberately descriptive
    instead of a token. ``conflicted_paths`` comes from the active index's
    unmerged entries. ``old_head_oid`` and ``new_base_oid`` name the exact replay
    that stopped. The path sets mirror the preservation proof's git facts so the
    caller can classify overlap without hardcoded project paths. ``git_output``
    carries the combined rebase-conflict output because Git may emit the
    conflict summary on stdout and the follow-up hints on stderr.
    ``operator_options`` lists safe manual commands the operator may choose
    after autonomous reconciliation is exhausted; sync-base does not run the
    abort option at handoff.
    """

    summary: str
    conflicted_paths: list[str]
    old_head_oid: str | None
    new_base_oid: str | None
    base_delta_paths: list[str] | None
    branch_paths_before: list[str] | None
    path_overlap: list[str] | None
    git_output: str
    operator_options: list[str]

    def to_json_dict(self) -> dict[str, object]:
        """Serialize conflict details with stable keys."""
        return {
            "summary": self.summary,
            "conflicted_paths": self.conflicted_paths,
            "old_head_oid": self.old_head_oid,
            "new_base_oid": self.new_base_oid,
            "base_delta_paths": self.base_delta_paths,
            "branch_paths_before": self.branch_paths_before,
            "path_overlap": self.path_overlap,
            "git_output": self.git_output,
            "operator_options": self.operator_options,
        }


@dataclass(frozen=True)
class SyncBaseResult:
    """The outcome of a synchronization run.

    ``base_ref`` is the bare base-branch name; ``remote_ref`` is its
    remote-tracking form ``origin/<base>``. ``branch`` is the synchronized
    branch, or ``None`` when no branch could be resolved (detached HEAD).
    ``preservation`` carries the readiness-preservation proof on a clean
    outcome, and is ``None`` for ``dirty_tree``, ``conflict``, and
    ``git_failure``. ``conflict`` carries inspectable conflict state only for a
    rebase conflict left active for reconciliation.
    """

    status: SyncStatus
    base_ref: str
    remote_ref: str
    branch: str | None
    detail: str
    preservation: Preservation | None = None
    conflict: ConflictDetails | None = None

    @property
    def exit_code(self) -> int:
        """Process exit code for this status."""
        return _EXIT_CODES[self.status]

    def to_json_dict(self) -> dict[str, object]:
        """Serialize to a JSON-ready dict with stable keys."""
        return {
            "status": self.status.value,
            "base_ref": self.base_ref,
            "remote_ref": self.remote_ref,
            "branch": self.branch,
            "detail": self.detail,
            "preservation": (
                self.preservation.to_json_dict()
                if self.preservation is not None
                else None
            ),
            "conflict": (
                self.conflict.to_json_dict() if self.conflict is not None else None
            ),
        }


def _git(
    repo: pathlib.Path, *args: str, stdin: str | None = None
) -> subprocess.CompletedProcess[str]:
    """Run a git command in ``repo``, capturing output without raising."""
    return subprocess.run(  # noqa: S603 — fixed argv, no shell, args from callers
        ["git", *args],  # noqa: S607
        cwd=repo,
        input=stdin,
        capture_output=True,
        text=True,
        check=False,
    )


def _rev(repo: pathlib.Path, ref: str) -> str | None:
    """Resolve ``ref`` to a full OID, or ``None`` when it does not resolve."""
    result = _git(repo, "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}")
    oid = result.stdout.strip()
    return oid if result.returncode == 0 and oid else None


def _merge_base(repo: pathlib.Path, a: str, b: str) -> str | None:
    """Return the merge-base OID of ``a`` and ``b``, or ``None`` when none exists."""
    result = _git(repo, "merge-base", a, b)
    oid = result.stdout.strip()
    return oid if result.returncode == 0 and oid else None


def _diff_paths(repo: pathlib.Path, spec: str) -> list[str] | None:
    """Return the sorted changed paths for a diff spec, or ``None`` on failure.

    ``spec`` is a two-dot (``a..b``, net base advance) or three-dot
    (``base...head``, branch's own changes) range. ``--no-renames`` keeps a
    rename as a delete of the old path plus an add of the new path, so a base
    rename of a path the branch also touched surfaces as a path overlap rather
    than hiding behind the new name and licensing a false reuse.
    """
    result = _git(repo, "diff", "--name-only", "--no-renames", spec)
    if result.returncode != 0:
        return None
    return sorted(p for p in result.stdout.splitlines() if p)


def _conflicted_paths(repo: pathlib.Path) -> list[str]:
    """Return sorted paths with unmerged index entries in the active conflict."""
    result = _git(repo, "diff", "--name-only", "--diff-filter=U")
    if result.returncode != 0:
        return []
    return sorted(p for p in result.stdout.splitlines() if p)


def _patch_id(repo: pathlib.Path, base: str, head: str) -> str | None:
    """Return the stable patch identity of ``base...head``, or ``None`` on failure.

    An empty diff yields the empty string, which compares equal across a sync
    that left the branch's changes identical.
    """
    diff = _git(repo, "diff", f"{base}...{head}")
    if diff.returncode != 0:
        return None
    if not diff.stdout.strip():
        return ""
    identified = _git(repo, "patch-id", "--stable", stdin=diff.stdout)
    if identified.returncode != 0:
        return None
    return identified.stdout.split()[0] if identified.stdout.strip() else ""


def _build_preservation(
    repo: pathlib.Path,
    *,
    old_base_oid: str | None,
    new_base_oid: str | None,
    old_head_oid: str | None,
    new_head_oid: str | None,
) -> Preservation:
    """Compute the readiness-preservation proof from before/after OIDs.

    ``branch_diff_unchanged`` is true only when every required OID resolved, the
    branch patch identity is unchanged, and no base-delta path overlaps the
    branch's changed paths — the git-only signal a caller reads to consider a
    prior local review reusable.
    """
    base_delta = (
        _diff_paths(repo, f"{old_base_oid}..{new_base_oid}")
        if old_base_oid and new_base_oid
        else None
    )
    paths_before = (
        _diff_paths(repo, f"{old_base_oid}...{old_head_oid}")
        if old_base_oid and old_head_oid
        else None
    )
    paths_after = (
        _diff_paths(repo, f"{new_base_oid}...{new_head_oid}")
        if new_base_oid and new_head_oid
        else None
    )
    overlap = (
        sorted(set(base_delta) & set(paths_after))
        if base_delta is not None and paths_after is not None
        else None
    )
    patch_before = (
        _patch_id(repo, old_base_oid, old_head_oid)
        if old_base_oid and old_head_oid
        else None
    )
    patch_after = (
        _patch_id(repo, new_base_oid, new_head_oid)
        if new_base_oid and new_head_oid
        else None
    )
    patch_known = patch_before is not None and patch_after is not None
    branch_patch_changed = patch_before != patch_after if patch_known else True
    branch_diff_unchanged = (
        patch_known
        and not branch_patch_changed
        and overlap is not None
        and len(overlap) == 0
    )
    return Preservation(
        old_base_oid=old_base_oid,
        new_base_oid=new_base_oid,
        old_head_oid=old_head_oid,
        new_head_oid=new_head_oid,
        base_delta_paths=base_delta,
        branch_paths_before=paths_before,
        branch_paths_after=paths_after,
        path_overlap=overlap,
        branch_patch_changed=branch_patch_changed,
        branch_diff_unchanged=branch_diff_unchanged,
    )


def _build_conflict_details(
    repo: pathlib.Path,
    *,
    old_base_oid: str | None,
    new_base_oid: str | None,
    old_head_oid: str | None,
    git_output: str,
) -> ConflictDetails:
    """Build the active-conflict report without resolving or aborting it."""
    base_delta = (
        _diff_paths(repo, f"{old_base_oid}..{new_base_oid}")
        if old_base_oid and new_base_oid
        else None
    )
    paths_before = (
        _diff_paths(repo, f"{old_base_oid}...{old_head_oid}")
        if old_base_oid and old_head_oid
        else None
    )
    conflicted = _conflicted_paths(repo)
    overlap = (
        sorted(set(base_delta) & set(paths_before))
        if base_delta is not None and paths_before is not None
        else None
    )
    return ConflictDetails(
        summary=CONFLICT_SUMMARY,
        conflicted_paths=conflicted,
        old_head_oid=old_head_oid,
        new_base_oid=new_base_oid,
        base_delta_paths=base_delta,
        branch_paths_before=paths_before,
        path_overlap=overlap,
        git_output=git_output,
        operator_options=[
            CONFLICT_INSPECT_STATUS,
            CONFLICT_INSPECT_DIFF,
            CONFLICT_INSPECT_STAGES,
            CONFLICT_CONTINUE,
            CONFLICT_ABORT,
        ],
    )


def _sync_detached(
    repo: pathlib.Path,
    base_ref: str,
    remote_ref: str,
    *,
    fetch: bool,
) -> SyncBaseResult:
    """Bring a detached-HEAD worktree current with its fetched base.

    A detached HEAD has no branch, so it is brought current by advancing the
    worktree to ``origin/<base>`` rather than by rebasing branch commits. The
    detached commit is compared to the fetched base: an ancestor (behind or
    equal) and clean is advanced and reported ``rebased``/``already_current``; an
    ancestor that is behind but dirty is ``dirty_tree``; a commit that has
    diverged from the base, or a base that does not resolve, is ``git_failure``,
    because advancing a diverged worktree would orphan its commits. The branch
    field is ``None`` for every detached outcome.
    """
    old_head_oid = _rev(repo, "HEAD")

    if fetch:
        fetched = _git(repo, "fetch", "origin", base_ref)
        if fetched.returncode != 0:
            return SyncBaseResult(
                SyncStatus.GIT_FAILURE,
                base_ref,
                remote_ref,
                None,
                f"detached HEAD: git fetch origin {base_ref} failed: "
                f"{fetched.stderr.strip()}",
            )

    new_base_oid = _rev(repo, remote_ref)
    if old_head_oid is None or new_base_oid is None:
        return SyncBaseResult(
            SyncStatus.GIT_FAILURE,
            base_ref,
            remote_ref,
            None,
            f"detached HEAD: base ref {remote_ref} does not resolve to a commit",
        )

    # An ancestor detached commit (behind or equal) carries nothing the base
    # lacks, so advancing it to the base tip loses no commits. A commit that is
    # not an ancestor has diverged — it carries its own commits — and advancing
    # would orphan them, so it stays a git failure: a detached HEAD has no branch
    # to rebase those commits onto.
    is_ancestor = _git(repo, "merge-base", "--is-ancestor", old_head_oid, new_base_oid)
    if is_ancestor.returncode != 0:
        return SyncBaseResult(
            SyncStatus.GIT_FAILURE,
            base_ref,
            remote_ref,
            None,
            f"detached HEAD {old_head_oid} has diverged from {remote_ref}: it "
            f"carries commits the base lacks and has no branch to rebase them onto",
        )

    # The fork point of an ancestor detached commit is the commit itself.
    old_base_oid = _merge_base(repo, old_head_oid, new_base_oid)

    if old_head_oid == new_base_oid:
        return SyncBaseResult(
            SyncStatus.ALREADY_CURRENT,
            base_ref,
            remote_ref,
            None,
            f"detached HEAD is already current with {remote_ref}",
            preservation=_build_preservation(
                repo,
                old_base_oid=old_base_oid,
                new_base_oid=new_base_oid,
                old_head_oid=old_head_oid,
                new_head_oid=old_head_oid,
            ),
        )

    # precondition: advancing a worktree over uncommitted tracked changes would
    # clobber them, so a dirty tree blocks the advance just as it blocks a rebase
    dirty = _git(repo, "status", "--porcelain", "--untracked-files=no")
    if dirty.returncode != 0:
        return SyncBaseResult(
            SyncStatus.GIT_FAILURE,
            base_ref,
            remote_ref,
            None,
            f"cannot inspect working tree state: {dirty.stderr.strip()}",
        )
    if dirty.stdout.strip():
        return SyncBaseResult(
            SyncStatus.DIRTY_TREE,
            base_ref,
            remote_ref,
            None,
            f"detached HEAD behind {remote_ref} has uncommitted changes to "
            f"tracked files; commit them before advancing to {remote_ref}",
        )

    advanced = _git(repo, "switch", "--detach", remote_ref)
    if advanced.returncode != 0:
        return SyncBaseResult(
            SyncStatus.GIT_FAILURE,
            base_ref,
            remote_ref,
            None,
            f"detached HEAD: cannot advance to {remote_ref}: {advanced.stderr.strip()}",
        )
    return SyncBaseResult(
        SyncStatus.REBASED,
        base_ref,
        remote_ref,
        None,
        f"advanced detached HEAD to {remote_ref}",
        preservation=_build_preservation(
            repo,
            old_base_oid=old_base_oid,
            new_base_oid=new_base_oid,
            old_head_oid=old_head_oid,
            new_head_oid=_rev(repo, "HEAD"),
        ),
    )


def _resolve_default_base(repo: pathlib.Path) -> str | SyncBaseResult:
    try:
        return detect_base_ref(repo)
    except BaseRefNotConfiguredError as exc:
        return SyncBaseResult(
            SyncStatus.GIT_FAILURE,
            "",
            "",
            None,
            str(exc),
        )


def sync_base(
    repo: pathlib.Path, *, base_ref: str | None = None, fetch: bool = True
) -> SyncBaseResult:
    """Bring ``repo``'s current branch current with its fetched base.

    ``base_ref`` is the bare base-branch name to synchronize onto. When omitted
    it is resolved from ``origin/HEAD`` through the shared changeset-scope
    primitives; callers that track a non-default base (a stacked pull request
    whose base is another feature branch) pass it explicitly. The base is
    fetched (unless ``fetch=False``) and the branch is rebased onto
    ``origin/<base>`` when it is behind. Returns a :class:`SyncBaseResult`;
    never raises for an ordinary git outcome.
    """
    if base_ref is None:
        resolved_base = _resolve_default_base(repo)
        if isinstance(resolved_base, SyncBaseResult):
            return resolved_base
        base_ref = resolved_base
    return _sync_resolved_base(repo, base_ref=base_ref, fetch=fetch)


def _sync_resolved_base(
    repo: pathlib.Path, *, base_ref: str, fetch: bool
) -> SyncBaseResult:
    """Synchronize onto a caller-resolved bare base branch."""
    remote_ref = remote_tracking_ref(base_ref)

    try:
        branch = detect_current_branch(repo)
    except DetachedHeadError:
        return _sync_detached(repo, base_ref, remote_ref, fetch=fetch)

    # Capture the pre-rebase HEAD for the preservation proof; the base fork point
    # is derived after the fetch (below) so the base delta stays accurate even
    # when the caller already fetched the base.
    old_head_oid = _rev(repo, "HEAD")

    if fetch:
        fetched = _git(repo, "fetch", "origin", base_ref)
        if fetched.returncode != 0:
            return SyncBaseResult(
                SyncStatus.GIT_FAILURE,
                base_ref,
                remote_ref,
                branch,
                f"git fetch origin {base_ref} failed: {fetched.stderr.strip()}",
            )

    resolved = _git(
        repo, "rev-parse", "--verify", "--quiet", f"{remote_ref}^{{commit}}"
    )
    if resolved.returncode != 0:
        return SyncBaseResult(
            SyncStatus.GIT_FAILURE,
            base_ref,
            remote_ref,
            branch,
            f"base ref {remote_ref} does not resolve to a commit",
        )

    behind = _git(repo, "rev-list", "--count", f"HEAD..{remote_ref}")
    if behind.returncode != 0:
        return SyncBaseResult(
            SyncStatus.GIT_FAILURE,
            base_ref,
            remote_ref,
            branch,
            f"cannot compute commits behind {remote_ref}: {behind.stderr.strip()}",
        )
    new_base_oid = _rev(repo, remote_ref)
    # Anchor the base delta at the branch's fork point from the base — the
    # merge-base of the pre-rebase HEAD and the current base. This is stable
    # whether or not the caller pre-fetched, where the pre-fetch remote ref would
    # already equal the post-fetch base and report an empty base delta.
    old_base_oid = (
        _merge_base(repo, old_head_oid, new_base_oid)
        if old_head_oid and new_base_oid
        else None
    )
    if int(behind.stdout.strip() or "0") == 0:
        return SyncBaseResult(
            SyncStatus.ALREADY_CURRENT,
            base_ref,
            remote_ref,
            branch,
            f"branch {branch} is already current with {remote_ref}",
            preservation=_build_preservation(
                repo,
                old_base_oid=old_base_oid,
                new_base_oid=new_base_oid,
                old_head_oid=old_head_oid,
                new_head_oid=old_head_oid,
            ),
        )

    # precondition: git refuses to replay over uncommitted tracked changes; untracked excluded
    dirty = _git(repo, "status", "--porcelain", "--untracked-files=no")
    if dirty.returncode != 0:
        return SyncBaseResult(
            SyncStatus.GIT_FAILURE,
            base_ref,
            remote_ref,
            branch,
            f"cannot inspect working tree state: {dirty.stderr.strip()}",
        )
    if dirty.stdout.strip():
        return SyncBaseResult(
            SyncStatus.DIRTY_TREE,
            base_ref,
            remote_ref,
            branch,
            f"working tree of {branch} has uncommitted changes to tracked files; "
            f"commit them before rebasing onto {remote_ref}",
        )

    rebased = _git(repo, "rebase", remote_ref)
    if rebased.returncode == 0:
        return SyncBaseResult(
            SyncStatus.REBASED,
            base_ref,
            remote_ref,
            branch,
            f"rebased {branch} onto {remote_ref}",
            preservation=_build_preservation(
                repo,
                old_base_oid=old_base_oid,
                new_base_oid=new_base_oid,
                old_head_oid=old_head_oid,
                new_head_oid=_rev(repo, "HEAD"),
            ),
        )

    conflict_details = _build_conflict_details(
        repo,
        old_base_oid=old_base_oid,
        new_base_oid=new_base_oid,
        old_head_oid=old_head_oid,
        git_output="\n".join(
            part for part in (rebased.stdout.strip(), rebased.stderr.strip()) if part
        ),
    )
    return SyncBaseResult(
        SyncStatus.CONFLICT,
        base_ref,
        remote_ref,
        branch,
        f"rebase of {branch} onto {remote_ref} stopped with active conflicts",
        conflict=conflict_details,
    )


def main(argv: list[str] | None = None) -> int:
    """CLI entry point: synchronize and print the result as JSON."""
    parser = argparse.ArgumentParser(
        description="Rebase the current branch onto its fetched base.",
    )
    parser.add_argument(
        "repo",
        nargs="?",
        default=".",
        help="Repository working tree (default: current directory).",
    )
    parser.add_argument(
        "--base",
        default=None,
        help="Bare base-branch name to sync onto (default: resolved from origin/HEAD).",
    )
    parser.add_argument(
        "--no-fetch",
        action="store_true",
        help="Skip fetching the base; use the existing remote-tracking ref.",
    )
    args = parser.parse_args(argv)
    result = sync_base(
        pathlib.Path(args.repo).resolve(),
        base_ref=args.base,
        fetch=not args.no_fetch,
    )
    print(json.dumps(result.to_json_dict()))
    return result.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
