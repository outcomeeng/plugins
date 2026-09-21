"""Test infrastructure for the shipped agent-mail adapter."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from tempfile import TemporaryDirectory
from types import ModuleType
from typing import Protocol, cast

from hypothesis import given, seed, settings

from outcomeeng_testing.generators.agent_mail import (
    DIAGNOSIS_CHECKS_NOT_ARRAY,
    DIAGNOSIS_EMPTY_READINGS,
    DIAGNOSIS_NO_CHECKS,
    DIAGNOSIS_NO_RECORD,
    DIAGNOSIS_NOT_OBJECT,
    DIAGNOSIS_OTHER_RECORD,
    DIAGNOSIS_RELATIVE_PATH,
    DIAGNOSIS_SHAPES,
    DIAGNOSIS_TWO_RECORDS,
    DIAGNOSIS_WITH_PATH,
    agent_names,
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
# Captured `am` responses for each operation's public command, and the
# captured `spx diagnose --format json` response the adapter reads the project
# key from (taken with `@outcomeeng/spx` 0.7.1; the `worktree-pool` record
# introduced in 0.7.0 carries the same readings).
RESPONSE_FIXTURE_ROOT = FIXTURE_ROOT / "responses"
DIAGNOSIS_FIXTURE = RESPONSE_FIXTURE_ROOT / "spx-diagnose.json"
RAW_MAIL_VIOLATION_FIXTURE = FIXTURE_ROOT / "raw_am_command.py.txt"
GIT_PROJECT_KEY_VIOLATION_FIXTURE = FIXTURE_ROOT / "git_project_key.py.txt"
RECORD_ROUNDTRIP_SEED = 2026091801
RECORD_ROUNDTRIP_EXAMPLES = 60
RECORD_ROUNDTRIP_REPLAY_PATH = (
    "spx/43-coding-agents.enabler/18-agent-mail.enabler/tests/"
    "test_agent_mail.property.l1.py"
)
TERMINAL_PROPERTY_SEED = 2026091802
TERMINAL_PROPERTY_EXAMPLES = 40
TERMINAL_PROPERTY_REPLAY_PATH = RECORD_ROUNDTRIP_REPLAY_PATH
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
# The store CLI's own project fallback; the adapter never reads it, and the
# compliance probe sets it as the fallback the adapter must ignore.
STORE_PROJECT_ENV = "AGENT_MAIL_PROJECT"
CLI_TIMEOUT_SECONDS = 60


class CommandResultContract(Protocol):
    returncode: int
    stdout: str
    stderr: str


class CaptureError(RuntimeError):
    """The captured store responses do not carry what a replay or variant needs."""


@dataclass(frozen=True)
class CapturedInboxRow:
    """One row of a captured `am mail inbox` response, with the capture's path."""

    capture: str
    item: dict[str, object]


@dataclass(frozen=True)
class CapturedInboxResponse:
    """One captured inbox response, or a named variant of one, replayable by path."""

    capture: str
    result: CommandResultContract
    payload: list[dict[str, object]]


@dataclass
class RecordingRunner:
    """Interaction-protocol collaborator: records every argv, replays results."""

    results: list[CommandResultContract]
    calls: list[tuple[tuple[str, ...], str | None]] = field(default_factory=list)

    def run(
        self, argv: tuple[str, ...], stdin: str | None = None
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
        self, argv: tuple[str, ...], stdin: str | None = None
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


def json_command_result(module: ModuleType, payload: object) -> CommandResultContract:
    """Return one controlled JSON response from a public command boundary."""
    return cast(CommandResultContract, module.CommandResult(0, json.dumps(payload), ""))


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


def _inbox_captures_with_bodies(module: ModuleType) -> list[Path]:
    """Every captured inbox listing taken with `--include-bodies`, in path order."""
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
            cast(
                list[dict[str, object]],
                json.loads(path.read_text(encoding="utf-8")),
            ),
        )
        for path in _inbox_captures_with_bodies(module)
    ]


def captured_inbox_rows_with_bodies(module: ModuleType) -> list[CapturedInboxRow]:
    """Every row across the captured `--include-bodies` inbox responses."""
    return [
        CapturedInboxRow(response.capture, cast(dict[str, object], item))
        for response in captured_inbox_responses_with_bodies(module)
        for item in response.payload
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
    items = response.payload
    if not items:
        raise CaptureError(f"{response.capture} lists no inbox row to vary")
    first = CapturedInboxRow(response.capture, items[0])
    if module.STORE_THREAD_ID_FIELD not in first.item:
        raise CaptureError(f"{response.capture} carries no thread on its first row")
    varied = {
        key: value
        for key, value in first.item.items()
        if key != module.STORE_THREAD_ID_FIELD
    }
    payload = [varied, *items[1:]]
    return CapturedInboxResponse(
        f"{response.capture} (first row without {module.STORE_THREAD_ID_FIELD})",
        cast(CommandResultContract, module.CommandResult(0, json.dumps(payload), "")),
        payload,
    )


def captured_diagnosis(module: ModuleType) -> dict[str, object]:
    """The captured `spx diagnose --format json` response, decoded."""
    payload = json.loads(DIAGNOSIS_FIXTURE.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise CaptureError(f"{DIAGNOSIS_FIXTURE} is not a JSON object")
    return cast(dict[str, object], payload)


def _captured_pool_record(
    module: ModuleType, payload: dict[str, object]
) -> tuple[list[dict[str, object]], dict[str, object]]:
    """The captured check list and its one worktree-pool record. A capture
    without the keys the adapter reads is a capture gap, never a passing case."""
    checks = payload.get(module.CHECKS_FIELD)
    if not isinstance(checks, list):
        raise CaptureError(
            f"{DIAGNOSIS_FIXTURE} carries no {module.CHECKS_FIELD} array"
        )
    records = [
        cast(dict[str, object], record)
        for record in cast(list[object], checks)
        if isinstance(record, dict)
        and record.get(module.NAME_FIELD) == module.WORKTREE_POOL_CHECK
    ]
    if len(records) != 1:
        raise CaptureError(
            f"{DIAGNOSIS_FIXTURE} carries {len(records)} {module.WORKTREE_POOL_CHECK} "
            "records"
        )
    readings = records[0].get(module.READINGS_FIELD)
    if not isinstance(readings, dict) or module.MAIN_CHECKOUT_PATH_FIELD not in cast(
        dict[str, object], readings
    ):
        raise CaptureError(
            f"{DIAGNOSIS_FIXTURE} {module.WORKTREE_POOL_CHECK} record carries no "
            f"{module.READINGS_FIELD}.{module.MAIN_CHECKOUT_PATH_FIELD}"
        )
    return [cast(dict[str, object], check) for check in checks], records[0]


def diagnosis_variant(module: ModuleType, shape: str, path: str) -> object:
    """One diagnosis payload of the named shape: the captured response with the
    generated path in place of the machine's, varied only in what the shape
    names. Every key comes from the capture."""
    payload = captured_diagnosis(module)
    checks, record = _captured_pool_record(module, payload)
    readings = cast(dict[str, object], record[module.READINGS_FIELD])
    with_path = {
        **record,
        module.READINGS_FIELD: {**readings, module.MAIN_CHECKOUT_PATH_FIELD: path},
    }
    others = [check for check in checks if check is not record]
    if shape == DIAGNOSIS_WITH_PATH:
        return {**payload, module.CHECKS_FIELD: [*others, with_path]}
    if shape == DIAGNOSIS_NO_RECORD:
        return {**payload, module.CHECKS_FIELD: others}
    if shape == DIAGNOSIS_OTHER_RECORD:
        renamed = {**with_path, module.NAME_FIELD: f"other-{path.strip('/')}"}
        return {**payload, module.CHECKS_FIELD: [*others, renamed]}
    if shape == DIAGNOSIS_TWO_RECORDS:
        return {**payload, module.CHECKS_FIELD: [*others, with_path, with_path]}
    if shape == DIAGNOSIS_EMPTY_READINGS:
        emptied = {**record, module.READINGS_FIELD: {}}
        return {**payload, module.CHECKS_FIELD: [*others, emptied]}
    if shape == DIAGNOSIS_RELATIVE_PATH:
        relative = {
            **record,
            module.READINGS_FIELD: {
                **readings,
                module.MAIN_CHECKOUT_PATH_FIELD: path.lstrip("/"),
            },
        }
        return {**payload, module.CHECKS_FIELD: [*others, relative]}
    if shape == DIAGNOSIS_NOT_OBJECT:
        return [*others, with_path]
    if shape == DIAGNOSIS_NO_CHECKS:
        return {
            key: value for key, value in payload.items() if key != module.CHECKS_FIELD
        }
    if shape == DIAGNOSIS_CHECKS_NOT_ARRAY:
        return {**payload, module.CHECKS_FIELD: with_path}
    raise CaptureError(f"No diagnosis shape named {shape!r}")


def diagnosis_with_main_checkout(module: ModuleType, main_checkout_path: str) -> object:
    return diagnosis_variant(module, DIAGNOSIS_WITH_PATH, main_checkout_path)


def diagnosis_seeded_runner(
    module: ModuleType, project_key: str, *results: CommandResultContract
) -> RecordingRunner:
    """A recording runner whose first reply is the diagnosis resolving
    `project_key`, followed by the store replies in order."""
    return RecordingRunner(
        [
            json_command_result(
                module, diagnosis_with_main_checkout(module, project_key)
            ),
            *results,
        ]
    )


def diagnosis_seeded_absent_store_runner(
    module: ModuleType, project_key: str
) -> AbsentExecutableRunner:
    """A runner that resolves `project_key` from the diagnosis and then finds
    no store executable."""
    return AbsentExecutableRunner(
        module.AM_COMMAND,
        [
            json_command_result(
                module, diagnosis_with_main_checkout(module, project_key)
            )
        ],
    )


def store_inbox_echo(
    module: ModuleType,
    send_fields: dict[str, object],
    message_id: int,
    row_ordinal: int,
) -> dict[str, object]:
    """Render a sent message the way the store's inbox surface returned one of
    the same acknowledgement class.

    The row is a captured `--include-bodies` inbox row. `row_ordinal` selects
    one row, and the sender, subject, thread, body, acknowledgement requirement,
    and id are replaced with the values the send wrote and the store assigned.
    Every other key stays the store's own bytes.
    """
    rows = captured_inbox_rows_with_bodies(module)
    if not rows:
        raise CaptureError("no captured inbox row with bodies shows the response shape")
    return _row_variant(
        rows[row_ordinal % len(rows)],
        {
            module.STORE_ID_FIELD: message_id,
            module.STORE_FROM_FIELD: send_fields[module.STORE_FROM_FIELD],
            module.STORE_SUBJECT_FIELD: send_fields[module.STORE_SUBJECT_FIELD],
            module.STORE_THREAD_ID_FIELD: send_fields[module.STORE_THREAD_ID_FIELD],
            module.STORE_BODY_FIELD: send_fields[module.STORE_BODY_FIELD],
            module.STORE_ACK_REQUIRED_FIELD: send_fields[
                module.STORE_ACK_REQUIRED_FIELD
            ],
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
    """Drive every diagnosis shape as a variant of the captured response, with
    generated paths inside each."""
    module = _load()

    def drive(shape: str) -> Callable[[], None]:
        @seed(PROJECT_KEY_MAPPING_SEED)
        @settings(
            max_examples=PROJECT_KEY_MAPPING_EXAMPLES, deadline=None, print_blob=True
        )
        @given(path=project_key_paths(), agent=agent_names())
        def generated_key_mapping(path: str, agent: str) -> None:
            payload = diagnosis_variant(module, shape, path)
            assert_key(module, shape, payload, expected_project_key(shape, path), agent)

        return generated_key_mapping

    for shape in DIAGNOSIS_SHAPES:
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


def agent_mail_source_texts() -> dict[str, str]:
    """Return the authoritative adapter source observation."""
    return _source_texts((AGENT_MAIL_PATH,))


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


def run_cli_without_executables(
    request: dict[str, object], *, fallback_project: str
) -> CommandResultContract:
    """Run the shipped CLI where no executable resolves and a fallback is offered."""
    module = _load()
    with TemporaryDirectory() as empty_path:
        completed = subprocess.run(
            [sys.executable, str(AGENT_MAIL_PATH), module.CliOperation.RUN],
            input=json.dumps(request),
            env={"PATH": empty_path, STORE_PROJECT_ENV: fallback_project},
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
