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
- ``detach_head``. Detaches HEAD so the branch cannot be resolved.

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


def detach_head(repo: pathlib.Path) -> None:
    """Detach HEAD so the branch cannot be resolved for a rebase."""
    sha = _git(repo, "rev-parse", "HEAD")
    _git(repo, "checkout", "-q", "--detach", sha)
