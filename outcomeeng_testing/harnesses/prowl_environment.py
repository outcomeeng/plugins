"""Test infrastructure for the shipped Prowl environment adapter."""

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
from hypothesis import strategies as st

from outcomeeng_testing.generators.prowl_environment import (
    DelegationTextCase,
    agent_identity,
    coordination_references,
    delegation_text_cases,
    message_texts,
    result_forms,
    subprocess_input_texts,
    unsupported_delegation_fields,
)
from outcomeeng_testing.harnesses.property_evidence import run_replayable_property

ROOT = Path(__file__).parents[2]
PROWL_ENVIRONMENT_PATH = (
    ROOT / "src/plugins/coding-agents/skills/operate-prowl/scripts/prowl_environment.py"
)
CODING_AGENTS_RUNTIME_ROOTS = (
    ROOT / "src/plugins/coding-agents",
    ROOT / "dist/claude/coding-agents",
    ROOT / "dist/codex/coding-agents",
)
OPERATE_PROWL_RELATIVE = Path("skills/operate-prowl")
RAW_PROWL_VIOLATION_FIXTURE = (
    ROOT / "outcomeeng_testing/fixtures/prowl_environment/raw_prowl_command.py.txt"
)
PROWL_HELP_VIOLATION_FIXTURE = (
    ROOT / "outcomeeng_testing/fixtures/prowl_environment/prowl_help_command.py.txt"
)
LOCAL_WORKTREE_ENUMERATION_VIOLATION_FIXTURE = (
    ROOT / "outcomeeng_testing/fixtures/prowl_environment/"
    "local_worktree_enumeration.py.txt"
)
LOCAL_FILESYSTEM_ENUMERATION_VIOLATION_FIXTURE = (
    ROOT / "outcomeeng_testing/fixtures/prowl_environment/"
    "local_filesystem_enumeration.py.txt"
)
PROPERTY_SEED = 2026071801
PROPERTY_EXAMPLES = 40
PROPERTY_REPLAY_PATH = (
    "spx/43-coding-agents.enabler/18-prowl-environment.enabler/tests/"
    "test_prowl_environment.property.l1.py"
)
TERMINAL_MAPPING_SEED = 2026081201
TERMINAL_MAPPING_EXAMPLES = 20
TERMINAL_MAPPING_REPLAY_PATH = (
    "spx/43-coding-agents.enabler/18-prowl-environment.enabler/tests/"
    "test_prowl_environment.mapping.l1.py"
)
TERMINAL_RESULT_COMPLIANCE_SEED = 2026081202
TERMINAL_RESULT_COMPLIANCE_EXAMPLES = 20
TERMINAL_RESULT_COMPLIANCE_REPLAY_PATH = (
    "spx/43-coding-agents.enabler/18-prowl-environment.enabler/tests/"
    "test_prowl_environment.compliance.l1.py"
)
DELEGATION_CLI_COMPLIANCE_SEED = 2026081203
DELEGATION_CLI_COMPLIANCE_EXAMPLES = 20
DELEGATION_CLI_COMPLIANCE_REPLAY_PATH = (
    "spx/43-coding-agents.enabler/18-prowl-environment.enabler/tests/"
    "test_prowl_environment.compliance.l1.py"
)
CHECKED_SEND_MAPPING_SEED = 2026081204
CHECKED_SEND_MAPPING_EXAMPLES = 20
CHECKED_SEND_MAPPING_REPLAY_PATH = (
    "spx/43-coding-agents.enabler/18-prowl-environment.enabler/tests/"
    "test_prowl_target_resolution.mapping.l1.py"
)
SUBPROCESS_INPUT_PROPERTY_SEED = 2026081101
SUBPROCESS_INPUT_PROPERTY_EXAMPLES = 40
SUBPROCESS_INPUT_PROPERTY_REPLAY_PATH = (
    "spx/43-coding-agents.enabler/18-prowl-environment.enabler/tests/"
    "test_prowl_subprocess_input.property.l1.py"
)


class CommandResultContract(Protocol):
    returncode: int
    stdout: str
    stderr: str


@dataclass
class RecordingRunner:
    results: list[CommandResultContract]
    calls: list[tuple[tuple[str, ...], str | None]] = field(default_factory=list)

    def run(
        self, argv: tuple[str, ...], stdin: str | None = None
    ) -> CommandResultContract:
        self.calls.append((argv, stdin))
        if not self.results:
            raise RuntimeError(f"Unexpected command: {argv}")
        return self.results.pop(0)


def _load() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "coding_agents_prowl_environment", PROWL_ENVIRONMENT_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(
            f"Cannot load Prowl environment module: {PROWL_ENVIRONMENT_PATH}"
        )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_prowl_environment() -> ModuleType:
    """Load the shipped adapter so linked tests can inspect its public contract."""
    return _load()


def prowl_agents_command_result(
    module: ModuleType, agents: list[dict[str, object]]
) -> CommandResultContract:
    """Return one controlled public agents response from the Prowl boundary."""
    return cast(
        CommandResultContract,
        module.CommandResult(
            0,
            json.dumps(
                {
                    module.OK_FIELD: True,
                    module.DATA_FIELD: {module.AGENTS_FIELD: agents},
                }
            ),
            "",
        ),
    )


def prowl_send_command_result(
    module: ModuleType, *, trailing_enter_sent: bool
) -> CommandResultContract:
    """Return one controlled public send response from the Prowl boundary."""
    return cast(
        CommandResultContract,
        module.CommandResult(
            0,
            json.dumps(
                {
                    module.OK_FIELD: True,
                    module.DATA_FIELD: {
                        module.INPUT_FIELD: {
                            module.TRAILING_ENTER_SENT_FIELD: trailing_enter_sent
                        }
                    },
                },
            ),
            "",
        ),
    )


def run_subprocess_input_probe(input_text: str | None) -> CommandResultContract:
    """Run a child that reports how the default runner connected stdin."""
    module = _load()
    return cast(
        CommandResultContract,
        module.SubprocessRunner().run(
            (
                sys.executable,
                "-c",
                """
import json
import os
import stat
import sys

print(json.dumps({
    "isCharDevice": stat.S_ISCHR(os.fstat(0).st_mode),
    "input": sys.stdin.read(),
}))
""",
            ),
            stdin=input_text,
        ),
    )


def run_subprocess_input_property(assert_input: Callable[[str], None]) -> None:
    """Drive generated explicit input while the linked test owns its predicate."""

    @seed(SUBPROCESS_INPUT_PROPERTY_SEED)
    @settings(
        max_examples=SUBPROCESS_INPUT_PROPERTY_EXAMPLES,
        deadline=None,
        print_blob=True,
    )
    @given(input_text=subprocess_input_texts())
    def generated_input_property(input_text: str) -> None:
        assert_input(input_text)

    run_replayable_property(
        generated_input_property,
        seed_value=SUBPROCESS_INPUT_PROPERTY_SEED,
        replay_path=SUBPROCESS_INPUT_PROPERTY_REPLAY_PATH,
    )


def run_terminal_property(
    assert_terminal: Callable[
        [
            ModuleType,
            dict[str, str],
            dict[str, str],
            DelegationTextCase,
            str,
            object,
            tuple[str | None, str | None, str | None],
        ],
        None,
    ],
) -> None:
    """Drive generated terminal cases while the linked test owns its predicate."""
    module = _load()
    sender = agent_identity(module, ordinal=1)
    recipient = agent_identity(module, ordinal=2)

    @seed(PROPERTY_SEED)
    @settings(max_examples=PROPERTY_EXAMPLES, deadline=None, print_blob=True)
    @given(
        property_text=delegation_text_cases(),
        reference=coordination_references(),
        terminal_kind=st.sampled_from(tuple(module.TerminalKind)),
        result_form=result_forms(),
    )
    def generated_terminal_property(
        property_text: DelegationTextCase,
        reference: str,
        terminal_kind: object,
        result_form: tuple[str | None, str | None, str | None],
    ) -> None:
        assert_terminal(
            module,
            sender,
            recipient,
            property_text,
            reference,
            terminal_kind,
            result_form,
        )

    run_replayable_property(
        generated_terminal_property,
        seed_value=PROPERTY_SEED,
        replay_path=PROPERTY_REPLAY_PATH,
    )


def run_terminal_mapping(
    assert_terminal: Callable[[ModuleType, DelegationTextCase], None],
) -> None:
    """Drive variable delegation text through the finite terminal-kind mapping."""
    module = _load()

    @seed(TERMINAL_MAPPING_SEED)
    @settings(max_examples=TERMINAL_MAPPING_EXAMPLES, deadline=None, print_blob=True)
    @given(content=delegation_text_cases())
    def generated_terminal_mapping(content: DelegationTextCase) -> None:
        assert_terminal(module, content)

    run_replayable_property(
        generated_terminal_mapping,
        seed_value=TERMINAL_MAPPING_SEED,
        replay_path=TERMINAL_MAPPING_REPLAY_PATH,
    )


def run_terminal_result_compliance(
    assert_result_forms: Callable[[ModuleType, DelegationTextCase], None],
) -> None:
    """Drive variable delegation text through terminal result-form violations."""
    module = _load()

    @seed(TERMINAL_RESULT_COMPLIANCE_SEED)
    @settings(
        max_examples=TERMINAL_RESULT_COMPLIANCE_EXAMPLES,
        deadline=None,
        print_blob=True,
    )
    @given(content=delegation_text_cases())
    def generated_result_compliance(content: DelegationTextCase) -> None:
        assert_result_forms(module, content)

    run_replayable_property(
        generated_result_compliance,
        seed_value=TERMINAL_RESULT_COMPLIANCE_SEED,
        replay_path=TERMINAL_RESULT_COMPLIANCE_REPLAY_PATH,
    )


def run_delegation_cli_compliance(
    assert_delegation: Callable[[ModuleType, DelegationTextCase, str], None],
) -> None:
    """Drive variable valid members and unsupported keys through delegation input."""
    module = _load()

    @seed(DELEGATION_CLI_COMPLIANCE_SEED)
    @settings(
        max_examples=DELEGATION_CLI_COMPLIANCE_EXAMPLES,
        deadline=None,
        print_blob=True,
    )
    @given(
        content=delegation_text_cases(),
        unsupported_field=unsupported_delegation_fields(module),
    )
    def generated_delegation_compliance(
        content: DelegationTextCase, unsupported_field: str
    ) -> None:
        assert_delegation(module, content, unsupported_field)

    run_replayable_property(
        generated_delegation_compliance,
        seed_value=DELEGATION_CLI_COMPLIANCE_SEED,
        replay_path=DELEGATION_CLI_COMPLIANCE_REPLAY_PATH,
    )


def run_checked_send_mapping(assert_send: Callable[[str], None]) -> None:
    """Drive variable message text through the checked-send mapping."""

    @seed(CHECKED_SEND_MAPPING_SEED)
    @settings(
        max_examples=CHECKED_SEND_MAPPING_EXAMPLES, deadline=None, print_blob=True
    )
    @given(message_text=message_texts())
    def generated_checked_send_mapping(message_text: str) -> None:
        assert_send(message_text)

    run_replayable_property(
        generated_checked_send_mapping,
        seed_value=CHECKED_SEND_MAPPING_SEED,
        replay_path=CHECKED_SEND_MAPPING_REPLAY_PATH,
    )


def _source_texts(paths: tuple[Path, ...]) -> dict[str, str]:
    return {
        str(path.relative_to(ROOT)): path.read_text(encoding="utf-8")
        for path in sorted(paths)
    }


def prowl_command_source_texts() -> dict[str, str]:
    """Return shipped Python source outside the sole Prowl command owner."""
    script_paths = tuple(
        path
        for runtime_root in CODING_AGENTS_RUNTIME_ROOTS
        for path in runtime_root.rglob("*.py")
        if OPERATE_PROWL_RELATIVE not in path.relative_to(runtime_root).parents
    )
    return _source_texts(script_paths)


def prowl_environment_source_texts() -> dict[str, str]:
    """Return the authoritative Prowl adapter source observation."""
    return _source_texts((PROWL_ENVIRONMENT_PATH,))


def raw_prowl_violation_source() -> tuple[str, dict[str, str]]:
    """Return the violating fixture identity and its source observation."""
    return (
        str(RAW_PROWL_VIOLATION_FIXTURE.relative_to(ROOT)),
        _source_texts((RAW_PROWL_VIOLATION_FIXTURE,)),
    )


def prowl_help_violation_source() -> tuple[str, dict[str, str]]:
    """Return the help-only fixture identity and its source observation."""
    return (
        str(PROWL_HELP_VIOLATION_FIXTURE.relative_to(ROOT)),
        _source_texts((PROWL_HELP_VIOLATION_FIXTURE,)),
    )


def local_worktree_enumeration_violation_source() -> tuple[str, dict[str, str]]:
    """Return the local-enumeration fixture identity and source observation."""
    return (
        str(LOCAL_WORKTREE_ENUMERATION_VIOLATION_FIXTURE.relative_to(ROOT)),
        _source_texts((LOCAL_WORKTREE_ENUMERATION_VIOLATION_FIXTURE,)),
    )


def local_filesystem_enumeration_violation_source() -> tuple[str, dict[str, str]]:
    """Return the filesystem-enumeration fixture and its source observation."""
    return (
        str(LOCAL_FILESYSTEM_ENUMERATION_VIOLATION_FIXTURE.relative_to(ROOT)),
        _source_texts((LOCAL_FILESYSTEM_ENUMERATION_VIOLATION_FIXTURE,)),
    )
