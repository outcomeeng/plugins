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
import shutil
import sys
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
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
PROVIDER_SKILL = "contribution-standards"
ENTRYPOINT_RELPATH = ("scripts", "resolve_target.py")
SCRIPT = SKILLS_DIR.joinpath(PROVIDER_SKILL, *ENTRYPOINT_RELPATH)

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


def account_lookups() -> Responses:
    """The account and organization reads the fork-absent path makes."""
    resolver = load_resolver()
    return {
        tuple(resolver.ACCOUNT_COMMAND): (0, json.dumps({"login": "operator"}), ""),
        tuple(resolver.ORGANIZATIONS_COMMAND): (
            0,
            json.dumps([{"login": "silvarbor"}]),
            "",
        ),
    }


def resolve_with(responses: Responses) -> tuple[ResolutionLike, RecordingRunner]:
    """Run the shipped resolver against controlled `gh` responses."""
    runner = RecordingRunner(responses)
    resolution: ResolutionLike = load_resolver().resolve(runner)
    return resolution, runner


def consumer_entrypoints() -> tuple[Path, ...]:
    """Every consuming skill's own resolver entrypoint, discovered from the tree.

    Discovered rather than enumerated: a skill added to the plugin enters this
    domain without a case being written for it here. The provider's own script is
    excluded — it is the shared resolver, not an entrypoint reaching one.
    """
    pattern = str(Path("*").joinpath(*ENTRYPOINT_RELPATH))
    return tuple(sorted(p for p in SKILLS_DIR.glob(pattern) if p != SCRIPT))


@contextmanager
def _isolated_module_state() -> Iterator[None]:
    """Restore `sys.modules` so one entrypoint's load cannot satisfy the next."""
    before = dict(sys.modules)
    try:
        yield
    finally:
        sys.modules.clear()
        sys.modules.update(before)


def _load_entrypoint(path: Path) -> ModuleType:
    """Load one entrypoint under a name unique to its skill directory."""
    name = f"entrypoint_{path.parent.parent.name.replace('-', '_')}"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load the entrypoint at {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@dataclass(frozen=True)
class EntrypointObservation:
    """What one entrypoint produced when asked for the shared resolver."""

    path: Path
    resolver_file: Path | None
    error: str | None


def observe_entrypoint(path: Path) -> EntrypointObservation:
    """Load `path` from the real tree and ask it for the shared resolver."""
    with _isolated_module_state():
        module = _load_entrypoint(path)
        sys.modules.pop(module.RESOLVER_MODULE, None)
        try:
            resolver = module.load_resolver()
        except RuntimeError as error:
            return EntrypointObservation(path, None, str(error))
        resolver_file = getattr(resolver, "__file__", None)
        return EntrypointObservation(
            path, Path(resolver_file) if resolver_file else None, None
        )


def observe_entrypoint_without_provider(path: Path) -> EntrypointObservation:
    """Load a copy of `path`'s skill placed where no provider skill exists.

    The consuming skill directory is copied alone into a temporary skills tree,
    so the sibling the entrypoint reaches for is genuinely absent rather than
    stubbed. This is the failure the entrypoint exists to make loud.
    """
    with TemporaryDirectory() as temporary_directory:
        skills = Path(temporary_directory) / "skills"
        skill = path.parent.parent
        shutil.copytree(skill, skills / skill.name)
        return observe_entrypoint(skills.joinpath(skill.name, *ENTRYPOINT_RELPATH))


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
