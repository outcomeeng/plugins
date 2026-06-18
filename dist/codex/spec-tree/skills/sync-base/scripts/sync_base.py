"""Bring a branch behind its fetched base current by rebasing.

Synchronization fetches the branch's base, detects whether the branch is
behind the remote-tracking base ref ``origin/<base>``, and rebases the
branch's own commits onto that ref. The mechanism is rebase, never
``git reset``: rebase replays the branch's commits onto the advanced base,
preserving the branch's work, where ``reset`` would repoint the branch while
leaving the working tree at the old base and silently revert merged changes.

A clean rebase runs without operator interaction. The only operator
touch-point is a rebase conflict that cannot be resolved autonomously or a
hard git failure; on a conflict the rebase is aborted (leaving the branch and
working tree intact) and the ``SYNC_BASE`` action token is surfaced.

The base ref and its remote-tracking form are resolved through the shared
changeset-scope primitives, never re-derived here. The primitives ship under a
runtime-substituted plugin skill directory and are not importable by package
name, so they are loaded through ``importlib`` and re-exported with object
identity preserved.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import pathlib
import subprocess
import sys
from dataclasses import dataclass
from enum import Enum
from types import ModuleType

_CHANGESET_SCOPE_PATH = (
    pathlib.Path(__file__).resolve().parent.parent.parent
    / "scope-changeset"
    / "scripts"
    / "changeset_scope.py"
)

#: Action token surfaced when a rebase conflict needs operator resolution.
SYNC_BASE_TOKEN = "SYNC_BASE"


def _load_changeset_scope() -> ModuleType:
    """Load the canonical ``changeset_scope`` module via importlib and cache it."""
    cached = sys.modules.get("changeset_scope")
    if cached is not None:
        return cached
    spec = importlib.util.spec_from_file_location(
        "changeset_scope", _CHANGESET_SCOPE_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load changeset_scope from {_CHANGESET_SCOPE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["changeset_scope"] = module
    spec.loader.exec_module(module)
    return module


_changeset_scope = _load_changeset_scope()

# Re-export the canonical primitives. ``is`` identity holds — these are the same
# function/class objects the changeset-scope module defines, so sync-base never
# re-implements base, remote-tracking, or branch derivation.
detect_base_ref = _changeset_scope.detect_base_ref
remote_tracking_ref = _changeset_scope.remote_tracking_ref
detect_current_branch = _changeset_scope.detect_current_branch
DetachedHeadError = _changeset_scope.DetachedHeadError


class SyncStatus(str, Enum):
    """Terminal outcome of a base-synchronization run."""

    ALREADY_CURRENT = "already_current"
    REBASED = "rebased"
    CONFLICT = "conflict"
    GIT_FAILURE = "git_failure"


#: Process exit code per terminal status.
_EXIT_CODES = {
    SyncStatus.ALREADY_CURRENT: 0,
    SyncStatus.REBASED: 0,
    SyncStatus.CONFLICT: 3,
    SyncStatus.GIT_FAILURE: 1,
}


@dataclass(frozen=True)
class SyncBaseResult:
    """The outcome of a synchronization run.

    ``base_ref`` is the bare base-branch name; ``remote_ref`` is its
    remote-tracking form ``origin/<base>``. ``branch`` is the synchronized
    branch, or ``None`` when no branch could be resolved (detached HEAD).
    """

    status: SyncStatus
    base_ref: str
    remote_ref: str
    branch: str | None
    detail: str

    @property
    def action_token(self) -> str | None:
        """``SYNC_BASE`` when a conflict needs the operator, else ``None``."""
        return SYNC_BASE_TOKEN if self.status is SyncStatus.CONFLICT else None

    @property
    def exit_code(self) -> int:
        """Process exit code for this status."""
        return _EXIT_CODES[self.status]

    def to_json_dict(self) -> dict[str, str | None]:
        """Serialize to a JSON-ready dict with stable keys."""
        return {
            "status": self.status.value,
            "base_ref": self.base_ref,
            "remote_ref": self.remote_ref,
            "branch": self.branch,
            "detail": self.detail,
            "action_token": self.action_token,
        }


def _git(repo: pathlib.Path, *args: str) -> subprocess.CompletedProcess[str]:
    """Run a git command in ``repo``, capturing output without raising."""
    return subprocess.run(  # noqa: S603 — fixed argv, no shell, args from callers
        ["git", *args],  # noqa: S607
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )


def sync_base(
    repo: pathlib.Path, *, base_ref: str | None = None, fetch: bool = True
) -> SyncBaseResult:
    """Bring ``repo``'s current branch current with its fetched base.

    ``base_ref`` is the bare base-branch name to synchronize onto. When omitted
    it is resolved from ``origin/HEAD`` through the shared changeset-scope
    primitives; callers that track a non-default base (a stacked pull request
    whose base is another feature branch) pass it explicitly. The base is
    fetched (unless ``fetch=False``) and the branch is rebased onto
    ``origin/<base>`` when it is behind. Returns a :class:`SyncBaseResult`;
    never raises for an ordinary git outcome.
    """
    if base_ref is None:
        base_ref = detect_base_ref(repo, strict=False)
    remote_ref = remote_tracking_ref(base_ref)

    try:
        branch = detect_current_branch(repo)
    except DetachedHeadError:
        return SyncBaseResult(
            SyncStatus.GIT_FAILURE,
            base_ref,
            remote_ref,
            None,
            "detached HEAD: no branch to rebase",
        )

    if fetch:
        fetched = _git(repo, "fetch", "origin", base_ref)
        if fetched.returncode != 0:
            return SyncBaseResult(
                SyncStatus.GIT_FAILURE,
                base_ref,
                remote_ref,
                branch,
                f"git fetch origin {base_ref} failed: {fetched.stderr.strip()}",
            )

    resolved = _git(
        repo, "rev-parse", "--verify", "--quiet", f"{remote_ref}^{{commit}}"
    )
    if resolved.returncode != 0:
        return SyncBaseResult(
            SyncStatus.GIT_FAILURE,
            base_ref,
            remote_ref,
            branch,
            f"base ref {remote_ref} does not resolve to a commit",
        )

    behind = _git(repo, "rev-list", "--count", f"HEAD..{remote_ref}")
    if behind.returncode != 0:
        return SyncBaseResult(
            SyncStatus.GIT_FAILURE,
            base_ref,
            remote_ref,
            branch,
            f"cannot compute commits behind {remote_ref}: {behind.stderr.strip()}",
        )
    if int(behind.stdout.strip() or "0") == 0:
        return SyncBaseResult(
            SyncStatus.ALREADY_CURRENT,
            base_ref,
            remote_ref,
            branch,
            f"branch {branch} is already current with {remote_ref}",
        )

    rebased = _git(repo, "rebase", remote_ref)
    if rebased.returncode == 0:
        return SyncBaseResult(
            SyncStatus.REBASED,
            base_ref,
            remote_ref,
            branch,
            f"rebased {branch} onto {remote_ref}",
        )

    # A conflict (or any rebase failure) leaves a partial rebase in progress.
    # Abort it so the branch and working tree return to their pre-rebase state;
    # never fall back to git reset.
    _git(repo, "rebase", "--abort")
    return SyncBaseResult(
        SyncStatus.CONFLICT,
        base_ref,
        remote_ref,
        branch,
        f"rebase of {branch} onto {remote_ref} conflicts; manual resolution required",
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
    )
    print(json.dumps(result.to_json_dict()))
    return result.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
