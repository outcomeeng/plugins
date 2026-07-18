"""Synthetic public-CLI evidence for exact-pane native-agent recovery."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from collections.abc import Callable
from io import StringIO
from dataclasses import dataclass, field
from functools import cache
from pathlib import Path
from typing import Protocol, TextIO, cast

from hypothesis import example, given, seed, settings

from outcomeeng_testing.generators.native_agent_recovery import (
    OPERATIONAL_RECOVERY_ROSTER,
    RecoveryRosterCase,
    non_native_agent_types,
    roster_cases,
)
from outcomeeng_testing.harnesses.property_evidence import run_replayable_property

ROOT = Path(__file__).parents[2]
RECOVERY_PATH = (
    ROOT
    / "src/plugins/coding-agents/skills/recover-prowl-agents/scripts/recover_agents.py"
)
RECOVERY_PROPERTY_EXAMPLES = 100
RECOVERY_PROPERTY_SEED = 20260715
RECOVERY_PROPERTY_REPLAY_PATH = (
    "just test spx/43-coding-agents.enabler/"
    "32-native-agent-recovery.enabler/tests/"
    "test_native_agent_recovery.property.l1.py"
)
NON_NATIVE_MAPPING_SEED = 20260717
NON_NATIVE_MAPPING_REPLAY_PATH = (
    "just test spx/43-coding-agents.enabler/"
    "32-native-agent-recovery.enabler/tests/"
    "test_native_agent_recovery.mapping.l1.py"
)


@dataclass(frozen=True)
class HarnessCommandResult:
    returncode: int
    stdout: str
    stderr: str


@dataclass
class RecordingRunner:
    results: list[HarnessCommandResult]
    calls: list[tuple[tuple[str, ...], Path | None, str | None]] = field(
        default_factory=list
    )

    def run(
        self,
        argv: tuple[str, ...],
        cwd: Path | None = None,
        stdin: str | None = None,
    ) -> HarnessCommandResult:
        self.calls.append((argv, cwd, stdin))
        if not self.results:
            raise AssertionError(f"Unexpected command: {argv}")
        return self.results.pop(0)


class OperationContract(Protocol):
    RECOVER: str
    VERIFY: str


class ResultStatusContract(Protocol):
    RESUMED: object
    ALREADY_CURRENT: object
    VERIFIED: object
    INVALID_TARGET: object
    PANE_OCCUPIED: object
    COMMAND_FAILED: object
    INVALID_SCHEMA: object


class ResolutionContract(Protocol):
    RESUMED: object
    ALREADY_CORRELATED: object


class AdapterErrorContract(Protocol):
    status: object


class RecoveryModule(Protocol):
    SCHEMA_VERSION: int
    SPX_RESUME_COMMAND: str
    RECOVERY_REASSESSMENT_PROMPT: str
    RECOVERY_INPUT: str
    PROWL_LIST_COMMAND: tuple[str, ...]
    PROWL_AGENTS_COMMAND: tuple[str, ...]
    PROWL_SEND_PREFIX: tuple[str, ...]
    PROWL_COMMAND: str
    PANE_OPTION: str
    NO_WAIT_OPTION: str
    JSON_FLAG: str
    DATA_FIELD: str
    ITEMS_FIELD: str
    AGENTS_FIELD: str
    OK_FIELD: str
    WORKTREE_FIELD: str
    PANE_FIELD: str
    ID_FIELD: str
    PATH_FIELD: str
    ROOT_PATH_FIELD: str
    TYPE_FIELD: str
    STATUS_FIELD: str
    TARGETS_FIELD: str
    VERIFIED_FIELD: str
    CORRELATIONS_FIELD: str
    CWD_FIELD: str
    PANE_ID_FIELD: str
    WORKTREE_ID_FIELD: str
    WORKTREE_PATH_FIELD: str
    REPOSITORY_ROOT_FIELD: str
    MISSING_PANE_IDS_FIELD: str
    DUPLICATE_PANE_IDS_FIELD: str
    OCCUPIED_PANE_IDS_FIELD: str
    UNEXPECTED_AGENT_PANE_IDS_FIELD: str
    COMMAND_FIELD: str
    REASSESSMENT_SENT_FIELD: str
    PANE_RESULT_FIELDS: frozenset[str]
    CORRELATION_FIELDS: frozenset[str]
    NATIVE_AGENT_TYPES: frozenset[str]
    Operation: OperationContract
    ResultStatus: ResultStatusContract
    Resolution: ResolutionContract
    AdapterError: type[Exception]

    def recover(
        self,
        selected_pane_ids: tuple[str, ...],
        runner: RecordingRunner,
    ) -> dict[str, object]: ...

    def verify(
        self,
        selected_pane_ids: tuple[str, ...],
        runner: RecordingRunner,
    ) -> dict[str, object]: ...

    def recovery_send_command(self, pane_id: str) -> tuple[str, ...]: ...

    def main(
        self,
        argv: list[str] | None = None,
        *,
        runner: RecordingRunner | None = None,
        stdout: TextIO | None = None,
    ) -> int: ...

    def _parser(self) -> argparse.ArgumentParser: ...


def _load() -> RecoveryModule:
    spec = importlib.util.spec_from_file_location(
        "coding_agents_native_agent_recovery", RECOVERY_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load recovery adapter module: {RECOVERY_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return cast(RecoveryModule, module)


def _pane_item(
    module: RecoveryModule,
    worktree: Path,
    pane_id: str,
) -> dict[str, object]:
    return {
        module.WORKTREE_FIELD: {
            module.ID_FIELD: str(worktree),
            module.PATH_FIELD: str(worktree),
            module.ROOT_PATH_FIELD: str(worktree.parent.with_suffix(".git")),
        },
        module.PANE_FIELD: {
            module.ID_FIELD: pane_id,
            module.CWD_FIELD: str(worktree),
        },
    }


def _agent_item(
    module: RecoveryModule,
    worktree: Path,
    pane_id: str,
    agent_type: str,
) -> dict[str, object]:
    return {
        module.TYPE_FIELD: agent_type,
        module.STATUS_FIELD: "idle",
        module.WORKTREE_FIELD: {
            module.ID_FIELD: str(worktree),
            module.PATH_FIELD: str(worktree),
        },
        module.PANE_FIELD: {module.ID_FIELD: pane_id},
    }


def _payload(module: RecoveryModule, field: str, values: object) -> str:
    return json.dumps(
        {
            module.OK_FIELD: True,
            module.DATA_FIELD: {field: values},
        }
    )


def _send_result(module: RecoveryModule) -> HarnessCommandResult:
    return HarnessCommandResult(
        0,
        json.dumps({module.OK_FIELD: True, module.DATA_FIELD: {}}),
        "",
    )


def _rosters(
    module: RecoveryModule,
    roster: RecoveryRosterCase,
    *,
    correlated_count: int | None = None,
    correlated_type: str | None = None,
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    pane_items = [
        _pane_item(module, worktree, pane_id)
        for pane_id, worktree in zip(
            roster.pane_ids, roster.worktree_paths, strict=True
        )
    ]
    count = roster.correlated_count if correlated_count is None else correlated_count
    native_agent_types = tuple(sorted(module.NATIVE_AGENT_TYPES))
    agent_items = [
        _agent_item(
            module,
            worktree,
            pane_id,
            (
                correlated_type
                if correlated_type is not None
                else native_agent_types[index % len(native_agent_types)]
            ),
        )
        for index, (pane_id, worktree) in enumerate(
            zip(
                roster.pane_ids[:count],
                roster.worktree_paths[:count],
                strict=True,
            )
        )
    ]
    return pane_items, agent_items


def _post_launch_rosters(
    module: RecoveryModule,
    roster: RecoveryRosterCase,
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    pane_items, _ = _rosters(module, roster, correlated_count=0)
    native_agent_types = tuple(sorted(module.NATIVE_AGENT_TYPES))
    agent_items = [
        _agent_item(
            module,
            worktree,
            pane_id,
            native_agent_types[index % len(native_agent_types)],
        )
        for index, (pane_id, worktree) in enumerate(
            zip(roster.pane_ids, roster.worktree_paths, strict=True)
        )
    ]
    return pane_items, agent_items


def _runner(
    module: RecoveryModule,
    roster: RecoveryRosterCase,
    *,
    correlated_count: int | None = None,
    correlated_type: str | None = None,
    include_sends: bool = True,
) -> RecordingRunner:
    pane_items, agent_items = _rosters(
        module,
        roster,
        correlated_count=correlated_count,
        correlated_type=correlated_type,
    )
    count = roster.correlated_count if correlated_count is None else correlated_count
    results = [
        HarnessCommandResult(0, _payload(module, module.ITEMS_FIELD, pane_items), ""),
        HarnessCommandResult(0, _payload(module, module.AGENTS_FIELD, agent_items), ""),
    ]
    if include_sends:
        for _ in roster.pane_ids[count:]:
            results.append(_send_result(module))
    return RecordingRunner(results)


def _expected_recovery_send_command(
    module: RecoveryModule,
    pane_id: str,
) -> tuple[str, ...]:
    return (
        *module.PROWL_SEND_PREFIX,
        module.PANE_OPTION,
        pane_id,
        module.NO_WAIT_OPTION,
        module.JSON_FLAG,
    )


def _send_calls(
    module: RecoveryModule,
    runner: RecordingRunner,
) -> list[tuple[tuple[str, ...], Path | None, str | None]]:
    return [
        call
        for call in runner.calls
        if call[0][: len(module.PROWL_SEND_PREFIX)] == module.PROWL_SEND_PREFIX
    ]


def _recovery_command_violations(
    module: RecoveryModule,
    selected_pane_ids: tuple[str, ...],
    calls: list[tuple[tuple[str, ...], Path | None, str | None]],
) -> list[tuple[str, ...]]:
    violations: list[tuple[str, ...]] = []
    for argv, _, _ in calls:
        if argv in {module.PROWL_LIST_COMMAND, module.PROWL_AGENTS_COMMAND}:
            continue
        if argv[: len(module.PROWL_SEND_PREFIX)] == module.PROWL_SEND_PREFIX:
            expected_shape = len(argv) == 6 and argv[2] == "--pane"
            if expected_shape and argv[3] in selected_pane_ids:
                continue
        violations.append(argv)
    return violations


@dataclass(frozen=True)
class RecoveryMappingEvidence:
    target_count: int
    selected_count: int
    correlated_statuses: tuple[object, ...]
    expected_correlated_statuses: tuple[object, ...]
    unoccupied_statuses: tuple[object, ...]
    expected_unoccupied_statuses: tuple[object, ...]
    native_type_statuses: tuple[tuple[str, tuple[object, ...]], ...]
    expected_native_type_statuses: tuple[tuple[str, tuple[object, ...]], ...]
    unknown_status: object
    expected_unknown_status: object
    unknown_send_count: int
    duplicate_status: object
    expected_duplicate_status: object
    multiple_status: object
    expected_multiple_status: object
    multiple_target_field_sets: tuple[frozenset[str], ...]
    expected_multiple_target_field_sets: tuple[frozenset[str], ...]
    multiple_send_count: int


def _adapter_error_status(
    action: Callable[[], object], error_type: type[Exception]
) -> object:
    try:
        action()
    except error_type as error:
        return cast(AdapterErrorContract, error).status
    return None


@cache
def native_agent_recovery_mapping_evidence() -> RecoveryMappingEvidence:
    module = _load()
    roster = OPERATIONAL_RECOVERY_ROSTER
    native_agent_types = tuple(sorted(module.NATIVE_AGENT_TYPES))
    mapping_runs: list[tuple[str, dict[str, object], list[dict[str, object]]]] = []
    for agent_type in native_agent_types:
        runner = _runner(module, roster, correlated_type=agent_type)
        result = module.recover(roster.pane_ids, runner)
        mapping_runs.append(
            (
                agent_type,
                result,
                cast(list[dict[str, object]], result[module.TARGETS_FIELD]),
            )
        )
    result = mapping_runs[0][1]
    unknown_runner = _runner(module, roster, include_sends=False)
    unknown_status = _adapter_error_status(
        lambda: module.recover((roster.unknown_pane_id,), unknown_runner),
        module.AdapterError,
    )
    duplicate_runner = _runner(module, roster, include_sends=False)
    duplicate_status = _adapter_error_status(
        lambda: module.recover(roster.duplicate_selection, duplicate_runner),
        module.AdapterError,
    )
    multiple_panes, multiple_agents = _rosters(
        module,
        roster,
        correlated_count=roster.non_native_occupied_count,
    )
    multiple_agents.append({**multiple_agents[0]})
    multiple_runner = RecordingRunner(
        [
            HarnessCommandResult(
                0, _payload(module, module.ITEMS_FIELD, multiple_panes), ""
            ),
            HarnessCommandResult(
                0, _payload(module, module.AGENTS_FIELD, multiple_agents), ""
            ),
        ]
    )
    multiple_result = module.recover((roster.pane_ids[0],), multiple_runner)
    targets = cast(list[dict[str, object]], result[module.TARGETS_FIELD])
    multiple_targets = cast(
        list[dict[str, object]], multiple_result[module.TARGETS_FIELD]
    )
    statuses = {
        cast(str, target[module.PANE_ID_FIELD]): target[module.STATUS_FIELD]
        for target in targets
    }
    return RecoveryMappingEvidence(
        target_count=len(targets),
        selected_count=len(roster.pane_ids),
        correlated_statuses=tuple(
            statuses[pane_id] for pane_id in roster.correlated_pane_ids
        ),
        expected_correlated_statuses=(module.Resolution.ALREADY_CORRELATED,)
        * len(roster.correlated_pane_ids),
        unoccupied_statuses=tuple(
            statuses[pane_id] for pane_id in roster.unoccupied_pane_ids
        ),
        expected_unoccupied_statuses=(module.Resolution.RESUMED,)
        * len(roster.unoccupied_pane_ids),
        native_type_statuses=tuple(
            (
                agent_type,
                tuple(
                    target[module.STATUS_FIELD]
                    for target in run_targets[: roster.correlated_count]
                ),
            )
            for agent_type, _, run_targets in mapping_runs
        ),
        expected_native_type_statuses=tuple(
            (
                agent_type,
                (module.Resolution.ALREADY_CORRELATED,) * roster.correlated_count,
            )
            for agent_type in native_agent_types
        ),
        unknown_status=unknown_status,
        expected_unknown_status=module.ResultStatus.INVALID_TARGET,
        unknown_send_count=len(_send_calls(module, unknown_runner)),
        duplicate_status=duplicate_status,
        expected_duplicate_status=module.ResultStatus.INVALID_TARGET,
        multiple_status=multiple_result[module.STATUS_FIELD],
        expected_multiple_status=module.ResultStatus.PANE_OCCUPIED,
        multiple_target_field_sets=tuple(
            frozenset(target) for target in multiple_targets
        ),
        expected_multiple_target_field_sets=(module.PANE_RESULT_FIELDS,)
        * len(multiple_targets),
        multiple_send_count=len(_send_calls(module, multiple_runner)),
    )


@dataclass(frozen=True)
class NonNativeOccupancyEvidence:
    status: object
    expected_status: object
    occupied_pane_ids: object
    expected_occupied_pane_ids: list[str]
    target_field_sets: tuple[frozenset[str], ...]
    expected_target_field_sets: tuple[frozenset[str], ...]
    send_count: int


def run_non_native_occupancy_mapping(
    assertion: Callable[[NonNativeOccupancyEvidence], None],
) -> None:
    module = _load()

    @seed(NON_NATIVE_MAPPING_SEED)
    @settings(
        max_examples=RECOVERY_PROPERTY_EXAMPLES,
        deadline=None,
        print_blob=True,
    )
    @given(agent_type=non_native_agent_types(module.NATIVE_AGENT_TYPES))
    def generated_non_native_occupancy(agent_type: str) -> None:
        roster = OPERATIONAL_RECOVERY_ROSTER
        runner = _runner(
            module,
            roster,
            correlated_count=roster.non_native_occupied_count,
            correlated_type=agent_type,
            include_sends=False,
        )
        result = module.recover(roster.pane_ids, runner)
        targets = cast(list[dict[str, object]], result[module.TARGETS_FIELD])
        assertion(
            NonNativeOccupancyEvidence(
                status=result[module.STATUS_FIELD],
                expected_status=module.ResultStatus.PANE_OCCUPIED,
                occupied_pane_ids=result[module.OCCUPIED_PANE_IDS_FIELD],
                expected_occupied_pane_ids=list(
                    roster.pane_ids[: roster.non_native_occupied_count]
                ),
                target_field_sets=tuple(frozenset(target) for target in targets),
                expected_target_field_sets=(module.PANE_RESULT_FIELDS,) * len(targets),
                send_count=len(_send_calls(module, runner)),
            )
        )

    run_replayable_property(
        generated_non_native_occupancy,
        seed_value=NON_NATIVE_MAPPING_SEED,
        replay_path=NON_NATIVE_MAPPING_REPLAY_PATH,
    )


@dataclass(frozen=True)
class RecoveryIdempotenceEvidence:
    module: RecoveryModule
    result: dict[str, object]
    send_count: int
    remaining_result_count: int


def run_native_agent_recovery_idempotence(
    assertion: Callable[[RecoveryIdempotenceEvidence], None],
) -> None:
    @seed(RECOVERY_PROPERTY_SEED)
    @settings(
        max_examples=RECOVERY_PROPERTY_EXAMPLES,
        deadline=None,
        print_blob=True,
    )
    @example(roster=OPERATIONAL_RECOVERY_ROSTER)
    @given(roster=roster_cases())
    def generated_idempotence(roster: RecoveryRosterCase) -> None:
        module = _load()
        for agent_type in sorted(module.NATIVE_AGENT_TYPES):
            runner = _runner(
                module,
                roster,
                correlated_count=len(roster.pane_ids),
                correlated_type=agent_type,
                include_sends=False,
            )
            result = module.recover(roster.pane_ids, runner)
            assertion(
                RecoveryIdempotenceEvidence(
                    module=module,
                    result=result,
                    send_count=len(_send_calls(module, runner)),
                    remaining_result_count=len(runner.results),
                )
            )

    run_replayable_property(
        generated_idempotence,
        seed_value=RECOVERY_PROPERTY_SEED,
        replay_path=RECOVERY_PROPERTY_REPLAY_PATH,
    )


RecoveryCall = tuple[tuple[str, ...], Path | None, str | None]


@dataclass(frozen=True)
class RecoveryComplianceEvidence:
    sends: tuple[RecoveryCall, ...]
    expected_sends: tuple[RecoveryCall, ...]
    recovery_input: str
    expected_recovery_input: str
    command_violation_count: int
    violating_call_count: int
    detected_violating_call_count: int
    failure_status: object
    expected_failure_status: object
    failure_send_count: int
    expected_failure_send_count: int
    verification_status: object
    expected_verification_status: object
    verified_count: object
    expected_verified_count: int
    correlation_field_sets: tuple[frozenset[str], ...]
    expected_correlation_field_sets: tuple[frozenset[str], ...]
    correlation_identities: tuple[tuple[object, object], ...]
    expected_correlation_identities: tuple[tuple[str, str], ...]
    verification_send_count: int
    recover_cli_exit: int
    expected_recover_cli_exit: int
    recover_cli_status: object
    expected_recover_cli_status: object
    recover_cli_command_violation_count: int
    verify_cli_exit: int
    expected_verify_cli_exit: int
    verify_cli_status: object
    expected_verify_cli_status: object
    verify_cli_command_violation_count: int
    parser_has_state: bool
    verbatim_worktree_path: object
    expected_verbatim_worktree_path: str
    verbatim_repository_root: object
    expected_verbatim_repository_root: str
    verbatim_cwd: object
    expected_verbatim_cwd: str
    non_absolute_path_status: object
    expected_non_absolute_path_status: object


@cache
def native_agent_recovery_compliance_evidence() -> RecoveryComplianceEvidence:
    module = _load()
    roster = OPERATIONAL_RECOVERY_ROSTER
    runner = _runner(module, roster)
    post_launch_panes, post_launch_agents = _post_launch_rosters(module, roster)
    runner.results.extend(
        [
            HarnessCommandResult(
                0, _payload(module, module.ITEMS_FIELD, post_launch_panes), ""
            ),
            HarnessCommandResult(
                0, _payload(module, module.AGENTS_FIELD, post_launch_agents), ""
            ),
        ]
    )
    module.recover(roster.pane_ids, runner)
    recovery_call_count = len(runner.calls)
    violating_calls: tuple[RecoveryCall, ...] = (
        ((module.PROWL_COMMAND, "tab", "create"), None, None),
        ((module.PROWL_COMMAND, "open", str(roster.worktree_paths[0])), None, None),
        (
            (module.PROWL_COMMAND, "focus", module.PANE_OPTION, roster.pane_ids[0]),
            None,
            None,
        ),
        (
            (
                module.PROWL_COMMAND,
                "pane",
                "close",
                module.PANE_OPTION,
                roster.pane_ids[0],
            ),
            None,
            None,
        ),
        (("git", "worktree", "list"), None, None),
        (
            _expected_recovery_send_command(module, roster.unknown_pane_id),
            None,
            module.RECOVERY_INPUT,
        ),
    )
    failure_panes, failure_agents = _rosters(
        module,
        roster,
        correlated_count=len(roster.pane_ids) - 1,
    )
    failure_runner = RecordingRunner(
        [
            HarnessCommandResult(
                0, _payload(module, module.ITEMS_FIELD, failure_panes), ""
            ),
            HarnessCommandResult(
                0, _payload(module, module.AGENTS_FIELD, failure_agents), ""
            ),
            HarnessCommandResult(1, "", "recovery input rejected"),
        ]
    )
    failure_status = _adapter_error_status(
        lambda: module.recover((roster.pane_ids[-1],), failure_runner),
        module.AdapterError,
    )
    verification = module.verify(roster.pane_ids, runner)
    verification_calls = runner.calls[recovery_call_count:]
    parsed = module._parser().parse_args(
        [module.Operation.RECOVER, module.PANE_OPTION, roster.pane_ids[0]]
    )
    recover_cli_runner = _runner(module, roster)
    recover_cli_stdout = StringIO()
    recover_cli_exit = module.main(
        [
            module.Operation.RECOVER,
            *(
                argument
                for pane_id in roster.pane_ids
                for argument in (module.PANE_OPTION, pane_id)
            ),
        ],
        runner=recover_cli_runner,
        stdout=recover_cli_stdout,
    )
    recover_cli_output = cast(
        dict[str, object], json.loads(recover_cli_stdout.getvalue())
    )
    verify_cli_runner = _runner(
        module,
        roster,
        correlated_count=len(roster.pane_ids),
        include_sends=False,
    )
    verify_cli_stdout = StringIO()
    verify_cli_exit = module.main(
        [
            module.Operation.VERIFY,
            *(
                argument
                for pane_id in roster.pane_ids
                for argument in (module.PANE_OPTION, pane_id)
            ),
        ],
        runner=verify_cli_runner,
        stdout=verify_cli_stdout,
    )
    verify_cli_output = cast(
        dict[str, object], json.loads(verify_cli_stdout.getvalue())
    )
    violating_call_results = tuple(
        tuple(_recovery_command_violations(module, roster.pane_ids, [violating_call]))
        for violating_call in violating_calls
    )
    verbatim_pane_id = roster.pane_ids[0]
    verbatim_worktree_path = f"{roster.worktree_paths[0]}/"
    verbatim_repository_root = f"{roster.worktree_paths[0].parent}/repository.git/"
    verbatim_cwd = f"{verbatim_worktree_path}nested/../cwd/"
    verbatim_pane = _pane_item(module, roster.worktree_paths[0], verbatim_pane_id)
    cast(dict[str, object], verbatim_pane[module.WORKTREE_FIELD])[module.PATH_FIELD] = (
        verbatim_worktree_path
    )
    cast(dict[str, object], verbatim_pane[module.WORKTREE_FIELD])[
        module.ROOT_PATH_FIELD
    ] = verbatim_repository_root
    cast(dict[str, object], verbatim_pane[module.PANE_FIELD])[module.CWD_FIELD] = (
        verbatim_cwd
    )
    verbatim_agent = _agent_item(
        module,
        roster.worktree_paths[0],
        verbatim_pane_id,
        min(module.NATIVE_AGENT_TYPES),
    )
    cast(dict[str, object], verbatim_agent[module.WORKTREE_FIELD])[
        module.PATH_FIELD
    ] = verbatim_worktree_path
    verbatim_runner = RecordingRunner(
        [
            HarnessCommandResult(
                0, _payload(module, module.ITEMS_FIELD, [verbatim_pane]), ""
            ),
            HarnessCommandResult(
                0, _payload(module, module.AGENTS_FIELD, [verbatim_agent]), ""
            ),
        ]
    )
    verbatim_result = module.recover((verbatim_pane_id,), verbatim_runner)
    verbatim_target = cast(
        list[dict[str, object]], verbatim_result[module.TARGETS_FIELD]
    )[0]
    non_absolute_pane = _pane_item(module, roster.worktree_paths[0], verbatim_pane_id)
    cast(dict[str, object], non_absolute_pane[module.WORKTREE_FIELD])[
        module.PATH_FIELD
    ] = "relative-worktree"
    non_absolute_runner = RecordingRunner(
        [
            HarnessCommandResult(
                0, _payload(module, module.ITEMS_FIELD, [non_absolute_pane]), ""
            ),
            HarnessCommandResult(0, _payload(module, module.AGENTS_FIELD, []), ""),
        ]
    )
    non_absolute_path_status = _adapter_error_status(
        lambda: module.recover((verbatim_pane_id,), non_absolute_runner),
        module.AdapterError,
    )
    correlations = cast(
        list[dict[str, object]], verification[module.CORRELATIONS_FIELD]
    )
    recovery_sends = tuple(_send_calls(module, runner))
    return RecoveryComplianceEvidence(
        sends=recovery_sends,
        expected_sends=tuple(
            (
                _expected_recovery_send_command(module, pane_id),
                None,
                module.RECOVERY_INPUT,
            )
            for pane_id in roster.unoccupied_pane_ids
        ),
        recovery_input=cast(str, recovery_sends[0][2]),
        expected_recovery_input=module.RECOVERY_INPUT,
        command_violation_count=len(
            _recovery_command_violations(module, roster.pane_ids, runner.calls)
        ),
        violating_call_count=len(violating_calls),
        detected_violating_call_count=sum(
            bool(result) for result in violating_call_results
        ),
        failure_status=failure_status,
        expected_failure_status=module.ResultStatus.COMMAND_FAILED,
        failure_send_count=len(_send_calls(module, failure_runner)),
        expected_failure_send_count=1,
        verification_status=verification[module.STATUS_FIELD],
        expected_verification_status=module.ResultStatus.VERIFIED,
        verified_count=verification[module.VERIFIED_FIELD],
        expected_verified_count=len(roster.pane_ids),
        correlation_field_sets=tuple(
            frozenset(correlation) for correlation in correlations
        ),
        expected_correlation_field_sets=(module.CORRELATION_FIELDS,)
        * len(correlations),
        correlation_identities=tuple(
            (
                correlation[module.PANE_ID_FIELD],
                correlation[module.WORKTREE_PATH_FIELD],
            )
            for correlation in correlations
        ),
        expected_correlation_identities=tuple(
            (pane_id, str(worktree))
            for pane_id, worktree in zip(
                roster.pane_ids, roster.worktree_paths, strict=True
            )
        ),
        verification_send_count=len(
            _send_calls(module, RecordingRunner([], calls=verification_calls))
        ),
        recover_cli_exit=recover_cli_exit,
        expected_recover_cli_exit=0,
        recover_cli_status=recover_cli_output[module.STATUS_FIELD],
        expected_recover_cli_status=module.ResultStatus.RESUMED,
        recover_cli_command_violation_count=len(
            _recovery_command_violations(
                module, roster.pane_ids, recover_cli_runner.calls
            )
        ),
        verify_cli_exit=verify_cli_exit,
        expected_verify_cli_exit=0,
        verify_cli_status=verify_cli_output[module.STATUS_FIELD],
        expected_verify_cli_status=module.ResultStatus.VERIFIED,
        verify_cli_command_violation_count=len(
            _recovery_command_violations(
                module, roster.pane_ids, verify_cli_runner.calls
            )
        ),
        parser_has_state=hasattr(parsed, "state"),
        verbatim_worktree_path=verbatim_target[module.WORKTREE_PATH_FIELD],
        expected_verbatim_worktree_path=verbatim_worktree_path,
        verbatim_repository_root=verbatim_target[module.REPOSITORY_ROOT_FIELD],
        expected_verbatim_repository_root=verbatim_repository_root,
        verbatim_cwd=verbatim_target[module.CWD_FIELD],
        expected_verbatim_cwd=verbatim_cwd,
        non_absolute_path_status=non_absolute_path_status,
        expected_non_absolute_path_status=module.ResultStatus.INVALID_SCHEMA,
    )
