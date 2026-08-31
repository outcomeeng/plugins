"""Test harness for the sync-base git base-synchronization module.

Exposes:

- An importlib loader for ``sync_base.py``. The module ships under a
  runtime-substituted plugin skill directory and is not importable by package
  name; tests load it through ``importlib``.
- ``build_behind_base_repo``. Constructs a real bare ``origin`` plus two clones
  so the working clone is genuinely behind ``origin/<base>`` until it fetches:
  the feature branch is cut before the base advances, and the base commit is
  pushed from a second clone the working clone has not fetched. A clean rebase
  replays the feature commit onto the advanced base.
- ``build_current_repo``. A working clone whose feature branch already contains
  every base commit, so synchronization performs no rebase.
- ``build_conflicting_repo``. The feature branch and the advanced base edit the
  same file divergently, so the rebase conflicts.
- ``build_dirty_behind_base_repo``. A behind-base clone with an uncommitted edit
  to a tracked file, so the rebase precondition fails before any replay.
- ``build_overlapping_base_repo``. A behind-base clone where base and branch edit
  one file in distinct regions, so the rebase auto-merges and the base delta
  overlaps the branch's changed paths.
- ``detach_head``. Detaches HEAD so the branch cannot be resolved.
- ``build_detached_behind_base_repo``. A worktree parked detached at a commit
  that is an ancestor of the advanced base — the stale-but-clean pool-worktree
  case — so synchronization advances it to the base tip.
- ``build_detached_current_repo``. A worktree parked detached at the base tip
  with no base advance, so synchronization reports it already current.
- ``build_detached_dirty_behind_base_repo``. A behind-base detached worktree
  with an uncommitted tracked edit, so synchronization reports ``dirty_tree``.
- ``build_detached_untracked_only_behind_base_repo``. A behind-base detached
  worktree whose only change is a non-colliding untracked file, so
  synchronization advances it rather than reporting ``dirty_tree``.
- ``build_detached_no_remote_repo``. A detached worktree with no ``origin``
  remote, so the base cannot be fetched and synchronization fails.

The harness owns the git lifecycle and the invented payload (file names and
commit messages); tests assert behavior against the returned handle.
"""

from __future__ import annotations

import importlib.util
import os
import pathlib
import subprocess
import sys
from dataclasses import dataclass
from types import ModuleType

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

BASE_BRANCH = "main"
FEATURE_BRANCH = "feature/x"
INITIAL_FILE = "README.md"
FEATURE_FILE = "feature.txt"
BASE_FILE = "base.txt"
FEATURE_COMMIT_MESSAGE = "feature change"


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


def _init_origin_with_base(root: pathlib.Path) -> pathlib.Path:
    """Create a bare origin seeded with an initial base commit; return its path.

    A ``pusher`` clone makes the initial commit and pushes it so ``origin`` has a
    ``main`` branch and default HEAD. The pusher is reused by callers that need
    to advance the base out of band.
    """
    origin = root / "origin.git"
    _git(root, "init", "--bare", "-b", BASE_BRANCH, str(origin), cwd=root)
    pusher = root / "pusher"
    _git(root, "clone", "-q", str(origin), str(pusher), cwd=root)
    _configure(pusher)
    _commit_file(pusher, INITIAL_FILE, "hello\n", "initial")
    _git(pusher, "push", "-q", "origin", BASE_BRANCH)
    return origin


def _working_clone_on_feature(root: pathlib.Path, origin: pathlib.Path) -> pathlib.Path:
    """Clone ``origin`` into ``repo`` and cut the feature branch off the base."""
    repo = root / "repo"
    _git(root, "clone", "-q", str(origin), str(repo), cwd=root)
    _configure(repo)
    _git(repo, "remote", "set-head", "origin", BASE_BRANCH)
    _git(repo, "switch", "-q", "-c", FEATURE_BRANCH)
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


def build_behind_base_repo(root: pathlib.Path) -> BehindBaseRepo:
    """Build a working clone behind its base by a not-yet-fetched base commit."""
    origin = _init_origin_with_base(root)
    repo = _working_clone_on_feature(root, origin)
    _commit_file(repo, FEATURE_FILE, "feature change\n", FEATURE_COMMIT_MESSAGE)

    pusher = root / "pusher"
    _commit_file(pusher, BASE_FILE, "base advance\n", "advance base")
    _git(pusher, "push", "-q", "origin", BASE_BRANCH)

    return BehindBaseRepo(
        repo=repo,
        base_ref=BASE_BRANCH,
        remote_ref=f"origin/{BASE_BRANCH}",
        feature_branch=FEATURE_BRANCH,
        feature_file=FEATURE_FILE,
        base_file=BASE_FILE,
        feature_commit_message=FEATURE_COMMIT_MESSAGE,
    )


DIRTY_MARKER = "uncommitted change\n"


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
    root: pathlib.Path, *, stage: bool = False
) -> DirtyBehindBaseRepo:
    """Build a behind-base working clone with an uncommitted change to a tracked file.

    ``stage=True`` stages the change (``git add``) without committing, so the
    dirty state is staged-but-uncommitted rather than unstaged. Both forms block
    a rebase and both must report ``dirty_tree``; ``git status --porcelain
    --untracked-files=no`` reports either.
    """
    behind = build_behind_base_repo(root)
    dirty_path = behind.repo / behind.feature_file
    dirty_path.write_text(
        dirty_path.read_text(encoding="utf-8") + DIRTY_MARKER, encoding="utf-8"
    )
    if stage:
        _git(behind.repo, "add", behind.feature_file)
    return DirtyBehindBaseRepo(
        repo=behind.repo,
        base_ref=behind.base_ref,
        remote_ref=behind.remote_ref,
        feature_branch=behind.feature_branch,
        dirty_file=behind.feature_file,
        dirty_marker=DIRTY_MARKER,
        base_file=behind.base_file,
    )


ALTERNATE_BRANCH = "release"
ALTERNATE_FILE = "release.txt"


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
    origin = _init_origin_with_base(root)
    pusher = root / "pusher"
    _git(pusher, "switch", "-q", "-c", ALTERNATE_BRANCH)
    _git(pusher, "push", "-q", "origin", ALTERNATE_BRANCH)

    repo = _working_clone_on_feature(root, origin)
    _commit_file(repo, FEATURE_FILE, "feature change\n", FEATURE_COMMIT_MESSAGE)

    _git(pusher, "switch", "-q", ALTERNATE_BRANCH)
    _commit_file(
        pusher, ALTERNATE_FILE, "alternate advance\n", "advance alternate base"
    )
    _git(pusher, "push", "-q", "origin", ALTERNATE_BRANCH)

    return AlternateBaseRepo(
        repo=repo,
        default_ref=BASE_BRANCH,
        alternate_ref=ALTERNATE_BRANCH,
        alternate_remote_ref=f"origin/{ALTERNATE_BRANCH}",
        feature_branch=FEATURE_BRANCH,
        feature_file=FEATURE_FILE,
        alternate_file=ALTERNATE_FILE,
    )


@dataclass(frozen=True)
class CurrentRepo:
    """A working clone whose feature branch already contains every base commit."""

    repo: pathlib.Path
    base_ref: str
    remote_ref: str
    feature_branch: str


def build_current_repo(root: pathlib.Path) -> CurrentRepo:
    """Build a working clone already current with its base (no base advance)."""
    origin = _init_origin_with_base(root)
    repo = _working_clone_on_feature(root, origin)
    _commit_file(repo, FEATURE_FILE, "feature change\n", FEATURE_COMMIT_MESSAGE)
    return CurrentRepo(
        repo=repo,
        base_ref=BASE_BRANCH,
        remote_ref=f"origin/{BASE_BRANCH}",
        feature_branch=FEATURE_BRANCH,
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
    origin = _init_origin_with_base(root)
    repo = _working_clone_on_feature(root, origin)
    _commit_file(repo, INITIAL_FILE, "feature edit\n", "feature edits readme")

    pusher = root / "pusher"
    _commit_file(pusher, INITIAL_FILE, "base edit\n", "base edits readme")
    _git(pusher, "push", "-q", "origin", BASE_BRANCH)

    return ConflictRepo(
        repo=repo,
        base_ref=BASE_BRANCH,
        remote_ref=f"origin/{BASE_BRANCH}",
        feature_branch=FEATURE_BRANCH,
        conflict_file=INITIAL_FILE,
    )


UNTRACKED_FILE = "scratch.local"


def build_untracked_only_behind_base_repo(root: pathlib.Path) -> BehindBaseRepo:
    """Build a behind-base clone whose only working-tree change is an untracked file.

    An untracked file (not ``git add``ed) does not block a rebase, so sync-base
    must rebase rather than report ``dirty_tree``. The untracked path does not
    collide with the base advance, so the replay proceeds and leaves it in place.
    Proves the ``--untracked-files=no`` scope of the dirty check is necessary:
    without it the untracked file would read as dirty and force ``dirty_tree``.
    """
    behind = build_behind_base_repo(root)
    (behind.repo / UNTRACKED_FILE).write_text("scratch\n", encoding="utf-8")
    return behind


def fetch_base(repo: pathlib.Path, base_ref: str = BASE_BRANCH) -> None:
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


def merge_base_oid(repo: pathlib.Path, left: str, right: str) -> str:
    """Return the full OID of the merge base between two refs in ``repo``."""
    return _git(repo, "merge-base", left, right)


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
    origin = _init_origin_with_base(root)
    repo = _working_clone_on_feature(root, origin)
    _commit_file(repo, INITIAL_FILE, "hello\nfeature line\n", "feature edits readme")

    pusher = root / "pusher"
    _commit_file(pusher, INITIAL_FILE, "base line\nhello\n", "base edits readme top")
    _git(pusher, "push", "-q", "origin", BASE_BRANCH)

    return OverlappingBaseRepo(
        repo=repo,
        base_ref=BASE_BRANCH,
        remote_ref=f"origin/{BASE_BRANCH}",
        feature_branch=FEATURE_BRANCH,
        overlap_file=INITIAL_FILE,
    )


RENAMED_FILE = "renamed.txt"


@dataclass(frozen=True)
class RenameBaseRepo:
    """A behind-base clone whose base advance renames a file the branch ignores.

    The base renames ``INITIAL_FILE`` to ``RENAMED_FILE``; the branch changes an
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
    origin = _init_origin_with_base(root)
    repo = _working_clone_on_feature(root, origin)
    _commit_file(repo, FEATURE_FILE, "feature change\n", FEATURE_COMMIT_MESSAGE)

    pusher = root / "pusher"
    _git(pusher, "mv", INITIAL_FILE, RENAMED_FILE)
    _git(pusher, "commit", "-q", "-m", "rename initial file")
    _git(pusher, "push", "-q", "origin", BASE_BRANCH)

    return RenameBaseRepo(
        repo=repo,
        base_ref=BASE_BRANCH,
        remote_ref=f"origin/{BASE_BRANCH}",
        feature_branch=FEATURE_BRANCH,
        old_path=INITIAL_FILE,
        new_path=RENAMED_FILE,
    )


def detach_head(repo: pathlib.Path) -> None:
    """Detach HEAD so the branch cannot be resolved for a rebase."""
    sha = _git(repo, "rev-parse", "HEAD")
    _git(repo, "checkout", "-q", "--detach", sha)


def _working_clone_detached_on_base(
    root: pathlib.Path, origin: pathlib.Path
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
    _git(repo, "remote", "set-head", "origin", BASE_BRANCH)
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
    origin = _init_origin_with_base(root)
    repo = _working_clone_detached_on_base(root, origin)
    detached_oid = _git(repo, "rev-parse", "HEAD")

    pusher = root / "pusher"
    _commit_file(pusher, BASE_FILE, "base advance\n", "advance base")
    _git(pusher, "push", "-q", "origin", BASE_BRANCH)

    return DetachedRepo(
        repo=repo,
        base_ref=BASE_BRANCH,
        remote_ref=f"origin/{BASE_BRANCH}",
        detached_oid=detached_oid,
        base_file=BASE_FILE,
    )


def build_detached_current_repo(root: pathlib.Path) -> DetachedRepo:
    """Build a clean detached worktree parked at the base tip (no base advance).

    HEAD is detached at the base tip and no base advance follows, so after the
    fetch the detached commit equals ``origin/<base>`` and synchronization
    reports it already current without advancing.
    """
    origin = _init_origin_with_base(root)
    repo = _working_clone_detached_on_base(root, origin)
    return DetachedRepo(
        repo=repo,
        base_ref=BASE_BRANCH,
        remote_ref=f"origin/{BASE_BRANCH}",
        detached_oid=_git(repo, "rev-parse", "HEAD"),
    )


def build_detached_dirty_behind_base_repo(root: pathlib.Path) -> DetachedRepo:
    """Build a behind-base detached worktree with an uncommitted tracked edit.

    Same parked-behind state as ``build_detached_behind_base_repo``, plus an
    uncommitted modification to the tracked initial file, so the advance
    precondition fails and synchronization reports ``dirty_tree`` without moving
    the worktree.
    """
    behind = build_detached_behind_base_repo(root)
    dirty_path = behind.repo / INITIAL_FILE
    dirty_path.write_text(
        dirty_path.read_text(encoding="utf-8") + DIRTY_MARKER, encoding="utf-8"
    )
    return DetachedRepo(
        repo=behind.repo,
        base_ref=behind.base_ref,
        remote_ref=behind.remote_ref,
        detached_oid=behind.detached_oid,
        base_file=behind.base_file,
        dirty_file=INITIAL_FILE,
        dirty_marker=DIRTY_MARKER,
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
    (behind.repo / UNTRACKED_FILE).write_text("scratch\n", encoding="utf-8")
    return behind


def build_detached_no_remote_repo(root: pathlib.Path) -> DetachedRepo:
    """Build a detached worktree with no ``origin`` remote to fetch the base from.

    A standalone repository (no clone, no remote) with HEAD detached: the base
    cannot be fetched and no remote base resolves, so synchronization reports a
    hard git failure rather than advancing.
    """
    repo = root / "repo"
    _git(root, "init", "-q", "-b", BASE_BRANCH, str(repo), cwd=root)
    _configure(repo)
    _commit_file(repo, INITIAL_FILE, "hello\n", "initial")
    sha = _git(repo, "rev-parse", "HEAD")
    _git(repo, "checkout", "-q", "--detach", sha)
    return DetachedRepo(
        repo=repo,
        base_ref=BASE_BRANCH,
        remote_ref=f"origin/{BASE_BRANCH}",
        detached_oid=sha,
    )
