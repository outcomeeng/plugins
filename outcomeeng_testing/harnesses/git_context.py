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


__all__ = ["accepted_git_context"]
