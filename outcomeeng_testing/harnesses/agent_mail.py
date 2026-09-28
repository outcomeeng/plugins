"""Test infrastructure for the shipped agent-mail adapter."""

from __future__ import annotations

import importlib.util
import json
import os
import re
import shlex
import subprocess
import sys
from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from functools import cache
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from types import ModuleType
from typing import Protocol, cast

from hypothesis import given, seed, settings
from hypothesis import strategies as st

from outcomeeng_testing.generators.agent_mail import (
    COMMON_DIR_EXACT,
    COMMON_DIR_SHAPES,
    SUBJECT_BRANCHES,
    SubjectShape,
    activity_moments,
    agent_names,
    common_dir_output,
    capture_row_ordinals,
    conflicting_handback_contents,
    coordination_references,
    correlations,
    expected_project_key,
    handback_contents,
    message_records,
    message_texts,
    non_terminal_record_kinds,
    nul_carrying_requests,
    nul_positions,
    operation_requests,
    program_names,
    project_key_paths,
    runner_errors,
    sent_record_kinds,
    store_exit_codes,
    store_message_ids,
    subject_shapes,
    terminal_record_kinds,
    UNREADABLE_INPUT_FAMILIES,
    unreadable_request_texts,
    unsupported_operation_names,
)
from outcomeeng_testing.harnesses.cli_usage import (
    OPTIONS_HEADING,
    ATTACHED_VALUE_SEPARATOR,
    USAGE_PREFIX,
    UsageContract,
    read_argv,
    usage_contract,
)
from outcomeeng_testing.harnesses.property_evidence import run_replayable_property

ROOT = Path(__file__).parents[2]
AGENT_MAIL_PATH = (
    ROOT / "src/plugins/coding-agents/skills/operate-agent-mail/scripts/agent_mail.py"
)
CODING_AGENTS_RUNTIME_ROOTS = (
    ROOT / "src/plugins/coding-agents",
    ROOT / "dist/claude/coding-agents",
    ROOT / "dist/codex/coding-agents",
)
OPERATE_AGENT_MAIL_RELATIVE = Path("skills/operate-agent-mail")
FIXTURE_ROOT = ROOT / "outcomeeng_testing/fixtures/agent_mail"
# Every usage and response capture is one observation envelope the installed-
# store probe committed, copied byte for byte: the tool and version that
# answered, the argument vector it answered, its exit code, and its verbatim
# stdout and stderr. The envelope is the capture's provenance, so a capture from
# another release names that release in the file that carries it.
# Captured `am <command> --help` envelopes: the store CLI's own grammar
# declaration.
USAGE_FIXTURE_ROOT = FIXTURE_ROOT / "usage"
# Captured `am` responses for each operation's public command. The project key
# has no captured oracle: the checkout shapes a real repository takes are what
# the resolver is read against.
RESPONSE_FIXTURE_ROOT = FIXTURE_ROOT / "responses"
# Captured failures, one per condition the probe drove, named
# `<command>.<store error type>.json`.
ERROR_FIXTURE_ROOT = RESPONSE_FIXTURE_ROOT / "errors"
CAPTURE_SUFFIX = ".json"
# The fields of one observation envelope, as the probe protocol records them.
CAPTURE_TOOL_FIELD = "tool"
CAPTURE_VERSION_FIELD = "version"
CAPTURE_ARGV_FIELD = "argv"
CAPTURE_EXIT_CODE_FIELD = "exitCode"
CAPTURE_STDOUT_FIELD = "stdout"
CAPTURE_STDERR_FIELD = "stderr"
# The shape of an environment-variable name inside a usage description; the
# names themselves are the store's, read from its captured declaration.
ENVIRONMENT_NAME_PATTERN = re.compile(r"\b[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)+\b")
# A usage option entry's head: its short and long spelling, then its value
# placeholder, then the start of its description.
OPTION_ENTRY_HEAD = re.compile(
    r"^\s*(?:-[A-Za-z],\s*)?(?P<long>--[a-z][a-z0-9-]*)(?:\s+<[^>]+>)?(?P<rest>.*)$"
)
# The probe's listing observations, grouped by the mode the probe took each
# in: protocol step 6 took the unjudged listing — once in the store's default
# form and once naming the mode — and step 8 took the complete listing.
UNJUDGED_LISTING_CAPTURES = ("robot-inbox.json", "robot-inbox.include-bodies.json")
COMPLETE_LISTING_CAPTURES = ("robot-inbox.all.json",)
RAW_MAIL_VIOLATION_FIXTURE = FIXTURE_ROOT / "raw_am_command.py.txt"
RAW_MAIL_SHELL_VIOLATION_FIXTURE = FIXTURE_ROOT / "raw_am_shell_command.py.txt"
GIT_PROJECT_KEY_VIOLATION_FIXTURE = FIXTURE_ROOT / "git_project_key.py.txt"
RECORD_ROUNDTRIP_SEED = 2026091801
RECORD_ROUNDTRIP_EXAMPLES = 60
STORE_REJECTED_ROUNDTRIP_EXAMPLES = 20
RECORD_ROUNDTRIP_REPLAY_PATH = (
    "spx/43-coding-agents.enabler/18-agent-mail.enabler/tests/"
    "test_agent_mail.property.l1.py"
)
DELEGATION_CHAIN_SEED = 2026092201
DELEGATION_CHAIN_EXAMPLES = 20
TERMINAL_PROPERTY_SEED = 2026091802
TERMINAL_PROPERTY_EXAMPLES = 40
TERMINAL_PROPERTY_REPLAY_PATH = RECORD_ROUNDTRIP_REPLAY_PATH
CONFLICTING_HANDBACK_SEED = 2026092801
CONFLICTING_HANDBACK_EXAMPLES = 40
CONFLICTING_HANDBACK_REPLAY_PATH = RECORD_ROUNDTRIP_REPLAY_PATH
DELEGATION_CHAIN_REPLAY_PATH = RECORD_ROUNDTRIP_REPLAY_PATH
PROJECT_KEY_MAPPING_SEED = 2026091803
PROJECT_KEY_MAPPING_EXAMPLES = 20
PROJECT_KEY_MAPPING_REPLAY_PATH = (
    "spx/43-coding-agents.enabler/18-agent-mail.enabler/tests/"
    "test_agent_mail.mapping.l1.py"
)
OPERATION_MAPPING_SEED = 2026091804
OPERATION_MAPPING_EXAMPLES = 10
OPERATION_MAPPING_REPLAY_PATH = PROJECT_KEY_MAPPING_REPLAY_PATH
COMPLIANCE_SEED = 2026091805
COMPLIANCE_EXAMPLES = 10
STORE_RESPONSE_SEED = 2026091806
STORE_RESPONSE_EXAMPLES = 10
STORE_RESPONSE_REPLAY_PATH = PROJECT_KEY_MAPPING_REPLAY_PATH
LISTING_ROW_SEED = 2026091807
LISTING_ROW_EXAMPLES = 10
LISTING_ROW_REPLAY_PATH = PROJECT_KEY_MAPPING_REPLAY_PATH
RECIPIENT_BOUNDARY_SEED = 2026091808
RECIPIENT_BOUNDARY_EXAMPLES = 20
RECIPIENT_BOUNDARY_REPLAY_PATH = PROJECT_KEY_MAPPING_REPLAY_PATH
LISTING_MAPPING_SEED = 2026092701
LISTING_MAPPING_EXAMPLES = 10
LISTING_MAPPING_REPLAY_PATH = PROJECT_KEY_MAPPING_REPLAY_PATH
REGISTRATION_SEED = 2026092702
REGISTRATION_EXAMPLES = 20
REGISTRATION_REPLAY_PATH = PROJECT_KEY_MAPPING_REPLAY_PATH
SUBJECT_CLASSIFICATION_SEED = 2026092703
SUBJECT_CLASSIFICATION_EXAMPLES = 30
SUBJECT_CLASSIFICATION_REPLAY_PATH = PROJECT_KEY_MAPPING_REPLAY_PATH
STORE_ERROR_SEED = 2026092704
STORE_ERROR_EXAMPLES = 5
STORE_ERROR_REPLAY_PATH = PROJECT_KEY_MAPPING_REPLAY_PATH
COMPLIANCE_REPLAY_PATH = (
    "spx/43-coding-agents.enabler/18-agent-mail.enabler/tests/"
    "test_agent_mail.compliance.l1.py"
)
ACTIVITY_TIMESTAMP_SEED = 2026092705
ACTIVITY_TIMESTAMP_EXAMPLES = 30
UNREADABLE_INPUT_SEED = 2026092706
UNREADABLE_INPUT_EXAMPLES = 15
RUNNER_ERROR_SEED = 2026092707
RUNNER_ERROR_EXAMPLES = 60
NUL_ARGUMENT_SEED = 2026092708
NUL_ARGUMENT_EXAMPLES = 5
CLI_TIMEOUT_SECONDS = 60
# The pool one probe builds: a bare repository, the main checkout beside it,
# and one linked worktree, so the resolver is read from all three shapes.
POOL_REPOSITORY_NAME = "pool"
POOL_MAIN_CHECKOUT_NAME = "main"
POOL_LINKED_WORKTREE_NAME = "linked"
POOL_SEED_NAME = "seed"
POOL_SYMLINK_NAME = "linked-by-symlink"
# A directory inside the main checkout, so a shape exists whose repository lies
# strictly above its working directory. A variable that bounds where Git may
# discover a repository reaches only such a shape: at a checkout's own root the
# repository is found before any ceiling above it applies.
POOL_NESTED_RELATIVE = ("workspace", "package")
# A second repository beside the pool, no checkout of it. A caller carrying a
# variable that names a repository can name it, so the pool can be read from an
# environment that points away from the working directory.
FOREIGN_REPOSITORY_NAME = "foreign"
# One absolute key for probes that need a repository but do not vary it.
SHARED_PROJECT_KEY = "/repository/pool.git"
POOL_DEFAULT_BRANCH = "main"


class CommandResultContract(Protocol):
    returncode: int
    stdout: str
    stderr: str


class CaptureError(RuntimeError):
    """The captured store responses do not carry what a replay or variant needs."""


@dataclass(frozen=True)
class CapturedListingRow:
    """One row of a captured listing response, with the capture's path."""

    capture: str
    item: dict[str, object]


@dataclass(frozen=True)
class CapturedListingResponse:
    """One captured listing response, or a named variant of one, replayable by
    path, with the argument vector the store answered it for."""

    capture: str
    argv: tuple[str, ...]
    result: CommandResultContract
    payload: dict[str, object]


@dataclass(frozen=True)
class ListingCaptures:
    """The captured listing responses, by the mode the probe took each in."""

    unjudged: tuple[CapturedListingResponse, ...]
    complete: tuple[CapturedListingResponse, ...]


@dataclass(frozen=True)
class ListingReplay:
    """A listing request paired with the captured response the store gave in
    the same mode and row shape."""

    request: dict[str, object]
    captured: CapturedListingResponse


@dataclass(frozen=True)
class StoreCapture:
    """One committed observation of the store, read from its envelope: the tool
    and version that answered, the argument vector it answered, and what it
    returned."""

    path: Path
    tool: str
    version: str
    argv: tuple[str, ...]
    exit_code: int
    stdout: str
    stderr: str


@dataclass(frozen=True)
class CapturedStoreResponse:
    """One captured store response replayable as a command result, with the
    capture's path."""

    capture: str
    result: CommandResultContract


@dataclass
class RecordingRunner:
    """Interaction-protocol collaborator: records every argv, replays results.

    ``env`` is accepted because the runner boundary carries it and dropped
    because a replayed result depends on no environment; what the repository
    lookup removes from it is read end to end, through the shipped CLI in a
    real repository, not from a recorded call.
    """

    results: list[CommandResultContract]
    calls: list[tuple[tuple[str, ...], str | None]] = field(default_factory=list)

    def run(
        self,
        argv: tuple[str, ...],
        stdin: str | None = None,
        env: Mapping[str, str] | None = None,
    ) -> CommandResultContract:
        self.calls.append((argv, stdin))
        if not self.results:
            raise RuntimeError(f"Unexpected command: {argv}")
        return self.results.pop(0)


@dataclass
class AbsentExecutableRunner:
    """Failure-simulation collaborator: the named executable is not installed."""

    absent_executable: str
    results: list[CommandResultContract] = field(default_factory=list)
    calls: list[tuple[tuple[str, ...], str | None]] = field(default_factory=list)

    def run(
        self,
        argv: tuple[str, ...],
        stdin: str | None = None,
        env: Mapping[str, str] | None = None,
    ) -> CommandResultContract:
        self.calls.append((argv, stdin))
        if argv[0] == self.absent_executable:
            raise FileNotFoundError(argv[0])
        if not self.results:
            raise RuntimeError(f"Unexpected command: {argv}")
        return self.results.pop(0)


@dataclass
class RaisingRunner:
    """Failure-simulation collaborator: running the named program raises
    ``error``; every other program replays ``results`` in order."""

    failing_program: str
    error: Exception
    results: list[CommandResultContract] = field(default_factory=list)
    calls: list[tuple[tuple[str, ...], str | None]] = field(default_factory=list)

    def run(
        self,
        argv: tuple[str, ...],
        stdin: str | None = None,
        env: Mapping[str, str] | None = None,
    ) -> CommandResultContract:
        self.calls.append((argv, stdin))
        if argv[0] == self.failing_program:
            raise self.error
        if not self.results:
            raise RuntimeError(f"Unexpected command: {argv}")
        return self.results.pop(0)


def _load() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "coding_agents_agent_mail", AGENT_MAIL_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load agent-mail module: {AGENT_MAIL_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_agent_mail() -> ModuleType:
    """Load the shipped adapter so linked tests can inspect its public contract."""
    return _load()


def text_command_result(module: ModuleType, text: str) -> CommandResultContract:
    return cast(CommandResultContract, module.CommandResult(0, text, ""))


def failed_command_result(
    module: ModuleType, returncode: int, stderr: str
) -> CommandResultContract:
    return cast(CommandResultContract, module.CommandResult(returncode, "", stderr))


def _command_path(module: ModuleType, operation: object) -> tuple[str, ...]:
    return tuple(module.PUBLIC_AM_COMMAND_PREFIXES[operation])


def _command_fixture_name(module: ModuleType, operation: object) -> str:
    return "-".join(_command_path(module, operation)[1:])


def _listing_operation(module: ModuleType) -> object:
    """The one operation whose request can ask the store for message bodies."""
    listing = [
        operation
        for operation, contract in module.OPERATION_CONTRACTS.items()
        if module.INCLUDE_BODIES_FIELD in contract.allowed_fields
    ]
    if len(listing) != 1:
        raise CaptureError(
            f"the registry declares {len(listing)} operations that take bodies; "
            "one is required"
        )
    return listing[0]


def _envelope_text(envelope: Mapping[str, object], name: str, path: Path) -> str:
    value = envelope.get(name)
    if not isinstance(value, str):
        raise CaptureError(f"{path} carries no text {name}")
    return value


def _read_envelope(path: Path) -> StoreCapture:
    """One observation envelope, read as the probe recorded it."""
    try:
        envelope = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise CaptureError(f"{path} is no readable observation envelope") from error
    if not isinstance(envelope, dict):
        raise CaptureError(f"{path} is no observation envelope")
    argv = envelope.get(CAPTURE_ARGV_FIELD)
    exit_code = envelope.get(CAPTURE_EXIT_CODE_FIELD)
    if not isinstance(argv, list) or not all(isinstance(token, str) for token in argv):
        raise CaptureError(f"{path} carries no argument vector")
    if not isinstance(exit_code, int) or isinstance(exit_code, bool):
        raise CaptureError(f"{path} carries no exit code")
    capture = StoreCapture(
        path=path,
        tool=_envelope_text(envelope, CAPTURE_TOOL_FIELD, path),
        version=_envelope_text(envelope, CAPTURE_VERSION_FIELD, path),
        argv=tuple(argv),
        exit_code=exit_code,
        stdout=_envelope_text(envelope, CAPTURE_STDOUT_FIELD, path),
        stderr=_envelope_text(envelope, CAPTURE_STDERR_FIELD, path),
    )
    if not capture.tool or not capture.version:
        raise CaptureError(f"{path} names no tool and version")
    if not capture.argv or capture.argv[0] != capture.tool:
        raise CaptureError(f"{path} records a command its tool did not run")
    return capture


@cache
def _capture_family_provenance() -> tuple[str, str]:
    """The one tool and version every committed capture was answered by.

    The captures are one probe run's observations, so a family whose members
    name different releases holds a stale oracle beside a current one.
    """
    paths = sorted(
        path
        for root in (USAGE_FIXTURE_ROOT, RESPONSE_FIXTURE_ROOT)
        for path in root.rglob(f"*{CAPTURE_SUFFIX}")
    )
    provenance = {
        (capture.tool, capture.version)
        for capture in (_read_envelope(path) for path in paths)
    }
    if len(provenance) != 1:
        raise CaptureError(
            f"the captures name {sorted(provenance)}; one tool and version is required"
        )
    return provenance.pop()


def _read_capture(path: Path, command_path: tuple[str, ...]) -> StoreCapture:
    """The capture at ``path``, which must record the subcommand path its name
    carries, answered by the release every other capture names.

    Only the subcommands are compared: the program the capture ran is the
    capture's own record, which the linked tests read against the adapter.
    """
    capture = _read_envelope(path)
    if (capture.tool, capture.version) != _capture_family_provenance():
        raise CaptureError(f"{path} was answered by another release than its family")
    subcommands = command_path[1:]
    if capture.argv[1 : 1 + len(subcommands)] != subcommands:
        raise CaptureError(f"{path} records {capture.argv}, not {subcommands}")
    return capture


def _usage_capture(module: ModuleType, operation: object) -> StoreCapture:
    name = _command_fixture_name(module, operation)
    return _read_capture(
        USAGE_FIXTURE_ROOT / f"{name}{CAPTURE_SUFFIX}",
        _command_path(module, operation),
    )


def usage_contract_for(module: ModuleType, operation: object) -> UsageContract:
    """The store CLI's captured usage declaration for one operation's command."""
    return usage_contract(_usage_capture(module, operation).stdout)


def _response_shaping_fields(module: ModuleType) -> tuple[str, ...]:
    """Request fields whose presence changes the row shape the store writes back:
    `--include-bodies` adds the body to every inbox row, while the other options
    filter or bound the same shape."""
    return (module.INCLUDE_BODIES_FIELD,)


def _shaping_suffix(module: ModuleType, arguments: dict[str, object] | None) -> str:
    """The option-named suffix of the capture a request shape selects: the base
    command's capture carries none, and one taken with `--include-bodies`
    carries `.include-bodies`."""
    present = arguments or {}
    return "".join(
        f".{module.PUBLIC_AM_ARGUMENT_OPTIONS[field_name].lstrip('-')}"
        for field_name in _response_shaping_fields(module)
        if present.get(field_name) is True
    )


def _response_fixture_path(
    module: ModuleType, operation: object, arguments: dict[str, object] | None
) -> Path:
    name = _command_fixture_name(module, operation)
    return (
        RESPONSE_FIXTURE_ROOT
        / f"{name}{_shaping_suffix(module, arguments)}{CAPTURE_SUFFIX}"
    )


def _result_from_capture(
    module: ModuleType, capture: StoreCapture
) -> CommandResultContract:
    """The captured answer as the runner boundary returns one: the recorded
    exit code, stdout, and stderr, unchanged."""
    return cast(
        CommandResultContract,
        module.CommandResult(capture.exit_code, capture.stdout, capture.stderr),
    )


def store_response_result(
    module: ModuleType,
    operation: object,
    arguments: dict[str, object] | None = None,
) -> CommandResultContract:
    """The store's captured response for one operation's request shape, by path:
    the capture taken under the same response-shaping options the request
    carries."""
    capture = _read_capture(
        _response_fixture_path(module, operation, arguments),
        _command_path(module, operation),
    )
    return _result_from_capture(module, capture)


def store_response_payload(
    module: ModuleType,
    operation: object,
    arguments: dict[str, object] | None = None,
) -> object:
    """The captured response decoded: JSON for JSON operations, text otherwise."""
    result = store_response_result(module, operation, arguments)
    if operation in module.JSON_OPERATIONS:
        return json.loads(result.stdout)
    return result.stdout.strip()


def store_response_text(
    module: ModuleType,
    operation: object,
    arguments: dict[str, object] | None = None,
) -> str:
    """The captured response exactly as the store printed it."""
    return store_response_result(module, operation, arguments).stdout


def store_error_responses(
    module: ModuleType, operation: object
) -> list[CapturedStoreResponse]:
    """Every captured failure of one operation's command, in path order, each
    replayable with the exit code and stderr the store answered."""
    name = _command_fixture_name(module, operation)
    command_path = _command_path(module, operation)
    return [
        CapturedStoreResponse(
            str(path.relative_to(ROOT)),
            _result_from_capture(module, _read_capture(path, command_path)),
        )
        for path in sorted(ERROR_FIXTURE_ROOT.glob(f"{name}.*{CAPTURE_SUFFIX}"))
    ]


def store_error_capture_names() -> frozenset[str]:
    """Every captured store failure, by its path."""
    return frozenset(
        str(path.relative_to(ROOT))
        for path in ERROR_FIXTURE_ROOT.glob(f"*{CAPTURE_SUFFIX}")
    )


# The store error type naming the capture of a send the store refused for its
# thread id, in the `<command>.<store error type>.json` convention.
THREAD_REJECTION_ERROR_TYPE = "invalid_thread_id"


def store_rejected_threads(module: ModuleType) -> tuple[str, ...]:
    """Every thread id the store refused a send under, read from the argument
    vector of each captured thread rejection."""
    operation = module.Operation.SEND
    name = _command_fixture_name(module, operation)
    prefix = f"{module.THREAD_ID_OPTION}{module.ATTACHED_OPTION_SEPARATOR}"
    threads: list[str] = []
    for path in sorted(
        ERROR_FIXTURE_ROOT.glob(
            f"{name}.{THREAD_REJECTION_ERROR_TYPE}*{CAPTURE_SUFFIX}"
        )
    ):
        capture = _read_capture(path, _command_path(module, operation))
        threads.extend(
            token[len(prefix) :] for token in capture.argv if token.startswith(prefix)
        )
    if not threads:
        raise CaptureError("no captured send failure names a rejected thread id")
    return tuple(threads)


def _listing_capture(module: ModuleType, name: str) -> CapturedListingResponse:
    path = RESPONSE_FIXTURE_ROOT / name
    capture = _read_capture(path, _command_path(module, _listing_operation(module)))
    payload = json.loads(capture.stdout)
    if not isinstance(payload, dict):
        raise CaptureError(f"{path} answered no listing object")
    return CapturedListingResponse(
        str(path.relative_to(ROOT)),
        capture.argv,
        _result_from_capture(module, capture),
        cast(dict[str, object], payload),
    )


def listing_captures(module: ModuleType) -> ListingCaptures:
    """Every captured listing response, by the mode the probe took it in.

    Every listing capture belongs to exactly one mode, so a capture added
    without a mode fails the read rather than going unexamined.
    """
    listed = {
        path.name
        for path in RESPONSE_FIXTURE_ROOT.glob(
            f"{_command_fixture_name(module, _listing_operation(module))}*{CAPTURE_SUFFIX}"
        )
    }
    grouped = set(UNJUDGED_LISTING_CAPTURES) | set(COMPLETE_LISTING_CAPTURES)
    if listed != grouped or set(UNJUDGED_LISTING_CAPTURES) & set(
        COMPLETE_LISTING_CAPTURES
    ):
        raise CaptureError(
            f"listing captures {sorted(listed)} are not each in exactly one mode "
            f"of {sorted(grouped)}"
        )
    return ListingCaptures(
        unjudged=tuple(
            _listing_capture(module, name) for name in UNJUDGED_LISTING_CAPTURES
        ),
        complete=tuple(
            _listing_capture(module, name) for name in COMPLETE_LISTING_CAPTURES
        ),
    )


def _carries_bodies(module: ModuleType, argv: tuple[str, ...]) -> bool:
    return module.PUBLIC_AM_ARGUMENT_OPTIONS[module.INCLUDE_BODIES_FIELD] in argv


def captured_listing_responses_with_bodies(
    module: ModuleType,
) -> list[CapturedListingResponse]:
    """Each captured listing response the store answered with bodies."""
    captures = listing_captures(module)
    return [
        captured
        for captured in (*captures.unjudged, *captures.complete)
        if _carries_bodies(module, captured.argv)
    ]


def captured_listing_rows_with_bodies(module: ModuleType) -> list[CapturedListingRow]:
    """Every row across the captured listing responses with bodies."""
    return [
        CapturedListingRow(response.capture, cast(dict[str, object], item))
        for response in captured_listing_responses_with_bodies(module)
        for item in cast(list[object], response.payload[module.STORE_INBOX_FIELD])
    ]


def _row_variant(
    row: CapturedListingRow, changes: dict[str, object]
) -> dict[str, object]:
    """The captured row with the named values replaced. A variant changes only
    values the capture carries; a key the store never wrote is a capture gap."""
    absent = sorted(set(changes) - set(row.item))
    if absent:
        raise CaptureError(
            f"{row.capture} carries no {', '.join(absent)}; a variant changes "
            "only values the captured row has"
        )
    return {**row.item, **changes}


def listing_response_without_thread(
    module: ModuleType, response: CapturedListingResponse
) -> CapturedListingResponse:
    """The captured listing response with the thread removed from its first
    row: the variant ranges over the thread value alone, and names the capture
    it varies."""
    items = cast(list[dict[str, object]], response.payload[module.STORE_INBOX_FIELD])
    if not items:
        raise CaptureError(f"{response.capture} lists no row to vary")
    first = CapturedListingRow(response.capture, items[0])
    if module.STORE_THREAD_FIELD not in first.item:
        raise CaptureError(f"{response.capture} carries no thread on its first row")
    varied = {
        key: value
        for key, value in first.item.items()
        if key != module.STORE_THREAD_FIELD
    }
    payload = {**response.payload, module.STORE_INBOX_FIELD: [varied, *items[1:]]}
    return CapturedListingResponse(
        f"{response.capture} (first row without {module.STORE_THREAD_FIELD})",
        response.argv,
        cast(CommandResultContract, module.CommandResult(0, json.dumps(payload), "")),
        payload,
    )


def acknowledgement_requirements(module: ModuleType) -> dict[int, bool]:
    """Whether each message the probe sent required an acknowledgement, read
    from the store's own answers rather than from any listing status.

    The captured send answers with the message's id and the store's own
    `ack_required` flag. The captured acknowledgement names the message the
    probe acknowledged, which protocol step 5 sent with `--ack-required` and
    step 8 acknowledged, so that message required one.
    """
    sent = store_response_payload(module, module.Operation.SEND)
    if not isinstance(sent, dict):
        raise CaptureError("the captured send answered no message object")
    sent_id = sent.get(module.STORE_ID_FIELD)
    sent_flag = sent.get(module.STORE_ACK_REQUIRED_FIELD)
    if not isinstance(sent_id, int) or not isinstance(sent_flag, bool):
        raise CaptureError("the captured send carries no id and acknowledgement flag")
    operation = module.Operation.ACKNOWLEDGE
    capture = _read_capture(
        _response_fixture_path(module, operation, None),
        _command_path(module, operation),
    )
    positionals = read_argv(
        usage_contract_for(module, operation), capture.argv
    ).positionals
    if len(positionals) != 1 or not positionals[0].isdigit():
        raise CaptureError(f"{capture.path} names no one acknowledged message")
    acknowledged = int(positionals[0])
    if acknowledged == sent_id and not sent_flag:
        raise CaptureError("the acknowledged message was sent requiring none")
    return {sent_id: sent_flag, acknowledged: True}


def common_dir_reply(module: ModuleType) -> CommandResultContract:
    """The repository lookup's reply naming one generated project key."""
    return text_command_result(
        module, common_dir_output(COMMON_DIR_EXACT, SHARED_PROJECT_KEY)
    )


def common_dir_seeded_runner(
    module: ModuleType, project_key: str, *results: CommandResultContract
) -> RecordingRunner:
    """A recording runner whose first reply is the repository lookup printing
    `project_key`, followed by the store replies in order."""
    return RecordingRunner(
        [
            text_command_result(
                module, common_dir_output(COMMON_DIR_EXACT, project_key)
            ),
            *results,
        ]
    )


def common_dir_seeded_absent_store_runner(
    module: ModuleType, project_key: str
) -> AbsentExecutableRunner:
    """A runner that resolves `project_key` from the repository and then finds
    no store executable."""
    return AbsentExecutableRunner(
        module.AM_COMMAND,
        [text_command_result(module, common_dir_output(COMMON_DIR_EXACT, project_key))],
    )


def store_listing_echo(
    module: ModuleType,
    send_fields: dict[str, object],
    message_id: int,
    row_ordinal: int,
) -> dict[str, object]:
    """Render a sent message the way the store's listing surface returned a
    message of the same acknowledgement requirement.

    The row is a captured listing row with bodies whose message the store
    answered as requiring an acknowledgement exactly when the send does — read
    from `acknowledgement_requirements`, never from the row's status — with
    the sender, subject, thread, body, and id the send wrote and the store
    assigned in place of the captured values. `row_ordinal` selects among the
    matching rows. The status, and every other key, stay the store's own bytes.
    """
    ack_required = send_fields[module.STORE_ACK_REQUIRED_FIELD] is True
    requirements = acknowledgement_requirements(module)
    rows = [
        row
        for row in captured_listing_rows_with_bodies(module)
        if requirements.get(cast(int, row.item.get(module.STORE_ID_FIELD)))
        is ack_required
    ]
    if not rows:
        raise CaptureError(
            "no captured listing row with bodies shows a message whose "
            f"acknowledgement requirement is {ack_required}"
        )
    return _row_variant(
        rows[row_ordinal % len(rows)],
        {
            module.STORE_ID_FIELD: message_id,
            module.STORE_FROM_FIELD: send_fields[module.STORE_FROM_FIELD],
            module.STORE_SUBJECT_FIELD: send_fields[module.STORE_SUBJECT_FIELD],
            module.STORE_THREAD_FIELD: send_fields[module.STORE_THREAD_ID_FIELD],
            module.STORE_BODY_FIELD: send_fields[module.STORE_BODY_FIELD],
        },
    )


def run_record_roundtrip_property(
    assert_roundtrip: Callable[
        [ModuleType, dict[str, object], int, int, frozenset[str]], None
    ],
) -> None:
    """Drive generated records while the linked test owns the round-trip predicate.

    Two runs share the predicate: records over the open correlation domain,
    and records whose correlation is one the store was observed rejecting as a
    thread id. The linked test receives those rejected correlations as the
    store's own observation.
    """
    module = _load()
    rejected = store_rejected_threads(module)
    domains = (
        (correlations(module, rejected), RECORD_ROUNDTRIP_EXAMPLES),
        (st.sampled_from(rejected), STORE_REJECTED_ROUNDTRIP_EXAMPLES),
    )

    def drive(correlation: st.SearchStrategy[str], examples: int) -> Callable[[], None]:
        @seed(RECORD_ROUNDTRIP_SEED)
        @settings(max_examples=examples, deadline=None, print_blob=True)
        @given(
            record=message_records(module, correlation),
            message_id=store_message_ids(),
            row_ordinal=capture_row_ordinals(),
        )
        def generated_roundtrip(
            record: dict[str, object], message_id: int, row_ordinal: int
        ) -> None:
            assert_roundtrip(
                module, record, message_id, row_ordinal, frozenset(rejected)
            )

        return generated_roundtrip

    for correlation, examples in domains:
        run_replayable_property(
            drive(correlation, examples),
            seed_value=RECORD_ROUNDTRIP_SEED,
            replay_path=RECORD_ROUNDTRIP_REPLAY_PATH,
        )


def run_delegation_chain_property(
    assert_chain: Callable[
        [ModuleType, str, list[dict[str, object]], RecordingRunner], None
    ],
) -> None:
    """Drive an order, its delegation request, and its one correlated terminal
    handback through the capability's own send path under one reference.

    The three records share a correlation, and each is delivered by the same
    `send` operation a caller uses, so the chain is evidenced where it happens
    rather than at the reduction that follows it.
    """
    module = _load()

    @seed(DELEGATION_CHAIN_SEED)
    @settings(max_examples=DELEGATION_CHAIN_EXAMPLES, deadline=None, print_blob=True)
    @given(
        reference=correlations(module, store_rejected_threads(module)),
        terminal_kind=terminal_record_kinds(module),
        sender=agent_names(),
        recipient=agent_names(),
        subject=message_texts(),
        body=message_texts(),
        project_key=project_key_paths(),
    )
    def generated_chain(
        reference: str,
        terminal_kind: object,
        sender: str,
        recipient: str,
        subject: str,
        body: str,
        project_key: str,
    ) -> None:
        def record(kind: object, from_agent: str, to_agent: str) -> dict[str, object]:
            return cast(
                dict[str, object],
                module.message_record(
                    kind=kind,
                    correlation=reference,
                    sender=from_agent,
                    recipient=to_agent,
                    subject=subject,
                    body=body,
                ),
            )

        chain = [
            record(module.RecordKind.ORDER, sender, recipient),
            record(module.RecordKind.DELEGATION_REQUEST, sender, recipient),
            record(terminal_kind, recipient, sender),
        ]
        # Each operation resolves the key before it reaches the store, so the
        # repository answers once per send rather than once per chain.
        replies: list[CommandResultContract] = []
        for _ in chain:
            replies.append(
                text_command_result(
                    module, common_dir_output(COMMON_DIR_EXACT, project_key)
                )
            )
            replies.append(store_response_result(module, module.Operation.SEND))
        assert_chain(module, reference, chain, RecordingRunner(replies))

    run_replayable_property(
        generated_chain,
        seed_value=DELEGATION_CHAIN_SEED,
        replay_path=DELEGATION_CHAIN_REPLAY_PATH,
    )


@dataclass(frozen=True)
class TerminalCase:
    """One generated terminal-handback case.

    ``reference`` and ``other_reference`` are distinct coordination
    references; ``first_kind`` and ``second_kind`` are terminal kinds, equal
    or not; ``non_terminal_kind`` closes no delegation; ``content`` is a
    generated sender, recipient, subject, and body.
    """

    reference: str
    other_reference: str
    first_kind: object
    second_kind: object
    non_terminal_kind: object
    content: dict[str, str]


def run_terminal_property(
    assert_terminal: Callable[[ModuleType, TerminalCase], None],
) -> None:
    """Drive generated terminal handbacks while the linked test owns the predicate."""
    module = _load()
    references = correlations(module, store_rejected_threads(module))

    @seed(TERMINAL_PROPERTY_SEED)
    @settings(max_examples=TERMINAL_PROPERTY_EXAMPLES, deadline=None, print_blob=True)
    @given(
        reference_pair=st.tuples(references, references).filter(
            lambda pair: pair[0] != pair[1]
        ),
        first_kind=terminal_record_kinds(module),
        second_kind=terminal_record_kinds(module),
        non_terminal_kind=non_terminal_record_kinds(module),
        content=handback_contents(module),
    )
    def generated_terminal(
        reference_pair: tuple[str, str],
        first_kind: object,
        second_kind: object,
        non_terminal_kind: object,
        content: dict[str, str],
    ) -> None:
        assert_terminal(
            module,
            TerminalCase(
                reference=reference_pair[0],
                other_reference=reference_pair[1],
                first_kind=first_kind,
                second_kind=second_kind,
                non_terminal_kind=non_terminal_kind,
                content=content,
            ),
        )

    run_replayable_property(
        generated_terminal,
        seed_value=TERMINAL_PROPERTY_SEED,
        replay_path=TERMINAL_PROPERTY_REPLAY_PATH,
    )


@dataclass(frozen=True)
class ConflictingHandbackCase:
    """One generated pair of same-kind terminal handbacks for one reference.

    ``kind`` is a terminal kind both handbacks carry; ``content`` and
    ``other_content`` are sender, recipient, subject, and body values that
    differ in a generated nonempty set of those fields.
    """

    reference: str
    kind: object
    content: dict[str, str]
    other_content: dict[str, str]


def run_conflicting_handback_property(
    assert_conflicting: Callable[[ModuleType, ConflictingHandbackCase], None],
) -> None:
    """Drive generated same-kind handback pairs while the linked test owns the predicate."""
    module = _load()

    @seed(CONFLICTING_HANDBACK_SEED)
    @settings(
        max_examples=CONFLICTING_HANDBACK_EXAMPLES, deadline=None, print_blob=True
    )
    @given(
        reference=correlations(module, store_rejected_threads(module)),
        kind=terminal_record_kinds(module),
        contents=conflicting_handback_contents(module),
    )
    def generated_conflicting(
        reference: str,
        kind: object,
        contents: tuple[dict[str, str], dict[str, str]],
    ) -> None:
        content, other_content = contents
        assert_conflicting(
            module,
            ConflictingHandbackCase(
                reference=reference,
                kind=kind,
                content=content,
                other_content=other_content,
            ),
        )

    run_replayable_property(
        generated_conflicting,
        seed_value=CONFLICTING_HANDBACK_SEED,
        replay_path=CONFLICTING_HANDBACK_REPLAY_PATH,
    )


def run_project_key_mapping(
    assert_key: Callable[[ModuleType, str, str, str | None, str], None],
) -> None:
    """Drive every shape the repository lookup's output takes, each built
    around a generated absolute path."""
    module = _load()

    def drive(shape: str) -> Callable[[], None]:
        @seed(PROJECT_KEY_MAPPING_SEED)
        @settings(
            max_examples=PROJECT_KEY_MAPPING_EXAMPLES, deadline=None, print_blob=True
        )
        @given(path=project_key_paths(), agent=agent_names())
        def generated_key_mapping(path: str, agent: str) -> None:
            output = common_dir_output(shape, path)
            assert_key(module, shape, output, expected_project_key(shape, path), agent)

        return generated_key_mapping

    for shape in COMMON_DIR_SHAPES:
        run_replayable_property(
            drive(shape),
            seed_value=PROJECT_KEY_MAPPING_SEED,
            replay_path=PROJECT_KEY_MAPPING_REPLAY_PATH,
        )


def run_operation_mapping(
    assert_operation: Callable[[ModuleType, dict[str, object], str], None],
) -> None:
    """Drive every registry request by construction under generated project keys."""
    module = _load()
    requests = operation_requests(module)

    @seed(OPERATION_MAPPING_SEED)
    @settings(max_examples=OPERATION_MAPPING_EXAMPLES, deadline=None, print_blob=True)
    @given(project_key=project_key_paths())
    def generated_mapping(project_key: str) -> None:
        for request in requests:
            assert_operation(module, request, project_key)

    run_replayable_property(
        generated_mapping,
        seed_value=OPERATION_MAPPING_SEED,
        replay_path=OPERATION_MAPPING_REPLAY_PATH,
    )


def run_listing_mapping(
    assert_request: Callable[[ModuleType, dict[str, object], str], None],
) -> None:
    """Drive every registry listing request by construction under generated
    project keys."""
    module = _load()
    listing = _listing_operation(module)
    requests = [
        request
        for request in operation_requests(module)
        if module.Operation(request[module.OPERATION_FIELD]) is listing
    ]

    @seed(LISTING_MAPPING_SEED)
    @settings(max_examples=LISTING_MAPPING_EXAMPLES, deadline=None, print_blob=True)
    @given(project_key=project_key_paths())
    def generated_listing(project_key: str) -> None:
        for request in requests:
            assert_request(module, request, project_key)

    run_replayable_property(
        generated_listing,
        seed_value=LISTING_MAPPING_SEED,
        replay_path=LISTING_MAPPING_REPLAY_PATH,
    )


def _listing_request_for(
    module: ModuleType, agent: str, *, complete: bool, bodies: bool
) -> dict[str, object]:
    return cast(
        dict[str, object],
        module.operation_request(
            _listing_operation(module),
            agent=agent,
            all_records=True if complete else None,
            include_bodies=True if bodies else None,
        ),
    )


def run_listing_row_mapping(
    assert_rows: Callable[[ModuleType, ListingReplay, str], None],
) -> None:
    """Drive every captured listing response, and the variant of each without
    a thread on its first row, through the listing request of the same mode
    and row shape, under generated project keys and recipients."""
    module = _load()
    captures = listing_captures(module)
    modes = [(captured, False) for captured in captures.unjudged] + [
        (captured, True) for captured in captures.complete
    ]
    responses = [
        (response, complete)
        for captured, complete in modes
        for response in (captured, listing_response_without_thread(module, captured))
    ]

    @seed(LISTING_ROW_SEED)
    @settings(max_examples=LISTING_ROW_EXAMPLES, deadline=None, print_blob=True)
    @given(project_key=project_key_paths(), agent=agent_names())
    def generated_rows(project_key: str, agent: str) -> None:
        for response, complete in responses:
            request = _listing_request_for(
                module,
                agent,
                complete=complete,
                bodies=_carries_bodies(module, response.argv),
            )
            assert_rows(module, ListingReplay(request, response), project_key)

    run_replayable_property(
        generated_rows,
        seed_value=LISTING_ROW_SEED,
        replay_path=LISTING_ROW_REPLAY_PATH,
    )


def _threaded_listing_rows(module: ModuleType) -> list[CapturedListingRow]:
    captures = listing_captures(module)
    rows = [
        CapturedListingRow(response.capture, cast(dict[str, object], item))
        for response in (*captures.unjudged, *captures.complete)
        for item in cast(list[object], response.payload[module.STORE_INBOX_FIELD])
    ]
    threaded = [row for row in rows if row.item.get(module.STORE_THREAD_FIELD)]
    if not threaded:
        raise CaptureError("no captured listing row carries a thread")
    return threaded


def run_subject_classification(
    assert_case: Callable[
        [ModuleType, str, dict[str, object], str, SubjectShape, bool], None
    ],
) -> None:
    """Drive every subject shape through a captured listing row, threaded and
    threadless, for a generated recipient.

    The row is a captured row with a thread, its subject replaced by the
    generated one; the threadless variant also drops the thread.
    """
    module = _load()
    rows = _threaded_listing_rows(module)

    def drive(branch: str) -> Callable[[], None]:
        @seed(SUBJECT_CLASSIFICATION_SEED)
        @settings(
            max_examples=SUBJECT_CLASSIFICATION_EXAMPLES,
            deadline=None,
            print_blob=True,
        )
        @given(
            shape=subject_shapes(module, branch),
            threadless=st.booleans(),
            recipient=agent_names(),
            row_ordinal=capture_row_ordinals(),
        )
        def generated_subject(
            shape: SubjectShape, threadless: bool, recipient: str, row_ordinal: int
        ) -> None:
            item = _row_variant(
                rows[row_ordinal % len(rows)],
                {module.STORE_SUBJECT_FIELD: shape.subject},
            )
            if threadless:
                item = {
                    key: value
                    for key, value in item.items()
                    if key != module.STORE_THREAD_FIELD
                }
            assert_case(module, branch, item, recipient, shape, threadless)

        return generated_subject

    for branch in SUBJECT_BRANCHES:
        run_replayable_property(
            drive(branch),
            seed_value=SUBJECT_CLASSIFICATION_SEED,
            replay_path=SUBJECT_CLASSIFICATION_REPLAY_PATH,
        )


def registration_response_named(module: ModuleType, name: str) -> CommandResultContract:
    """The captured registration response with the store-assigned name
    replaced by ``name``; every other byte of the answer stays the store's."""
    payload = store_response_payload(module, module.Operation.REGISTER)
    if not isinstance(payload, dict) or module.STORE_NAME_FIELD not in payload:
        raise CaptureError("the captured registration answered no agent name")
    return text_command_result(
        module, json.dumps({**payload, module.STORE_NAME_FIELD: name})
    )


def run_registration_cases(
    assert_case: Callable[[ModuleType, dict[str, object], str, str, str], None],
) -> None:
    """Drive generated registration requests, a name a caller might try to
    give, and a name the store assigns, under generated project keys.

    The callback receives the request, the name the caller would give, the
    name the store assigns, and the project key.
    """
    module = _load()

    @seed(REGISTRATION_SEED)
    @settings(max_examples=REGISTRATION_EXAMPLES, deadline=None, print_blob=True)
    @given(
        program=program_names(),
        model=agent_names(),
        task=st.one_of(st.none(), program_names()),
        requested=agent_names(),
        assigned=agent_names(),
        project_key=project_key_paths(),
    )
    def generated_registration(
        program: str,
        model: str,
        task: str | None,
        requested: str,
        assigned: str,
        project_key: str,
    ) -> None:
        request = cast(
            dict[str, object],
            module.operation_request(
                module.Operation.REGISTER,
                program=program,
                agent_model=model,
                task=task,
            ),
        )
        assert_case(module, request, requested, assigned, project_key)

    run_replayable_property(
        generated_registration,
        seed_value=REGISTRATION_SEED,
        replay_path=REGISTRATION_REPLAY_PATH,
    )


def run_store_error_cases(
    assert_case: Callable[
        [ModuleType, dict[str, object], str, CapturedStoreResponse], None
    ],
) -> None:
    """Drive every captured store failure through a request of the operation
    whose command failed, under generated project keys."""
    module = _load()
    cases = [
        (request, captured)
        for request in requests_over_every_operation(module)
        for captured in store_error_responses(
            module, module.Operation(request[module.OPERATION_FIELD])
        )
    ]
    if not cases:
        raise CaptureError("no captured store failure matches an operation")

    @seed(STORE_ERROR_SEED)
    @settings(max_examples=STORE_ERROR_EXAMPLES, deadline=None, print_blob=True)
    @given(project_key=project_key_paths())
    def generated_errors(project_key: str) -> None:
        for request, captured in cases:
            assert_case(module, request, project_key, captured)

    run_replayable_property(
        generated_errors,
        seed_value=STORE_ERROR_SEED,
        replay_path=STORE_ERROR_REPLAY_PATH,
    )


def run_recipient_boundary(
    assert_case: Callable[[ModuleType, dict[str, object], str], None],
) -> None:
    """Drive records whose recipient joins two generated names with the store's
    separator — the one text the store reads as several agents — under
    generated project keys."""
    module = _load()

    @seed(RECIPIENT_BOUNDARY_SEED)
    @settings(max_examples=RECIPIENT_BOUNDARY_EXAMPLES, deadline=None, print_blob=True)
    @given(
        kind=sent_record_kinds(module),
        first=agent_names(),
        second=agent_names(),
        sender=agent_names(),
        correlation=coordination_references(),
        subject=message_texts(),
        body=message_texts(),
        project_key=project_key_paths(),
    )
    def generated_case(
        kind: object,
        first: str,
        second: str,
        sender: str,
        correlation: str,
        subject: str,
        body: str,
        project_key: str,
    ) -> None:
        record = {
            module.RECORD_SCHEMA_FIELD: module.RECORD_SCHEMA_VERSION,
            module.KIND_FIELD: kind,
            module.CORRELATION_FIELD: correlation,
            module.SENDER_FIELD: sender,
            module.RECIPIENT_FIELD: (
                f"{first}{module.STORE_RECIPIENT_SEPARATOR}{second}"
            ),
            module.RECORD_SUBJECT_FIELD: subject,
            module.BODY_FIELD: body,
            module.ACK_REQUIRED_FIELD: False,
        }
        assert_case(module, record, project_key)

    run_replayable_property(
        generated_case,
        seed_value=RECIPIENT_BOUNDARY_SEED,
        replay_path=RECIPIENT_BOUNDARY_REPLAY_PATH,
    )


def run_generated_identities(
    assert_case: Callable[[ModuleType, str, str, str, str], None],
) -> None:
    """Drive generated incidental identities and keys through a linked predicate."""
    module = _load()

    @seed(COMPLIANCE_SEED)
    @settings(max_examples=COMPLIANCE_EXAMPLES, deadline=None, print_blob=True)
    @given(
        agent=agent_names(),
        program=program_names(),
        model=agent_names(),
        project_key=project_key_paths(),
    )
    def generated_case(agent: str, program: str, model: str, project_key: str) -> None:
        assert_case(module, agent, program, model, project_key)

    run_replayable_property(
        generated_case,
        seed_value=COMPLIANCE_SEED,
        replay_path=COMPLIANCE_REPLAY_PATH,
    )


def run_store_response_cases(
    assert_case: Callable[[ModuleType, str, str, int, str, str, str], None],
) -> None:
    """Drive generated store failure responses — a nonzero exit with its detail,
    malformed output, an unsupported operation name — through a linked predicate
    under generated keys."""
    module = _load()

    @seed(STORE_RESPONSE_SEED)
    @settings(max_examples=STORE_RESPONSE_EXAMPLES, deadline=None, print_blob=True)
    @given(
        agent=agent_names(),
        project_key=project_key_paths(),
        exit_code=store_exit_codes(),
        detail=message_texts(),
        malformed=message_texts(),
        unsupported=unsupported_operation_names(module),
    )
    def generated_case(
        agent: str,
        project_key: str,
        exit_code: int,
        detail: str,
        malformed: str,
        unsupported: str,
    ) -> None:
        assert_case(
            module, agent, project_key, exit_code, detail, malformed, unsupported
        )

    run_replayable_property(
        generated_case,
        seed_value=STORE_RESPONSE_SEED,
        replay_path=STORE_RESPONSE_REPLAY_PATH,
    )


def _is_timestamp(value: object) -> bool:
    if not isinstance(value, str):
        return False
    try:
        datetime.fromisoformat(value)
    except ValueError:
        return False
    return True


def registration_timestamp_fields(module: ModuleType) -> tuple[str, ...]:
    """The fields of the captured registration answer that carry a timestamp —
    among them the per-agent activity timestamp the store reports — read from
    the answer's values rather than named here."""
    payload = store_response_payload(module, module.Operation.REGISTER)
    if not isinstance(payload, dict):
        raise CaptureError("the captured registration answered no agent object")
    fields = tuple(
        sorted(name for name, value in payload.items() if _is_timestamp(value))
    )
    if not fields:
        raise CaptureError("the captured registration reports no timestamp")
    return fields


def run_activity_timestamp_cases(
    assert_case: Callable[
        [ModuleType, dict[str, object], str, CommandResultContract, dict[str, str]],
        None,
    ],
) -> None:
    """Drive the captured registration answer with every timestamp it reports
    moved to a generated moment, from long past to far future.

    The callback receives the request, the project key, the varied answer as
    the runner returns it, and the moment each timestamp field now carries.
    """
    module = _load()
    fields = registration_timestamp_fields(module)
    captured = store_response_payload(module, module.Operation.REGISTER)
    if not isinstance(captured, dict):
        raise CaptureError("the captured registration answered no agent object")

    @seed(ACTIVITY_TIMESTAMP_SEED)
    @settings(max_examples=ACTIVITY_TIMESTAMP_EXAMPLES, deadline=None, print_blob=True)
    @given(
        moments=st.lists(
            activity_moments(), min_size=len(fields), max_size=len(fields)
        ),
        program=program_names(),
        model=agent_names(),
        project_key=project_key_paths(),
    )
    def generated_case(
        moments: list[str], program: str, model: str, project_key: str
    ) -> None:
        moved = dict(zip(fields, moments, strict=True))
        request = cast(
            dict[str, object],
            module.operation_request(
                module.Operation.REGISTER, program=program, agent_model=model
            ),
        )
        varied = text_command_result(module, json.dumps({**captured, **moved}))
        assert_case(module, request, project_key, varied, moved)

    run_replayable_property(
        generated_case,
        seed_value=ACTIVITY_TIMESTAMP_SEED,
        replay_path=COMPLIANCE_REPLAY_PATH,
    )


def run_cli_in_process(
    module: ModuleType, stdin_text: str, runner: object
) -> tuple[int, str]:
    """Run the adapter's request form in process on ``stdin_text`` through
    ``runner``, returning its exit code and everything it wrote to stdout."""
    stdout = StringIO()
    exit_code = module.main(
        [module.CliOperation.RUN.value],
        stdin=StringIO(stdin_text),
        stdout=stdout,
        runner=runner,
    )
    return cast(int, exit_code), stdout.getvalue()


def run_unreadable_input_cases(
    assert_case: Callable[[ModuleType, str, str], None],
) -> None:
    """Drive every family of request input that names no request — text that
    does not parse as JSON, JSON nested past the reader's reach, JSON that is
    no object — through a linked predicate; the callback receives the family
    and the input."""
    module = _load()

    def drive(family: str) -> Callable[[], None]:
        @seed(UNREADABLE_INPUT_SEED)
        @settings(
            max_examples=UNREADABLE_INPUT_EXAMPLES, deadline=None, print_blob=True
        )
        @given(text=unreadable_request_texts(family))
        def generated_case(text: str) -> None:
            assert_case(module, family, text)

        return generated_case

    for family in UNREADABLE_INPUT_FAMILIES:
        run_replayable_property(
            drive(family),
            seed_value=UNREADABLE_INPUT_SEED,
            replay_path=COMPLIANCE_REPLAY_PATH,
        )


def run_runner_error_cases(
    assert_case: Callable[
        [ModuleType, dict[str, object], str, Exception, RaisingRunner], None
    ],
) -> None:
    """Drive a generated runner error at each program the adapter runs, for a
    request of every operation, under generated project keys.

    The callback receives the request, the program whose run raises, the
    error, and the runner: a lookup reply precedes the store's run, so an
    error at the store is reached only after the key resolves.
    """
    module = _load()
    requests = requests_over_every_operation(module)
    programs = sorted(adapter_programs(module))

    @seed(RUNNER_ERROR_SEED)
    @settings(max_examples=RUNNER_ERROR_EXAMPLES, deadline=None, print_blob=True)
    @given(error=runner_errors(), project_key=project_key_paths())
    def generated_case(error: Exception, project_key: str) -> None:
        for request in requests:
            for program in programs:
                runner = RaisingRunner(
                    program,
                    error,
                    [
                        text_command_result(
                            module, common_dir_output(COMMON_DIR_EXACT, project_key)
                        )
                    ],
                )
                assert_case(module, request, program, error, runner)

    run_replayable_property(
        generated_case,
        seed_value=RUNNER_ERROR_SEED,
        replay_path=COMPLIANCE_REPLAY_PATH,
    )


def run_nul_argument_cases(
    assert_case: Callable[[ModuleType, str, dict[str, object]], None],
) -> None:
    """Drive every registry request with each text value it carries holding a
    NUL at a generated position; the callback receives the varied value's
    location and the varied request."""
    module = _load()
    requests = operation_requests(module)

    @seed(NUL_ARGUMENT_SEED)
    @settings(max_examples=NUL_ARGUMENT_EXAMPLES, deadline=None, print_blob=True)
    @given(position=nul_positions())
    def generated_case(position: int) -> None:
        for request in requests:
            for location, varied in nul_carrying_requests(module, request, position):
                assert_case(module, location, varied)

    run_replayable_property(
        generated_case,
        seed_value=NUL_ARGUMENT_SEED,
        replay_path=COMPLIANCE_REPLAY_PATH,
    )


def argv_option_values(
    contract: UsageContract, argv: tuple[str, ...]
) -> dict[str, list[str | None]]:
    """Every option an argument vector carries, with the value each occurrence
    binds: an attached `--option=value` value, the next token for an option the
    usage declares as taking one, or none for a flag. The vector is read the
    way `read_argv` reads it; this records what it binds rather than counting."""
    values: dict[str, list[str | None]] = {}
    index = len(contract.command_path) + 1
    while index < len(argv):
        token = argv[index]
        if token.startswith("--"):
            option, attached, value = token.partition(ATTACHED_VALUE_SEPARATOR)
            if attached:
                values.setdefault(option, []).append(value)
                index += 1
            elif contract.options.get(option) and index + 1 < len(argv):
                values.setdefault(option, []).append(argv[index + 1])
                index += 2
            else:
                values.setdefault(option, []).append(None)
                index += 1
            continue
        index += 1
    return values


def _source_texts(paths: tuple[Path, ...]) -> dict[str, str]:
    return {
        str(path.relative_to(ROOT)): path.read_text(encoding="utf-8")
        for path in sorted(paths)
    }


def mail_command_source_texts() -> dict[str, str]:
    """Return shipped Python source outside the sole store-command owner."""
    script_paths = tuple(
        path
        for runtime_root in CODING_AGENTS_RUNTIME_ROOTS
        for path in runtime_root.rglob("*.py")
        if OPERATE_AGENT_MAIL_RELATIVE not in path.relative_to(runtime_root).parents
    )
    return _source_texts(script_paths)


def raw_mail_violation_source() -> tuple[str, dict[str, str]]:
    return (
        str(RAW_MAIL_VIOLATION_FIXTURE.relative_to(ROOT)),
        _source_texts((RAW_MAIL_VIOLATION_FIXTURE,)),
    )


def raw_mail_shell_violation_source() -> tuple[str, dict[str, str]]:
    return (
        str(RAW_MAIL_SHELL_VIOLATION_FIXTURE.relative_to(ROOT)),
        _source_texts((RAW_MAIL_SHELL_VIOLATION_FIXTURE,)),
    )


def git_project_key_violation_source() -> tuple[str, dict[str, str]]:
    return (
        str(GIT_PROJECT_KEY_VIOLATION_FIXTURE.relative_to(ROOT)),
        _source_texts((GIT_PROJECT_KEY_VIOLATION_FIXTURE,)),
    )


@dataclass(frozen=True)
class MailPool:
    """One real repository reached through its three checkout shapes.

    ``bare`` is the repository every shape shares, so it is the key the
    resolver must return from each of them. ``nested`` is a directory inside the
    main checkout, the shape whose repository lies strictly above its working
    directory. ``outside`` is the pool's parent directory, which is no
    repository. ``foreign`` is a second repository no shape belongs to, so a key
    that followed a caller's environment rather than its working directory would
    return it.
    """

    bare: Path
    main_checkout: Path
    linked_worktree: Path
    symlinked_worktree: Path
    nested: Path
    outside: Path
    foreign: Path

    @property
    def checkout_shapes(self) -> dict[str, Path]:
        """Every working directory that belongs to this pool, by name."""
        return {
            "bare": self.bare,
            "main-checkout": self.main_checkout,
            "linked-worktree": self.linked_worktree,
            "symlinked-worktree": self.symlinked_worktree,
            "nested-directory": self.nested,
        }


def _git_in(directory: Path, *arguments: str) -> None:
    subprocess.run(
        ["git", "-C", str(directory), *arguments],
        check=True,
        capture_output=True,
    )


@contextmanager
def mail_pool() -> Iterator[MailPool]:
    """Yield a throwaway pool: a bare repository and two worktrees attached to
    it — the main checkout and one linked worktree — under a parent directory
    that is no repository.

    The main checkout is a worktree of the bare repository, the shape a
    provisioned pool takes, rather than its own clone. A symlink to the linked
    worktree gives one checkout a second route, so a key that varied with the
    path a caller typed would differ from the key its physical route returns.
    """
    with TemporaryDirectory(ignore_cleanup_errors=True) as raw:
        outside = Path(raw).resolve()
        seed_checkout = outside / POOL_SEED_NAME
        subprocess.run(
            ["git", "init", "--quiet", "-b", POOL_DEFAULT_BRANCH, str(seed_checkout)],
            check=True,
            capture_output=True,
        )
        _git_in(seed_checkout, "config", "user.email", "test@example.invalid")
        _git_in(seed_checkout, "config", "user.name", "Spec Tree Test")
        _git_in(seed_checkout, "config", "commit.gpgsign", "false")
        (seed_checkout / "README.md").write_text("seed\n", encoding="utf-8")
        _git_in(seed_checkout, "add", "README.md")
        _git_in(seed_checkout, "commit", "--quiet", "-m", "seed")
        bare = outside / f"{POOL_REPOSITORY_NAME}.git"
        subprocess.run(
            ["git", "clone", "--quiet", "--bare", str(seed_checkout), str(bare)],
            check=True,
            capture_output=True,
        )
        main_checkout = outside / POOL_MAIN_CHECKOUT_NAME
        _git_in(
            bare, "worktree", "add", "--quiet", str(main_checkout), POOL_DEFAULT_BRANCH
        )
        linked_worktree = outside / POOL_LINKED_WORKTREE_NAME
        _git_in(bare, "worktree", "add", "--quiet", "--detach", str(linked_worktree))
        symlinked_worktree = outside / POOL_SYMLINK_NAME
        symlinked_worktree.symlink_to(linked_worktree)
        nested = main_checkout.joinpath(*POOL_NESTED_RELATIVE)
        nested.mkdir(parents=True)
        foreign = outside / f"{FOREIGN_REPOSITORY_NAME}.git"
        subprocess.run(
            ["git", "init", "--quiet", "--bare", str(foreign)],
            check=True,
            capture_output=True,
        )
        yield MailPool(
            bare=bare,
            main_checkout=main_checkout,
            linked_worktree=linked_worktree,
            symlinked_worktree=symlinked_worktree,
            nested=nested,
            outside=outside,
            foreign=foreign,
        )


def run_cli_project_key(
    working_directory: Path,
    environment: Mapping[str, str] | None = None,
) -> tuple[int, dict[str, object]]:
    """Run the shipped CLI's project-key operation in ``working_directory``.

    ``environment`` names variables to add to the inherited environment for
    this run, so the variables a caller could answer a location question from
    are carried into the process the way a hook carries them.
    """
    module = _load()
    completed = subprocess.run(
        [sys.executable, str(AGENT_MAIL_PATH), module.CliOperation.PROJECT_KEY],
        cwd=working_directory,
        capture_output=True,
        text=True,
        timeout=CLI_TIMEOUT_SECONDS,
        check=False,
        env=None if environment is None else {**os.environ, **environment},
    )
    return completed.returncode, cast(dict[str, object], json.loads(completed.stdout))


@dataclass(frozen=True)
class GitLocationProbe:
    """One variable Git's own behaviour shows moves a lookup's answer off the
    invoking working directory.

    ``environment`` is the caller's environment that produced ``outcome`` from
    ``working_directory``: ``misdirected`` when raw Git answered with another
    repository's common directory, ``unresolved`` when raw Git gave the same
    answer it gives in a directory that is no repository at all.
    """

    variable: str
    shape: str
    working_directory: Path
    environment: dict[str, str]
    outcome: str


MISDIRECTED_OUTCOME = "misdirected"
UNRESOLVED_OUTCOME = "unresolved"

# Git's own question about which repository a working directory belongs to,
# spelled here rather than read from the adapter: the adapter's argv is the
# subject under test, so a probe that borrowed it would confirm nothing the
# adapter did not already agree with.
GIT_COMMON_DIR_QUESTION = (
    "git",
    "rev-parse",
    "--path-format=absolute",
    "--git-common-dir",
)
# Git's own report of the environment variables local to a repository. It is
# the candidate space, not the answer.
GIT_LOCAL_ENV_VARS_QUESTION = ("git", "rev-parse", "--local-env-vars")
# Candidate names beyond that report: the discovery-bounding variables, which
# move the answer off the working directory by hiding the repository it belongs
# to. A variable that only widens the search
# toward the repository genuinely there is not a candidate, because it cannot
# move the answer off the working directory at all. This list only widens the
# search — a candidate joins the confirmed domain solely where Git's behaviour
# shows the answer moved, so a name that changes nothing confirms nothing.
GIT_DISCOVERY_CANDIDATES: tuple[str, ...] = ("GIT_CEILING_DIRECTORIES",)
GIT_PROBE_TIMEOUT_SECONDS = 30


def _ask_git(
    argv: tuple[str, ...], cwd: Path, extra: Mapping[str, str]
) -> tuple[int, str, str]:
    """Ask Git one question from ``cwd``, carrying only ``extra`` of `GIT_*`."""
    inherited = {
        name: value for name, value in os.environ.items() if not name.startswith("GIT_")
    }
    completed = subprocess.run(
        list(argv),
        cwd=cwd,
        env={**inherited, **extra},
        capture_output=True,
        text=True,
        timeout=GIT_PROBE_TIMEOUT_SECONDS,
        check=False,
    )
    return completed.returncode, completed.stdout.strip(), completed.stderr.strip()


def _probe_value_pairs(
    working_directory: Path, pool: MailPool
) -> list[tuple[str, str]]:
    """Redirecting values paired with an inert control of the same shape.

    A candidate is confirmed only where the first value redirects Git and the
    second leaves its answer untouched, so a variable that rejects any value of
    this shape — a count, a config specification — fails the control and stays
    out of the domain.
    """
    return [
        (str(pool.foreign), str(pool.bare)),
        (str(working_directory.parent), str(pool.foreign)),
        ("0", "1"),
        ("1", "0"),
    ]


def git_location_variables(pool: MailPool) -> list[GitLocationProbe]:
    """The variables Git itself confirms move a lookup's answer off the invoking
    working directory, with the case confirming each.

    The candidate space is Git's own `rev-parse --local-env-vars` report widened
    by `GIT_DISCOVERY_CANDIDATES`; the oracle is Git's behaviour in ``pool``. A
    candidate is confirmed where one value makes raw Git answer with another
    repository, or gives the answer Git gives where no repository exists, while
    an inert value of the same shape leaves the answer unchanged. A variable
    that only widens discovery toward the repository genuinely there confirms
    under neither outcome, which is why the claim leaves it out of the class.
    """
    reported = _ask_git(GIT_LOCAL_ENV_VARS_QUESTION, pool.main_checkout, {})
    if reported[0] != 0 or not reported[1].split():
        raise CaptureError(f"Git reports no repository-local variables: {reported}")
    candidates = list(dict.fromkeys([*reported[1].split(), *GIT_DISCOVERY_CANDIDATES]))

    unresolved = _ask_git(GIT_COMMON_DIR_QUESTION, pool.outside, {})
    if unresolved[0] == 0:
        raise CaptureError(
            f"The pool's parent directory resolves a repository: {unresolved}"
        )
    shapes = pool.checkout_shapes
    baselines = {
        name: _ask_git(GIT_COMMON_DIR_QUESTION, directory, {})
        for name, directory in shapes.items()
    }
    for name, answer in baselines.items():
        if answer[0] != 0 or answer[1] != str(pool.bare):
            raise CaptureError(f"Shape {name} does not resolve the pool: {answer}")

    confirmed: list[GitLocationProbe] = []
    for variable in candidates:
        probe = _confirm_variable(variable, pool, shapes, baselines, unresolved)
        if probe is not None:
            confirmed.append(probe)
    outcomes = {probe.outcome for probe in confirmed}
    if outcomes != {MISDIRECTED_OUTCOME, UNRESOLVED_OUTCOME}:
        raise CaptureError(
            "Git confirms no variable of each redirection class; "
            f"the probe found {sorted(outcomes)} over {sorted(p.variable for p in confirmed)}"
        )
    return confirmed


def _confirm_variable(
    variable: str,
    pool: MailPool,
    shapes: Mapping[str, Path],
    baselines: Mapping[str, tuple[int, str, str]],
    unresolved: tuple[int, str, str],
) -> GitLocationProbe | None:
    for shape, directory in shapes.items():
        baseline = baselines[shape]
        for redirecting, inert in _probe_value_pairs(directory, pool):
            environment = {variable: redirecting}
            answer = _ask_git(GIT_COMMON_DIR_QUESTION, directory, environment)
            if answer == baseline:
                continue
            if answer[0] == 0 and answer[1] != baseline[1]:
                outcome = MISDIRECTED_OUTCOME
            elif answer == unresolved:
                outcome = UNRESOLVED_OUTCOME
            else:
                continue
            if (
                _ask_git(GIT_COMMON_DIR_QUESTION, directory, {variable: inert})
                != baseline
            ):
                continue
            return GitLocationProbe(
                variable=variable,
                shape=shape,
                working_directory=directory,
                environment=environment,
                outcome=outcome,
            )
    return None


def requests_over_every_operation(module: ModuleType) -> list[dict[str, object]]:
    """Exactly one request per source-owned operation.

    A rule quantified over operations is read against every member, so a
    program or fallback reached only from one operation's path still falsifies
    it. Record kind is no dimension of those rules, so the send request is one
    record rather than one per kind: the operation enumeration is what the
    rules range over, and repeating a launch per kind buys no falsification.
    """
    operations = {operation.value for operation in module.Operation}
    chosen: dict[str, dict[str, object]] = {}
    for request in operation_requests(module):
        name = cast(str, request[module.OPERATION_FIELD])
        if name not in chosen and _minimal_request(module, request):
            chosen[name] = request
    if set(chosen) != operations:
        raise CaptureError(
            f"The generated requests cover {sorted(chosen)}, not every operation"
        )
    return [chosen[name] for name in sorted(chosen)]


def _minimal_request(module: ModuleType, request: dict[str, object]) -> bool:
    """Whether the request carries only its operation's required fields."""
    operation = module.Operation(request[module.OPERATION_FIELD])
    arguments = cast(dict[str, object], request[module.ARGUMENTS_FIELD])
    return any(
        set(arguments) == set(shape.required_fields)
        for shape in module.OPERATION_CONTRACTS[operation].request_shapes
    )


def adapter_programs(module: ModuleType) -> frozenset[str]:
    """The external programs the adapter's own command vectors name."""
    return frozenset(
        {prefix[0] for prefix in module.PUBLIC_AM_COMMAND_PREFIXES.values()}
        | {module.PUBLIC_GIT_COMMON_DIR_COMMAND[0]}
    )


def run_cli_with_only_adapter_programs(
    request: dict[str, object], *, project_key: str, store_response: str
) -> CommandResultContract:
    """Run the shipped CLI where only the adapter's own programs resolve.

    Every program the adapter names gets a stub on an otherwise empty ``PATH``:
    the repository lookup prints ``project_key`` and the store prints
    ``store_response``. An operation that reached any other program would find
    it absent and could not succeed.
    """
    module = _load()
    programs = adapter_programs(module)
    replies = {
        module.PUBLIC_GIT_COMMON_DIR_COMMAND[0]: project_key,
        module.AM_COMMAND: store_response,
    }
    missing = sorted(programs - set(replies))
    if missing:
        raise CaptureError(
            f"The adapter names programs this probe stubs no reply for: {missing}"
        )
    with TemporaryDirectory() as raw:
        stub_path = Path(raw)
        for program in sorted(programs):
            stub = stub_path / program
            stub.write_text(
                f"#!/bin/sh\nprintf '%s' {shlex.quote(replies[program])}\n",
                encoding="utf-8",
            )
            stub.chmod(0o755)
        completed = subprocess.run(
            [sys.executable, str(AGENT_MAIL_PATH), module.CliOperation.RUN],
            input=json.dumps(request),
            env={"PATH": str(stub_path)},
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=CLI_TIMEOUT_SECONDS,
            check=False,
        )
    return cast(
        CommandResultContract,
        module.CommandResult(completed.returncode, completed.stdout, completed.stderr),
    )


def store_program_names(module: ModuleType) -> frozenset[str]:
    """The program name every captured usage line opens with.

    The store declares its own program in the first token of each usage line,
    which the usage-contract reader discards. Reading it here gives the
    adapter's store constant an oracle outside the source it is checked
    against, so renaming that constant to another program fails the read.
    """
    names: set[str] = set()
    for operation in module.Operation:
        capture = _usage_capture(module, operation)
        for line in capture.stdout.splitlines():
            stripped = line.strip()
            if stripped.startswith(USAGE_PREFIX):
                tokens = stripped[len(USAGE_PREFIX) :].split()
                if not tokens:
                    raise CaptureError(f"{capture.path} usage line names no program")
                names.add(tokens[0])
                break
        else:
            raise CaptureError(f"{capture.path} carries no usage line")
    return frozenset(names)


def _option_descriptions(usage_text: str) -> dict[str, str]:
    """Each option of a usage text's options section with its whole description.

    An entry opens on the line naming the option and runs to the next such
    line, so a description the store prints beneath its option belongs to it
    as fully as one printed beside it.
    """
    entries: dict[str, list[str]] = {}
    current: list[str] | None = None
    in_options = False
    for line in usage_text.splitlines():
        stripped = line.strip()
        if stripped == OPTIONS_HEADING:
            in_options = True
            continue
        if not in_options:
            continue
        if stripped and not line.startswith((" ", "\t")):
            break
        head = OPTION_ENTRY_HEAD.match(line)
        if head is not None and stripped.startswith("-"):
            current = entries.setdefault(head.group("long"), [])
            current.append(head.group("rest"))
        elif current is not None:
            current.append(line)
    return {option: " ".join(lines) for option, lines in entries.items()}


def store_project_fallback_variable(module: ModuleType) -> str:
    """The environment variable the store CLI falls back to for its project.

    The adapter never reads it; the compliance probe sets it as the fallback
    the adapter must ignore.

    Read from the captured usage of every operation's command, where the store
    describes its project option, so the probe's fallback is the store's own
    statement in the observation that carries its tool and version rather than
    a token restated beside the adapter. Exactly one name must be declared
    across those descriptions; a capture whose wording drifts fails the read.
    """
    names: set[str] = set()
    for operation in module.Operation:
        capture = _usage_capture(module, operation)
        description = _option_descriptions(capture.stdout).get(module.PROJECT_OPTION)
        if description is not None:
            names.update(ENVIRONMENT_NAME_PATTERN.findall(description))
    if len(names) != 1:
        raise CaptureError(
            f"the captured usage declares {sorted(names)} as project fallback "
            f"variables for {module.PROJECT_OPTION}; one is required"
        )
    return names.pop()


def run_cli_without_executables(
    request: dict[str, object], *, fallback_project: str
) -> CommandResultContract:
    """Run the shipped CLI where no executable resolves and a fallback is offered."""
    module = _load()
    with TemporaryDirectory() as empty_path:
        completed = subprocess.run(
            [sys.executable, str(AGENT_MAIL_PATH), module.CliOperation.RUN],
            input=json.dumps(request),
            env={
                "PATH": empty_path,
                store_project_fallback_variable(module): fallback_project,
            },
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=CLI_TIMEOUT_SECONDS,
            check=False,
        )
    return cast(
        CommandResultContract,
        module.CommandResult(completed.returncode, completed.stdout, completed.stderr),
    )
