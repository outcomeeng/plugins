"""Resolve the base repository, head repository, and operator permission for one contribution.

`gh` resolves a fork's base to its parent, so a command that names no repository
says nothing about where its artifact lands: a branch pushed to one repository and
a pull request opened from it can reach a different organization entirely. This
script performs that resolution once and emits a classification the contribute
skills act on, so the decision never depends on reading `isFork`, `parent`, and
`viewerPermission` by eye. The rule binds this script's own reads first: the
checkout's repository is read by naming `origin`, because a nameless read in a
fork checkout reports the parent and hides the head the contribution pushes from.

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
from enum import StrEnum
from typing import Final, Protocol

CONTROLLED_PERMISSIONS = frozenset({"ADMIN", "MAINTAIN", "WRITE"})
# TRIAGE carries issue and pull-request management without code-write access, so
# it contributes rather than controls. Omitting it blocks a real collaborator.
CONTRIBUTOR_PERMISSIONS = frozenset({"READ", "TRIAGE", "NONE"})


class Classification(StrEnum):
    """The classifications one resolution can produce.

    The skills branch on these values and the emitted JSON carries them, so they
    are the resolver's vocabulary rather than four literals repeated across its
    own branches.
    """

    CONTROLLED = "controlled"
    UPSTREAM_CONTRIBUTION = "upstream-contribution"
    HEAD_AMBIGUOUS = "head-ambiguous"
    FORK_ABSENT = "fork-absent"
    BLOCKED = "blocked"


# The invocations this resolution makes, named here so a caller reading the
# resolver's interaction protocol reads the commands themselves rather than a
# copy that drifts when an argument list changes.
#
# The checkout's own repository is read from `origin` rather than from `gh`'s
# default resolution. `gh repo view` with no repository resolves a fork checkout
# to its parent, so a nameless read reports the base where the checkout was
# asked for — the same default every write in this plugin is forbidden from
# accepting, and the one that decides whether a head exists at all.
CHECKOUT_REMOTE_COMMAND: Final[tuple[str, ...]] = ("git", "remote", "get-url", "origin")
ACCOUNT_COMMAND: Final[tuple[str, ...]] = ("gh", "api", "user")
ORGANIZATIONS_COMMAND: Final[tuple[str, ...]] = ("gh", "api", "user/orgs")


def checkout_view_command(repository: str) -> tuple[str, ...]:
    """The command that reads `repository`'s fork state, parent, and full name.

    `repository` is whatever `origin` reports, passed through unchanged. `gh`
    normalizes every remote form to the same repository — the HTTPS URL, the
    `ssh://` URL, and the SCP-style `git@host:owner/name.git` a push-capable
    contributor checkout commonly carries — so no form needs parsing here, and
    parsing one would be a second implementation of a mapping `gh` already owns.
    """
    return ("gh", "repo", "view", repository, "--json", "isFork,parent,nameWithOwner")


# How many forks one owner's listing returns. An operator holding more forks than
# this under one account would have a match fall outside the page, so the bound is
# generous rather than tuned.
FORK_LIST_LIMIT: Final = 200


def permission_command(base: str) -> tuple[str, ...]:
    """The command that reads the operator's permission on `base`."""
    return ("gh", "repo", "view", base, "--json", "viewerPermission")


def fork_list_command(owner: str) -> tuple[str, ...]:
    """The command that lists `owner`'s forks with the repository each came from."""
    return (
        "gh",
        "repo",
        "list",
        owner,
        "--fork",
        "--limit",
        str(FORK_LIST_LIMIT),
        "--json",
        "nameWithOwner,parent",
    )


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

    classification: Classification
    base: str | None = None
    head: str | None = None
    permission: str | None = None
    fork_matches: list[str] = field(default_factory=list)
    fork_candidates: list[str] = field(default_factory=list)
    detail: str = ""

    def as_dict(self) -> dict[str, object]:
        return {
            "classification": self.classification,
            "base": self.base,
            "head": self.head,
            "permission": self.permission,
            "fork": {"matches": self.fork_matches, "candidates": self.fork_candidates},
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


def _fork_candidates(runner: CommandRunner) -> tuple[list[str], str]:
    """Accounts and organizations that could hold a fork, and why enumeration stopped.

    A failed lookup leaves the search domain unknown rather than smaller. Dropping
    an unreadable account would let the search conclude absence from the accounts
    it happened to read, which is the inference the absence rule forbids, so the
    failure travels back and blocks instead.
    """
    user, detail = _json_field(runner, list(ACCOUNT_COMMAND))
    if user is None:
        return [], detail
    login = user.get("login")
    if not isinstance(login, str) or not login:
        return [], "gh reported no login for the authenticated account"
    candidates = [login]

    result = runner.run(list(ORGANIZATIONS_COMMAND))
    if result.returncode != 0:
        return candidates, (
            result.stderr or result.stdout
        ).strip() or f"{' '.join(ORGANIZATIONS_COMMAND)} failed"
    try:
        orgs = json.loads(result.stdout)
    except json.JSONDecodeError:
        return (
            candidates,
            f"{' '.join(ORGANIZATIONS_COMMAND)} returned output that is not JSON",
        )
    if not isinstance(orgs, list):
        return (
            candidates,
            f"{' '.join(ORGANIZATIONS_COMMAND)} returned {type(orgs).__name__}, expected a list",
        )
    candidates.extend(
        org["login"]
        for org in orgs
        if isinstance(org, dict) and isinstance(org.get("login"), str)
    )
    return candidates, ""


def _forked_from(entry: object) -> str | None:
    """The `owner/name` a repository record reports as its parent.

    Every `gh --json parent` field reports the source as separate `owner.login`
    and `name` fields — the fork listing and the single-repository view alike —
    and never as a `nameWithOwner` inside the parent object. Both readings join
    the two here into the one spelling every comparison uses.
    """
    if not isinstance(entry, dict):
        return None
    parent = entry.get("parent")
    if not isinstance(parent, dict):
        return None
    owner = parent.get("owner")
    name = parent.get("name")
    login = owner.get("login") if isinstance(owner, dict) else None
    if not isinstance(login, str) or not isinstance(name, str) or not login or not name:
        return None
    return f"{login}/{name}"


def _forks_of(runner: CommandRunner, owner: str, base: str) -> tuple[list[str], str]:
    """Every fork of `base` that `owner` holds, and why the listing stopped short.

    GitHub preserves a repository's case and matches it without one, so a fork of
    `onevcat/Prowl` is the same repository an operator names `onevcat/prowl`.
    Comparing case-sensitively would report a real fork as absent.

    A listing that fills the page is indistinguishable from one that overflows it,
    so a full page reports incompleteness rather than the matches it happened to
    contain.
    """
    result = runner.run(list(fork_list_command(owner)))
    if result.returncode != 0:
        return [], (
            result.stderr or result.stdout
        ).strip() or f"listing {owner}'s forks failed"
    try:
        listing = json.loads(result.stdout)
    except json.JSONDecodeError:
        return [], f"listing {owner}'s forks returned output that is not JSON"
    if not isinstance(listing, list):
        return (
            [],
            f"listing {owner}'s forks returned {type(listing).__name__}, expected a list",
        )
    if len(listing) >= FORK_LIST_LIMIT:
        return [], (
            f"{owner} holds at least {FORK_LIST_LIMIT} forks, which is the whole page "
            f"this search reads, so a fork of {base} beyond it would go unseen"
        )
    wanted = base.casefold()
    matches: list[str] = []
    for entry in listing:
        source = _forked_from(entry)
        if source is None or source.casefold() != wanted:
            continue
        name = entry.get("nameWithOwner") if isinstance(entry, dict) else None
        if isinstance(name, str) and name:
            matches.append(name)
    return matches, ""


def _search_for_head(
    runner: CommandRunner, base: str
) -> tuple[list[str], list[str], str]:
    """Forks of `base` the operator holds, the owners searched, and why the search stopped.

    The owners are the search domain and double as the destinations a fork could
    be created in, so one enumeration answers both "where is the head" and, when
    nothing matches, "where could one go".

    A non-empty third value means the search did not cover its domain, so its
    matches establish nothing about absence.
    """
    owners, detail = _fork_candidates(runner)
    if detail:
        return [], owners, detail
    matches: list[str] = []
    for owner in owners:
        found, failure = _forks_of(runner, owner, base)
        if failure:
            return [], owners, failure
        matches.extend(found)
    return matches, owners, ""


def resolve(runner: CommandRunner) -> Resolution:
    """Classify the contribution target from the current checkout."""
    remote = runner.run(list(CHECKOUT_REMOTE_COMMAND))
    origin = remote.stdout.strip()
    if remote.returncode != 0 or not origin:
        return Resolution(
            Classification.BLOCKED,
            detail=(
                remote.stderr.strip()
                or "git reported no origin remote for this checkout, so the "
                "repository the contribution pushes from is unknown"
            ),
        )

    checkout, detail = _json_field(runner, list(checkout_view_command(origin)))
    if checkout is None:
        return Resolution(Classification.BLOCKED, detail=detail)

    head = checkout.get("nameWithOwner")
    if not isinstance(head, str) or not head:
        return Resolution(
            Classification.BLOCKED,
            detail="gh reported no nameWithOwner for this checkout",
        )

    is_fork = bool(checkout.get("isFork"))
    parent_name = _forked_from(checkout)
    if is_fork and not parent_name:
        # A fork whose parent gh does not report must never fall back to itself:
        # the operator usually controls their own fork, so treating it as the base
        # would classify a contribution as `controlled` and send it nowhere.
        return Resolution(
            Classification.BLOCKED,
            head=head,
            detail="gh reported a fork with no parent repository",
        )
    base = parent_name if is_fork else head
    if not isinstance(base, str) or not base:
        return Resolution(
            Classification.BLOCKED,
            head=head,
            detail="gh reported no base repository for this checkout",
        )

    permissions, detail = _json_field(runner, list(permission_command(base)))
    if permissions is None:
        return Resolution(Classification.BLOCKED, base=base, head=head, detail=detail)

    permission = permissions.get("viewerPermission")
    if not isinstance(permission, str) or not permission:
        return Resolution(
            Classification.BLOCKED,
            base=base,
            head=head,
            detail=(
                f"gh reported no viewerPermission for {base}; permission is never inferred "
                "from a git remote, the authenticated account, or a successful push"
            ),
        )

    if permission in CONTROLLED_PERMISSIONS:
        return Resolution(
            Classification.CONTROLLED,
            base=base,
            head=head,
            permission=permission,
            detail=f"the operator controls {base} ({permission})",
        )

    if permission not in CONTRIBUTOR_PERMISSIONS:
        return Resolution(
            Classification.BLOCKED,
            base=base,
            head=head,
            permission=permission,
            detail=f"gh reported an unrecognized viewerPermission {permission!r} for {base}",
        )

    if is_fork:
        return Resolution(
            Classification.UPSTREAM_CONTRIBUTION,
            base=base,
            head=head,
            permission=permission,
            fork_matches=[head],
            detail=f"{head} is a fork of {base} ({permission})",
        )

    # The checkout is the base itself, which is an ordinary way to arrive: a clone
    # of the upstream carries no head. Search the operator's accounts for one
    # rather than reporting absence the checkout cannot establish.
    matches, owners, search_detail = _search_for_head(runner, base)

    if search_detail:
        # A search that did not cover its domain proves nothing about absence, and
        # reporting `fork-absent` here would hand the operator a `gh repo fork`
        # command GitHub rejects whenever the unread account already holds one.
        return Resolution(
            Classification.BLOCKED,
            base=base,
            head=None,
            permission=permission,
            fork_candidates=owners,
            detail=(
                f"the search for a fork of {base} did not cover the operator's "
                f"accounts, so absence is unestablished: {search_detail}"
            ),
        )

    if len(matches) == 1:
        return Resolution(
            Classification.UPSTREAM_CONTRIBUTION,
            base=base,
            head=matches[0],
            permission=permission,
            fork_matches=matches,
            detail=f"{matches[0]} is a fork of {base} ({permission})",
        )

    if matches:
        return Resolution(
            Classification.HEAD_AMBIGUOUS,
            base=base,
            head=None,
            permission=permission,
            fork_matches=matches,
            fork_candidates=owners,
            detail=(
                f"{len(matches)} forks of {base} to contribute from "
                f"({', '.join(matches)}); choosing among them is the operator's"
            ),
        )

    return Resolution(
        Classification.FORK_ABSENT,
        base=base,
        head=None,
        permission=permission,
        fork_candidates=owners,
        detail=(
            f"no fork of {base} under {', '.join(owners) or 'any account read'}; run "
            f"`gh repo fork {base} --org <destination>` after choosing a destination"
        ),
    )


def main() -> int:
    resolution = resolve(SubprocessRunner())
    print(json.dumps(resolution.as_dict(), indent=2))
    return 0 if resolution.classification is not Classification.BLOCKED else 1


if __name__ == "__main__":
    sys.exit(main())
