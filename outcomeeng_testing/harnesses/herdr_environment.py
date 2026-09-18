"""Test infrastructure for the shipped herdr environment adapter."""

from __future__ import annotations

import importlib.util
import json
import sys
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from types import ModuleType
from typing import Protocol, cast

from hypothesis import given, seed, settings

from outcomeeng_testing.generators.herdr_environment import (
    agent_item_variant,
    agent_names,
    agent_states,
    inventories,
    operation_requests,
    unknown_operation_names,
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
FIXTURE_ROOT = ROOT / "outcomeeng_testing/fixtures/herdr_environment"
# Captured `herdr <command> --help` texts: herdr's own grammar declaration.
USAGE_FIXTURE_ROOT = FIXTURE_ROOT / "usage"
# Captured herdr responses, by command: what herdr wrote to stdout on success
# (`<command>.json`, or `<command>.txt` for a text command) and, under
# `errors/`, the envelope it wrote to stderr on failure (`<command>.<code>.json`).
RESPONSE_FIXTURE_ROOT = FIXTURE_ROOT / "responses"
ERROR_FIXTURE_ROOT = RESPONSE_FIXTURE_ROOT / "errors"
RAW_HERDR_VIOLATION_FIXTURE = FIXTURE_ROOT / "raw_herdr_command.py.txt"
HERDR_HELP_VIOLATION_FIXTURE = FIXTURE_ROOT / "herdr_help_command.py.txt"
# herdr's exit code on every captured error envelope.
CAPTURED_ERROR_EXIT_CODE = 1
INVENTORY_SEED = 2026091812
INVENTORY_EXAMPLES = 40
INVENTORY_REPLAY_PATH = (
    "spx/43-coding-agents.enabler/18-herdr-environment.enabler/tests/"
    "test_herdr_environment.mapping.l1.py"
)
UNKNOWN_OPERATION_SEED = 2026091813
UNKNOWN_OPERATION_EXAMPLES = 20
UNKNOWN_OPERATION_REPLAY_PATH = INVENTORY_REPLAY_PATH
# The child the bound probe runs in place of herdr outlives every bound the
# adapter derives from the smallest request timeout.
BOUND_PROBE_CHILD_SLEEP_SECONDS = 30


class CommandResultContract(Protocol):
    returncode: int
    stdout: str
    stderr: str


class BoundedRunnerContract(Protocol):
    def run(
        self,
        argv: tuple[str, ...],
        stdin: str | None = None,
        *,
        timeout_seconds: int = 0,
    ) -> CommandResultContract: ...


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


@dataclass
class BoundProbeRunner:
    """Failure-simulation collaborator: runs the adapter's real default runner
    against a child that outlives the bound the adapter passes, so the timeout
    the adapter derives is enforced by a real subprocess and propagates as
    herdr's would."""

    default_runner: BoundedRunnerContract
    bounds: list[int] = field(default_factory=list)

    def run(
        self,
        argv: tuple[str, ...],
        stdin: str | None = None,
        *,
        timeout_seconds: int = 0,
    ) -> CommandResultContract:
        self.bounds.append(timeout_seconds)
        child = (
            sys.executable,
            "-c",
            f"import time; time.sleep({BOUND_PROBE_CHILD_SLEEP_SECONDS})",
        )
        return self.default_runner.run(child, stdin, timeout_seconds=timeout_seconds)


@dataclass(frozen=True)
class CapturedResponse:
    """One response herdr emitted for one operation's command, read by path."""

    operation: object
    path: str
    result: CommandResultContract
    error_code: str | None


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


def _command_fixture_name(module: ModuleType, operation: object) -> str:
    prefix = module.PUBLIC_HERDR_COMMAND_PREFIXES[operation]
    return "-".join(prefix[1:])


def usage_contract_for(module: ModuleType, operation: object) -> UsageContract:
    """Herdr's captured usage declaration for one operation's command."""
    return usage_contract_from_path(
        USAGE_FIXTURE_ROOT / f"{_command_fixture_name(module, operation)}.txt"
    )


def _success_result(module: ModuleType, path: Path) -> CommandResultContract:
    return cast(
        CommandResultContract,
        module.CommandResult(0, path.read_text(encoding="utf-8"), ""),
    )


def _error_result(module: ModuleType, path: Path) -> CommandResultContract:
    return cast(
        CommandResultContract,
        module.CommandResult(
            CAPTURED_ERROR_EXIT_CODE, "", path.read_text(encoding="utf-8")
        ),
    )


def _error_code(module: ModuleType, path: Path) -> str:
    envelope = json.loads(path.read_text(encoding="utf-8"))
    return str(envelope[module.ERROR_FIELD][module.CODE_FIELD])


def captured_success_response(
    module: ModuleType, operation: object
) -> CapturedResponse | None:
    """Herdr's captured success response for one operation, when one exists."""
    name = _command_fixture_name(module, operation)
    suffix = "txt" if operation in module.TEXT_OPERATIONS else "json"
    path = RESPONSE_FIXTURE_ROOT / f"{name}.{suffix}"
    if not path.is_file():
        return None
    return CapturedResponse(
        operation, str(path.relative_to(ROOT)), _success_result(module, path), None
    )


def captured_error_responses(
    module: ModuleType, operation: object
) -> list[CapturedResponse]:
    """Every error envelope herdr emitted for one operation's command."""
    name = _command_fixture_name(module, operation)
    return [
        CapturedResponse(
            operation,
            str(path.relative_to(ROOT)),
            _error_result(module, path),
            _error_code(module, path),
        )
        for path in sorted(ERROR_FIXTURE_ROOT.glob(f"{name}.*.json"))
    ]


def captured_responses(module: ModuleType) -> list[CapturedResponse]:
    """Every captured response, success and error, across every operation."""
    responses: list[CapturedResponse] = []
    for operation in module.Operation:
        success = captured_success_response(module, operation)
        if success is not None:
            responses.append(success)
        responses.extend(captured_error_responses(module, operation))
    return responses


def captured_payload(response: CapturedResponse) -> object:
    """The captured response decoded: the JSON envelope, or the text verbatim."""
    if response.error_code is not None:
        return json.loads(response.result.stderr)
    try:
        return json.loads(response.result.stdout)
    except json.JSONDecodeError:
        return response.result.stdout


def captured_error_message(module: ModuleType, response: CapturedResponse) -> str:
    envelope = cast(dict[str, object], captured_payload(response))
    error = cast(dict[str, object], envelope[module.ERROR_FIELD])
    return str(error[module.MESSAGE_FIELD])


def captured_agent_item(module: ModuleType) -> dict[str, object]:
    """The first hosted agent session in herdr's captured inventory."""
    inventory = captured_success_response(module, module.Operation.INVENTORY)
    if inventory is None:
        raise RuntimeError("No captured herdr inventory response.")
    envelope = cast(dict[str, object], captured_payload(inventory))
    result = cast(dict[str, object], envelope[module.RESULT_FIELD])
    agents = cast(list[dict[str, object]], result[module.AGENTS_FIELD])
    return agents[0]


def projected_error_variants(module: ModuleType) -> list[CapturedResponse]:
    """A captured error envelope varied to each projected code herdr did not
    emit under the capture conditions: only the code changes, so the envelope's
    shape, stream, and exit code stay what herdr wrote."""
    template = next(
        response
        for response in captured_responses(module)
        if response.error_code in module.HERDR_ERROR_STATUSES
    )
    envelope = cast(dict[str, object], captured_payload(template))
    captured_codes = {
        response.error_code
        for response in captured_responses(module)
        if response.error_code is not None
    }
    variants: list[CapturedResponse] = []
    for code in module.HERDR_ERROR_STATUSES:
        if code in captured_codes:
            continue
        error = dict(cast(dict[str, object], envelope[module.ERROR_FIELD]))
        error[module.CODE_FIELD] = code
        variant = json.dumps({**envelope, module.ERROR_FIELD: error})
        variants.append(
            CapturedResponse(
                template.operation,
                f"{template.path} varied to {code}",
                cast(
                    CommandResultContract,
                    module.CommandResult(CAPTURED_ERROR_EXIT_CODE, "", variant),
                ),
                code,
            )
        )
    return variants


def request_for(module: ModuleType, operation: object) -> dict[str, object]:
    """The first registry request of one operation, from the generated set."""
    return next(
        request
        for request in operation_requests(module)
        if module.Operation(request[module.OPERATION_FIELD]) is operation
    )


def run_inventory_mapping(
    assert_inventory: Callable[
        [ModuleType, list[dict[str, object]], str, object], None
    ],
) -> None:
    """Drive the captured inventory, inventories that carry every server state
    by construction from its first item, and generated inventories, through the
    participant projection."""
    module = _load()
    template = captured_agent_item(module)
    inventory = captured_success_response(module, module.Operation.INVENTORY)
    if inventory is None:
        raise RuntimeError("No captured herdr inventory response.")
    envelope = cast(dict[str, object], captured_payload(inventory))
    captured = cast(
        list[dict[str, object]],
        cast(dict[str, object], envelope[module.RESULT_FIELD])[module.AGENTS_FIELD],
    )
    every_state = [
        agent_item_variant(module, template, ordinal, state)
        for ordinal, state in enumerate(module.AgentState, start=1)
    ]

    @seed(INVENTORY_SEED)
    @settings(max_examples=INVENTORY_EXAMPLES, deadline=None, print_blob=True)
    @given(
        agents=inventories(module, template),
        absent_name=agent_names(),
        state=agent_states(module),
    )
    def generated_inventory(
        agents: list[dict[str, object]], absent_name: str, state: object
    ) -> None:
        assert_inventory(module, captured, absent_name, state)
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


def run_bound_through_execute(
    module: ModuleType, request: dict[str, object]
) -> tuple[dict[str, object], list[int], int]:
    """Execute one request against the real default runner bound, with a child
    that outlives it; return the result, the bounds the adapter passed, and the
    child's sleep."""
    probe = BoundProbeRunner(cast(BoundedRunnerContract, module.SubprocessRunner()))
    result = module.execute(request, probe)
    return result, probe.bounds, BOUND_PROBE_CHILD_SLEEP_SECONDS


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
