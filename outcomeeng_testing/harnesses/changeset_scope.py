"""Test harness for the changeset-scope skill's git-derivation module.

Exposes:

- An importlib loader for ``changeset_scope.py``. The module ships under a
  runtime-substituted plugin skill directory and is not importable by package
  name; tests load it through ``importlib`` instead.
- ``build_stale_local_base_repo``. Constructs a git repository reproducing the
  multi-worktree staleness bug: the feature branch contains a commit that has
  been merged into ``origin/<base>`` while the local base branch ref lags behind
  it. Scoping against the local ref re-includes the merged commit; scoping
  against the remote-tracking ref excludes it.
- ``build_repo_without_origin``. A repository with a branch and a commit but no
  ``refs/remotes/origin/HEAD`` symbolic ref, for the base-ref fallback paths.
- ``build_repo_with_modified_spaced_note``. A repository whose only working-tree
  change is a committed-then-modified coordination note at a path containing a
  space, for the porcelain-quoting case.

The harness owns the scenario's invented payload (the merged-file and
feature-file names) and the git lifecycle; tests assert behavior against the
returned handle.
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
CHANGESET_SCOPE_SCRIPTS_DIR = (
    REPO_ROOT
    / "src"
    / "plugins"
    / "spec-tree"
    / "skills"
    / "scope-changeset"
    / "scripts"
)
CHANGESET_SCOPE_MODULE_PATH = CHANGESET_SCOPE_SCRIPTS_DIR / "changeset_scope.py"

MERGED_FILE = "merged.txt"
FEATURE_FILE = "feature.txt"
INITIAL_FILE = "README.md"
BASE_BRANCH = "main"
FEATURE_BRANCH = "feature/x"
SPACED_NOTE_PATH = "spx dir/PLAN.md"


def load_changeset_scope_module() -> ModuleType:
    """Load the ``changeset_scope`` module via importlib and cache it."""
    cached = sys.modules.get("changeset_scope")
    if cached is not None:
        return cached
    spec = importlib.util.spec_from_file_location(
        "changeset_scope", CHANGESET_SCOPE_MODULE_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(
            f"Cannot load changeset_scope from {CHANGESET_SCOPE_MODULE_PATH}"
        )
    module = importlib.util.module_from_spec(spec)
    sys.modules["changeset_scope"] = module
    spec.loader.exec_module(module)
    return module


def _git(repo: pathlib.Path, *args: str, cwd: pathlib.Path | None = None) -> str:
    """Run a git command with isolated config, returning stripped stdout.

    Global and system config are suppressed and a fixed identity is injected so
    the call does not inherit operator settings or commit signing.
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
        ["git", *args],
        cwd=cwd if cwd is not None else repo,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def _commit_file(repo: pathlib.Path, name: str, content: str, message: str) -> None:
    (repo / name).write_text(content, encoding="utf-8")
    _git(repo, "add", name)
    _git(repo, "commit", "-q", "-m", message)


@dataclass(frozen=True)
class StaleBaseRepo:
    """A repo where the feature branch holds a commit already merged to origin.

    ``base_ref`` is the bare base-branch name. ``merged_file`` was committed on
    the base and is present on ``origin/<base_ref>`` (current) but absent from
    the lagging local base ref. ``feature_file`` is the feature branch's own
    change. A changeset scoped against ``origin/<base_ref>`` contains
    ``feature_file`` only; one scoped against the stale local ref also contains
    ``merged_file``.
    """

    repo: pathlib.Path
    base_ref: str
    feature_branch: str
    merged_file: str
    feature_file: str


def build_stale_local_base_repo(repo: pathlib.Path) -> StaleBaseRepo:
    """Build the staleness scenario and return its handle.

    Sequence: initial commit A on ``main``; merged commit M on ``main``; point
    ``refs/remotes/origin/{main,HEAD}`` at A+M; branch the feature off A+M so it
    contains M; add feature commit F; reset the local ``main`` ref back to A so
    it lags ``origin/main`` by the merged commit.
    """
    _git(repo, "init", "-q", "-b", BASE_BRANCH, str(repo), cwd=pathlib.Path.cwd())
    _git(repo, "config", "commit.gpgsign", "false")
    _commit_file(repo, INITIAL_FILE, "hello\n", "initial")
    initial_sha = _git(repo, "rev-parse", "HEAD")

    _commit_file(repo, MERGED_FILE, "merged change\n", "merge change into base")
    advanced_sha = _git(repo, "rev-parse", "HEAD")

    # origin/main (and origin/HEAD) point at the advanced base A+M.
    _git(repo, "update-ref", f"refs/remotes/origin/{BASE_BRANCH}", advanced_sha)
    _git(
        repo,
        "symbolic-ref",
        "refs/remotes/origin/HEAD",
        f"refs/remotes/origin/{BASE_BRANCH}",
    )

    # Feature branches off A+M (so it contains the merged commit) and adds F.
    _git(repo, "switch", "-q", "-c", FEATURE_BRANCH)
    _commit_file(repo, FEATURE_FILE, "feature change\n", "feature change")

    # The local base ref lags origin by the merged commit.
    _git(repo, "update-ref", f"refs/heads/{BASE_BRANCH}", initial_sha)

    return StaleBaseRepo(
        repo=repo,
        base_ref=BASE_BRANCH,
        feature_branch=FEATURE_BRANCH,
        merged_file=MERGED_FILE,
        feature_file=FEATURE_FILE,
    )


def build_repo_without_origin(repo: pathlib.Path) -> str:
    """Build a repo with a branch and a commit but no origin/HEAD symbolic ref.

    Returns the branch name. Exercises the base-ref fallback paths
    (``strict=False`` returns the default, ``strict=True`` raises).
    """
    _git(repo, "init", "-q", "-b", BASE_BRANCH, str(repo), cwd=pathlib.Path.cwd())
    _git(repo, "config", "commit.gpgsign", "false")
    _commit_file(repo, INITIAL_FILE, "hello\n", "initial")
    return BASE_BRANCH


@dataclass(frozen=True)
class SpacedNoteRepo:
    """A repo whose only working-tree change is a modified spaced-path note.

    ``note_path`` is a coordination note (``PLAN.md``) under a directory whose
    name contains a space. It is committed first (so git lists the individual
    file rather than collapsing an untracked directory) and then modified, so it
    appears as a working-tree change. ``git status --porcelain`` without ``-z``
    C-quotes the spaced path; consumers must use ``-z`` to recover the unquoted
    name that matches ``git diff --name-only`` output.
    """

    repo: pathlib.Path
    note_path: str


def build_repo_with_modified_spaced_note(repo: pathlib.Path) -> SpacedNoteRepo:
    """Build a repo with a committed-then-modified coordination note at a spaced path.

    Sequence: initialise the repo with a base commit (no origin needed — the
    working-tree query does not read it); create the spaced directory; commit
    the note so git tracks the individual file; modify it so it surfaces as a
    working-tree change. Returns the handle carrying the note's unquoted path.
    """
    build_repo_without_origin(repo)
    (repo / "spx dir").mkdir()
    _commit_file(repo, SPACED_NOTE_PATH, "v1\n", "add spaced note")
    (repo / SPACED_NOTE_PATH).write_text("v2\n", encoding="utf-8")
    return SpacedNoteRepo(repo=repo, note_path=SPACED_NOTE_PATH)


def detach_head(repo: pathlib.Path) -> None:
    """Put ``repo`` on a detached HEAD so ``detect_current_branch`` raises.

    Resolves the current commit and checks it out by SHA, detaching HEAD
    from the branch ref.
    """
    sha = _git(repo, "rev-parse", "HEAD")
    _git(repo, "checkout", "-q", "--detach", sha)


def write_branch_state_file(
    state_dir: pathlib.Path, slug: str, branch: str
) -> pathlib.Path:
    """Write a state file at ``state_dir/<slug>.md`` recording ``branch``.

    The file carries the YAML frontmatter ``branch_slug`` reads for
    state-collision disambiguation: a ``branch:`` key fenced by
    ``changeset_scope.FRONTMATTER_DELIMITER``. Returns the written path.
    """
    delimiter = load_changeset_scope_module().FRONTMATTER_DELIMITER
    state_dir.mkdir(parents=True, exist_ok=True)
    path = state_dir / f"{slug}.md"
    path.write_text(f"{delimiter}\nbranch: {branch}\n{delimiter}\n", encoding="utf-8")
    return path
