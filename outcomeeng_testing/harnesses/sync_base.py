"""Real Git lifecycle and observations for synchronization evidence."""

from __future__ import annotations

import importlib.util
import os
import pathlib
import subprocess
import sys
from dataclasses import dataclass
from tempfile import mkdtemp
from types import ModuleType

from outcomeeng_testing.generators.sync_base import (
    RepositoryDomain,
    TrackedEdit,
    repository_domain,
)

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
SYNC_BASE_MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "plugins"
    / "spec-tree"
    / "skills"
    / "sync-base"
    / "scripts"
    / "sync_base.py"
)


def repository_root(tmp_path: pathlib.Path) -> pathlib.Path:
    """Allocate a unique root beneath pytest's cleanup-owned directory."""
    return pathlib.Path(mkdtemp(dir=tmp_path))


def load_sync_base_module() -> ModuleType:
    """Load the ``sync_base`` module via importlib and cache it."""
    cached = sys.modules.get("sync_base")
    if cached is not None:
        return cached
    spec = importlib.util.spec_from_file_location("sync_base", SYNC_BASE_MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load sync_base from {SYNC_BASE_MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["sync_base"] = module
    spec.loader.exec_module(module)
    return module


def _git(repo: pathlib.Path, *args: str, cwd: pathlib.Path | None = None) -> str:
    """Run a git command with isolated config and fixed identity.

    Global and system config are suppressed so the harness does not inherit
    operator settings; a fixed identity and disabled signing make commits and
    rebases deterministic on any machine.
    """
    env = {
        **os.environ,
        "GIT_CONFIG_GLOBAL": "/dev/null",
        "GIT_CONFIG_SYSTEM": "/dev/null",
        "GIT_AUTHOR_NAME": "test",
        "GIT_AUTHOR_EMAIL": "test@example.invalid",
        "GIT_COMMITTER_NAME": "test",
        "GIT_COMMITTER_EMAIL": "test@example.invalid",
    }
    result = subprocess.run(  # noqa: S603 — fixed argv, no shell, args from the harness
        ["git", *args],  # noqa: S607
        cwd=cwd if cwd is not None else repo,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def _configure(repo: pathlib.Path) -> None:
    """Pin identity and disable signing as repo-local config.

    ``sync_base`` runs plain ``git`` without the harness's injected environment,
    so the repository itself must carry a committer identity and disabled
    signing for an in-process rebase to succeed.
    """
    _git(repo, "config", "user.name", "test")
    _git(repo, "config", "user.email", "test@example.invalid")
    _git(repo, "config", "commit.gpgsign", "false")


def _commit_file(repo: pathlib.Path, name: str, content: str, message: str) -> None:
    (repo / name).write_text(content, encoding="utf-8")
    _git(repo, "add", name)
    _git(repo, "commit", "-q", "-m", message)


def _init_origin_with_base(root: pathlib.Path, data: RepositoryDomain) -> pathlib.Path:
    """Create a bare origin seeded with an initial base commit; return its path.

    A ``pusher`` clone seeds the generated base branch and default HEAD, then
    remains available to advance the base out of band.
    """
    origin = root / "origin.git"
    _git(root, "init", "--bare", "-b", data.base_branch, str(origin), cwd=root)
    pusher = root / "pusher"
    _git(root, "clone", "-q", str(origin), str(pusher), cwd=root)
    _configure(pusher)
    _commit_file(pusher, data.initial_file, data.initial_content, data.initial_message)
    _git(pusher, "push", "-q", "origin", data.base_branch)
    return origin


def _working_clone_on_feature(
    root: pathlib.Path, origin: pathlib.Path, data: RepositoryDomain
) -> pathlib.Path:
    """Clone ``origin`` into ``repo`` and cut the feature branch off the base."""
    repo = root / "repo"
    _git(root, "clone", "-q", str(origin), str(repo), cwd=root)
    _configure(repo)
    _git(repo, "remote", "set-head", "origin", data.base_branch)
    _git(repo, "switch", "-q", "-c", data.feature_branch)
    return repo


@dataclass(frozen=True)
class BehindBaseRepo:
    """A working clone behind ``origin/<base>`` by one base commit.

    ``feature_file`` is the feature branch's own commit; ``base_file`` is the
    commit pushed to the base after the feature branched. The working clone has
    not fetched the base advance, so it is behind until ``sync_base`` fetches.
    """

    repo: pathlib.Path
    base_ref: str
    remote_ref: str
    feature_branch: str
    feature_file: str
    base_file: str
    feature_commit_message: str
    data: RepositoryDomain


def build_behind_base_repo(root: pathlib.Path) -> BehindBaseRepo:
    """Build a working clone behind its base by a not-yet-fetched base commit."""
    data = repository_domain()
    origin = _init_origin_with_base(root, data)
    repo = _working_clone_on_feature(root, origin, data)
    _commit_file(repo, data.feature_file, data.feature_content, data.feature_message)

    pusher = root / "pusher"
    _commit_file(pusher, data.base_file, data.base_content, data.base_message)
    _git(pusher, "push", "-q", "origin", data.base_branch)

    return BehindBaseRepo(
        repo=repo,
        base_ref=data.base_branch,
        remote_ref=f"origin/{data.base_branch}",
        feature_branch=data.feature_branch,
        feature_file=data.feature_file,
        base_file=data.base_file,
        feature_commit_message=data.feature_message,
        data=data,
    )


@dataclass(frozen=True)
class DirtyBehindBaseRepo:
    """A working clone behind ``origin/<base>`` with an uncommitted tracked edit.

    ``dirty_file`` is a tracked file carrying an uncommitted modification, so
    ``git rebase`` refuses to start. ``dirty_marker`` is the appended content the
    test asserts survives untouched. ``base_file`` is the base advance that would
    only enter the working tree if a rebase ran — its absence proves none did.
    """

    repo: pathlib.Path
    base_ref: str
    remote_ref: str
    feature_branch: str
    dirty_file: str
    dirty_marker: str
    base_file: str


def build_dirty_behind_base_repo(
    root: pathlib.Path, *, edit: TrackedEdit
) -> DirtyBehindBaseRepo:
    """Build a behind-base working clone with an uncommitted change to a tracked file.

    A staged edit runs ``git add`` without committing, so the
    dirty state is staged-but-uncommitted rather than unstaged. Both forms block
    a rebase and both must report ``dirty_tree``; ``git status --porcelain
    --untracked-files=no`` reports either.
    """
    behind = build_behind_base_repo(root)
    dirty_path = behind.repo / behind.feature_file
    dirty_path.write_text(
        dirty_path.read_text(encoding="utf-8") + edit.content, encoding="utf-8"
    )
    if edit.staged:
        _git(behind.repo, "add", behind.feature_file)
    return DirtyBehindBaseRepo(
        repo=behind.repo,
        base_ref=behind.base_ref,
        remote_ref=behind.remote_ref,
        feature_branch=behind.feature_branch,
        dirty_file=behind.feature_file,
        dirty_marker=edit.content,
        base_file=behind.base_file,
    )


@dataclass(frozen=True)
class AlternateBaseRepo:
    """A working clone current with the default base but behind an alternate base.

    ``default_ref`` is ``origin/HEAD``; the feature contains every commit on it.
    ``alternate_ref`` is a second pushed branch advanced past the feature's fork
    point and not yet fetched by the working clone, so synchronizing onto it
    rebases while synchronizing onto the default does nothing — proving a
    caller-supplied base targets that base, not ``origin/HEAD``.
    """

    repo: pathlib.Path
    default_ref: str
    alternate_ref: str
    alternate_remote_ref: str
    feature_branch: str
    feature_file: str
    alternate_file: str


def build_alternate_base_repo(root: pathlib.Path) -> AlternateBaseRepo:
    """Build a working clone current with the default base but behind an alternate."""
    data = repository_domain()
    origin = _init_origin_with_base(root, data)
    pusher = root / "pusher"
    _git(pusher, "switch", "-q", "-c", data.alternate_branch)
    _git(pusher, "push", "-q", "origin", data.alternate_branch)

    repo = _working_clone_on_feature(root, origin, data)
    _commit_file(repo, data.feature_file, data.feature_content, data.feature_message)

    _git(pusher, "switch", "-q", data.alternate_branch)
    _commit_file(
        pusher, data.alternate_file, data.alternate_content, data.alternate_message
    )
    _git(pusher, "push", "-q", "origin", data.alternate_branch)

    return AlternateBaseRepo(
        repo=repo,
        default_ref=data.base_branch,
        alternate_ref=data.alternate_branch,
        alternate_remote_ref=f"origin/{data.alternate_branch}",
        feature_branch=data.feature_branch,
        feature_file=data.feature_file,
        alternate_file=data.alternate_file,
    )


@dataclass(frozen=True)
class CurrentRepo:
    """A working clone whose feature branch already contains every base commit."""

    repo: pathlib.Path
    base_ref: str
    remote_ref: str
    feature_branch: str
    missing_branch: str


def build_current_repo(root: pathlib.Path) -> CurrentRepo:
    """Build a working clone already current with its base (no base advance)."""
    data = repository_domain()
    origin = _init_origin_with_base(root, data)
    repo = _working_clone_on_feature(root, origin, data)
    _commit_file(repo, data.feature_file, data.feature_content, data.feature_message)
    return CurrentRepo(
        repo=repo,
        base_ref=data.base_branch,
        remote_ref=f"origin/{data.base_branch}",
        feature_branch=data.feature_branch,
        missing_branch=data.missing_branch,
    )


@dataclass(frozen=True)
class ConflictRepo:
    """A working clone whose feature and advanced base edit the same file."""

    repo: pathlib.Path
    base_ref: str
    remote_ref: str
    feature_branch: str
    conflict_file: str


def build_conflicting_repo(root: pathlib.Path) -> ConflictRepo:
    """Build a working clone whose rebase onto the advanced base conflicts."""
    data = repository_domain()
    origin = _init_origin_with_base(root, data)
    repo = _working_clone_on_feature(root, origin, data)
    _commit_file(repo, data.initial_file, data.feature_content, data.feature_message)

    pusher = root / "pusher"
    _commit_file(pusher, data.initial_file, data.base_content, data.base_message)
    _git(pusher, "push", "-q", "origin", data.base_branch)

    return ConflictRepo(
        repo=repo,
        base_ref=data.base_branch,
        remote_ref=f"origin/{data.base_branch}",
        feature_branch=data.feature_branch,
        conflict_file=data.initial_file,
    )


def build_untracked_only_behind_base_repo(root: pathlib.Path) -> BehindBaseRepo:
    """Build a behind-base clone whose only working-tree change is an untracked file.

    An untracked file (not ``git add``ed) does not block a rebase, so sync-base
    must rebase rather than report ``dirty_tree``. The untracked path does not
    collide with the base advance, so the replay proceeds and leaves it in place.
    Proves the ``--untracked-files=no`` scope of the dirty check is necessary:
    without it the untracked file would read as dirty and force ``dirty_tree``.
    """
    behind = build_behind_base_repo(root)
    (behind.repo / behind.data.untracked_file).write_text(
        behind.data.scratch_content, encoding="utf-8"
    )
    return behind


def fetch_base(repo: pathlib.Path, base_ref: str) -> None:
    """Fetch the base into ``repo`` to simulate a caller that pre-fetched.

    After this the working clone's ``origin/<base>`` already points at the
    advanced base, so a preservation proof that anchored the base delta at the
    pre-fetch remote ref would report an empty delta.
    """
    _git(repo, "fetch", "origin", base_ref)


def head_oid(repo: pathlib.Path) -> str:
    """Return the full OID ``HEAD`` resolves to in ``repo``."""
    return _git(repo, "rev-parse", "HEAD")


def resolve_ref(repo: pathlib.Path, ref: str) -> str:
    """Return the full OID ``ref`` resolves to in ``repo``."""
    return _git(repo, "rev-parse", ref)


def merge_base_oid(repo: pathlib.Path, ref: str) -> str:
    """Observe the complete shared ancestor object ID through Git."""
    return _git(repo, "merge-base", "HEAD", ref)


def working_tree_has_tracked_changes(repo: pathlib.Path) -> bool:
    """Report whether the working tree has uncommitted changes to tracked files.

    A non-empty ``git status --porcelain --untracked-files=no`` means a tracked
    file is modified or staged — the state that blocks a rebase. Proves an edit
    was neither committed (the tree would be clean) nor stashed (the edit gone).
    """
    return bool(_git(repo, "status", "--porcelain", "--untracked-files=no"))


@dataclass(frozen=True)
class OverlappingBaseRepo:
    """A behind-base clone where base and branch both edit one file, no conflict.

    The branch appends a line to ``overlap_file`` and the base prepends a
    different line to the same file, so the rebase auto-merges (distinct
    regions) and the base-delta paths overlap the branch's changed paths.
    """

    repo: pathlib.Path
    base_ref: str
    remote_ref: str
    feature_branch: str
    overlap_file: str


def build_overlapping_base_repo(root: pathlib.Path) -> OverlappingBaseRepo:
    """Build a behind-base clone whose base advance overlaps the branch's file."""
    data = repository_domain()
    origin = _init_origin_with_base(root, data)
    repo = _working_clone_on_feature(root, origin, data)
    _commit_file(
        repo,
        data.initial_file,
        data.initial_content + data.feature_content,
        data.feature_message,
    )

    pusher = root / "pusher"
    _commit_file(
        pusher,
        data.initial_file,
        data.base_content + data.initial_content,
        data.base_message,
    )
    _git(pusher, "push", "-q", "origin", data.base_branch)

    return OverlappingBaseRepo(
        repo=repo,
        base_ref=data.base_branch,
        remote_ref=f"origin/{data.base_branch}",
        feature_branch=data.feature_branch,
        overlap_file=data.initial_file,
    )


@dataclass(frozen=True)
class RenameBaseRepo:
    """A behind-base clone whose base advance renames a file the branch ignores.

    The base renames ``old_path`` to ``new_path``; the branch changes an
    unrelated file, so the rebase is clean. With ``--no-renames`` the base delta
    reports both the old and the new path, the property a caller relies on to
    catch a base rename of a path the branch also touched.
    """

    repo: pathlib.Path
    base_ref: str
    remote_ref: str
    feature_branch: str
    old_path: str
    new_path: str


def build_rename_base_repo(root: pathlib.Path) -> RenameBaseRepo:
    """Build a behind-base clone whose base advance is a rename."""
    data = repository_domain()
    origin = _init_origin_with_base(root, data)
    repo = _working_clone_on_feature(root, origin, data)
    _commit_file(repo, data.feature_file, data.feature_content, data.feature_message)

    pusher = root / "pusher"
    _git(pusher, "mv", data.initial_file, data.renamed_file)
    _git(pusher, "commit", "-q", "-m", data.rename_message)
    _git(pusher, "push", "-q", "origin", data.base_branch)

    return RenameBaseRepo(
        repo=repo,
        base_ref=data.base_branch,
        remote_ref=f"origin/{data.base_branch}",
        feature_branch=data.feature_branch,
        old_path=data.initial_file,
        new_path=data.renamed_file,
    )


def detach_head(repo: pathlib.Path) -> None:
    """Detach HEAD so the branch cannot be resolved for a rebase."""
    sha = _git(repo, "rev-parse", "HEAD")
    _git(repo, "checkout", "-q", "--detach", sha)


def _working_clone_detached_on_base(
    root: pathlib.Path, origin: pathlib.Path, data: RepositoryDomain
) -> pathlib.Path:
    """Clone ``origin`` into ``repo`` and park HEAD detached at the base tip.

    No feature branch is cut: HEAD is detached at the cloned base commit, the
    normal parked state of a free bare-repository pool worktree. The clone has
    not fetched any later base advance, so the detached commit is an ancestor of
    ``origin/<base>`` once the base moves on.
    """
    repo = root / "repo"
    _git(root, "clone", "-q", str(origin), str(repo), cwd=root)
    _configure(repo)
    _git(repo, "remote", "set-head", "origin", data.base_branch)
    sha = _git(repo, "rev-parse", "HEAD")
    _git(repo, "checkout", "-q", "--detach", sha)
    return repo


@dataclass(frozen=True)
class DetachedRepo:
    """A worktree with HEAD detached, used for the detached-base-sync cases.

    ``detached_oid`` is the commit HEAD is parked at. ``base_file`` is the base
    advance the worktree is behind by — present only when a base advance was
    pushed (``None`` for the already-current case). ``dirty_file`` and
    ``dirty_marker`` are populated only for the dirty case.
    """

    repo: pathlib.Path
    base_ref: str
    remote_ref: str
    detached_oid: str
    data: RepositoryDomain
    base_file: str | None = None
    dirty_file: str | None = None
    dirty_marker: str | None = None


def build_detached_behind_base_repo(root: pathlib.Path) -> DetachedRepo:
    """Build a clean detached worktree parked behind the advanced base.

    HEAD is detached at the cloned base commit; the base then advances out of
    band and the clone has not fetched it, so the detached commit is a strict
    ancestor of ``origin/<base>``. Synchronization must advance the worktree to
    the base tip and bring the base advance into the working tree.
    """
    data = repository_domain()
    origin = _init_origin_with_base(root, data)
    repo = _working_clone_detached_on_base(root, origin, data)
    detached_oid = _git(repo, "rev-parse", "HEAD")

    pusher = root / "pusher"
    _commit_file(pusher, data.base_file, data.base_content, data.base_message)
    _git(pusher, "push", "-q", "origin", data.base_branch)

    return DetachedRepo(
        repo=repo,
        base_ref=data.base_branch,
        remote_ref=f"origin/{data.base_branch}",
        detached_oid=detached_oid,
        data=data,
        base_file=data.base_file,
    )


def build_detached_current_repo(root: pathlib.Path) -> DetachedRepo:
    """Build a clean detached worktree parked at the base tip (no base advance).

    HEAD is detached at the base tip and no base advance follows, so after the
    fetch the detached commit equals ``origin/<base>`` and synchronization
    reports it already current without advancing.
    """
    data = repository_domain()
    origin = _init_origin_with_base(root, data)
    repo = _working_clone_detached_on_base(root, origin, data)
    return DetachedRepo(
        repo=repo,
        base_ref=data.base_branch,
        remote_ref=f"origin/{data.base_branch}",
        detached_oid=_git(repo, "rev-parse", "HEAD"),
        data=data,
    )


def build_detached_dirty_behind_base_repo(
    root: pathlib.Path, *, edit: TrackedEdit
) -> DetachedRepo:
    """Build a behind-base detached worktree with an uncommitted tracked edit.

    Same parked-behind state as ``build_detached_behind_base_repo``, plus an
    uncommitted modification to the tracked initial file, so the advance
    precondition fails and synchronization reports ``dirty_tree`` without moving
    the worktree.
    """
    behind = build_detached_behind_base_repo(root)
    data = behind.data
    dirty_path = behind.repo / data.initial_file
    dirty_path.write_text(
        dirty_path.read_text(encoding="utf-8") + edit.content, encoding="utf-8"
    )
    if edit.staged:
        _git(behind.repo, "add", data.initial_file)
    return DetachedRepo(
        repo=behind.repo,
        base_ref=behind.base_ref,
        remote_ref=behind.remote_ref,
        detached_oid=behind.detached_oid,
        data=data,
        base_file=behind.base_file,
        dirty_file=data.initial_file,
        dirty_marker=edit.content,
    )


def build_detached_untracked_only_behind_base_repo(
    root: pathlib.Path,
) -> DetachedRepo:
    """Build a behind-base detached worktree whose only change is an untracked file.

    Same parked-behind state as ``build_detached_behind_base_repo``, plus an
    untracked file that does not collide with the base advance. An untracked file
    does not block the advance, so sync-base advances the worktree rather than
    reporting ``dirty_tree`` — the detached analogue of the branch untracked-only
    case, proving the advance's ``--untracked-files=no`` scope is necessary.
    """
    behind = build_detached_behind_base_repo(root)
    (behind.repo / behind.data.untracked_file).write_text(
        behind.data.scratch_content, encoding="utf-8"
    )
    return behind


def build_detached_no_remote_repo(root: pathlib.Path) -> DetachedRepo:
    """Build a detached worktree with no ``origin`` remote to fetch the base from.

    A standalone repository (no clone, no remote) with HEAD detached: the base
    cannot be fetched and no remote base resolves, so synchronization reports a
    hard git failure rather than advancing.
    """
    data = repository_domain()
    repo = root / "repo"
    _git(root, "init", "-q", "-b", data.base_branch, str(repo), cwd=root)
    _configure(repo)
    _commit_file(repo, data.initial_file, data.initial_content, data.initial_message)
    sha = _git(repo, "rev-parse", "HEAD")
    _git(repo, "checkout", "-q", "--detach", sha)
    return DetachedRepo(
        repo=repo,
        base_ref=data.base_branch,
        remote_ref=f"origin/{data.base_branch}",
        detached_oid=sha,
        data=data,
    )
