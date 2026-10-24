"""Classify and provision a repository's git worktree layout.

Stdlib-only (`python3` >= 3.11), portable across consumer checkouts. The skill
invokes this module as
``python3 "${CLAUDE_SKILL_DIR}/scripts/init_worktrees.py" <command> ...``.

Three layouts are recognized: a ``single`` working tree, a compliant bare-repo
worktree ``pool``, and ``non-compliant`` (anything matching neither). The pure
``classify`` function decides a layout from ``GitFacts``; ``probe`` reads those
facts from a real checkout with git; ``provision`` builds the pool — pushing a
prior checkout's local branches and tags to the remote, cloning the bare
repository, adding the repository-name main checkout and detached pool
worktrees, renaming an in-place prior checkout aside to a ``.migrate`` husk, and
carrying the prior checkout's gitignored state across (``.spx/`` to the container
level, every other gitignored path into the main checkout). The main checkout
is designated by the ``origin`` repository name and its sibling placement,
independent of the checked-out or default branch; it tracks the git-resolved
default branch (``origin/<default>``). The destructive removal of the prior husk
is never performed here: the skill emits that command for the operator.

Tested behaviors (verified over real git in temporary directories): ``classify``
maps every ``GitFacts`` combination to its layout; ``provision`` builds the bare
pool with detached worktrees, derives the repository name from both slash-form
and scp-like SSH origin URLs, pushes a prior checkout's local-only refs to the
remote, carries a prior ``.spx/`` across byte-for-byte plus other gitignored
paths into the main checkout, renames an in-place prior checkout aside, refuses
a non-in-place provision into a container that already holds ``.spx/``, and
designates the main checkout independent of the default branch; ``probe``
classifies single, pool, no-origin, and misnamed-checkout layouts; every pool
worktree resolves the one ``.spx/`` beside the git-common-dir.
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
    the ``main_worktree_*`` fields describe the main checkout's presence — a
    worktree whose directory basename equals the ``origin`` repository name — and
    its sibling placement next to the common dir; and ``spx_beside_common_dir``
    is whether ``.spx/`` sits next to the common dir. The main checkout is
    identified by repository name and placement, never by the branch it has
    checked out.
    """

    common_dir_is_bare: bool
    has_linked_worktrees: bool
    main_worktree_present: bool
    main_worktree_beside_common_dir: bool
    spx_beside_common_dir: bool


def classify(facts: GitFacts) -> Layout:
    """Map observable git facts to a layout verdict.

    A lone working tree on a non-bare repository is ``SINGLE``. A bare repository
    whose main checkout — the sibling worktree named for the repository — is
    present beside the common dir with ``.spx/`` beside it is ``POOL``.
    Everything else — linked worktrees on a non-bare root, or a bare pool missing
    the repository-name main checkout sibling or its sibling ``.spx/`` — is
    ``NON_COMPLIANT``.
    """
    if not facts.common_dir_is_bare:
        return Layout.SINGLE if not facts.has_linked_worktrees else Layout.NON_COMPLIANT
    pool = (
        facts.main_worktree_present
        and facts.main_worktree_beside_common_dir
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


def _gitignored_entries(repo: Path) -> list[str]:
    """Return ``repo``'s gitignored paths, directories collapsed, no trailing slash.

    Enumerated via ``git ls-files --others --ignored --exclude-standard
    --directory`` — the same source the carry moves — so the carry and the
    pre-carry guards agree on exactly what is gitignored, independent of which
    ``.gitignore`` pattern form (``.spx`` or ``.spx/``) matched.
    """
    listing = _git_out(
        "ls-files",
        "--others",
        "--ignored",
        "--exclude-standard",
        "--directory",
        cwd=repo,
    )
    entries: list[str] = []
    for raw in listing.splitlines():
        rel = raw.strip().rstrip("/")
        if rel:
            entries.append(rel)
    return entries


def _repo_name_from_url(url: str) -> str | None:
    """Return the repository basename of a git remote URL, or ``None``.

    The last path segment with any ``.git`` suffix removed, handling both
    slash-separated (HTTPS, filesystem) and colon-separated (scp-like SSH) URL
    forms. ``None`` when the URL yields no name.
    """
    tail = url.rstrip("/").rsplit("/", 1)[-1].rsplit(":", 1)[-1]
    return tail.removesuffix(".git") or None


def _origin_repo_name(path: Path) -> str | None:
    """Return the ``origin`` remote's repository basename, or ``None``.

    Reads ``git remote get-url origin`` from ``path`` and parses the name with
    :func:`_repo_name_from_url`. ``None`` when no ``origin`` remote is
    configured: such a checkout cannot host a main checkout identified by
    repository name.
    """
    try:
        url = _git_out("remote", "get-url", "origin", cwd=path)
    except subprocess.CalledProcessError:
        return None
    return _repo_name_from_url(url)


@dataclass(frozen=True)
class _WorktreeEntry:
    path: Path | None
    is_bare: bool


def _parse_worktree_list(porcelain: str) -> list[_WorktreeEntry]:
    """Parse ``git worktree list --porcelain`` output into structured entries."""
    entries: list[_WorktreeEntry] = []
    path: Path | None = None
    is_bare = False
    for line in porcelain.splitlines():
        if line.startswith("worktree "):
            path = Path(line[len("worktree ") :])
            is_bare = False
        elif line == "bare":
            is_bare = True
        elif line == "":
            if path is not None:
                entries.append(_WorktreeEntry(path, is_bare))
            path, is_bare = None, False
    if path is not None:
        entries.append(_WorktreeEntry(path, is_bare))
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

    repo_name = _origin_repo_name(path)
    main_entry = None
    if repo_name is not None:
        main_entry = next(
            (e for e in working if e.path is not None and e.path.name == repo_name),
            None,
        )
    main_present = main_entry is not None
    main_beside = False
    if main_entry is not None and main_entry.path is not None:
        main_beside = main_entry.path.resolve().parent == container.resolve()

    spx_beside = (container / ".spx").is_dir()

    return GitFacts(
        common_dir_is_bare=common_dir_is_bare,
        has_linked_worktrees=has_linked_worktrees,
        main_worktree_present=main_present,
        main_worktree_beside_common_dir=main_beside,
        spx_beside_common_dir=spx_beside,
    )


@dataclass(frozen=True)
class ProvisionResult:
    """The paths a provisioning run created or relocated.

    ``prior_husk`` is the renamed-aside prior checkout the operator removes after
    provisioning, or ``None`` when no in-place rename occurred (a fresh build, or
    a prior checkout at a path other than the target container).
    """

    container: Path
    bare_dir: Path
    main_worktree: Path
    pool_worktrees: tuple[Path, ...]
    spx_dir: Path
    prior_husk: Path | None = None


def _carry_gitignored(prior: Path, container: Path, main_worktree: Path) -> Path:
    """Move ``prior``'s gitignored artifacts into the new pool, return ``.spx/``.

    Gitignored state is the only state a remote cannot restore, so it is carried
    to its layout-correct home: ``.spx/`` to the container level beside the
    git-common-dir (where every pool worktree resolves it), and every other
    gitignored path into the ``main_worktree`` working tree. Enumerated via
    ``git ls-files --others --ignored --exclude-standard --directory`` so an
    ignored directory moves whole rather than file-by-file. ``.spx/`` is created
    empty when ``prior`` carries none.

    No carry destination can already exist: the ``.spx/`` home is verified absent
    by :func:`provision` before any building, and every other destination lies in
    the freshly-added ``main_worktree`` (tracked files only, which an
    untracked-ignored path can never collide with).
    """
    spx_dir = container / ".spx"
    for rel in _gitignored_entries(prior):
        src = prior / rel
        if not src.exists():
            continue
        dst = spx_dir if rel == ".spx" else main_worktree / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))
    spx_dir.mkdir(exist_ok=True)
    return spx_dir


def provision(
    *,
    container: Path,
    origin_url: str | None = None,
    from_checkout: Path | None = None,
    pool_worktree_names: tuple[str, ...] = (),
) -> ProvisionResult:
    """Provision the bare-repository worktree pool in ``container``.

    The layout is defined by the target state, not by the prior checkout's shape:
    the repository name comes from ``origin_url`` (or, with ``from_checkout``, from
    that checkout's ``origin`` remote) — the same source the classifier reads — so
    the provisioned main checkout's basename always matches the name
    classification resolves, taking no separate repository-name input.

    With ``from_checkout`` (a migration), every local branch and tag is first
    pushed to the remote so no local-only ref is lost; if the prior checkout
    occupies the target ``container`` path it is renamed aside to a ``.migrate``
    husk (reported in ``prior_husk`` for the operator to remove) so the pool can
    be built at the original path. Then ``origin_url`` is cloned bare into
    ``{repo}.git``, the ``origin/*`` fetch refspec a bare clone omits is restored,
    the default branch is resolved from the clone's HEAD, the main checkout is
    added at the repository-name sibling ``{repo}`` tracking ``origin/<default>``
    with one detached worktree per ``pool_worktree_names`` at the
    ``origin/<default>`` tip, and the prior checkout's gitignored artifacts are
    carried in via :func:`_carry_gitignored`. The prior husk is never deleted
    here — the skill emits that command for the operator.
    """
    if from_checkout is not None:
        from_checkout = Path(from_checkout)
        origin_url = _git_out("remote", "get-url", "origin", cwd=from_checkout)
    if origin_url is None:
        raise ValueError("provision requires origin_url or from_checkout")
    repo_name = _repo_name_from_url(origin_url)
    if repo_name is None:
        raise ValueError(
            f"cannot derive a repository name from origin URL: {origin_url!r}"
        )
    # The pool nests as <repo>/<repo>, so the container is the repository-name
    # directory — never the multi-repository workspace that holds it. Enforce it
    # here so a mis-pointed container cannot scatter the bare repo, .spx/, and
    # worktrees across the workspace — a layout the classifier would still call a
    # pool because it only checks placement relative to the git-common-dir.
    if container.name != repo_name:
        raise ValueError(
            f"container basename {container.name!r} must equal the repository name "
            f"{repo_name!r}: the pool nests as <repo>/<repo>, so --container is the "
            f"repository-name directory, not the workspace that holds it"
        )

    if from_checkout is not None:
        # The carry enumerates gitignored paths, so a .spx/ that is not gitignored
        # would be skipped and abandoned with the removed husk. Refuse before the
        # push or rename below so its session state is never silently lost.
        if (from_checkout / ".spx").exists() and ".spx" not in _gitignored_entries(
            from_checkout
        ):
            raise ValueError(
                f"{from_checkout / '.spx'} is not gitignored; add .spx/ to "
                f".gitignore in the prior checkout so its state is carried into the "
                f"pool rather than abandoned with the removed husk"
            )
        # All read-only guards passed; push every local branch and tag so the
        # remote holds every commit. A rejected push (a diverged branch) fails
        # fast rather than risking loss.
        _git(from_checkout, "push", "--quiet", "origin", "--all")
        _git(from_checkout, "push", "--quiet", "origin", "--tags")

    main_worktree = container / repo_name
    prior_husk: Path | None = None
    if from_checkout is not None and from_checkout.resolve() == container.resolve():
        prior_husk = from_checkout.with_name(f"{from_checkout.name}.migrate")
        if prior_husk.exists():
            # The push above has already run — safe and intentional, since the
            # husk's branches are on the remote; only the rename is blocked here.
            raise FileExistsError(
                f"{prior_husk} already exists; remove it before provisioning in place"
            )
        from_checkout.rename(prior_husk)
        from_checkout = prior_husk

    container.mkdir(parents=True, exist_ok=True)
    # Fail before building when the carry's .spx/ home is already occupied —
    # the only carry destination that can pre-exist, since every other gitignored
    # path lands in the freshly-built main checkout (a fresh `git worktree add`
    # holds tracked files only, and an untracked-ignored path cannot already
    # occupy it). Checking .spx/ here keeps a carry collision from leaving a
    # half-built pool behind. An in-place migration recreated the container empty
    # above, so container/.spx cannot pre-exist then — this guard only fires for a
    # non-in-place provision into a container that already holds .spx/.
    if from_checkout is not None and (container / ".spx").exists():
        raise FileExistsError(
            f"{container / '.spx'} already exists; cannot carry the prior checkout's "
            f".spx/ into a container that already holds one"
        )
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

    # A bare clone sets HEAD to the remote's default branch; resolve it there
    # rather than assuming a literal `main`.
    default_branch = _git_out("symbolic-ref", "--short", "HEAD", cwd=bare_dir)

    _git(bare_dir, "worktree", "add", "--quiet", str(main_worktree), default_branch)
    _git(
        main_worktree,
        "branch",
        f"--set-upstream-to=origin/{default_branch}",
        default_branch,
    )

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
            f"origin/{default_branch}",
        )
        pool_worktrees.append(worktree)

    if from_checkout is not None:
        spx_dir = _carry_gitignored(from_checkout, container, main_worktree)
    else:
        spx_dir = container / ".spx"
        spx_dir.mkdir(exist_ok=True)

    return ProvisionResult(
        container=container,
        bare_dir=bare_dir,
        main_worktree=main_worktree,
        pool_worktrees=tuple(pool_worktrees),
        spx_dir=spx_dir,
        prior_husk=prior_husk,
    )


def _cmd_classify(args: argparse.Namespace) -> int:
    facts = probe(Path(args.path))
    print(json.dumps({"layout": str(classify(facts)), "facts": asdict(facts)}))
    return 0


def _cmd_provision(args: argparse.Namespace) -> int:
    from_checkout = Path(args.from_checkout) if args.from_checkout is not None else None
    result = provision(
        container=Path(args.container),
        origin_url=args.origin,
        from_checkout=from_checkout,
        pool_worktree_names=tuple(args.worktree),
    )
    print(
        json.dumps(
            {
                "container": str(result.container),
                "bare_dir": str(result.bare_dir),
                "main_worktree": str(result.main_worktree),
                "pool_worktrees": [str(p) for p in result.pool_worktrees],
                "spx_dir": str(result.spx_dir),
                "prior_husk": (
                    str(result.prior_husk) if result.prior_husk is not None else None
                ),
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
    # --origin (fresh build) and --from (migration) are mutually exclusive and
    # one is required: with --from the origin URL is read from the prior
    # checkout, so passing --origin too would be silently ignored.
    source = provision_parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--origin")
    source.add_argument("--from", dest="from_checkout")
    provision_parser.add_argument("--worktree", action="append", default=[])
    provision_parser.set_defaults(func=_cmd_provision)

    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
