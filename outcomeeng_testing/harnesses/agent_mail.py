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
from pathlib import Path
from tempfile import TemporaryDirectory
from types import ModuleType
from typing import Protocol, cast

from hypothesis import given, seed, settings

from outcomeeng_testing.generators.agent_mail import (
    COMMON_DIR_EXACT,
    COMMON_DIR_SHAPES,
    agent_names,
    common_dir_output,
    capture_row_ordinals,
    coordination_references,
    expected_project_key,
    message_records,
    message_texts,
    operation_requests,
    program_names,
    project_key_paths,
    sent_record_kinds,
    store_exit_codes,
    store_message_ids,
    terminal_record_kinds,
    unsupported_operation_names,
)
from outcomeeng_testing.harnesses.cli_usage import (
    UsageContract,
    usage_contract_from_path,
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
# Captured `am <command> --help` texts: the store CLI's own grammar declaration.
USAGE_FIXTURE_ROOT = FIXTURE_ROOT / "usage"
# Captured `am` responses for each operation's public command. The project key
# has no captured oracle: the checkout shapes a real repository takes are what
# the resolver is read against.
RESPONSE_FIXTURE_ROOT = FIXTURE_ROOT / "responses"
RAW_MAIL_VIOLATION_FIXTURE = FIXTURE_ROOT / "raw_am_command.py.txt"
GIT_PROJECT_KEY_VIOLATION_FIXTURE = FIXTURE_ROOT / "git_project_key.py.txt"
RECORD_ROUNDTRIP_SEED = 2026091801
RECORD_ROUNDTRIP_EXAMPLES = 60
RECORD_ROUNDTRIP_REPLAY_PATH = (
    "spx/43-coding-agents.enabler/18-agent-mail.enabler/tests/"
    "test_agent_mail.property.l1.py"
)
DELEGATION_CHAIN_SEED = 2026092201
DELEGATION_CHAIN_EXAMPLES = 20
TERMINAL_PROPERTY_SEED = 2026091802
TERMINAL_PROPERTY_EXAMPLES = 40
TERMINAL_PROPERTY_REPLAY_PATH = RECORD_ROUNDTRIP_REPLAY_PATH
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
INBOX_ROW_SEED = 2026091807
INBOX_ROW_EXAMPLES = 10
INBOX_ROW_REPLAY_PATH = PROJECT_KEY_MAPPING_REPLAY_PATH
RECIPIENT_BOUNDARY_SEED = 2026091808
RECIPIENT_BOUNDARY_EXAMPLES = 20
RECIPIENT_BOUNDARY_REPLAY_PATH = PROJECT_KEY_MAPPING_REPLAY_PATH
COMPLIANCE_REPLAY_PATH = (
    "spx/43-coding-agents.enabler/18-agent-mail.enabler/tests/"
    "test_agent_mail.compliance.l1.py"
)
# The token a captured usage line opens with, before the program name.
USAGE_LINE_PREFIX = "Usage:"
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
class CapturedInboxRow:
    """One row of a captured `am robot inbox` response, with the capture's path."""

    capture: str
    item: dict[str, object]


@dataclass(frozen=True)
class CapturedInboxResponse:
    """One captured inbox response, or a named variant of one, replayable by path."""

    capture: str
    result: CommandResultContract
    payload: dict[str, object]


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


def _command_fixture_name(module: ModuleType, operation: object) -> str:
    prefix = module.PUBLIC_AM_COMMAND_PREFIXES[operation]
    return "-".join(prefix[1:])


def usage_contract_for(module: ModuleType, operation: object) -> UsageContract:
    """The store CLI's captured usage declaration for one operation's command."""
    return usage_contract_from_path(
        USAGE_FIXTURE_ROOT / f"{_command_fixture_name(module, operation)}.txt"
    )


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
    suffix = "json" if operation in module.JSON_OPERATIONS else "txt"
    return (
        RESPONSE_FIXTURE_ROOT / f"{name}{_shaping_suffix(module, arguments)}.{suffix}"
    )


def _result_from_path(module: ModuleType, path: Path) -> CommandResultContract:
    return cast(
        CommandResultContract,
        module.CommandResult(0, path.read_text(encoding="utf-8"), ""),
    )


def store_response_result(
    module: ModuleType,
    operation: object,
    arguments: dict[str, object] | None = None,
) -> CommandResultContract:
    """The store's captured response for one operation's request shape, by path:
    the capture taken under the same response-shaping options the request
    carries."""
    return _result_from_path(
        module, _response_fixture_path(module, operation, arguments)
    )


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


def _inbox_captures_with_bodies(module: ModuleType) -> list[Path]:
    """Every captured inbox response taken with `--include-bodies`, in path
    order: the store answered the same command while a receipt was pending and
    again after it was recorded."""
    base = _response_fixture_path(
        module, module.Operation.INBOX, {module.INCLUDE_BODIES_FIELD: True}
    )
    return sorted(RESPONSE_FIXTURE_ROOT.glob(f"{base.stem}*.json"))


def captured_inbox_responses_with_bodies(
    module: ModuleType,
) -> list[CapturedInboxResponse]:
    """Each captured `--include-bodies` inbox response, replayable by path."""
    return [
        CapturedInboxResponse(
            str(path.relative_to(ROOT)),
            _result_from_path(module, path),
            json.loads(path.read_text(encoding="utf-8")),
        )
        for path in _inbox_captures_with_bodies(module)
    ]


def captured_inbox_rows_with_bodies(module: ModuleType) -> list[CapturedInboxRow]:
    """Every row across the captured `--include-bodies` inbox responses."""
    return [
        CapturedInboxRow(response.capture, cast(dict[str, object], item))
        for response in captured_inbox_responses_with_bodies(module)
        for item in cast(list[object], response.payload[module.STORE_INBOX_FIELD])
    ]


def _row_variant(
    row: CapturedInboxRow, changes: dict[str, object]
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


def inbox_response_without_thread(
    module: ModuleType, response: CapturedInboxResponse
) -> CapturedInboxResponse:
    """The captured inbox response with the thread removed from its first row:
    the variant ranges over the thread value alone, and names the capture it
    varies."""
    items = cast(list[dict[str, object]], response.payload[module.STORE_INBOX_FIELD])
    if not items:
        raise CaptureError(f"{response.capture} lists no inbox row to vary")
    first = CapturedInboxRow(response.capture, items[0])
    if module.STORE_THREAD_FIELD not in first.item:
        raise CaptureError(f"{response.capture} carries no thread on its first row")
    varied = {
        key: value
        for key, value in first.item.items()
        if key != module.STORE_THREAD_FIELD
    }
    payload = {**response.payload, module.STORE_INBOX_FIELD: [varied, *items[1:]]}
    return CapturedInboxResponse(
        f"{response.capture} (first row without {module.STORE_THREAD_FIELD})",
        cast(CommandResultContract, module.CommandResult(0, json.dumps(payload), "")),
        payload,
    )


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


def store_inbox_echo(
    module: ModuleType,
    send_fields: dict[str, object],
    message_id: int,
    row_ordinal: int,
) -> dict[str, object]:
    """Render a sent message the way the store's inbox surface returned one of
    the same acknowledgement class.

    The row is a captured `--include-bodies` inbox row whose acknowledgement
    status matches the send's requirement — `row_ordinal` selects among the
    matching rows, so a required acknowledgement is echoed both pending and
    recorded — with the sender, subject, thread, body, and id the send wrote
    and the store assigned in place of the captured values. The status, the
    body field, and every other key stay the store's own bytes.
    """
    ack_required = send_fields[module.STORE_ACK_REQUIRED_FIELD] is True
    rows = [
        row
        for row in captured_inbox_rows_with_bodies(module)
        if (
            row.item.get(module.STORE_ACK_STATUS_FIELD)
            in module.STORE_ACK_REQUIRED_STATUSES
        )
        is ack_required
    ]
    if not rows:
        raise CaptureError(
            "no captured inbox row with bodies shows a message whose "
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
    assert_roundtrip: Callable[[ModuleType, dict[str, object], int, int], None],
) -> None:
    """Drive generated records while the linked test owns the round-trip predicate."""
    module = _load()

    @seed(RECORD_ROUNDTRIP_SEED)
    @settings(max_examples=RECORD_ROUNDTRIP_EXAMPLES, deadline=None, print_blob=True)
    @given(
        record=message_records(module),
        message_id=store_message_ids(),
        row_ordinal=capture_row_ordinals(),
    )
    def generated_roundtrip(
        record: dict[str, object], message_id: int, row_ordinal: int
    ) -> None:
        assert_roundtrip(module, record, message_id, row_ordinal)

    run_replayable_property(
        generated_roundtrip,
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
        reference=coordination_references(),
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


def run_terminal_property(
    assert_terminal: Callable[[ModuleType, str, object, object, dict[str, str]], None],
) -> None:
    """Drive generated terminal handbacks while the linked test owns the predicate."""
    module = _load()

    @seed(TERMINAL_PROPERTY_SEED)
    @settings(max_examples=TERMINAL_PROPERTY_EXAMPLES, deadline=None, print_blob=True)
    @given(
        reference=coordination_references(),
        first_kind=terminal_record_kinds(module),
        second_kind=terminal_record_kinds(module),
        sender=agent_names(),
        recipient=agent_names(),
        subject=message_texts(),
        body=message_texts(),
    )
    def generated_terminal(
        reference: str,
        first_kind: object,
        second_kind: object,
        sender: str,
        recipient: str,
        subject: str,
        body: str,
    ) -> None:
        content = {
            module.SENDER_FIELD: sender,
            module.RECIPIENT_FIELD: recipient,
            module.RECORD_SUBJECT_FIELD: subject,
            module.BODY_FIELD: body,
        }
        assert_terminal(module, reference, first_kind, second_kind, content)

    run_replayable_property(
        generated_terminal,
        seed_value=TERMINAL_PROPERTY_SEED,
        replay_path=TERMINAL_PROPERTY_REPLAY_PATH,
    )


def run_project_key_mapping(
    assert_key: Callable[[ModuleType, str, object, str | None, str], None],
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


def inbox_request_with_bodies(module: ModuleType) -> dict[str, object]:
    """The first registry inbox request that asks the store for bodies."""
    for request in operation_requests(module):
        arguments = cast(dict[str, object], request[module.ARGUMENTS_FIELD])
        if (
            module.Operation(request[module.OPERATION_FIELD]) is module.Operation.INBOX
            and arguments.get(module.INCLUDE_BODIES_FIELD) is True
        ):
            return request
    raise CaptureError("the registry declares no inbox request with bodies")


def run_inbox_row_mapping(
    assert_rows: Callable[
        [ModuleType, dict[str, object], str, CapturedInboxResponse], None
    ],
) -> None:
    """Drive every captured `--include-bodies` inbox response, and the variant
    of each without a thread on its first row, through the inbox request under
    generated project keys."""
    module = _load()
    request = inbox_request_with_bodies(module)
    responses: list[CapturedInboxResponse] = []
    for captured in captured_inbox_responses_with_bodies(module):
        responses.append(captured)
        responses.append(inbox_response_without_thread(module, captured))
    if not responses:
        raise CaptureError("no captured inbox response with bodies exists")

    @seed(INBOX_ROW_SEED)
    @settings(max_examples=INBOX_ROW_EXAMPLES, deadline=None, print_blob=True)
    @given(project_key=project_key_paths())
    def generated_rows(project_key: str) -> None:
        for response in responses:
            assert_rows(module, request, project_key, response)

    run_replayable_property(
        generated_rows,
        seed_value=INBOX_ROW_SEED,
        replay_path=INBOX_ROW_REPLAY_PATH,
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
        capture = USAGE_FIXTURE_ROOT / f"{_command_fixture_name(module, operation)}.txt"
        for line in capture.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped.startswith(USAGE_LINE_PREFIX):
                tokens = stripped[len(USAGE_LINE_PREFIX) :].split()
                if not tokens:
                    raise CaptureError(f"{capture} usage line names no program")
                names.add(tokens[0])
                break
        else:
            raise CaptureError(f"{capture} carries no usage line")
    return frozenset(names)


def store_project_fallback_variable(module: ModuleType) -> str:
    """The environment variable the store CLI falls back to for its project.

    The adapter never reads it; the compliance probe sets it as the fallback
    the adapter must ignore.

    Read from the captured usage text that declares it, so the probe's fallback
    is the store's own statement rather than a token restated beside the
    adapter, and a capture whose wording drifts fails the read.
    """
    capture = USAGE_FIXTURE_ROOT / (
        f"{_command_fixture_name(module, module.Operation.INBOX)}.txt"
    )
    names = {
        match.group(1)
        for line in capture.read_text(encoding="utf-8").splitlines()
        if line.lstrip().startswith(module.PROJECT_OPTION)
        for match in [re.search(r"\b([A-Z][A-Z0-9]*(?:_[A-Z0-9]+)+)\b", line)]
        if match
    }
    if len(names) != 1:
        raise CaptureError(
            f"{capture} declares {len(names)} project fallback variables for "
            f"{module.PROJECT_OPTION}; one is required"
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
