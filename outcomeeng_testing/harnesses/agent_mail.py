"""Test infrastructure for the shipped agent-mail adapter."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from tempfile import TemporaryDirectory
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from types import ModuleType
from typing import Protocol, cast

from hypothesis import given, seed, settings

from outcomeeng_testing.generators.agent_mail import (
    coordination_references,
    diagnosis_payloads,
    message_records,
    store_message_ids,
    terminal_record_kinds,
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
RAW_MAIL_VIOLATION_FIXTURE = (
    ROOT / "outcomeeng_testing/fixtures/agent_mail/raw_am_command.py.txt"
)
GIT_PROJECT_KEY_VIOLATION_FIXTURE = (
    ROOT / "outcomeeng_testing/fixtures/agent_mail/git_project_key.py.txt"
)
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
PROJECT_KEY_MAPPING_EXAMPLES = 40
PROJECT_KEY_MAPPING_REPLAY_PATH = (
    "spx/43-coding-agents.enabler/18-agent-mail.enabler/tests/"
    "test_agent_mail.mapping.l1.py"
)
# The store renders a delivered message on the inbox surface with these names;
# the echo below is the contract probe for that rendering (am 0.3.24).
STORE_ACK_STATUS_PENDING = "pending"
# The store CLI's own project fallback; the adapter never reads it.
STORE_PROJECT_ENV = "AGENT_MAIL_PROJECT"
CLI_TIMEOUT_SECONDS = 60


class CommandResultContract(Protocol):
    returncode: int
    stdout: str
    stderr: str


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


def diagnosis_with_main_checkout(
    module: ModuleType, main_checkout_path: str
) -> dict[str, object]:
    return {
        module.CHECKS_FIELD: [
            {
                module.NAME_FIELD: module.WORKTREE_POOL_CHECK,
                module.READINGS_FIELD: {
                    module.MAIN_CHECKOUT_PATH_FIELD: main_checkout_path
                },
            }
        ]
    }


def store_inbox_echo(
    module: ModuleType, send_fields: dict[str, object], message_id: int
) -> dict[str, object]:
    """Render a sent message the way the store's inbox surface returns it."""
    ack_required = send_fields[module.STORE_ACK_REQUIRED_FIELD]
    return {
        module.STORE_ID_FIELD: message_id,
        module.STORE_FROM_FIELD: send_fields[module.STORE_FROM_FIELD],
        module.STORE_SUBJECT_FIELD: send_fields[module.STORE_SUBJECT_FIELD],
        module.STORE_THREAD_FIELD: send_fields[module.STORE_THREAD_ID_FIELD],
        module.STORE_ACK_STATUS_FIELD: (
            STORE_ACK_STATUS_PENDING
            if ack_required is True
            else module.STORE_ACK_STATUS_NONE
        ),
        module.STORE_BODY_FIELD: send_fields[module.STORE_BODY_FIELD],
    }


def run_record_roundtrip_property(
    assert_roundtrip: Callable[[ModuleType, dict[str, object], int], None],
) -> None:
    """Drive generated records while the linked test owns the round-trip predicate."""
    module = _load()

    @seed(RECORD_ROUNDTRIP_SEED)
    @settings(max_examples=RECORD_ROUNDTRIP_EXAMPLES, deadline=None, print_blob=True)
    @given(record=message_records(module), message_id=store_message_ids())
    def generated_roundtrip(record: dict[str, object], message_id: int) -> None:
        assert_roundtrip(module, record, message_id)

    run_replayable_property(
        generated_roundtrip,
        seed_value=RECORD_ROUNDTRIP_SEED,
        replay_path=RECORD_ROUNDTRIP_REPLAY_PATH,
    )


def run_terminal_property(
    assert_terminal: Callable[[ModuleType, str, object, object], None],
) -> None:
    """Drive generated terminal handbacks while the linked test owns the predicate."""
    module = _load()

    @seed(TERMINAL_PROPERTY_SEED)
    @settings(max_examples=TERMINAL_PROPERTY_EXAMPLES, deadline=None, print_blob=True)
    @given(
        reference=coordination_references(),
        first_kind=terminal_record_kinds(module),
        second_kind=terminal_record_kinds(module),
    )
    def generated_terminal(
        reference: str, first_kind: object, second_kind: object
    ) -> None:
        assert_terminal(module, reference, first_kind, second_kind)

    run_replayable_property(
        generated_terminal,
        seed_value=TERMINAL_PROPERTY_SEED,
        replay_path=TERMINAL_PROPERTY_REPLAY_PATH,
    )


def run_project_key_mapping(
    assert_key: Callable[[ModuleType, dict[str, object], str | None], None],
) -> None:
    """Drive the spec's diagnosis shapes while the linked test owns the predicate."""
    module = _load()

    @seed(PROJECT_KEY_MAPPING_SEED)
    @settings(max_examples=PROJECT_KEY_MAPPING_EXAMPLES, deadline=None, print_blob=True)
    @given(case=diagnosis_payloads(module))
    def generated_key_mapping(case: tuple[dict[str, object], str | None]) -> None:
        payload, expected_key = case
        assert_key(module, payload, expected_key)

    run_replayable_property(
        generated_key_mapping,
        seed_value=PROJECT_KEY_MAPPING_SEED,
        replay_path=PROJECT_KEY_MAPPING_REPLAY_PATH,
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
