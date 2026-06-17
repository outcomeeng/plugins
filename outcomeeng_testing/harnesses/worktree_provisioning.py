"""Test harness for the init-worktrees provisioning module.

Exposes:

- ``load_init_worktrees_module``. An importlib loader for ``init_worktrees.py``.
  The module ships under a runtime-substituted plugin skill directory and is not
  importable by package name; tests load it through ``importlib`` instead.
- ``provisioning_env``. A context manager yielding a :class:`ProvisioningEnv`
  backed by a bare ``origin`` remote — ``{repo_name}.git`` (default ``repo``) on
  ``default_branch`` (default ``main``), each overridable so a test can exercise
  a repository whose name or default branch differs — with one commit, plus
  helpers to reach the checkout shapes the provisioning tests need: a non-bare
  single checkout, a non-bare checkout carrying linked worktrees, a bare
  repository without an origin remote, and an empty container directory to
  provision the pool into.

The harness owns the git lifecycle (the remote, the seed commit, temporary
directories, and teardown on every exit path); it owns no expected outputs and
does not call the behavior under test. Tests construct the system-under-test's
inputs from these handles and assert against its returned values.

Exception case per ``plugins/spec-tree/skills/test/references/methodology.md``:
none. These are real local git repositories (L1: git plus tmp dirs), not test
doubles.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from types import ModuleType

REPO_ROOT = Path(__file__).resolve().parents[2]
INIT_WORKTREES_MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "plugins"
    / "spec-tree"
    / "skills"
    / "init-worktrees"
    / "scripts"
    / "init_worktrees.py"
)


def load_init_worktrees_module() -> ModuleType:
    """Load the ``init_worktrees`` module via importlib and cache it."""
    cached = sys.modules.get("init_worktrees")
    if cached is not None:
        return cached
    spec = importlib.util.spec_from_file_location(
        "init_worktrees", INIT_WORKTREES_MODULE_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(
            f"Cannot load init_worktrees from {INIT_WORKTREES_MODULE_PATH}"
        )
    module = importlib.util.module_from_spec(spec)
    sys.modules["init_worktrees"] = module
    spec.loader.exec_module(module)
    return module


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


def _git_out(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


@dataclass
class ProvisioningEnv:
    """A bare ``origin`` remote plus helpers to reach each checkout shape.

    ``origin`` is a bare repository on its ``default_branch`` with one commit.
    The helpers clone non-bare checkouts from it, attach linked worktrees to
    expose the non-compliant shape, and hand back empty container directories to
    provision the pool into. Every path lives under one temporary tree the
    context manager removes on exit.
    """

    tmp: Path
    origin: Path
    repo_name: str
    default_branch: str

    def origin_default_tip(self) -> str:
        """Return the commit SHA at the bare remote's default-branch tip."""
        return _git_out(self.origin, "rev-parse", self.default_branch)

    def single_checkout(self, name: str = "checkout") -> Path:
        """Clone a non-bare single working tree from ``origin``."""
        checkout = self.tmp / name
        subprocess.run(
            ["git", "clone", "--quiet", str(self.origin), str(checkout)],
            check=True,
            capture_output=True,
        )
        _git(checkout, "config", "user.email", "test@example.invalid")
        _git(checkout, "config", "user.name", "Spec Tree Test")
        _git(checkout, "config", "commit.gpgsign", "false")
        return checkout

    def ignore(self, checkout: Path, *patterns: str) -> None:
        """Append ``patterns`` to the checkout's ``.gitignore`` and commit it."""
        gitignore = checkout / ".gitignore"
        prior = gitignore.read_text(encoding="utf-8") if gitignore.exists() else ""
        gitignore.write_text(
            prior + "".join(f"{p}\n" for p in patterns), encoding="utf-8"
        )
        _git(checkout, "add", ".gitignore")
        _git(checkout, "commit", "--quiet", "-m", "ignore patterns")

    def write_ignored(self, checkout: Path, rel: str, data: bytes) -> Path:
        """Write a gitignored file at ``rel`` under ``checkout`` and return its path."""
        target = checkout / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        return target

    def create_local_branch(self, checkout: Path, name: str) -> None:
        """Create a local branch carrying one commit, left unpushed."""
        _git(checkout, "checkout", "--quiet", "-b", name)
        (checkout / f"{name}.txt").write_text(name, encoding="utf-8")
        _git(checkout, "add", f"{name}.txt")
        _git(checkout, "commit", "--quiet", "-m", f"local {name}")
        _git(checkout, "checkout", "--quiet", self.default_branch)

    def create_local_tag(self, checkout: Path, name: str) -> None:
        """Create a lightweight tag, left unpushed."""
        _git(checkout, "tag", name)

    def origin_branches(self) -> list[str]:
        """Return the branch names present on the bare ``origin`` remote."""
        return _git_out(
            self.origin, "for-each-ref", "--format=%(refname:short)", "refs/heads"
        ).splitlines()

    def origin_tags(self) -> list[str]:
        """Return the tag names present on the bare ``origin`` remote."""
        return [t for t in _git_out(self.origin, "tag").splitlines() if t]

    def commit_file(self, checkout: Path, name: str, content: str = "x") -> None:
        """Commit a tracked file on the checkout's current branch."""
        (checkout / name).write_text(content, encoding="utf-8")
        _git(checkout, "add", name)
        _git(checkout, "commit", "--quiet", "-m", f"add {name}")

    def push_default(self, checkout: Path) -> None:
        """Push the checkout's default branch to ``origin``, advancing the remote."""
        _git(checkout, "push", "--quiet", "origin", self.default_branch)

    def pool_tracking_refs(self, bare_dir: Path) -> list[str]:
        """Return the ``origin/*`` remote-tracking refs the pool's bare clone holds."""
        return _git_out(
            bare_dir, "for-each-ref", "--format=%(refname:short)", "refs/remotes/origin"
        ).splitlines()

    def attach_linked_worktree(self, checkout: Path, name: str = "wt") -> Path:
        """Attach a linked worktree to a non-bare ``checkout`` (the non-compliant shape)."""
        worktree = checkout.parent / f"{checkout.name}-{name}"
        _git(checkout, "worktree", "add", "--quiet", "--detach", str(worktree))
        return worktree

    def container(self) -> Path:
        """Return an empty repository-name directory to provision a pool into.

        Named for the repository because ``provision`` requires the container
        basename to equal the origin repository name (the pool nests as
        ``<repo>/<repo>``).
        """
        target = self.tmp / self.repo_name
        target.mkdir()
        return target

    def bare_without_origin(self, name: str = "no-origin") -> Path:
        """Return a bare repository that has no ``origin`` remote.

        The classifier reads the repository name from ``git remote get-url
        origin`` to identify the main checkout; with no origin it can name none,
        so this shape exercises the no-origin probe fallback.
        """
        bare = self.tmp / f"{name}.git"
        subprocess.run(
            ["git", "init", "--quiet", "--bare", str(bare)],
            check=True,
            capture_output=True,
        )
        return bare

    def set_origin_url(self, repo: Path, url: str) -> None:
        """Re-point ``repo``'s ``origin`` remote at ``url``.

        Writes the remote URL into config without contacting it, so a test can
        exercise a non-filesystem URL form (HTTPS, scp-like SSH) that the
        repository-name parser must handle.
        """
        _git(repo, "remote", "set-url", "origin", url)

    def move_worktree(self, repo: Path, src: Path, dst: Path) -> None:
        """Move a worktree from ``src`` to ``dst`` via ``git worktree move``.

        Updates git's worktree tracking, so a test can give the main checkout a
        directory basename that no longer matches the origin repository name.
        """
        _git(repo, "worktree", "move", str(src), str(dst))


@contextmanager
def provisioning_env(
    repo_name: str = "repo", default_branch: str = "main"
) -> Iterator[ProvisioningEnv]:
    """Yield a :class:`ProvisioningEnv` backed by a throwaway bare remote.

    The remote is a bare ``{repo_name}.git`` on ``default_branch``, seeded with
    one commit pushed from a scratch checkout. Its directory basename carries
    ``repo_name`` so the layout classifier — which reads the repository name from
    ``git remote get-url origin`` — resolves the same name ``provision`` places
    the main checkout under. ``default_branch`` is ``main`` unless a test
    exercises a repository whose default branch is named otherwise. The whole
    tree is removed on exit; read-only git objects that resist cleanup are
    ignored so teardown never fails the run.
    """
    with TemporaryDirectory(ignore_cleanup_errors=True) as raw:
        tmp = Path(raw)
        origin = tmp / f"{repo_name}.git"
        subprocess.run(
            ["git", "init", "--quiet", "--bare", "-b", default_branch, str(origin)],
            check=True,
            capture_output=True,
        )
        seed = tmp / "seed"
        subprocess.run(
            ["git", "init", "--quiet", "-b", default_branch, str(seed)],
            check=True,
            capture_output=True,
        )
        _git(seed, "config", "user.email", "test@example.invalid")
        _git(seed, "config", "user.name", "Spec Tree Test")
        _git(seed, "config", "commit.gpgsign", "false")
        (seed / "README.md").write_text("seed\n", encoding="utf-8")
        _git(seed, "add", "README.md")
        _git(seed, "commit", "--quiet", "-m", "seed")
        _git(seed, "remote", "add", "origin", str(origin))
        _git(seed, "push", "--quiet", "-u", "origin", default_branch)
        yield ProvisioningEnv(
            tmp=tmp,
            origin=origin,
            repo_name=repo_name,
            default_branch=default_branch,
        )


def head_sha(path: Path) -> str:
    """Return the commit SHA at the working tree's current HEAD."""
    return _git_out(path, "rev-parse", "HEAD")


def is_detached(path: Path) -> bool:
    """Return whether the working tree's HEAD is detached (on no branch)."""
    result = subprocess.run(
        ["git", "-C", str(path), "symbolic-ref", "-q", "HEAD"],
        capture_output=True,
    )
    return result.returncode != 0


def is_bare_repo(path: Path) -> bool:
    """Return whether ``path`` is a bare git repository."""
    return _git_out(path, "rev-parse", "--is-bare-repository") == "true"


def git_common_dir(path: Path) -> Path:
    """Return the absolute git-common-dir of the checkout containing ``path``."""
    return Path(
        _git_out(path, "rev-parse", "--path-format=absolute", "--git-common-dir")
    )


def upstream_ref(path: Path) -> str:
    """Return the upstream tracking ref of the worktree's checked-out branch."""
    return _git_out(path, "rev-parse", "--abbrev-ref", "@{upstream}")


__all__ = [
    "ProvisioningEnv",
    "git_common_dir",
    "head_sha",
    "is_bare_repo",
    "is_detached",
    "load_init_worktrees_module",
    "provisioning_env",
    "upstream_ref",
]
