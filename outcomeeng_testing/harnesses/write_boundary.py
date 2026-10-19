"""Test infrastructure: run the shipped pre-write hook command as the runtime would.

The harness reads the spec-tree plugin's shipped ``dist/claude`` ``hooks.json``,
selects the ``PreToolUse`` command that equals the contract pair
``PRE_WRITE_COMMAND_CLAUDE`` (any other command is a setup error), and runs it
through ``/bin/sh`` in a temporary workspace with a controlled environment. It
owns lifecycle only: the temporary workspace, token substitution into a fixture's
files, copying a fixture's optional ``workspace/`` tree into the workspace, the
environment scrub, and the subprocess with its stdin and bound. It holds no case
value, accepts no expected result, calls no assertion API, and returns no verdict.

Every case is an inert whole-payload fixture directory under
``outcomeeng_testing/fixtures/write_boundary/<group>--<instance>/``; the directory
name states the one case it holds. A case holds:

- ``payload.json``: the hook payload written to the command's standard input,
  verbatim; a case without the file runs the command with an empty standard input.
- ``environment.json``: the environment variables the case sets for the command.
- ``granted_roots.json``: the roots the case's denial reason must name, when the
  case is a denial.
- ``workspace/``: files copied into the workspace before the run.

The harness substitutes three tokens in the bytes of a case's files: the
workspace root, the user id, and the tool name the caller supplies. The adapter module is loaded from its authored path so a
test imports the adapter's own output vocabulary.

Exception case: none.
"""

from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from tempfile import TemporaryDirectory
from types import ModuleType
from typing import Final

from outcomeeng.validation.hook_contract import (
    CLAUDE_RUNTIME_TREE,
    PRE_TOOL_USE_EVENT,
    PRE_WRITE_COMMAND_CLAUDE,
    PRE_WRITE_KILL_SWITCH,
    PRE_WRITE_PLUGIN,
)
from outcomeeng_testing.harnesses.hooks import event_commands, shipped_hook_events

REPO_ROOT: Final = Path(__file__).resolve().parents[2]
WRITE_BOUNDARY_FIXTURES: Final = (
    REPO_ROOT / "outcomeeng_testing" / "fixtures" / "write_boundary"
)
ADAPTER_PATH: Final = (
    REPO_ROOT / "src" / "plugins" / "spec-tree" / "scripts" / "write_boundary.py"
)
ADAPTER_MODULE_NAME: Final = "write_boundary"
GROUP_SEPARATOR: Final = "--"
PAYLOAD_FILE: Final = "payload.json"
ENVIRONMENT_FILE: Final = "environment.json"
GRANTED_ROOTS_FILE: Final = "granted_roots.json"
WORKSPACE_TREE: Final = "workspace"
FIXTURE_ENCODING: Final = "utf-8"
WORKSPACE_TOKEN: Final = "@WORKSPACE@"
USER_ID_TOKEN: Final = "@UID@"
TOOL_TOKEN: Final = "@TOOL@"
# Variables of the harness environment the ambient process must not leak into a case.
AMBIENT_PREFIXES: Final = ("CLAUDE", "SPECTREE_")
PLUGIN_ROOT_ENV: Final = "CLAUDE_PLUGIN_ROOT"
SHELL: Final = "/bin/sh"
# The hook entry declares its own five-second bound; the harness bounds the
# subprocess well above it so a hung command surfaces as a harness failure.
SUBPROCESS_TIMEOUT_S: Final = 60


class FixtureGroup(StrEnum):
    """The directory-name prefix that gathers the fixtures of one claim."""

    DENY = "deny"
    GRANT = "grant"
    KILL_SWITCH = "kill-switch"
    FAILURE = "failure"


@dataclass(frozen=True)
class FixtureCase:
    """One fixture directory: a name stating the case and its path."""

    name: str
    path: Path


@dataclass(frozen=True)
class HookObservation:
    """What one run of the shipped command produced, with the case inputs it ran on."""

    exit_code: int
    stdout: str
    stderr: str
    payload_text: str | None
    granted_roots: tuple[str, ...]
    workspace: Path


def case_id(case: FixtureCase) -> str:
    """Return the parametrize id of one fixture case: its directory name."""
    return case.name


def fixture_cases(group: FixtureGroup) -> tuple[FixtureCase, ...]:
    """Return every fixture of one group, ordered by name.

    A group with no fixture raises, so a parametrization never vanishes silently.
    """
    found = sorted(
        child
        for child in WRITE_BOUNDARY_FIXTURES.iterdir()
        if child.is_dir() and child.name.startswith(f"{group}{GROUP_SEPARATOR}")
    )
    if not found:
        raise FileNotFoundError(f"no write-boundary fixture of group {group.value}")
    return tuple(FixtureCase(name=child.name, path=child) for child in found)


def load_adapter() -> ModuleType:
    """Import the write-boundary adapter from its authored path."""
    cached = sys.modules.get(ADAPTER_MODULE_NAME)
    if cached is not None:
        return cached
    spec = importlib.util.spec_from_file_location(ADAPTER_MODULE_NAME, ADAPTER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(
            f"Cannot load the write-boundary adapter from {ADAPTER_PATH}"
        )
    module = importlib.util.module_from_spec(spec)
    sys.modules[ADAPTER_MODULE_NAME] = module
    spec.loader.exec_module(module)
    return module


def shipped_pre_write_command() -> str:
    """Return the shipped ``dist/claude`` pre-write command, which must be the contract pair."""
    events = shipped_hook_events(CLAUDE_RUNTIME_TREE, __file__)
    commands = event_commands(events[PRE_TOOL_USE_EVENT])
    if commands != [PRE_WRITE_COMMAND_CLAUDE]:
        raise RuntimeError(
            f"shipped {PRE_TOOL_USE_EVENT} commands differ from the contract pair: {commands}"
        )
    return commands[0]


def _substitute(data: bytes, workspace: Path, tool: str) -> bytes:
    """Replace the harness tokens in one fixture file's bytes."""
    return (
        data.replace(WORKSPACE_TOKEN.encode(), str(workspace).encode())
        .replace(USER_ID_TOKEN.encode(), str(os.getuid()).encode())
        .replace(TOOL_TOKEN.encode(), tool.encode())
    )


def _environment(case: FixtureCase, workspace: Path, tool: str) -> dict[str, str]:
    """Return the command's environment: the scrubbed ambient one plus the case's."""
    env = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith(AMBIENT_PREFIXES) and key != PRE_WRITE_KILL_SWITCH
    }
    env[PLUGIN_ROOT_ENV] = str(REPO_ROOT / CLAUDE_RUNTIME_TREE / PRE_WRITE_PLUGIN)
    declared = json.loads(
        _substitute(
            (case.path / ENVIRONMENT_FILE).read_bytes(), workspace, tool
        ).decode(FIXTURE_ENCODING)
    )
    env.update(declared)
    return env


@contextmanager
def temporary_workspace() -> Iterator[Path]:
    """Yield an empty temporary workspace, resolved through its symbolic links."""
    with TemporaryDirectory() as directory:
        yield Path(directory).resolve()


def run_pre_write_hook(case: FixtureCase, tool: str) -> HookObservation:
    """Run the shipped pre-write command on one case with ``tool`` as the payload's tool name."""
    command = shipped_pre_write_command()
    with temporary_workspace() as workspace:
        tree = case.path / WORKSPACE_TREE
        if tree.is_dir():
            shutil.copytree(tree, workspace, dirs_exist_ok=True)
        payload_file = case.path / PAYLOAD_FILE
        payload = (
            _substitute(payload_file.read_bytes(), workspace, tool)
            if payload_file.is_file()
            else b""
        )
        roots_file = case.path / GRANTED_ROOTS_FILE
        granted_roots: tuple[str, ...] = (
            tuple(
                json.loads(
                    _substitute(roots_file.read_bytes(), workspace, tool).decode(
                        FIXTURE_ENCODING
                    )
                )
            )
            if roots_file.is_file()
            else ()
        )
        completed = subprocess.run(  # noqa: S603 — the command is the shipped hook artifact under test.
            [SHELL, "-c", command],
            input=payload,
            capture_output=True,
            env=_environment(case, workspace, tool),
            cwd=workspace,
            timeout=SUBPROCESS_TIMEOUT_S,
            check=False,
        )
        return HookObservation(
            exit_code=completed.returncode,
            stdout=completed.stdout.decode(FIXTURE_ENCODING, errors="replace"),
            stderr=completed.stderr.decode(FIXTURE_ENCODING, errors="replace"),
            payload_text=(
                payload.decode(FIXTURE_ENCODING, errors="replace")
                if payload_file.is_file()
                else None
            ),
            granted_roots=granted_roots,
            workspace=workspace,
        )


__all__ = [
    "WRITE_BOUNDARY_FIXTURES",
    "FixtureCase",
    "FixtureGroup",
    "HookObservation",
    "case_id",
    "fixture_cases",
    "load_adapter",
    "run_pre_write_hook",
    "shipped_pre_write_command",
    "temporary_workspace",
]
