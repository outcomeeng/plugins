"""Harness for evidence over the bundled ``workflow_inspect.py`` helper.

Loads the script from the checkout, replaces its single ``_run`` seam with a
recording collaborator that returns scripted ``gh`` replies, and exposes the
observations (exit code, stdout, issued ``gh`` commands). The harness holds no
predicate and no expected outcome; linked tests decide what each observation
means.
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final, Protocol, cast

from hypothesis import given, seed, settings
from hypothesis.strategies import SearchStrategy

from outcomeeng_testing.harnesses.property_evidence import run_replayable_property

REPO_ROOT: Final = Path(__file__).resolve().parents[2]
SCRIPT_PATH: Final = (
    REPO_ROOT
    / "src"
    / "plugins"
    / "product-tree"
    / "skills"
    / "inspect-github-actions"
    / "scripts"
    / "workflow_inspect.py"
)
FIXTURE_ROOT: Final = REPO_ROOT / "outcomeeng_testing" / "fixtures" / "workflow_inspect"
SCRIPT_NAME: Final = SCRIPT_PATH.name

# Bounded wait that replaces the production subprocess timeout in the real-runner evidence.
TEST_TIMEOUT_SECONDS: Final = 0.5
# A real child that outlasts the injected timeout.
HANGING_COMMAND: Final = (sys.executable, "-c", "import time; time.sleep(30)")

PROPERTY_SEED: Final = 20261024
PROPERTY_EXAMPLES: Final = 60
PROPERTY_REPLAY_PATH: Final = (
    "just test-v spx/21-product-tree.enabler/13-infrastructure.enabler/"
    "21-github-actions.enabler/32-workflow-observability.enabler/tests"
)


@dataclass(frozen=True)
class GhReply:
    """One scripted answer to a ``gh`` call: exit code, stdout, stripped stderr."""

    code: int
    stdout: str
    stderr: str = ""


@dataclass(frozen=True)
class CliObservation:
    """What one in-process CLI invocation produced."""

    exit_code: int
    stdout: str
    gh_calls: tuple[tuple[str, ...], ...]


@dataclass(frozen=True)
class ProcessObservation:
    """What one real script process produced."""

    exit_code: int
    stdout: str
    stderr: str


class WorkflowInspectModule(Protocol):
    """The surface of the loaded script that the harness reads and replaces."""

    SUBPROCESS_TIMEOUT_SECONDS: float
    _run: Callable[[list[str]], tuple[int, str, str]]

    def main(self, argv: list[str]) -> int: ...


def load_module() -> WorkflowInspectModule:
    """Load a fresh copy of the script from its checkout path."""
    spec = importlib.util.spec_from_file_location(
        "workflow_inspect_under_test", SCRIPT_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not build module spec for {SCRIPT_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return cast(WorkflowInspectModule, module)


def fixture_path(name: str) -> Path:
    """Path of one inert sample payload."""
    return FIXTURE_ROOT / name


def fixture_text(name: str) -> str:
    """Verbatim text of one inert sample payload."""
    return fixture_path(name).read_text(encoding="utf-8")


def fixture_json(name: str) -> Any:
    """Parsed form of one inert sample payload."""
    return json.loads(fixture_text(name))


def run_cli(argv: list[str], reply: GhReply) -> CliObservation:
    """Run ``main`` in-process with every ``gh`` call answered by ``reply``."""
    module = load_module()
    calls: list[tuple[str, ...]] = []

    def recording_run(cmd: list[str]) -> tuple[int, str, str]:
        calls.append(tuple(cmd))
        return reply.code, reply.stdout, reply.stderr

    module._run = recording_run
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        exit_code = module.main([SCRIPT_NAME, *argv])
    return CliObservation(exit_code, buffer.getvalue(), tuple(calls))


def run_real_runner(command: tuple[str, ...] | list[str]) -> tuple[int, str, str]:
    """Run the script's real ``_run`` seam on a real child under the bounded test timeout."""
    module = load_module()
    module.SUBPROCESS_TIMEOUT_SECONDS = TEST_TIMEOUT_SECONDS
    return module._run(list(command))


def run_script_process(args: list[str]) -> ProcessObservation:
    """Run the script as a real ``python3`` subprocess."""
    proc = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), *args],
        capture_output=True,
        text=True,
        stdin=subprocess.DEVNULL,
    )
    return ProcessObservation(proc.returncode, proc.stdout, proc.stderr)


def workflow_inspect_property(
    strategy: SearchStrategy[Any], *, argument: str
) -> Callable[[Callable[..., None]], Callable[[], None]]:
    """Bind a test function to a generated domain with seed, run count, and replay diagnostics."""

    def decorate(test_func: Callable[..., None]) -> Callable[[], None]:
        configured = seed(PROPERTY_SEED)(
            settings(max_examples=PROPERTY_EXAMPLES, deadline=None)(
                given(**{argument: strategy})(test_func)
            )
        )

        def wrapper() -> None:
            run_replayable_property(
                configured,
                seed_value=PROPERTY_SEED,
                replay_path=PROPERTY_REPLAY_PATH,
            )

        wrapper.__name__ = test_func.__name__
        return wrapper

    return decorate
