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

A branch stacked on a predecessor branch carries a stack record in git
configuration — ``branch.<name>.stackPredecessor`` and ``branch.<name>.stackTip``
— written from git facts at the moments the relation is knowable: when a
rebase rewrites a branch, every local branch containing the pre-rebase head
receives a record naming the rewritten branch and that head; when a caller
supplies a non-default ``--base``, the synchronized branch receives a record
naming that base. A later sync of a recorded branch takes the predecessor as
its base and resolves the predecessor's state: open and containing the
recorded tip is an ordinary rebase onto it; open and rewritten replays only
the commits above the recorded tip onto it; merged into the default branch
(or absent from origin with no surviving local branch) replays only the
commits above the recorded tip onto ``origin/<default>`` and clears the
record. An unpublished predecessor — absent from origin while its local branch
survives unmerged — stands in through that local branch. A branch with no
record derives a predecessor from local topology by the nearest-fork rule: among
the local branches that forked from the default before the branch forked from
them, the one whose fork descends from every other candidate's is recorded;
unordered candidates yield no predecessor and no record.

The base ref and its remote-tracking form are resolved through the shared
changeset-scope primitives, never re-derived here. The primitives ship under a
runtime-substituted plugin skill directory and are not importable by package
name, so they are loaded through ``importlib`` and re-exported with object
identity preserved.
"""

from __future__ import annotations

import argparse
import dataclasses
import hashlib
import importlib.util
import json
import pathlib
import subprocess
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum
from types import ModuleType
from typing import Literal, Protocol

_CHANGESET_SCOPE_PATH = (
    pathlib.Path(__file__).resolve().parent.parent.parent
    / "scope-changeset"
    / "scripts"
    / "changeset_scope.py"
)

CONFLICT_SUMMARY = "Base sync stopped: rebase conflict requires reconciliation"
# ``git config --unset`` exits 5 when the key is absent; an absent key is not a failed removal.
CONFIG_KEY_ABSENT_EXIT = 5
CONFLICT_INSPECT_STATUS = "git status"
CONFLICT_INSPECT_DIFF = "git diff"
CONFLICT_INSPECT_STAGES = "git ls-files -u"
CONFLICT_CONTINUE = "git add <resolved-paths> && git rebase --continue"
CONFLICT_ABORT = "git rebase --abort"
#: Placeholder the operator replaces with the fork commit in the restack option.
RESTACK_FORK_PLACEHOLDER = "<fork>"

#: Branch-configuration keys of the stack record, under ``branch.<name>.``.
STACK_PREDECESSOR_KEY = "stackPredecessor"
STACK_TIP_KEY = "stackTip"

#: Schema version of the readiness-preservation proof embedded in the result.
READINESS_SCHEMA_VERSION = 2


def stack_config_key(branch: str, key: str) -> str:
    """Return the git-configuration key of one stack-record field for ``branch``."""
    return f"branch.{branch}.{key}"


def restack_operator_option(remote_ref: str) -> str:
    """Return the restack form an operator names a fork for after a conflict."""
    return f"git rebase --onto {remote_ref} {RESTACK_FORK_PLACEHOLDER}"


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


class GitRunner(Protocol):
    """Execute one git command through an injectable process boundary.

    ``subprocess.run`` satisfies this protocol and is the default runner. The
    shape matches the changeset-scope ``Runner`` protocol so one injected runner
    serves both the synchronizer's own git calls and the shared primitives it
    reaches; ``input`` carries the diff ``git patch-id`` reads from stdin.
    """

    def __call__(
        self,
        argv: Sequence[str],
        /,
        *,
        cwd: pathlib.Path,
        capture_output: bool,
        text: Literal[True],
        check: bool,
        input: str | None = None,  # noqa: A002 — subprocess.run's parameter name
    ) -> subprocess.CompletedProcess[str]: ...


@dataclass(frozen=True)
class _Repository:
    """A working tree together with the runner every git call goes through."""

    path: pathlib.Path
    runner: GitRunner


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
class StackRecord:
    """The stack relation a branch carries in its git configuration.

    ``predecessor`` is the branch this branch is stacked on; ``tip`` is the full
    OID of the predecessor commit this branch last sat on — the bound between
    the predecessor's commits and the branch's own.
    """

    predecessor: str
    tip: str


def read_stack_record(
    repo: pathlib.Path, branch: str, *, runner: GitRunner = subprocess.run
) -> StackRecord | None:
    """Return ``branch``'s stack record, or ``None`` when either key is absent."""
    return _read_stack_record(_Repository(repo, runner), branch)


def write_stack_record(
    repo: pathlib.Path,
    branch: str,
    record: StackRecord,
    *,
    runner: GitRunner = subprocess.run,
) -> None:
    """Write both stack-record keys for ``branch``."""
    _write_stack_record(_Repository(repo, runner), branch, record)


def _read_stack_record(repo: _Repository, branch: str) -> StackRecord | None:
    predecessor = _git(
        repo, "config", "--get", stack_config_key(branch, STACK_PREDECESSOR_KEY)
    )
    tip = _git(repo, "config", "--get", stack_config_key(branch, STACK_TIP_KEY))
    if predecessor.returncode != 0 or tip.returncode != 0:
        return None
    predecessor_name = predecessor.stdout.strip()
    tip_oid = tip.stdout.strip()
    if not predecessor_name or not tip_oid:
        return None
    return StackRecord(predecessor=predecessor_name, tip=tip_oid)


class StackRecordError(RuntimeError):
    """A stack-record write or removal failed after git reported it.

    Raised by the record writers and converted by :func:`sync_base` into a
    ``git_failure`` result naming the failed mutation, so a sync never reports
    a record the repository does not carry.
    """

    def __init__(self, branch: str, detail: str) -> None:
        super().__init__(detail)
        self.branch = branch
        self.detail = detail


def _write_stack_record(repo: _Repository, branch: str, record: StackRecord) -> None:
    for key, value in (
        (STACK_PREDECESSOR_KEY, record.predecessor),
        (STACK_TIP_KEY, record.tip),
    ):
        config_key = stack_config_key(branch, key)
        written = _git(repo, "config", config_key, value)
        if written.returncode != 0:
            raise StackRecordError(
                branch,
                f"stack record write failed: git config {config_key} exited "
                f"{written.returncode}: {written.stderr.strip()}",
            )


def _clear_stack_record(repo: _Repository, branch: str) -> None:
    for key in (STACK_PREDECESSOR_KEY, STACK_TIP_KEY):
        config_key = stack_config_key(branch, key)
        cleared = _git(repo, "config", "--unset", config_key)
        if cleared.returncode not in (0, CONFIG_KEY_ABSENT_EXIT):
            raise StackRecordError(
                branch,
                f"stack record removal failed: git config --unset {config_key} "
                f"exited {cleared.returncode}: {cleared.stderr.strip()}",
            )


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
    ``branch_diff_unchanged`` is ``False``. ``stack_predecessor``,
    ``stack_tip_before``, and ``stack_tip_after`` carry the stack record the
    sync read and wrote — ``stack_tip_after`` is ``None`` once a restack onto the
    default branch cleared it — and are all ``None`` for a branch with no stack.

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
    stack_predecessor: str | None = None
    stack_tip_before: str | None = None
    stack_tip_after: str | None = None

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
            "stack_predecessor": self.stack_predecessor,
            "stack_tip_before": self.stack_tip_before,
            "stack_tip_after": self.stack_tip_after,
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
    repo: _Repository, *args: str, stdin: str | None = None
) -> subprocess.CompletedProcess[str]:
    """Run a git command in ``repo`` through its runner, capturing output without raising."""
    return repo.runner(
        ["git", *args],
        cwd=repo.path,
        input=stdin,
        capture_output=True,
        text=True,
        check=False,
    )


def _rev(repo: _Repository, ref: str) -> str | None:
    """Resolve ``ref`` to a full OID, or ``None`` when it does not resolve."""
    result = _git(repo, "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}")
    oid = result.stdout.strip()
    return oid if result.returncode == 0 and oid else None


def _merge_base(repo: _Repository, a: str, b: str) -> str | None:
    """Return the merge-base OID of ``a`` and ``b``, or ``None`` when none exists."""
    result = _git(repo, "merge-base", a, b)
    oid = result.stdout.strip()
    return oid if result.returncode == 0 and oid else None


def _is_ancestor(repo: _Repository, ancestor: str, descendant: str) -> bool:
    """Return whether ``ancestor`` is reachable from ``descendant``."""
    return (
        _git(repo, "merge-base", "--is-ancestor", ancestor, descendant).returncode == 0
    )


def _local_branches(repo: _Repository) -> list[str]:
    """Return the short names of every ref under ``refs/heads/``."""
    listed = _git(repo, "for-each-ref", "--format=%(refname:short)", "refs/heads/")
    if listed.returncode != 0:
        return []
    return [name for name in listed.stdout.split() if name]


def _write_dependent_records(repo: _Repository, branch: str, old_head_oid: str) -> None:
    """Record ``branch`` and its pre-rebase head on every local branch stacked on it.

    A local branch that contains the pre-rebase head sat on it. A dependent that
    already records a different predecessor keeps that record: its own
    restack flows through that nearer predecessor when that one is rewritten.
    """
    for dependent in _local_branches(repo):
        if dependent == branch or not _is_ancestor(repo, old_head_oid, dependent):
            continue
        existing = _read_stack_record(repo, dependent)
        if existing is not None and existing.predecessor != branch:
            continue
        _write_stack_record(
            repo, dependent, StackRecord(predecessor=branch, tip=old_head_oid)
        )


def _diff_paths(repo: _Repository, spec: str) -> list[str] | None:
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


def _conflicted_paths(repo: _Repository) -> list[str]:
    """Return sorted paths with unmerged index entries in the active conflict."""
    result = _git(repo, "diff", "--name-only", "--diff-filter=U")
    if result.returncode != 0:
        return []
    return sorted(p for p in result.stdout.splitlines() if p)


def _patch_id(repo: _Repository, base: str, head: str) -> str | None:
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
    repo: _Repository,
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
    repo: _Repository,
    *,
    remote_ref: str,
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
            restack_operator_option(remote_ref),
            CONFLICT_ABORT,
        ],
    )


def _sync_detached(
    repo: _Repository,
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


def _resolve_default_base(repo: _Repository) -> str | SyncBaseResult:
    try:
        return detect_base_ref(repo.path, runner=repo.runner)
    except BaseRefNotConfiguredError as exc:
        return SyncBaseResult(
            SyncStatus.GIT_FAILURE,
            "",
            "",
            None,
            str(exc),
        )


def _with_stack(
    result: SyncBaseResult,
    *,
    predecessor: str,
    tip_before: str | None,
    tip_after: str | None,
) -> SyncBaseResult:
    """Return ``result`` with the stack facts carried in its preservation proof."""
    if result.preservation is None:
        return result
    return dataclasses.replace(
        result,
        preservation=dataclasses.replace(
            result.preservation,
            stack_predecessor=predecessor,
            stack_tip_before=tip_before,
            stack_tip_after=tip_after,
        ),
    )


def sync_base(
    repo: pathlib.Path,
    *,
    base_ref: str | None = None,
    fetch: bool = True,
    runner: GitRunner = subprocess.run,
) -> SyncBaseResult:
    """Bring ``repo``'s current branch current with its fetched base.

    ``base_ref`` is the bare base-branch name to synchronize onto. When omitted,
    a branch carrying a stack record — or one whose predecessor local topology
    derives — synchronizes against that predecessor by its recorded state, and
    every other branch synchronizes onto the default base resolved from
    ``origin/HEAD`` through the shared changeset-scope primitives. A caller that
    tracks a non-default base passes it explicitly; the synchronized branch then
    records that base as its predecessor. The base is fetched (unless
    ``fetch=False``) and the branch is rebased onto it when it is behind.
    ``runner`` is the process boundary every git command goes through;
    ``subprocess.run`` is the default and a controlled implementation may be
    injected. Returns a :class:`SyncBaseResult`; never raises for an ordinary
    git outcome.
    """
    repository = _Repository(repo, runner)
    try:
        return _sync(repository, base_ref=base_ref, fetch=fetch)
    except StackRecordError as error:
        return _record_failure(repository, base_ref, error)


def _record_failure(
    repo: _Repository, base_ref: str | None, error: StackRecordError
) -> SyncBaseResult:
    """Report a failed stack-record mutation as a ``git_failure`` result."""
    base = base_ref
    if base is None:
        default = _resolve_default_base(repo)
        base = default if isinstance(default, str) else default.base_ref
    remote_ref = remote_tracking_ref(base) if base else base
    return SyncBaseResult(
        SyncStatus.GIT_FAILURE, base, remote_ref, error.branch, error.detail
    )


def _sync(repo: _Repository, *, base_ref: str | None, fetch: bool) -> SyncBaseResult:
    default = _resolve_default_base(repo)
    default_name = default if isinstance(default, str) else None

    try:
        branch = detect_current_branch(repo.path, runner=repo.runner)
    except DetachedHeadError:
        if base_ref is None:
            if isinstance(default, SyncBaseResult):
                return default
            base_ref = default
        return _sync_detached(
            repo, base_ref, remote_tracking_ref(base_ref), fetch=fetch
        )

    if base_ref is not None:
        record = _read_stack_record(repo, branch)
        result = _sync_branch_onto(
            repo, branch, base_ref, remote_tracking_ref(base_ref), fetch=fetch
        )
        new_base_oid = (
            result.preservation.new_base_oid
            if result.preservation is not None
            else None
        )
        if (
            result.status in (SyncStatus.REBASED, SyncStatus.ALREADY_CURRENT)
            and default_name is not None
            and base_ref != default_name
            and new_base_oid is not None
        ):
            _write_stack_record(
                repo, branch, StackRecord(predecessor=base_ref, tip=new_base_oid)
            )
            return _with_stack(
                result,
                predecessor=base_ref,
                tip_before=record.tip if record is not None else None,
                tip_after=new_base_oid,
            )
        return result

    if isinstance(default, SyncBaseResult):
        return default
    record = _read_stack_record(repo, branch)
    if record is None:
        record = _derive_predecessor(repo, branch, default)
    if record is not None:
        return _sync_stacked(repo, branch, record, default, fetch=fetch)
    return _sync_branch_onto(
        repo, branch, default, remote_tracking_ref(default), fetch=fetch
    )


def _derive_predecessor(
    repo: _Repository, branch: str, default_name: str
) -> StackRecord | None:
    """Derive and record ``branch``'s predecessor from local topology, or ``None``.

    A candidate is a local branch other than ``branch`` and the default branch
    that does not contain HEAD and whose merge-base with HEAD lies strictly
    above HEAD's merge-base with ``origin/<default>``: ``branch`` forked from it
    after it forked from the default. The candidate whose merge-base descends
    from every other candidate's is the predecessor; unordered candidates yield
    none, and no record is written.
    """
    head = _rev(repo, "HEAD")
    default_fork = _merge_base(repo, "HEAD", remote_tracking_ref(default_name))
    if head is None or default_fork is None:
        return None
    candidates: list[tuple[str, str]] = []
    for name in _local_branches(repo):
        if name in (branch, default_name) or _is_ancestor(repo, head, name):
            continue
        fork = _merge_base(repo, "HEAD", name)
        if (
            fork is None
            or fork == default_fork
            or not _is_ancestor(repo, default_fork, fork)
        ):
            continue
        candidates.append((name, fork))
    winners = [
        candidate
        for candidate in candidates
        if all(
            _is_ancestor(repo, other_fork, candidate[1]) for _, other_fork in candidates
        )
    ]
    if len(winners) != 1:
        return None
    name, fork = winners[0]
    record = StackRecord(predecessor=name, tip=fork)
    _write_stack_record(repo, branch, record)
    return record


def _sync_stacked(
    repo: _Repository,
    branch: str,
    record: StackRecord,
    default_name: str,
    *,
    fetch: bool,
) -> SyncBaseResult:
    """Synchronize a recorded branch against its predecessor's current state.

    After a pruning fetch, ``origin/<predecessor>`` decides the state: present
    and containing the recorded tip is an ordinary behind-base rebase onto it;
    present without the recorded tip is a restack from the recorded tip onto it;
    absent with a surviving unmerged local predecessor is the same two states
    through that local branch; absent with no such branch, or reachable from
    ``origin/<default>``, is merged — a restack from the recorded tip onto the
    default, after which the record is removed.
    """
    default_remote = remote_tracking_ref(default_name)
    predecessor_remote = remote_tracking_ref(record.predecessor)

    if fetch:
        fetched = _git(repo, "fetch", "--prune", "origin")
        if fetched.returncode != 0:
            return SyncBaseResult(
                SyncStatus.GIT_FAILURE,
                record.predecessor,
                predecessor_remote,
                branch,
                f"git fetch --prune origin failed: {fetched.stderr.strip()}",
            )

    default_oid = _rev(repo, default_remote)
    if default_oid is None:
        return SyncBaseResult(
            SyncStatus.GIT_FAILURE,
            default_name,
            default_remote,
            branch,
            f"base ref {default_remote} does not resolve to a commit",
        )

    target_ref = predecessor_remote
    predecessor_oid = _rev(repo, predecessor_remote)
    if predecessor_oid is None:
        local_oid = _rev(repo, f"refs/heads/{record.predecessor}")
        if local_oid is not None and not _is_ancestor(repo, local_oid, default_oid):
            # Unpublished predecessor: its local branch stands in for the
            # remote-tracking ref so the stack is never collapsed onto the
            # default without the commits it depends on.
            target_ref = record.predecessor
            predecessor_oid = local_oid

    if predecessor_oid is None or _is_ancestor(repo, predecessor_oid, default_oid):
        result = _restack(
            repo,
            branch,
            base_ref=default_name,
            target_ref=default_remote,
            target_oid=default_oid,
            fork_oid=record.tip,
        )
        if result.status in (SyncStatus.REBASED, SyncStatus.ALREADY_CURRENT):
            _clear_stack_record(repo, branch)
        return _with_stack(
            result,
            predecessor=record.predecessor,
            tip_before=record.tip,
            tip_after=None,
        )

    if _is_ancestor(repo, record.tip, predecessor_oid):
        result = _sync_branch_onto(
            repo, branch, record.predecessor, target_ref, fetch=False
        )
    else:
        result = _restack(
            repo,
            branch,
            base_ref=record.predecessor,
            target_ref=target_ref,
            target_oid=predecessor_oid,
            fork_oid=record.tip,
        )
    if result.status in (SyncStatus.REBASED, SyncStatus.ALREADY_CURRENT):
        _write_stack_record(
            repo,
            branch,
            StackRecord(predecessor=record.predecessor, tip=predecessor_oid),
        )
    return _with_stack(
        result,
        predecessor=record.predecessor,
        tip_before=record.tip,
        tip_after=predecessor_oid,
    )


def _dirty_tree(repo: _Repository) -> subprocess.CompletedProcess[str]:
    """Report uncommitted changes to tracked files; untracked files are excluded."""
    return _git(repo, "status", "--porcelain", "--untracked-files=no")


def _restack(
    repo: _Repository,
    branch: str,
    *,
    base_ref: str,
    target_ref: str,
    target_oid: str,
    fork_oid: str,
) -> SyncBaseResult:
    """Replay only the commits above ``fork_oid`` onto ``target_ref``.

    ``fork_oid`` is the recorded predecessor tip that bounds the branch's own
    commits. The movement is ``git rebase --onto``, a rebase of those commits;
    the preservation proof names ``fork_oid`` as the old base.
    """
    old_head_oid = _rev(repo, "HEAD")
    if old_head_oid is None or not _is_ancestor(repo, fork_oid, old_head_oid):
        return SyncBaseResult(
            SyncStatus.GIT_FAILURE,
            base_ref,
            target_ref,
            branch,
            f"recorded stack tip {fork_oid} is not an ancestor of {branch}; the "
            f"record does not describe this branch",
        )

    if _is_ancestor(repo, target_oid, old_head_oid):
        return SyncBaseResult(
            SyncStatus.ALREADY_CURRENT,
            base_ref,
            target_ref,
            branch,
            f"branch {branch} is already current with {target_ref}",
            preservation=_build_preservation(
                repo,
                old_base_oid=_merge_base(repo, old_head_oid, target_oid),
                new_base_oid=target_oid,
                old_head_oid=old_head_oid,
                new_head_oid=old_head_oid,
            ),
        )

    dirty = _dirty_tree(repo)
    if dirty.returncode != 0:
        return SyncBaseResult(
            SyncStatus.GIT_FAILURE,
            base_ref,
            target_ref,
            branch,
            f"cannot inspect working tree state: {dirty.stderr.strip()}",
        )
    if dirty.stdout.strip():
        return SyncBaseResult(
            SyncStatus.DIRTY_TREE,
            base_ref,
            target_ref,
            branch,
            f"working tree of {branch} has uncommitted changes to tracked files; "
            f"commit them before restacking onto {target_ref}",
        )

    rebased = _git(repo, "rebase", "--onto", target_ref, fork_oid)
    if rebased.returncode == 0:
        _write_dependent_records(repo, branch, old_head_oid)
        return SyncBaseResult(
            SyncStatus.REBASED,
            base_ref,
            target_ref,
            branch,
            f"restacked {branch} onto {target_ref} from {fork_oid}",
            preservation=_build_preservation(
                repo,
                old_base_oid=fork_oid,
                new_base_oid=target_oid,
                old_head_oid=old_head_oid,
                new_head_oid=_rev(repo, "HEAD"),
            ),
        )
    return SyncBaseResult(
        SyncStatus.CONFLICT,
        base_ref,
        target_ref,
        branch,
        f"restack of {branch} onto {target_ref} stopped with active conflicts",
        conflict=_build_conflict_details(
            repo,
            remote_ref=target_ref,
            old_base_oid=fork_oid,
            new_base_oid=target_oid,
            old_head_oid=old_head_oid,
            git_output=_combined_output(rebased),
        ),
    )


def _combined_output(completed: subprocess.CompletedProcess[str]) -> str:
    """Join stdout and stderr, because git splits a conflict summary across them."""
    return "\n".join(
        part for part in (completed.stdout.strip(), completed.stderr.strip()) if part
    )


def _sync_branch_onto(
    repo: _Repository,
    branch: str,
    base_ref: str,
    target_ref: str,
    *,
    fetch: bool,
) -> SyncBaseResult:
    """Bring ``branch`` current with ``target_ref`` by an ordinary rebase.

    ``base_ref`` is the bare base-branch name and ``target_ref`` the ref the
    branch rebases onto — its remote-tracking form for a fetched base, or the
    local branch of an unpublished predecessor.
    """
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
                target_ref,
                branch,
                f"git fetch origin {base_ref} failed: {fetched.stderr.strip()}",
            )

    new_base_oid = _rev(repo, target_ref)
    if new_base_oid is None:
        return SyncBaseResult(
            SyncStatus.GIT_FAILURE,
            base_ref,
            target_ref,
            branch,
            f"base ref {target_ref} does not resolve to a commit",
        )

    behind = _git(repo, "rev-list", "--count", f"HEAD..{target_ref}")
    if behind.returncode != 0:
        return SyncBaseResult(
            SyncStatus.GIT_FAILURE,
            base_ref,
            target_ref,
            branch,
            f"cannot compute commits behind {target_ref}: {behind.stderr.strip()}",
        )
    # Anchor the base delta at the branch's fork point from the base — the
    # merge-base of the pre-rebase HEAD and the current base. This is stable
    # whether or not the caller pre-fetched, where the pre-fetch remote ref would
    # already equal the post-fetch base and report an empty base delta.
    old_base_oid = (
        _merge_base(repo, old_head_oid, new_base_oid) if old_head_oid else None
    )
    if int(behind.stdout.strip() or "0") == 0:
        return SyncBaseResult(
            SyncStatus.ALREADY_CURRENT,
            base_ref,
            target_ref,
            branch,
            f"branch {branch} is already current with {target_ref}",
            preservation=_build_preservation(
                repo,
                old_base_oid=old_base_oid,
                new_base_oid=new_base_oid,
                old_head_oid=old_head_oid,
                new_head_oid=old_head_oid,
            ),
        )

    # precondition: git refuses to replay over uncommitted tracked changes; untracked excluded
    dirty = _dirty_tree(repo)
    if dirty.returncode != 0:
        return SyncBaseResult(
            SyncStatus.GIT_FAILURE,
            base_ref,
            target_ref,
            branch,
            f"cannot inspect working tree state: {dirty.stderr.strip()}",
        )
    if dirty.stdout.strip():
        return SyncBaseResult(
            SyncStatus.DIRTY_TREE,
            base_ref,
            target_ref,
            branch,
            f"working tree of {branch} has uncommitted changes to tracked files; "
            f"commit them before rebasing onto {target_ref}",
        )

    rebased = _git(repo, "rebase", target_ref)
    if rebased.returncode == 0:
        if old_head_oid is not None:
            _write_dependent_records(repo, branch, old_head_oid)
        return SyncBaseResult(
            SyncStatus.REBASED,
            base_ref,
            target_ref,
            branch,
            f"rebased {branch} onto {target_ref}",
            preservation=_build_preservation(
                repo,
                old_base_oid=old_base_oid,
                new_base_oid=new_base_oid,
                old_head_oid=old_head_oid,
                new_head_oid=_rev(repo, "HEAD"),
            ),
        )

    return SyncBaseResult(
        SyncStatus.CONFLICT,
        base_ref,
        target_ref,
        branch,
        f"rebase of {branch} onto {target_ref} stopped with active conflicts",
        conflict=_build_conflict_details(
            repo,
            remote_ref=target_ref,
            old_base_oid=old_base_oid,
            new_base_oid=new_base_oid,
            old_head_oid=old_head_oid,
            git_output=_combined_output(rebased),
        ),
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
        runner=subprocess.run,
    )
    print(json.dumps(result.to_json_dict()))
    return result.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
