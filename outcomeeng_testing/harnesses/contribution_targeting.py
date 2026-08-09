"""Harness for the contribute plugin's target resolver.

Loads the shipped script from its authored location and drives it with a
controlled command runner. Injection is sanctioned here because the subject is
an external-tool interaction protocol and its failure modes: the resolver's whole
job is reading `gh`'s JSON correctly and refusing to classify when it cannot, and
neither a real GitHub API nor a real repository can produce an unrecognized
permission value or an authenticated-but-unreadable base on demand.

The runner records every command, so a regression that reached for `git remote`,
the authenticated account, or any other signal fails a test rather than shipping.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType
from typing import Protocol

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = (
    REPO_ROOT
    / "src"
    / "plugins"
    / "contribute"
    / "skills"
    / "contribution-standards"
    / "scripts"
    / "resolve_target.py"
)

CHECKOUT_VIEW: tuple[str, ...] = (
    "gh",
    "repo",
    "view",
    "--json",
    "isFork,parent,nameWithOwner",
)
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


def _checkout(is_fork: bool) -> tuple[int, str, str]:
    payload: dict[str, object] = {
        "isFork": is_fork,
        "nameWithOwner": FORK if is_fork else PARENT,
        "parent": {"nameWithOwner": PARENT} if is_fork else None,
    }
    return (0, json.dumps(payload), "")


def _permission(base: str, value: str | None) -> Responses:
    payload = {} if value is None else {"viewerPermission": value}
    key: tuple[str, ...] = ("gh", "repo", "view", base, "--json", "viewerPermission")
    return {key: (0, json.dumps(payload), "")}


def _account_lookups() -> Responses:
    user_key: tuple[str, ...] = ("gh", "api", "user")
    orgs_key: tuple[str, ...] = ("gh", "api", "user/orgs")
    return {
        user_key: (0, json.dumps({"login": "operator"}), ""),
        orgs_key: (0, json.dumps([{"login": "silvarbor"}]), ""),
    }


def _resolve(responses: Responses) -> tuple[ResolutionLike, RecordingRunner]:
    runner = RecordingRunner(responses)
    resolution: ResolutionLike = load_resolver().resolve(runner)
    return resolution, runner


def verify_target_classification_mappings() -> list[str]:
    """Every observed fork state and permission maps to exactly one classification."""
    cases: list[tuple[bool, str, str]] = [
        (False, "ADMIN", "controlled"),
        (False, "MAINTAIN", "controlled"),
        (False, "WRITE", "controlled"),
        (True, "ADMIN", "controlled"),
        (True, "READ", "parent-contribution"),
        (True, "NONE", "parent-contribution"),
        (False, "READ", "fork-absent"),
        (False, "NONE", "fork-absent"),
        (False, "TRIAGE", "blocked"),
        (True, "TRIAGE", "blocked"),
    ]
    mismatches: list[str] = []
    for is_fork, permission, expected in cases:
        responses: Responses = {CHECKOUT_VIEW: _checkout(is_fork)}
        responses.update(_permission(PARENT, permission))
        responses.update(_account_lookups())
        resolution, _ = _resolve(responses)
        if resolution.classification != expected:
            mismatches.append(
                f"isFork={is_fork} viewerPermission={permission}: "
                f"expected {expected}, got {resolution.classification}"
            )
    return mismatches


def verify_permission_never_inferred() -> list[str]:
    """No signal other than viewerPermission on the resolved base yields a permission class."""
    violations: list[str] = []

    unreadable: Responses = {CHECKOUT_VIEW: _checkout(True)}
    unreadable.update(_permission(PARENT, None))
    resolution, runner = _resolve(unreadable)
    if resolution.classification != "blocked":
        violations.append(
            "an absent viewerPermission produced "
            f"{resolution.classification!r} rather than blocked"
        )
    if resolution.permission is not None:
        violations.append(
            f"an absent viewerPermission produced permission {resolution.permission!r}"
        )
    non_gh = [command for command in runner.commands if command[:1] != ("gh",)]
    if non_gh:
        violations.append(f"the resolver reached beyond gh for permission: {non_gh}")

    permission_key: tuple[str, ...] = (
        "gh",
        "repo",
        "view",
        PARENT,
        "--json",
        "viewerPermission",
    )
    failing_view: Responses = {
        CHECKOUT_VIEW: _checkout(True),
        permission_key: (1, "", "HTTP 404: Not Found"),
    }
    resolution, _ = _resolve(failing_view)
    if resolution.classification != "blocked":
        violations.append(
            "a failed permission read produced "
            f"{resolution.classification!r} rather than blocked"
        )
    if "HTTP 404: Not Found" not in resolution.detail:
        violations.append("a failed permission read dropped the gh error from detail")

    unavailable: Responses = {CHECKOUT_VIEW: (127, "", "gh: command not found")}
    resolution, runner = _resolve(unavailable)
    if resolution.classification != "blocked":
        violations.append(
            "an unavailable gh produced "
            f"{resolution.classification!r} rather than blocked"
        )
    if len(runner.commands) != 1:
        violations.append(
            f"an unavailable gh did not stop at the first command: {runner.commands}"
        )

    orphan_fork: Responses = {
        CHECKOUT_VIEW: (
            0,
            json.dumps({"isFork": True, "nameWithOwner": FORK, "parent": None}),
            "",
        )
    }
    resolution, _ = _resolve(orphan_fork)
    if resolution.classification != "blocked":
        violations.append(
            "a fork with no parent produced "
            f"{resolution.classification!r} rather than blocked"
        )

    if not hasattr(load_resolver(), "CommandRunner"):
        violations.append(
            "the resolver exposes no CommandRunner protocol to inject through"
        )

    return violations
