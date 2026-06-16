"""Git work-context harness for spec-tree session-command tests.

`spx session handoff` (the spx CLI) refuses to create a handoff session unless
the invocation's working directory is a git work context it accepts: a root
worktree on a named branch or detached HEAD, or a clean linked worktree
detached at the tip of `origin/<default>`. Any other linked-worktree state, or
a non-git directory, raises `SessionHandoffBaseError`.

Session-command scenario tests shell out to the real `spx` binary, so the
command's outcome depends on the git context of whatever directory the
subprocess runs in. Without a provisioned context the test inherits the
runner's ambient git state — green in a root checkout or a worktree detached at
`origin/HEAD`, red in a linked worktree on a feature branch or a non-git
sandbox. That coupling is the defect this harness removes.

`accepted_git_context()` provisions the simplest accepted context — a root
worktree on a named branch with one commit and a clean working tree — and tears
it down on every exit path. Tests pass the yielded path as the subprocess `cwd`
so handoff sees a controlled, accepted context rather than the runner's.

Exception case per `plugins/spec-tree/skills/testing/references/methodology.md`:
none. This is a real local git repository (L1: git plus tmp dirs), not a test
double. The harness owns resource setup, teardown, and cleanup; it does not
replace the behavior under test.
"""

from __future__ import annotations

import subprocess
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


@contextmanager
def accepted_git_context() -> Iterator[Path]:
    """Yield a root-worktree git repo on a named branch that spx handoff accepts.

    The repo is initialized on branch ``main`` with one commit and a clean
    working tree, so ``spx session handoff`` records the branch name and
    proceeds. The whole tree is removed on context exit, including on failure.
    """
    with TemporaryDirectory() as tmp:
        repo = Path(tmp)
        _git(repo, "init", "-b", "main")
        _git(repo, "config", "user.email", "test@example.invalid")
        _git(repo, "config", "user.name", "Spec Tree Test")
        # Disable commit signing locally so the seed commit succeeds regardless
        # of a contributor's global commit.gpgsign (no signing key in this repo).
        _git(repo, "config", "commit.gpgsign", "false")
        (repo / "README.md").write_text("seed\n", encoding="utf-8")
        _git(repo, "add", "README.md")
        _git(repo, "commit", "-m", "seed")
        yield repo


def _git_out(repo: Path, *args: str) -> str:
    """Run ``git -C repo args`` and return stripped stdout, raising on failure."""
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


@dataclass
class HandoffGitEnv:
    """A repo with an ``origin`` remote plus helpers to reach each handoff state.

    ``root`` is a root checkout on ``default_branch`` whose HEAD sits one commit
    ahead of the ``origin/<default>`` tip, so a worktree detached at HEAD is off
    the tip. The ``linked_*`` helpers add linked worktrees in specific states;
    ``detach_root`` detaches the root checkout. Tests pass the yielded paths as
    the subprocess ``cwd`` and compare the recorded ``git_ref`` against the
    accepted contexts' expected values.
    """

    root: Path
    default_branch: str
    origin_tip: str

    def head_sha(self) -> str:
        """Return the full SHA at the root checkout's current HEAD."""
        return _git_out(self.root, "rev-parse", "HEAD")

    def detach_root(self) -> None:
        """Detach the root checkout at its current HEAD (one commit past the tip)."""
        _git(self.root, "switch", "--detach", self.head_sha())

    def linked_at_origin_tip(self) -> Path:
        """Add a linked worktree detached at the ``origin/<default>`` tip."""
        worktree = self.root.parent / "wt-at-tip"
        _git(self.root, "worktree", "add", "--detach", str(worktree), self.origin_tip)
        return worktree

    def linked_on_branch(self, name: str = "feature") -> Path:
        """Add a linked worktree checked out on a new named branch."""
        worktree = self.root.parent / f"wt-{name}"
        _git(self.root, "worktree", "add", str(worktree), "-b", name)
        return worktree

    def linked_detached_off_tip(self) -> Path:
        """Add a linked worktree detached at HEAD (one commit past the tip)."""
        worktree = self.root.parent / "wt-off-tip"
        _git(self.root, "worktree", "add", "--detach", str(worktree), self.head_sha())
        return worktree

    def push_work_branch(self, name: str = "work/feature") -> str:
        """Create a branch at the ``origin/<default>`` tip, push it to origin, and
        materialize its remote-tracking ref.

        An explicit handoff ``git_ref`` is recorded only when
        ``refs/remotes/origin/<name>`` resolves, so the fetch after the push is
        what makes the branch reachable from every worktree sharing this repo's
        git dir. Returns the branch name for the test to pass as the explicit
        ref and compare against the recorded value.
        """
        _git(self.root, "branch", name, self.origin_tip)
        _git(self.root, "push", "origin", name)
        _git(self.root, "fetch", "origin")
        return name


@contextmanager
def handoff_git_env() -> Iterator[HandoffGitEnv]:
    """Yield a :class:`HandoffGitEnv` backed by a throwaway repo with a remote.

    The root checkout is on ``main`` with ``origin/HEAD`` resolved and a second
    commit so HEAD is ahead of the ``origin/main`` tip. The whole tree is removed
    on exit; read-only git objects that resist cleanup are ignored so teardown
    never fails the run. Provisions the linked-worktree and detached states the
    worktree-state scenario tests need beyond the simple accepted context above.
    """
    with TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        base = Path(tmp)
        remote = base / "remote.git"
        root = base / "repo"
        subprocess.run(
            ["git", "init", "--quiet", "--bare", "-b", "main", str(remote)],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "init", "--quiet", "-b", "main", str(root)],
            check=True,
            capture_output=True,
        )
        _git(root, "config", "user.email", "test@example.invalid")
        _git(root, "config", "user.name", "Spec Tree Test")
        _git(root, "config", "commit.gpgsign", "false")
        (root / "README.md").write_text("seed\n", encoding="utf-8")
        _git(root, "add", "README.md")
        _git(root, "commit", "-m", "seed")
        _git(root, "remote", "add", "origin", str(remote))
        _git(root, "push", "--quiet", "-u", "origin", "main")
        _git(root, "remote", "set-head", "origin", "-a")
        origin_tip = _git_out(root, "rev-parse", "origin/main")
        _git(root, "commit", "--allow-empty", "-m", "ahead of origin tip")
        yield HandoffGitEnv(root=root, default_branch="main", origin_tip=origin_tip)


@contextmanager
def worktree_against_origin(
    *, behind: int = 0, default_branch: str = "main"
) -> Iterator[Path]:
    """Yield a repo whose HEAD trails ``origin/<default_branch>`` by ``behind`` commits.

    Provisions a bare remote on ``default_branch`` and a checkout that pushes a
    seed commit, then advances ``origin`` by ``behind`` commits and resets the
    local branch back to the seed — so the remote-tracking ref sits ``behind``
    commits ahead of HEAD without any fetch left for the reader to run, and
    ``origin/HEAD`` resolves to ``default_branch``. With ``behind=0`` the checkout
    is current with the tip. The whole tree is removed on exit; read-only git
    objects that resist cleanup are ignored so teardown never fails the run.

    Exception case per `plugins/spec-tree/skills/testing/references/methodology.md`:
    none. This is a real local git repository (L1: git plus tmp dirs), not a test
    double. The harness owns resource setup, teardown, and cleanup; it does not
    replace the behavior under test.
    """
    with TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        base = Path(tmp)
        remote = base / "remote.git"
        repo = base / "repo"
        subprocess.run(
            ["git", "init", "--quiet", "--bare", "-b", default_branch, str(remote)],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "init", "--quiet", "-b", default_branch, str(repo)],
            check=True,
            capture_output=True,
        )
        _git(repo, "config", "user.email", "test@example.invalid")
        _git(repo, "config", "user.name", "Spec Tree Test")
        _git(repo, "config", "commit.gpgsign", "false")
        (repo / "README.md").write_text("seed\n", encoding="utf-8")
        _git(repo, "add", "README.md")
        _git(repo, "commit", "-m", "seed")
        _git(repo, "remote", "add", "origin", str(remote))
        _git(repo, "push", "--quiet", "-u", "origin", default_branch)
        _git(repo, "remote", "set-head", "origin", "-a")
        seed_sha = _git_out(repo, "rev-parse", "HEAD")
        for index in range(behind):
            _git(repo, "commit", "--allow-empty", "-m", f"origin advance {index + 1}")
            _git(repo, "push", "--quiet", "origin", default_branch)
        if behind:
            _git(repo, "reset", "--hard", seed_sha)
        yield repo


__all__ = [
    "HandoffGitEnv",
    "accepted_git_context",
    "handoff_git_env",
    "worktree_against_origin",
]
