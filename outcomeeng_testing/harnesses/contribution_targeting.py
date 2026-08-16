"""Harness mediating the contribute plugin's shipped target resolver.

Loads the script from its authored location and offers a controlled command
runner in place of the GitHub CLI. Injection is sanctioned here because the
subject is an external-tool interaction protocol and its failure modes: the
resolver's whole job is reading `gh`'s JSON correctly and refusing to classify
when it cannot, and neither a real GitHub API nor a real repository can produce
an unrecognized permission value or an authenticated-but-unreadable base on
demand.

This harness owns mediation only — script loading, the runner, and the shapes of
`gh`'s responses. Every case, expectation, and comparison belongs to the test
files that link the assertions.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from collections.abc import Callable
from pathlib import Path
from types import ModuleType
from typing import Final, Protocol

from hypothesis import given, seed, settings

from outcomeeng_testing.generators.contribution_targeting import (
    fork_states,
    unrecognized_permissions,
)
from outcomeeng_testing.harnesses.property_evidence import run_replayable_property

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILLS_DIR = REPO_ROOT / "src" / "plugins" / "contribute" / "skills"
RESOLVER_SKILL = "upstream"
RESOLVER_RELPATH = ("scripts", "resolve_target.py")
SCRIPT = SKILLS_DIR.joinpath(RESOLVER_SKILL, *RESOLVER_RELPATH)

FORK = "silvarbor/example"
PARENT = "someone/example"

Responses = dict[tuple[str, ...], tuple[int, str, str]]


class CommandResultLike(Protocol):
    """The result shape the loaded resolver constructs."""

    returncode: int
    stdout: str
    stderr: str


class ResolutionLike(Protocol):
    """The resolution shape the loaded resolver returns."""

    classification: str
    base: str | None
    head: str | None
    permission: str | None
    detail: str


def load_resolver() -> ModuleType:
    """Import the shipped script from its authored path."""
    cached = sys.modules.get("resolve_target")
    if cached is not None:
        return cached
    spec = importlib.util.spec_from_file_location("resolve_target", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load the target resolver from {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    # Register before executing: `dataclasses` resolves a class's module through
    # `sys.modules` while processing field annotations, and an unregistered module
    # makes that lookup return None.
    sys.modules["resolve_target"] = module
    spec.loader.exec_module(module)
    return module


class RecordingRunner:
    """A controlled command runner that records every command it is asked to run."""

    def __init__(self, responses: Responses) -> None:
        self.responses = responses
        self.commands: list[tuple[str, ...]] = []

    def run(self, args: list[str]) -> CommandResultLike:
        key = tuple(args)
        self.commands.append(key)
        returncode, stdout, stderr = self.responses.get(
            key, (1, "", f"unexpected command: {' '.join(args)}")
        )
        result: CommandResultLike = load_resolver().CommandResult(
            returncode, stdout, stderr
        )
        return result


def checkout_response(is_fork: bool) -> tuple[int, str, str]:
    """What `gh repo view --json isFork,parent,nameWithOwner` reports for a checkout."""
    payload: dict[str, object] = {
        "isFork": is_fork,
        "nameWithOwner": FORK if is_fork else PARENT,
        "parent": {"nameWithOwner": PARENT} if is_fork else None,
    }
    return (0, json.dumps(payload), "")


def orphan_fork_response() -> tuple[int, str, str]:
    """A checkout `gh` reports as a fork while reporting no parent for it."""
    payload = {"isFork": True, "nameWithOwner": FORK, "parent": None}
    return (0, json.dumps(payload), "")


def checkout_view_key() -> tuple[str, ...]:
    """The checkout-view command the resolver issues, read from the resolver."""
    return tuple(load_resolver().CHECKOUT_VIEW_COMMAND)


def permission_key(base: str) -> tuple[str, ...]:
    """The permission-read command the resolver issues for `base`, read from it."""
    return tuple(load_resolver().permission_command(base))


def permission_response(value: str | None) -> tuple[int, str, str]:
    """What the permission read reports; `None` omits the field entirely."""
    payload = {} if value is None else {"viewerPermission": value}
    return (0, json.dumps(payload), "")


OWNERS: Final = ("operator", "silvarbor")


def account_lookups() -> Responses:
    """The account and organization reads the head search makes."""
    resolver = load_resolver()
    return {
        tuple(resolver.ACCOUNT_COMMAND): (0, json.dumps({"login": OWNERS[0]}), ""),
        tuple(resolver.ORGANIZATIONS_COMMAND): (
            0,
            json.dumps([{"login": OWNERS[1]}]),
            "",
        ),
    }


def fork_list_key(owner: str) -> tuple[str, ...]:
    """The fork-listing command the resolver issues for `owner`, read from it."""
    return tuple(load_resolver().fork_list_command(owner))


def fork_list_response(forks: list[tuple[str, str]]) -> tuple[int, str, str]:
    """What one owner's fork listing reports.

    Each entry is the fork's own `owner/name` paired with the `owner/name` it was
    forked from. `gh` reports that source as separate `owner.login` and `name`
    fields, which is the shape the resolver reads.
    """
    payload = [
        {
            "nameWithOwner": fork,
            "parent": {
                "owner": {"login": source.split("/")[0]},
                "name": source.split("/")[1],
            },
        }
        for fork, source in forks
    ]
    return (0, json.dumps(payload), "")


def head_search_lookups(matches: int) -> Responses:
    """Account, organization, and fork-listing reads yielding `matches` forks of PARENT.

    Matches are spread across the owners so a count above one is genuinely found
    in more than one place, which is the state the ambiguous classification names.
    Every owner also holds one fork of an unrelated repository, so a listing that
    matched on presence rather than on the source would classify wrongly.
    """
    lookups: Responses = dict(account_lookups())
    remaining = matches
    for index, owner in enumerate(OWNERS):
        forks = [(f"{owner}/unrelated", "someone-else/unrelated")]
        if remaining > 0:
            forks.append((f"{owner}/example", PARENT))
            remaining -= 1
        lookups[fork_list_key(owner)] = fork_list_response(forks)
        if index == len(OWNERS) - 1 and remaining > 0:
            raise ValueError(
                f"cannot place {matches} matches across {len(OWNERS)} owners"
            )
    return lookups


def resolve_with(responses: Responses) -> tuple[ResolutionLike, RecordingRunner]:
    """Run the shipped resolver against controlled `gh` responses."""
    runner = RecordingRunner(responses)
    resolution: ResolutionLike = load_resolver().resolve(runner)
    return resolution, runner


TARGETING_PROPERTY_EXAMPLES: Final = 100
TARGETING_PROPERTY_SEED: Final = 20260809
TARGETING_PROPERTY_REPLAY_PATH: Final = (
    "just test spx/43-contribute.enabler/21-targeting.enabler/tests/"
    "test_target_resolution.property.l1.py"
)


def run_unrecognized_permission_property(check: Callable[[bool, str], None]) -> None:
    """Drive `check` over fork states and permissions outside both buckets."""
    resolver = load_resolver()
    recognized: frozenset[str] = (
        resolver.CONTROLLED_PERMISSIONS | resolver.CONTRIBUTOR_PERMISSIONS
    )

    @seed(TARGETING_PROPERTY_SEED)
    @settings(
        max_examples=TARGETING_PROPERTY_EXAMPLES,
        deadline=None,
        print_blob=True,
    )
    @given(
        is_fork=fork_states(),
        permission=unrecognized_permissions(recognized),
    )
    def run(is_fork: bool, permission: str) -> None:
        check(is_fork, permission)

    run_replayable_property(
        run,
        seed_value=TARGETING_PROPERTY_SEED,
        replay_path=TARGETING_PROPERTY_REPLAY_PATH,
    )
