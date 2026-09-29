"""Test infrastructure for the shipped herdr environment adapter."""

from __future__ import annotations

import functools
import importlib.util
import json
import os
import subprocess
import sys
import uuid
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from itertools import combinations
from pathlib import Path
from tempfile import TemporaryDirectory
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
from outcomeeng_testing.harnesses.hooks import (
    WORKTREE_CONTROLLING_PID_ENV,
    worktree_occupancy,
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
# A capture under `<operation>/` is the one that operation's own run produced
# where operations share a command: stop's exit prompt, and the relaunch into
# the pane that stop kept.
RESPONSE_FIXTURE_ROOT = FIXTURE_ROOT / "responses"
ERROR_FIXTURE_ROOT = RESPONSE_FIXTURE_ROOT / "errors"
# Responses herdr wrote for agent sessions whose evidence lacks projected
# fields: a session started by a shell command outside the adapter, which
# carries no name and no interactive_ready, and a start blocked during startup,
# which carries no interactive_ready. The inventory lists both beside one
# complete session.
INCOMPLETE_FIXTURE_ROOT = RESPONSE_FIXTURE_ROOT / "incomplete"
# The pane list herdr wrote for the stopped pane's workspace once the exit
# prompt ended its session.
STOPPED_PANE_LIST_FIXTURE = RESPONSE_FIXTURE_ROOT / "stop" / "pane-list.json"
# Herdr's pane-list envelope field listing the panes; the adapter never reads a
# pane list, so this field is the capture's own shape.
PANE_LIST_FIELD = "panes"
# The worktree list herdr wrote for the workspace the captured create-worktree
# and open-worktree requests named, taken once after both ran: herdr's own
# record of the worktrees grouped with that workspace and the workspace each is
# open in. The adapter never lists worktrees, so these fields are the capture's
# own shape.
WORKTREE_LIST_FIXTURE = RESPONSE_FIXTURE_ROOT / "worktree-list.json"
WORKTREE_LIST_SOURCE_FIELD = "source"
WORKTREE_LIST_SOURCE_WORKSPACE_FIELD = "source_workspace_id"
WORKTREE_LIST_FIELD = "worktrees"
LISTED_OPEN_WORKSPACE_FIELD = "open_workspace_id"
LISTED_LINKED_WORKTREE_FIELD = "is_linked_worktree"
RAW_HERDR_VIOLATION_FIXTURE = FIXTURE_ROOT / "raw_herdr_command.py.txt"
HERDR_HELP_VIOLATION_FIXTURE = FIXTURE_ROOT / "herdr_help_command.py.txt"
# The fixture family's own provenance record: the source tool and version that
# wrote each captured usage and response artifact, the pin the family is
# captured at, and, for an error response, the exit code herdr exited with in
# the run that wrote the envelope. Every captured artifact under the usage and
# response roots is declared there; a replay reads its artifact only through
# that declaration.
PROVENANCE_MANIFEST = FIXTURE_ROOT / "provenance.json"
CAPTURED_ARTIFACT_ROOTS = (USAGE_FIXTURE_ROOT, RESPONSE_FIXTURE_ROOT)
PROVENANCE_PIN_FIELD = "pin"
PROVENANCE_ARTIFACTS_FIELD = "artifacts"
PROVENANCE_PATH_FIELD = "path"
PROVENANCE_TOOL_FIELD = "tool"
PROVENANCE_VERSION_FIELD = "version"
PROVENANCE_EXIT_CODE_FIELD = "exitCode"
INVENTORY_SEED = 2026091812
INVENTORY_EXAMPLES = 40
INVENTORY_REPLAY_PATH = (
    "spx/43-coding-agents.enabler/18-herdr-environment.enabler/tests/"
    "test_herdr_environment.mapping.l1.py"
)
OPTION_PREFIX_SEED = 2026091814
OPTION_PREFIX_EXAMPLES = 10
OPTION_PREFIX_REPLAY_PATH = (
    "spx/43-coding-agents.enabler/18-herdr-environment.enabler/tests/"
    "test_herdr_environment.mapping.l1.py"
)
UNKNOWN_OPERATION_SEED = 2026091813
UNKNOWN_OPERATION_EXAMPLES = 20
UNKNOWN_OPERATION_REPLAY_PATH = INVENTORY_REPLAY_PATH
# The child the bound probe runs in place of herdr outlives every bound the
# adapter derives from the smallest request timeout.
BOUND_PROBE_CHILD_SLEEP_SECONDS = 30
# The disposable repository a created worktree lives in: its primary checkout
# and the linked worktree, each a directory under one temporary root. Git runs
# there with no global or system configuration, so signing, hooks, and identity
# settings of the machine never reach it.
DISPOSABLE_PRIMARY_DIRECTORY = "repo"
DISPOSABLE_WORKTREE_DIRECTORY = "worktree"
DISPOSABLE_GIT_IDENTITY = (
    "-c",
    "user.name=herdr-evidence",
    "-c",
    "user.email=herdr-evidence@invalid",
)
DISPOSABLE_GIT_ENV = {"GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"}
DISPOSABLE_COMMAND_TIMEOUT_SECONDS = 30


class CaptureError(RuntimeError):
    """The captured responses do not cover the shape a replay asked for, or an
    artifact's provenance does not admit it as an oracle."""


@dataclass(frozen=True)
class CaptureSource:
    """The tool and version that wrote one captured artifact."""

    tool: str
    version: str


@dataclass(frozen=True)
class CaptureProvenance:
    """One captured artifact's declared provenance: its path in the family, its
    source, and, for an error response, the exit code of the run that wrote it."""

    path: str
    source: CaptureSource
    exit_code: int | None


def _captured_artifact_paths() -> set[str]:
    return {
        str(path.relative_to(FIXTURE_ROOT))
        for root in CAPTURED_ARTIFACT_ROOTS
        for path in root.rglob("*")
        if path.is_file() and not path.name.startswith(".")
    }


@functools.cache
def _provenance() -> tuple[CaptureSource, dict[str, CaptureProvenance]]:
    manifest = cast(
        dict[str, object], json.loads(PROVENANCE_MANIFEST.read_text(encoding="utf-8"))
    )
    pin = cast(dict[str, str], manifest[PROVENANCE_PIN_FIELD])
    declared: dict[str, CaptureProvenance] = {}
    for entry in cast(list[dict[str, object]], manifest[PROVENANCE_ARTIFACTS_FIELD]):
        path = str(entry[PROVENANCE_PATH_FIELD])
        exit_code = entry.get(PROVENANCE_EXIT_CODE_FIELD)
        declared[path] = CaptureProvenance(
            path,
            CaptureSource(
                str(entry[PROVENANCE_TOOL_FIELD]), str(entry[PROVENANCE_VERSION_FIELD])
            ),
            exit_code if isinstance(exit_code, int) else None,
        )
    on_disk = _captured_artifact_paths()
    if set(declared) != on_disk:
        raise CaptureError(
            f"{PROVENANCE_MANIFEST.relative_to(ROOT)} does not declare exactly the "
            f"captured artifacts: undeclared {sorted(on_disk - set(declared))}, "
            f"absent {sorted(set(declared) - on_disk)}"
        )
    return (
        CaptureSource(pin[PROVENANCE_TOOL_FIELD], pin[PROVENANCE_VERSION_FIELD]),
        declared,
    )


def provenance_for(path: Path) -> CaptureProvenance:
    """The declared provenance of one captured artifact, admitted as an oracle
    only when its source is the family's pin; an artifact captured from any other
    source is stale until recaptured."""
    pin, declared = _provenance()
    key = str(path.relative_to(FIXTURE_ROOT))
    provenance = declared.get(key)
    if provenance is None:
        raise CaptureError(f"{key} is not declared in {PROVENANCE_MANIFEST.name}")
    if provenance.source != pin:
        raise CaptureError(
            f"{key} was captured from {provenance.source.tool} "
            f"{provenance.source.version}, not the pinned {pin.tool} {pin.version}; "
            "recapture it before it serves as an oracle"
        )
    return provenance


def _captured_text(path: Path) -> str:
    provenance_for(path)
    return path.read_text(encoding="utf-8")


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
    """One response herdr emitted for one operation's command, read by path.

    `shaping_fields` names the request fields whose presence selected this
    capture — a command answers `--wait` with a different response than the
    same command without it — so a replay pairs the capture with a request of
    the same shape.
    """

    operation: object
    path: str
    # The tool and version that wrote the capture this response replays.
    source: CaptureSource
    result: CommandResultContract
    error_code: str | None
    shaping_fields: frozenset[str] = frozenset()
    # The captured response of the evidence command the operation runs after its
    # own, when it runs one.
    evidence: CommandResultContract | None = None


def replay(captured: CapturedResponse) -> list[CommandResultContract]:
    """The command results a run of the captured operation receives, in order."""
    if captured.evidence is None:
        return [captured.result]
    return [captured.result, captured.evidence]


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


def _prefix_fixture_name(prefix: tuple[str, ...]) -> str:
    return "-".join(prefix[1:])


def _command_fixture_name(module: ModuleType, operation: object) -> str:
    return _prefix_fixture_name(module.PUBLIC_HERDR_COMMAND_PREFIXES[operation])


def _usage_contract(path: Path) -> UsageContract:
    provenance_for(path)
    return usage_contract_from_path(path)


def usage_contract_for(module: ModuleType, operation: object) -> UsageContract:
    """Herdr's captured usage declaration for one operation's command."""
    return _usage_contract(
        USAGE_FIXTURE_ROOT / f"{_command_fixture_name(module, operation)}.txt"
    )


def evidence_usage_contract_for(module: ModuleType, operation: object) -> UsageContract:
    """Herdr's captured usage declaration for one operation's evidence command."""
    prefix = module.EVIDENCE_COMMAND_PREFIXES[operation]
    return _usage_contract(USAGE_FIXTURE_ROOT / f"{_prefix_fixture_name(prefix)}.txt")


def _capture_path(root: Path, operation: object, file_name: str) -> Path:
    """The operation's own capture of a command when one exists, else the
    command's capture."""
    own = root / str(operation) / file_name
    return own if own.is_file() else root / file_name


def _evidence_result(
    module: ModuleType, operation: object, root: Path
) -> CommandResultContract | None:
    prefix = module.EVIDENCE_COMMAND_PREFIXES.get(operation)
    if prefix is None:
        return None
    path = _capture_path(root, operation, f"{_prefix_fixture_name(prefix)}.json")
    if not path.is_file():
        raise CaptureError(f"no captured evidence response at {path}")
    return _success_result(module, path)


def _success_result(module: ModuleType, path: Path) -> CommandResultContract:
    return cast(
        CommandResultContract,
        module.CommandResult(0, _captured_text(path), ""),
    )


def _error_result(module: ModuleType, path: Path) -> CommandResultContract:
    """The failing run that wrote a captured error envelope: the exit code the
    family records for that run, and the envelope on the stream herdr wrote."""
    exit_code = provenance_for(path).exit_code
    if exit_code is None:
        raise CaptureError(f"no exit code is captured for {path.relative_to(ROOT)}")
    return cast(
        CommandResultContract,
        module.CommandResult(exit_code, "", _captured_text(path)),
    )


def _replayable_error_paths(pattern: str) -> list[Path]:
    """Captured error envelopes whose run's exit code the family records. An
    envelope captured without its exit code is not replayed: the process status
    a replay would pair with it has no captured source."""
    return [
        path
        for path in sorted(ERROR_FIXTURE_ROOT.glob(pattern))
        if provenance_for(path).exit_code is not None
    ]


def _error_code(module: ModuleType, path: Path) -> str:
    envelope = json.loads(_captured_text(path))
    return str(envelope[module.ERROR_FIELD][module.CODE_FIELD])


def _response_shaping_fields(module: ModuleType) -> tuple[str, ...]:
    """Request fields whose presence changes what the command writes back.

    Herdr answers `agent prompt` with the state it observed after `--wait` and
    with the submission alone without it, so the two shapes are captured
    separately; every other option filters or bounds the same response shape.
    """
    return (module.WAIT_FIELD,)


def _shaping_suffix(module: ModuleType, fields: frozenset[str]) -> str:
    """The option-named suffix of the capture a request shape selects: the base
    command's capture carries none, and a capture taken with `--wait` carries
    `.wait`."""
    return "".join(
        f".{module.PUBLIC_HERDR_ARGUMENT_OPTIONS[field_name].lstrip('-')}"
        for field_name in _response_shaping_fields(module)
        if field_name in fields
    )


def _shaping_fields_of(
    module: ModuleType, arguments: dict[str, object] | None
) -> frozenset[str]:
    present = arguments or {}
    return frozenset(
        field_name
        for field_name in _response_shaping_fields(module)
        if present.get(field_name) is True
    )


def captured_success_response(
    module: ModuleType,
    operation: object,
    arguments: dict[str, object] | None = None,
) -> CapturedResponse | None:
    """Herdr's captured success response for one operation's request shape,
    when one exists: the capture taken under the same response-shaping options
    the request carries."""
    return _captured_success_under(
        module, operation, RESPONSE_FIXTURE_ROOT, _shaping_fields_of(module, arguments)
    )


def _captured_success_under(
    module: ModuleType, operation: object, root: Path, fields: frozenset[str]
) -> CapturedResponse | None:
    name = _command_fixture_name(module, operation)
    suffix = "txt" if operation in module.TEXT_OPERATIONS else "json"
    path = _capture_path(
        root, operation, f"{name}{_shaping_suffix(module, fields)}.{suffix}"
    )
    if not path.is_file():
        return None
    return CapturedResponse(
        operation,
        str(path.relative_to(ROOT)),
        provenance_for(path).source,
        _success_result(module, path),
        None,
        fields,
        _evidence_result(module, operation, root),
    )


def captured_incomplete_response(
    module: ModuleType, operation: object
) -> CapturedResponse:
    """Herdr's captured response of one operation's command for an agent session
    whose evidence lacks projected fields."""
    captured = _captured_success_under(
        module, operation, INCOMPLETE_FIXTURE_ROOT, frozenset()
    )
    if captured is None:
        raise CaptureError(f"no captured incomplete-evidence response for {operation}")
    return captured


def captured_session_payload(captured: CapturedResponse) -> dict[str, object]:
    """The captured JSON envelope carrying the session a result projects: the
    evidence command's when the operation runs one, else the operation's own.
    Only a success capture carries a session."""
    if captured.evidence is not None:
        return cast(dict[str, object], json.loads(captured.evidence.stdout))
    return cast(dict[str, object], captured_payload(captured))


def captured_session_agent(
    module: ModuleType, captured: CapturedResponse
) -> dict[str, object]:
    """The hosted agent session herdr wrote into a captured session envelope."""
    envelope = captured_session_payload(captured)
    result = cast(dict[str, object], envelope[module.RESULT_FIELD])
    return cast(dict[str, object], result[module.SESSION_FIELD])


def session_envelope(
    module: ModuleType, captured: CapturedResponse, agent: dict[str, object]
) -> CapturedResponse:
    """A captured session response with only its agent replaced, so the
    envelope's shape, stream, and exit code stay what herdr wrote."""
    envelope = captured_session_payload(captured)
    result = cast(dict[str, object], envelope[module.RESULT_FIELD])
    varied = json.dumps(
        {**envelope, module.RESULT_FIELD: {**result, module.SESSION_FIELD: agent}}
    )
    carrying = captured.evidence or captured.result
    result_varied = cast(
        CommandResultContract, module.CommandResult(carrying.returncode, varied, "")
    )
    if captured.evidence is not None:
        return CapturedResponse(
            captured.operation,
            f"{captured.path} with its evidence agent varied",
            captured.source,
            captured.result,
            None,
            captured.shaping_fields,
            result_varied,
        )
    return CapturedResponse(
        captured.operation,
        f"{captured.path} with its agent varied",
        captured.source,
        result_varied,
        None,
        captured.shaping_fields,
    )


def worktree_envelope(
    module: ModuleType, captured: CapturedResponse, checkout: Path
) -> CapturedResponse:
    """A captured worktree create or open response with only the created
    worktree's checkout path varied: every place herdr wrote that path — the
    worktree's own path, its workspace's checkout path, and its root pane's
    working directories — names `checkout` instead, so the envelope's shape,
    stream, and exit code stay what herdr wrote."""
    envelope = cast(dict[str, object], captured_payload(captured))
    result = cast(dict[str, object], envelope[module.RESULT_FIELD])
    worktree = cast(dict[str, object], result[module.WORKTREE_RESPONSE_FIELD])
    written = worktree[module.WORKTREE_PATH_RESPONSE_FIELD]

    def varied(value: object) -> object:
        if isinstance(value, dict):
            return {key: varied(item) for key, item in value.items()}
        if isinstance(value, list):
            return [varied(item) for item in value]
        return str(checkout) if value == written else value

    return CapturedResponse(
        captured.operation,
        f"{captured.path} with its worktree checkout path varied",
        captured.source,
        cast(
            CommandResultContract,
            module.CommandResult(
                captured.result.returncode, json.dumps(varied(envelope)), ""
            ),
        ),
        None,
        captured.shaping_fields,
    )


def captured_incomplete_agents(module: ModuleType) -> list[dict[str, object]]:
    """The hosted agent sessions herdr listed in the captured inventory that
    carries incomplete evidence."""
    captured = captured_incomplete_response(module, module.Operation.INVENTORY)
    envelope = cast(dict[str, object], captured_payload(captured))
    result = cast(dict[str, object], envelope[module.RESULT_FIELD])
    return cast(list[dict[str, object]], result[module.AGENTS_FIELD])


def captured_stopped_panes(module: ModuleType) -> list[dict[str, object]]:
    """The panes herdr listed in the stopped pane's workspace after stop."""
    envelope = json.loads(_captured_text(STOPPED_PANE_LIST_FIXTURE))
    result = cast(dict[str, object], envelope[module.RESULT_FIELD])
    return cast(list[dict[str, object]], result[PANE_LIST_FIELD])


@dataclass(frozen=True)
class ListedWorktree:
    """One Git worktree herdr's worktree list names: its checkout path, the
    workspace herdr has it open in, if any, and whether it is a linked worktree
    rather than the repository's primary checkout."""

    path: str
    open_workspace: str | None
    linked: bool


@dataclass(frozen=True)
class CapturedWorktreeList:
    """Herdr's captured worktree list: the workspace the list was taken for —
    the one the captured worktree requests named — and every worktree it lists."""

    named_workspace: str
    worktrees: tuple[ListedWorktree, ...]


def captured_worktree_list(module: ModuleType) -> CapturedWorktreeList:
    """The worktree list herdr wrote for the workspace the captured
    create-worktree and open-worktree requests named."""
    envelope = json.loads(_captured_text(WORKTREE_LIST_FIXTURE))
    result = cast(dict[str, object], envelope[module.RESULT_FIELD])
    source = cast(dict[str, object], result[WORKTREE_LIST_SOURCE_FIELD])
    listed = cast(list[dict[str, object]], result[WORKTREE_LIST_FIELD])
    return CapturedWorktreeList(
        str(source[WORKTREE_LIST_SOURCE_WORKSPACE_FIELD]),
        tuple(
            ListedWorktree(
                str(entry[module.WORKTREE_PATH_RESPONSE_FIELD]),
                cast(str | None, entry.get(LISTED_OPEN_WORKSPACE_FIELD)),
                cast(bool, entry[LISTED_LINKED_WORKTREE_FIELD]),
            )
            for entry in listed
        ),
    )


def _captured_success_variants(
    module: ModuleType, operation: object
) -> list[CapturedResponse]:
    """Every captured success response of one operation: the base command's and
    each option-shaped one its own request shapes admit."""
    allowed = module.OPERATION_CONTRACTS[operation].allowed_fields
    shaping = tuple(
        field_name
        for field_name in _response_shaping_fields(module)
        if field_name in allowed
    )
    variants: list[CapturedResponse] = []
    for size in range(len(shaping) + 1):
        for chosen in combinations(shaping, size):
            captured = captured_success_response(
                module, operation, dict.fromkeys(chosen, True)
            )
            if captured is not None:
                variants.append(captured)
    return variants


def captured_error_responses(
    module: ModuleType, operation: object
) -> list[CapturedResponse]:
    """Every error envelope herdr emitted for one operation's command, and for
    its evidence command after the operation's own command succeeded."""
    name = _command_fixture_name(module, operation)
    responses = [
        CapturedResponse(
            operation,
            str(path.relative_to(ROOT)),
            provenance_for(path).source,
            _error_result(module, path),
            _error_code(module, path),
        )
        for path in _replayable_error_paths(f"{name}.*.json")
    ]
    prefix = module.EVIDENCE_COMMAND_PREFIXES.get(operation)
    own = _captured_success_under(module, operation, RESPONSE_FIXTURE_ROOT, frozenset())
    if prefix is not None and own is not None:
        evidence_name = _prefix_fixture_name(prefix)
        responses.extend(
            CapturedResponse(
                operation,
                str(path.relative_to(ROOT)),
                provenance_for(path).source,
                own.result,
                _error_code(module, path),
                own.shaping_fields,
                _error_result(module, path),
            )
            for path in _replayable_error_paths(f"{evidence_name}.*.json")
        )
    return responses


def captured_responses(module: ModuleType) -> list[CapturedResponse]:
    """Every captured response, success and error, across every operation."""
    responses: list[CapturedResponse] = []
    for operation in module.Operation:
        responses.extend(_captured_success_variants(module, operation))
        responses.extend(captured_error_responses(module, operation))
    return responses


def captured_payload(response: CapturedResponse) -> object:
    """The captured response decoded: the JSON envelope, or the text verbatim."""
    if response.error_code is not None:
        failing = response.evidence or response.result
        return json.loads(failing.stderr)
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


def _captured_inventory_envelope(module: ModuleType) -> dict[str, object]:
    inventory = captured_success_response(module, module.Operation.INVENTORY)
    if inventory is None:
        raise RuntimeError("No captured herdr inventory response.")
    return cast(dict[str, object], captured_payload(inventory))


def inventory_envelope(
    module: ModuleType, agents: list[dict[str, object]]
) -> dict[str, object]:
    """Herdr's captured inventory envelope with only its agents list replaced."""
    envelope = _captured_inventory_envelope(module)
    result = cast(dict[str, object], envelope[module.RESULT_FIELD])
    return {
        **envelope,
        module.RESULT_FIELD: {**result, module.AGENTS_FIELD: agents},
    }


def projected_error_variants(module: ModuleType) -> list[CapturedResponse]:
    """A captured error envelope varied to each projected code herdr did not
    emit under the capture conditions: only the code changes, so the envelope's
    shape, stream, and exit code stay what herdr wrote in the captured run."""
    template = next(
        response
        for response in captured_responses(module)
        if response.error_code in module.HERDR_ERROR_STATUSES
    )
    failing = template.evidence or template.result
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
                template.source,
                cast(
                    CommandResultContract,
                    module.CommandResult(failing.returncode, "", variant),
                ),
                code,
            )
        )
    return variants


def request_for(
    module: ModuleType,
    operation: object,
    shaping_fields: frozenset[str] = frozenset(),
) -> dict[str, object]:
    """The first registry request of one operation whose response-shaping
    fields are exactly `shaping_fields`, from the generated set."""
    for request in operation_requests(module):
        if module.Operation(request[module.OPERATION_FIELD]) is not operation:
            continue
        arguments = cast(dict[str, object], request[module.ARGUMENTS_FIELD])
        if _shaping_fields_of(module, arguments) == shaping_fields:
            return request
    raise CaptureError(
        f"no registry request of {operation} carries exactly {sorted(shaping_fields)}"
    )


def run_inventory_mapping(
    assert_inventory: Callable[
        [ModuleType, dict[str, object], list[dict[str, object]], str, object], None
    ],
) -> None:
    """Drive herdr's captured inventory envelope as emitted, that envelope with
    an agents list carrying every server state by construction from its first
    item, and that envelope with generated agents lists, through the participant
    projection."""
    module = _load()
    template = captured_agent_item(module)
    captured = _captured_inventory_envelope(module)
    captured_agents = cast(
        list[dict[str, object]],
        cast(dict[str, object], captured[module.RESULT_FIELD])[module.AGENTS_FIELD],
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
        assert_inventory(module, captured, captured_agents, absent_name, state)
        assert_inventory(
            module,
            inventory_envelope(module, every_state),
            every_state,
            absent_name,
            state,
        )
        assert_inventory(
            module, inventory_envelope(module, agents), agents, absent_name, state
        )

    run_replayable_property(
        generated_inventory,
        seed_value=INVENTORY_SEED,
        replay_path=INVENTORY_REPLAY_PATH,
    )


def option_prefixed_requests(
    module: ModuleType, text: str
) -> list[tuple[dict[str, object], str]]:
    """Every registry request with one of herdr's own text arguments replaced by
    `text` under herdr's long-option prefix, paired with the field replaced.
    Agent arguments follow herdr's separator and are left as they are."""
    prefixed = f"{module.LONG_OPTION_PREFIX}{text}"
    variants: list[tuple[dict[str, object], str]] = []
    for request in operation_requests(module):
        arguments = cast(dict[str, object], request[module.ARGUMENTS_FIELD])
        for field_name in sorted(arguments):
            if field_name in module.TEXT_ARGUMENT_FIELDS:
                changed = {**arguments, field_name: prefixed}
            elif (
                field_name in module.TEXT_LIST_ARGUMENT_FIELDS
                and field_name != module.AGENT_ARGUMENTS_FIELD
            ):
                changed = {**arguments, field_name: [prefixed]}
            else:
                continue
            variants.append(({**request, module.ARGUMENTS_FIELD: changed}, field_name))
    return variants


def run_option_prefix_rejections(
    assert_case: Callable[[ModuleType, dict[str, object], str], None],
) -> None:
    """Drive generated texts under herdr's long-option prefix through every
    text argument of every registry request."""
    module = _load()

    @seed(OPTION_PREFIX_SEED)
    @settings(max_examples=OPTION_PREFIX_EXAMPLES, deadline=None, print_blob=True)
    @given(text=agent_names())
    def generated_prefix(text: str) -> None:
        for request, field_name in option_prefixed_requests(module, text):
            assert_case(module, request, field_name)

    run_replayable_property(
        generated_prefix,
        seed_value=OPTION_PREFIX_SEED,
        replay_path=OPTION_PREFIX_REPLAY_PATH,
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


def _disposable_git(*arguments: str, cwd: Path) -> None:
    subprocess.run(  # noqa: S603, S607 — git is a standard dev tool on PATH.
        ["git", *DISPOSABLE_GIT_IDENTITY, *arguments],
        check=True,
        capture_output=True,
        text=True,
        cwd=str(cwd),
        env={**os.environ, **DISPOSABLE_GIT_ENV},
        timeout=DISPOSABLE_COMMAND_TIMEOUT_SECONDS,
    )


@dataclass(frozen=True)
class DisposableWorktree:
    """A linked Git worktree in a disposable repository, standing where a
    created worktree stands: `path` is the checkout, `root` holds it together
    with the repository's primary checkout."""

    root: Path
    path: Path

    def occupancy(self) -> list[dict[str, object]]:
        """Spx's own occupancy report for the worktree, read from inside it."""
        return cast(list[dict[str, object]], worktree_occupancy(self.path))

    def files(self) -> dict[str, bytes]:
        """Every file under the disposable root, by relative path, with its bytes."""
        return {
            str(path.relative_to(self.root)): path.read_bytes()
            for path in sorted(self.root.rglob("*"))
            if path.is_file()
        }

    def record_claim(self) -> None:
        """Record a real worktree-occupancy claim on the worktree through spx,
        held by this process so spx reads it as live."""
        subprocess.run(  # noqa: S603, S607 — spx is the methodology CLI on PATH.
            ["spx", "worktree", "claim", "--session-id", str(uuid.uuid4())],
            check=True,
            capture_output=True,
            text=True,
            cwd=str(self.path),
            env={
                "PATH": os.environ.get("PATH", ""),
                "HOME": os.environ.get("HOME", ""),
                WORKTREE_CONTROLLING_PID_ENV: str(os.getpid()),
            },
            timeout=DISPOSABLE_COMMAND_TIMEOUT_SECONDS,
        )


@contextmanager
def disposable_worktree() -> Iterator[DisposableWorktree]:
    """Yield a linked worktree of a disposable repository and remove both on exit."""
    with TemporaryDirectory() as directory:
        root = Path(directory).resolve()
        primary = root / DISPOSABLE_PRIMARY_DIRECTORY
        worktree = root / DISPOSABLE_WORKTREE_DIRECTORY
        primary.mkdir()
        _disposable_git("init", "-q", cwd=primary)
        _disposable_git("commit", "-q", "--allow-empty", "-m", "initial", cwd=primary)
        _disposable_git(
            "worktree",
            "add",
            "-q",
            "-b",
            DISPOSABLE_WORKTREE_DIRECTORY,
            str(worktree),
            cwd=primary,
        )
        yield DisposableWorktree(root, worktree)


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
