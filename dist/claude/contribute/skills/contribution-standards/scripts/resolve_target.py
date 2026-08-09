"""Resolve the base repository, head repository, and operator permission for one contribution.

`gh` resolves a fork's base to its parent, so a command that names no repository
says nothing about where its artifact lands: a branch pushed to one repository and
a pull request opened from it can reach a different organization entirely. This
script performs that resolution once and emits a classification the contribute
skills act on, so the decision never depends on reading `isFork`, `parent`, and
`viewerPermission` by eye.

Plugin-local by design: this is runtime-specific adapter logic over the GitHub CLI.
Moving it into a runtime-neutral CLI would couple that CLI to one external runtime,
so it stays beside the skills that own the GitHub boundary — deterministic, bounded,
standard-library-only, and independently tested.

Portability: stdlib only — no third-party packages, no `uv`, no project imports.
This script ships into consumer plugin trees where only the standard library exists.
"""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass, field
from typing import Protocol

CONTROLLED_PERMISSIONS = frozenset({"ADMIN", "MAINTAIN", "WRITE"})
CONTRIBUTOR_PERMISSIONS = frozenset({"READ", "NONE"})


@dataclass(frozen=True)
class CommandResult:
    """One completed command invocation."""

    returncode: int
    stdout: str
    stderr: str


class CommandRunner(Protocol):
    """The external-command collaborator this module depends on."""

    def run(self, args: list[str]) -> CommandResult: ...


class SubprocessRunner:
    """The production adapter, bound at the entrypoint."""

    def run(self, args: list[str]) -> CommandResult:
        completed = subprocess.run(args, capture_output=True, text=True, check=False)
        return CommandResult(completed.returncode, completed.stdout, completed.stderr)


@dataclass(frozen=True)
class Resolution:
    """The resolved contribution target."""

    classification: str
    base: str | None = None
    head: str | None = None
    permission: str | None = None
    fork_present: bool = False
    fork_candidates: list[str] = field(default_factory=list)
    detail: str = ""

    def as_dict(self) -> dict[str, object]:
        return {
            "classification": self.classification,
            "base": self.base,
            "head": self.head,
            "permission": self.permission,
            "fork": {"present": self.fork_present, "candidates": self.fork_candidates},
            "detail": self.detail,
        }


def _json_field(
    runner: CommandRunner, args: list[str]
) -> tuple[dict[str, object] | None, str]:
    result = runner.run(args)
    if result.returncode != 0:
        return None, (
            result.stderr or result.stdout
        ).strip() or f"{' '.join(args)} failed"
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        return (
            None,
            f"{' '.join(args)} returned output that is not JSON: {result.stdout[:200]!r}",
        )
    if not isinstance(payload, dict):
        return (
            None,
            f"{' '.join(args)} returned {type(payload).__name__}, expected an object",
        )
    return payload, ""


def _fork_candidates(runner: CommandRunner) -> list[str]:
    """Accounts and organizations that could hold a fork, best effort."""
    candidates: list[str] = []
    user, _ = _json_field(runner, ["gh", "api", "user"])
    if user and isinstance(user.get("login"), str):
        candidates.append(user["login"])
    result = runner.run(["gh", "api", "user/orgs"])
    if result.returncode == 0:
        try:
            orgs = json.loads(result.stdout)
        except json.JSONDecodeError:
            orgs = []
        if isinstance(orgs, list):
            candidates.extend(
                org["login"]
                for org in orgs
                if isinstance(org, dict) and isinstance(org.get("login"), str)
            )
    return candidates


def resolve(runner: CommandRunner) -> Resolution:
    """Classify the contribution target from the current checkout."""
    checkout, detail = _json_field(
        runner, ["gh", "repo", "view", "--json", "isFork,parent,nameWithOwner"]
    )
    if checkout is None:
        return Resolution("blocked", detail=detail)

    head = checkout.get("nameWithOwner")
    if not isinstance(head, str) or not head:
        return Resolution(
            "blocked", detail="gh reported no nameWithOwner for this checkout"
        )

    parent = checkout.get("parent")
    is_fork = bool(checkout.get("isFork")) and isinstance(parent, dict)
    base = parent.get("nameWithOwner") if is_fork and isinstance(parent, dict) else head
    if not isinstance(base, str) or not base:
        return Resolution(
            "blocked", head=head, detail="gh reported a fork with no parent repository"
        )

    permissions, detail = _json_field(
        runner, ["gh", "repo", "view", base, "--json", "viewerPermission"]
    )
    if permissions is None:
        return Resolution("blocked", base=base, head=head, detail=detail)

    permission = permissions.get("viewerPermission")
    if not isinstance(permission, str) or not permission:
        return Resolution(
            "blocked",
            base=base,
            head=head,
            detail=(
                f"gh reported no viewerPermission for {base}; permission is never inferred "
                "from a git remote, the authenticated account, or a successful push"
            ),
        )

    if permission in CONTROLLED_PERMISSIONS:
        return Resolution(
            "controlled",
            base=base,
            head=head,
            permission=permission,
            fork_present=is_fork,
            detail=f"the operator controls {base} ({permission})",
        )

    if permission not in CONTRIBUTOR_PERMISSIONS:
        return Resolution(
            "blocked",
            base=base,
            head=head,
            permission=permission,
            detail=f"gh reported an unrecognized viewerPermission {permission!r} for {base}",
        )

    if is_fork:
        return Resolution(
            "parent-contribution",
            base=base,
            head=head,
            permission=permission,
            fork_present=True,
            detail=f"{head} is a fork of {base} ({permission})",
        )

    return Resolution(
        "fork-absent",
        base=base,
        head=None,
        permission=permission,
        fork_present=False,
        fork_candidates=_fork_candidates(runner),
        detail=(
            f"no fork of {base} to contribute from; run "
            f"`gh repo fork {base} --org <destination>` after choosing a destination"
        ),
    )


def main() -> int:
    resolution = resolve(SubprocessRunner())
    print(json.dumps(resolution.as_dict(), indent=2))
    return 0 if resolution.classification != "blocked" else 1


if __name__ == "__main__":
    sys.exit(main())
