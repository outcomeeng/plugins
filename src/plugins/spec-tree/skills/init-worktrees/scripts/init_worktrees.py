"""Classify and provision a repository's git worktree layout.

Stdlib-only (`python3` >= 3.11), portable across consumer checkouts. The skill
invokes this module as
``python3 "${CLAUDE_SKILL_DIR}/scripts/init_worktrees.py" <command> ...``.

Three layouts are recognized: a ``single`` working tree, a compliant bare-repo
worktree ``pool``, and ``non-compliant`` (anything matching neither). The pure
``classify`` function decides a layout from ``GitFacts``; ``probe`` reads those
facts from a real checkout with git; ``provision`` builds the pool — cloning the
bare repository, adding the ``main`` and detached pool worktrees, and carrying a
prior checkout's ``.spx/`` across. The destructive removal of a prior working
tree is never performed here: the skill emits that command for the operator.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from enum import StrEnum
from pathlib import Path


class Layout(StrEnum):
    """The recognized repository git layouts."""

    SINGLE = "single"
    POOL = "pool"
    NON_COMPLIANT = "non-compliant"


@dataclass(frozen=True)
class GitFacts:
    """The observable git facts a layout classification reads.

    ``common_dir_is_bare`` is whether the git-common-dir is a bare repository;
    ``has_linked_worktrees`` is whether more than one working tree is registered;
    the ``main_worktree_*`` fields describe the ``main`` worktree's presence,
    sibling placement next to the common dir, and ``origin/main`` tracking; and
    ``spx_beside_common_dir`` is whether ``.spx/`` sits next to the common dir.
    """

    common_dir_is_bare: bool
    has_linked_worktrees: bool
    main_worktree_present: bool
    main_worktree_beside_common_dir: bool
    main_tracks_origin_main: bool
    spx_beside_common_dir: bool


def classify(facts: GitFacts) -> Layout:
    """Map observable git facts to a layout verdict.

    A lone working tree on a non-bare repository is ``SINGLE``. A bare repository
    whose ``main`` worktree is a sibling tracking ``origin/main`` with ``.spx/``
    beside the common dir is ``POOL``. Everything else — linked worktrees on a
    non-bare root, or a bare pool missing the ``main`` sibling, its tracking, or
    its sibling ``.spx/`` — is ``NON_COMPLIANT``.
    """
    if not facts.common_dir_is_bare:
        return Layout.SINGLE if not facts.has_linked_worktrees else Layout.NON_COMPLIANT
    pool = (
        facts.main_worktree_present
        and facts.main_worktree_beside_common_dir
        and facts.main_tracks_origin_main
        and facts.spx_beside_common_dir
    )
    return Layout.POOL if pool else Layout.NON_COMPLIANT


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


def _git_out(*args: str, cwd: Path | None = None) -> str:
    proc = subprocess.run(
        ["git", *args],
        check=True,
        capture_output=True,
        text=True,
        cwd=None if cwd is None else str(cwd),
    )
    return proc.stdout.strip()


@dataclass(frozen=True)
class _WorktreeEntry:
    path: Path | None
    branch: str | None
    is_bare: bool


def _parse_worktree_list(porcelain: str) -> list[_WorktreeEntry]:
    """Parse ``git worktree list --porcelain`` output into structured entries."""
    entries: list[_WorktreeEntry] = []
    path: Path | None = None
    branch: str | None = None
    is_bare = False
    for line in porcelain.splitlines():
        if line.startswith("worktree "):
            path = Path(line[len("worktree ") :])
            branch, is_bare = None, False
        elif line.startswith("branch "):
            ref = line[len("branch ") :]
            branch = ref.removeprefix("refs/heads/")
        elif line == "bare":
            is_bare = True
        elif line == "":
            if path is not None:
                entries.append(_WorktreeEntry(path, branch, is_bare))
            path, branch, is_bare = None, None, False
    if path is not None:
        entries.append(_WorktreeEntry(path, branch, is_bare))
    return entries


def probe(path: Path) -> GitFacts:
    """Read the :class:`GitFacts` of the checkout containing ``path`` with git."""
    common_dir = Path(
        _git_out("rev-parse", "--path-format=absolute", "--git-common-dir", cwd=path)
    )
    container = common_dir.parent
    common_dir_is_bare = (
        _git_out("--git-dir", str(common_dir), "rev-parse", "--is-bare-repository")
        == "true"
    )

    entries = _parse_worktree_list(
        _git_out("worktree", "list", "--porcelain", cwd=path)
    )
    working = [e for e in entries if not e.is_bare]
    has_linked_worktrees = len(working) > 1

    main_entry = next((e for e in working if e.branch == "main"), None)
    main_present = main_entry is not None
    main_beside = False
    main_tracks = False
    if main_entry is not None and main_entry.path is not None:
        main_beside = main_entry.path.resolve().parent == container.resolve()
        try:
            upstream = _git_out(
                "rev-parse", "--abbrev-ref", "main@{upstream}", cwd=main_entry.path
            )
            main_tracks = upstream == "origin/main"
        except subprocess.CalledProcessError:
            main_tracks = False

    spx_beside = (container / ".spx").is_dir()

    return GitFacts(
        common_dir_is_bare=common_dir_is_bare,
        has_linked_worktrees=has_linked_worktrees,
        main_worktree_present=main_present,
        main_worktree_beside_common_dir=main_beside,
        main_tracks_origin_main=main_tracks,
        spx_beside_common_dir=spx_beside,
    )


@dataclass(frozen=True)
class ProvisionResult:
    """The paths a provisioning run created or relocated."""

    container: Path
    bare_dir: Path
    main_worktree: Path
    pool_worktrees: tuple[Path, ...]
    spx_dir: Path


def provision(
    *,
    container: Path,
    repo_name: str,
    origin_url: str,
    pool_worktree_names: tuple[str, ...] = (),
    carry_spx: Path | None = None,
) -> ProvisionResult:
    """Provision the bare-repository worktree pool in ``container``.

    Clones ``origin_url`` bare into ``{repo_name}.git``, restores the
    ``origin/*`` fetch refspec a bare clone omits, adds a sibling ``main``
    worktree tracking ``origin/main`` and one detached worktree per
    ``pool_worktree_names`` at the ``origin/main`` tip, and places ``.spx/``
    beside the bare dir — moving ``carry_spx`` there when given, else creating it.
    """
    container.mkdir(parents=True, exist_ok=True)
    bare_dir = container / f"{repo_name}.git"
    subprocess.run(
        ["git", "clone", "--quiet", "--bare", origin_url, str(bare_dir)],
        check=True,
        capture_output=True,
    )
    # Bare clones do not set up origin/* tracking refs — restore the refspec.
    _git(
        bare_dir, "config", "remote.origin.fetch", "+refs/heads/*:refs/remotes/origin/*"
    )
    _git(bare_dir, "fetch", "--quiet", "origin")

    main_worktree = container / "main"
    _git(bare_dir, "worktree", "add", "--quiet", str(main_worktree), "main")
    _git(main_worktree, "branch", "--set-upstream-to=origin/main", "main")

    pool_worktrees: list[Path] = []
    for name in pool_worktree_names:
        worktree = container / name
        _git(
            bare_dir,
            "worktree",
            "add",
            "--quiet",
            "--detach",
            str(worktree),
            "origin/main",
        )
        pool_worktrees.append(worktree)

    spx_dir = container / ".spx"
    if carry_spx is not None:
        if spx_dir.exists():
            raise FileExistsError(
                f"{spx_dir} already exists; provision into a container without a .spx/ "
                f"so the carried directory is not nested inside it"
            )
        shutil.move(str(carry_spx), str(spx_dir))
    else:
        spx_dir.mkdir(exist_ok=True)

    return ProvisionResult(
        container=container,
        bare_dir=bare_dir,
        main_worktree=main_worktree,
        pool_worktrees=tuple(pool_worktrees),
        spx_dir=spx_dir,
    )


def _cmd_classify(args: argparse.Namespace) -> int:
    facts = probe(Path(args.path))
    print(json.dumps({"layout": str(classify(facts)), "facts": asdict(facts)}))
    return 0


def _cmd_provision(args: argparse.Namespace) -> int:
    if args.from_checkout is not None:
        prior = Path(args.from_checkout)
        origin_url = _git_out("remote", "get-url", "origin", cwd=prior)
        prior_spx = prior / ".spx"
        carry_spx = prior_spx if prior_spx.is_dir() else None
    else:
        origin_url = args.origin
        carry_spx = None
    result = provision(
        container=Path(args.container),
        repo_name=args.repo,
        origin_url=origin_url,
        pool_worktree_names=tuple(args.worktree),
        carry_spx=carry_spx,
    )
    print(
        json.dumps(
            {
                "container": str(result.container),
                "bare_dir": str(result.bare_dir),
                "main_worktree": str(result.main_worktree),
                "pool_worktrees": [str(p) for p in result.pool_worktrees],
                "spx_dir": str(result.spx_dir),
            }
        )
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    classify_parser = sub.add_parser(
        "classify", help="classify the layout of the checkout at --path"
    )
    classify_parser.add_argument("--path", default=".")
    classify_parser.set_defaults(func=_cmd_classify)

    provision_parser = sub.add_parser("provision", help="provision the bare-repo pool")
    provision_parser.add_argument("--container", required=True)
    provision_parser.add_argument("--repo", required=True)
    provision_parser.add_argument("--origin")
    provision_parser.add_argument("--from", dest="from_checkout")
    provision_parser.add_argument("--worktree", action="append", default=[])
    provision_parser.set_defaults(func=_cmd_provision)

    args = parser.parse_args(argv)
    if (
        args.command == "provision"
        and args.origin is None
        and args.from_checkout is None
    ):
        parser.error("provision requires --origin or --from")
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
