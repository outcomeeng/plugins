"""Test infrastructure for the shipped herdr environment adapter."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from types import ModuleType
from typing import Protocol, cast

from hypothesis import given, seed, settings

from outcomeeng_testing.generators.herdr_environment import (
    agent_names,
    agent_states,
    error_messages,
    herdr_agent_item,
    inventories,
    unknown_operation_names,
    unprojected_error_codes,
    wait_timeouts,
)
from outcomeeng_testing.harnesses.cli_usage import (
    UsageContract,
    usage_contract_from_path,
)
from outcomeeng_testing.harnesses.property_evidence import run_replayable_property

ROOT = Path(__file__).parents[2]
HERDR_ENVIRONMENT_PATH = (
    ROOT / "src/plugins/coding-agents/skills/operate-herdr/scripts/herdr_environment.py"
)
CODING_AGENTS_RUNTIME_ROOTS = (
    ROOT / "src/plugins/coding-agents",
    ROOT / "dist/claude/coding-agents",
    ROOT / "dist/codex/coding-agents",
)
OPERATE_HERDR_RELATIVE = Path("skills/operate-herdr")
# Captured `herdr <command> --help` texts: herdr's own grammar declaration.
USAGE_FIXTURE_ROOT = ROOT / "outcomeeng_testing/fixtures/herdr_environment/usage"
RAW_HERDR_VIOLATION_FIXTURE = (
    ROOT / "outcomeeng_testing/fixtures/herdr_environment/raw_herdr_command.py.txt"
)
HERDR_HELP_VIOLATION_FIXTURE = (
    ROOT / "outcomeeng_testing/fixtures/herdr_environment/herdr_help_command.py.txt"
)
ERROR_PROJECTION_SEED = 2026091811
ERROR_PROJECTION_EXAMPLES = 40
ERROR_PROJECTION_REPLAY_PATH = (
    "spx/43-coding-agents.enabler/18-herdr-environment.enabler/tests/"
    "test_herdr_environment.mapping.l1.py"
)
INVENTORY_SEED = 2026091812
INVENTORY_EXAMPLES = 40
INVENTORY_REPLAY_PATH = ERROR_PROJECTION_REPLAY_PATH
UNKNOWN_OPERATION_SEED = 2026091813
UNKNOWN_OPERATION_EXAMPLES = 20
UNKNOWN_OPERATION_REPLAY_PATH = ERROR_PROJECTION_REPLAY_PATH
# Bound for the real child the runner-bound probe runs against.
RUNNER_BOUND_SECONDS = 1
RUNNER_BOUND_CHILD_SLEEP_SECONDS = 30
# A herdr envelope id in the CLI's own form.
ENVELOPE_ID = "cli:agent:list"


class CommandResultContract(Protocol):
    returncode: int
    stdout: str
    stderr: str


@dataclass
class RecordingRunner:
    """Interaction-protocol collaborator: records argv and bound, replays results."""

    results: list[CommandResultContract]
    calls: list[tuple[tuple[str, ...], str | None, int]] = field(default_factory=list)

    def run(
        self,
        argv: tuple[str, ...],
        stdin: str | None = None,
        *,
        timeout_seconds: int = 0,
    ) -> CommandResultContract:
        self.calls.append((argv, stdin, timeout_seconds))
        if not self.results:
            raise RuntimeError(f"Unexpected command: {argv}")
        return self.results.pop(0)


@dataclass
class AbsentExecutableRunner:
    """Failure-simulation collaborator: the herdr executable is not installed."""

    calls: list[tuple[str, ...]] = field(default_factory=list)

    def run(
        self,
        argv: tuple[str, ...],
        stdin: str | None = None,
        *,
        timeout_seconds: int = 0,
    ) -> CommandResultContract:
        self.calls.append(argv)
        raise FileNotFoundError(argv[0])


def _load() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "coding_agents_herdr_environment", HERDR_ENVIRONMENT_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load herdr module: {HERDR_ENVIRONMENT_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_herdr_environment() -> ModuleType:
    """Load the shipped adapter so linked tests can inspect its public contract."""
    return _load()


def usage_contract_for(module: ModuleType, operation: object) -> UsageContract:
    """Herdr's captured usage declaration for one operation's command."""
    prefix = module.PUBLIC_HERDR_COMMAND_PREFIXES[operation]
    return usage_contract_from_path(USAGE_FIXTURE_ROOT / f"{'-'.join(prefix[1:])}.txt")


def herdr_success_result(module: ModuleType, result: object) -> CommandResultContract:
    """Return one controlled public success envelope from the herdr boundary."""
    return cast(
        CommandResultContract,
        module.CommandResult(
            0,
            json.dumps({module.ID_FIELD: ENVELOPE_ID, module.RESULT_FIELD: result}),
            "",
        ),
    )


def herdr_inventory_result(
    module: ModuleType, agents: list[dict[str, object]]
) -> CommandResultContract:
    return herdr_success_result(module, {module.AGENTS_FIELD: agents})


def herdr_error_result(
    module: ModuleType, code: str, message: str
) -> CommandResultContract:
    """Return one controlled public error envelope as herdr writes it on stderr."""
    return cast(
        CommandResultContract,
        module.CommandResult(
            1,
            "",
            json.dumps(
                {
                    module.ID_FIELD: ENVELOPE_ID,
                    module.ERROR_FIELD: {
                        module.CODE_FIELD: code,
                        module.MESSAGE_FIELD: message,
                    },
                }
            ),
        ),
    )


def run_error_projection_mapping(
    assert_projection: Callable[[ModuleType, str, str, bool, str, int], None],
) -> None:
    """Drive every projected herdr error code by construction, and generated
    unprojected codes, through the adapter with generated selectors and bounds."""
    module = _load()
    projected_codes = tuple(module.HERDR_ERROR_STATUSES)

    @seed(ERROR_PROJECTION_SEED)
    @settings(max_examples=ERROR_PROJECTION_EXAMPLES, deadline=None, print_blob=True)
    @given(
        unprojected=unprojected_error_codes(module),
        message=error_messages(),
        selector=agent_names(),
        timeout=wait_timeouts(module),
    )
    def generated_projection(
        unprojected: str, message: str, selector: str, timeout: int
    ) -> None:
        for code in projected_codes:
            assert_projection(module, code, message, True, selector, timeout)
        assert_projection(module, unprojected, message, False, selector, timeout)

    run_replayable_property(
        generated_projection,
        seed_value=ERROR_PROJECTION_SEED,
        replay_path=ERROR_PROJECTION_REPLAY_PATH,
    )


def run_inventory_mapping(
    assert_inventory: Callable[
        [ModuleType, list[dict[str, object]], str, object], None
    ],
) -> None:
    """Drive inventories that carry every server state by construction, plus
    generated inventories, through the participant projection."""
    module = _load()
    every_state = [
        herdr_agent_item(module, ordinal, state)
        for ordinal, state in enumerate(module.AgentState, start=1)
    ]

    @seed(INVENTORY_SEED)
    @settings(max_examples=INVENTORY_EXAMPLES, deadline=None, print_blob=True)
    @given(
        agents=inventories(module),
        absent_name=agent_names(),
        state=agent_states(module),
    )
    def generated_inventory(
        agents: list[dict[str, object]], absent_name: str, state: object
    ) -> None:
        assert_inventory(module, every_state, absent_name, state)
        assert_inventory(module, agents, absent_name, state)

    run_replayable_property(
        generated_inventory,
        seed_value=INVENTORY_SEED,
        replay_path=INVENTORY_REPLAY_PATH,
    )


def run_unknown_operation_mapping(
    assert_unknown: Callable[[ModuleType, str], None],
) -> None:
    module = _load()

    @seed(UNKNOWN_OPERATION_SEED)
    @settings(max_examples=UNKNOWN_OPERATION_EXAMPLES, deadline=None, print_blob=True)
    @given(name=unknown_operation_names(module))
    def generated_unknown(name: str) -> None:
        assert_unknown(module, name)

    run_replayable_property(
        generated_unknown,
        seed_value=UNKNOWN_OPERATION_SEED,
        replay_path=UNKNOWN_OPERATION_REPLAY_PATH,
    )


def run_runner_bound_probe() -> tuple[int, int, subprocess.TimeoutExpired | None]:
    """Run the default runner against a child that outlives its bound."""
    module = _load()
    argv = (
        sys.executable,
        "-c",
        f"import time; time.sleep({RUNNER_BOUND_CHILD_SLEEP_SECONDS})",
    )
    try:
        module.SubprocessRunner().run(argv, timeout_seconds=RUNNER_BOUND_SECONDS)
    except subprocess.TimeoutExpired as error:
        return RUNNER_BOUND_SECONDS, RUNNER_BOUND_CHILD_SLEEP_SECONDS, error
    return RUNNER_BOUND_SECONDS, RUNNER_BOUND_CHILD_SLEEP_SECONDS, None


def _source_texts(paths: tuple[Path, ...]) -> dict[str, str]:
    return {
        str(path.relative_to(ROOT)): path.read_text(encoding="utf-8")
        for path in sorted(paths)
    }


def herdr_command_source_texts() -> dict[str, str]:
    """Return shipped Python source outside the sole herdr command owner."""
    script_paths = tuple(
        path
        for runtime_root in CODING_AGENTS_RUNTIME_ROOTS
        for path in runtime_root.rglob("*.py")
        if OPERATE_HERDR_RELATIVE not in path.relative_to(runtime_root).parents
    )
    return _source_texts(script_paths)


def raw_herdr_violation_source() -> tuple[str, dict[str, str]]:
    return (
        str(RAW_HERDR_VIOLATION_FIXTURE.relative_to(ROOT)),
        _source_texts((RAW_HERDR_VIOLATION_FIXTURE,)),
    )


def herdr_help_violation_source() -> tuple[str, dict[str, str]]:
    return (
        str(HERDR_HELP_VIOLATION_FIXTURE.relative_to(ROOT)),
        _source_texts((HERDR_HELP_VIOLATION_FIXTURE,)),
    )
