"""Test infrastructure for exact-pane native-agent recovery planning."""

from __future__ import annotations

import importlib.util
import json
import sys
from collections.abc import Callable
from io import StringIO
from pathlib import Path
from types import ModuleType
from typing import cast

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
    "just test spx/43-coding-agents.enabler/32-native-agent-recovery.enabler/"
    "tests/test_native_agent_recovery.property.l1.py"
)
NON_NATIVE_MAPPING_SEED = 20260717
NON_NATIVE_MAPPING_REPLAY_PATH = (
    "just test spx/43-coding-agents.enabler/32-native-agent-recovery.enabler/"
    "tests/test_native_agent_recovery.mapping.l1.py"
)


def _load() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "coding_agents_native_agent_recovery", RECOVERY_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load recovery module: {RECOVERY_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _pane_item(module: ModuleType, worktree: Path, pane_id: str) -> dict[str, object]:
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
    module: ModuleType,
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


def _rosters(
    module: ModuleType,
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
    native_types = tuple(sorted(module.NATIVE_AGENT_TYPES))
    agent_items = [
        _agent_item(
            module,
            worktree,
            pane_id,
            (
                correlated_type
                if correlated_type is not None
                else native_types[index % len(native_types)]
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
    module: ModuleType, roster: RecoveryRosterCase
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    panes, _ = _rosters(module, roster, correlated_count=0)
    native_types = tuple(sorted(module.NATIVE_AGENT_TYPES))
    agents = [
        _agent_item(
            module,
            worktree,
            pane_id,
            native_types[index % len(native_types)],
        )
        for index, (pane_id, worktree) in enumerate(
            zip(roster.pane_ids, roster.worktree_paths, strict=True)
        )
    ]
    return panes, agents


def _error_status(module: ModuleType, action: Callable[[], object]) -> object:
    try:
        action()
    except module.AdapterError as error:
        return error.status
    return None


def verify_native_agent_recovery_mappings() -> list[str]:
    module = _load()
    failures: list[str] = []
    roster = OPERATIONAL_RECOVERY_ROSTER
    panes, agents = _rosters(module, roster)
    result = module.recover(roster.pane_ids, panes, agents)
    targets = cast(list[dict[str, object]], result[module.TARGETS_FIELD])
    statuses = {
        cast(str, target[module.PANE_ID_FIELD]): target[module.STATUS_FIELD]
        for target in targets
    }
    for pane_id in roster.correlated_pane_ids:
        if statuses[pane_id] != module.Resolution.ALREADY_CORRELATED:
            failures.append(
                f"correlated pane {pane_id} did not map to already-correlated"
            )
    for pane_id in roster.unoccupied_pane_ids:
        if statuses[pane_id] != module.Resolution.RESUMED:
            failures.append(f"unoccupied pane {pane_id} did not map to resumed")
    deliveries = cast(list[dict[str, object]], result[module.DELIVERIES_FIELD])
    if [delivery[module.PANE_ID_FIELD] for delivery in deliveries] != list(
        roster.unoccupied_pane_ids
    ):
        failures.append("recovery deliveries did not map exactly to unoccupied panes")

    unknown_status = _error_status(
        module,
        lambda: module.recover((roster.unknown_pane_id,), panes, agents),
    )
    if unknown_status != module.ResultStatus.INVALID_TARGET:
        failures.append("unknown pane did not map to invalid-target")
    duplicate_status = _error_status(
        module,
        lambda: module.recover(roster.duplicate_selection, panes, agents),
    )
    if duplicate_status != module.ResultStatus.INVALID_TARGET:
        failures.append("duplicate selection did not map to invalid-target")

    duplicate_agents = [*agents, {**agents[0]}]
    occupied = module.recover((roster.pane_ids[0],), panes, duplicate_agents)
    if occupied[module.STATUS_FIELD] != module.ResultStatus.PANE_OCCUPIED:
        failures.append("multiple correlations did not map to pane-occupied")
    if occupied[module.DELIVERIES_FIELD]:
        failures.append("multiple correlations produced a partial delivery")

    @seed(NON_NATIVE_MAPPING_SEED)
    @settings(max_examples=RECOVERY_PROPERTY_EXAMPLES, deadline=None, print_blob=True)
    @given(agent_type=non_native_agent_types(module.NATIVE_AGENT_TYPES))
    def generated_non_native(agent_type: str) -> None:
        generated_panes, generated_agents = _rosters(
            module,
            roster,
            correlated_count=roster.non_native_occupied_count,
            correlated_type=agent_type,
        )
        generated = module.recover(roster.pane_ids, generated_panes, generated_agents)
        if generated[module.STATUS_FIELD] != module.ResultStatus.PANE_OCCUPIED:
            failures.append(f"non-native {agent_type} did not map to pane-occupied")
        if generated[module.DELIVERIES_FIELD]:
            failures.append(f"non-native {agent_type} produced a partial delivery")

    run_replayable_property(
        generated_non_native,
        seed_value=NON_NATIVE_MAPPING_SEED,
        replay_path=NON_NATIVE_MAPPING_REPLAY_PATH,
    )
    return failures


def verify_native_agent_recovery_properties() -> list[str]:
    module = _load()
    failures: list[str] = []

    @seed(RECOVERY_PROPERTY_SEED)
    @settings(max_examples=RECOVERY_PROPERTY_EXAMPLES, deadline=None, print_blob=True)
    @example(roster=OPERATIONAL_RECOVERY_ROSTER)
    @given(roster=roster_cases())
    def generated_idempotence(roster: RecoveryRosterCase) -> None:
        for agent_type in sorted(module.NATIVE_AGENT_TYPES):
            panes, agents = _rosters(
                module,
                roster,
                correlated_count=len(roster.pane_ids),
                correlated_type=agent_type,
            )
            result = module.recover(roster.pane_ids, panes, agents)
            if result[module.STATUS_FIELD] != module.ResultStatus.ALREADY_CURRENT:
                failures.append(
                    "fully correlated roster did not map to already-current"
                )
            if result[module.DELIVERIES_FIELD]:
                failures.append("idempotent recovery produced a delivery")

    run_replayable_property(
        generated_idempotence,
        seed_value=RECOVERY_PROPERTY_SEED,
        replay_path=RECOVERY_PROPERTY_REPLAY_PATH,
    )
    return failures


def verify_native_agent_recovery_compliance() -> list[str]:
    module = _load()
    failures: list[str] = []
    roster = OPERATIONAL_RECOVERY_ROSTER
    panes, agents = _rosters(module, roster)
    plan = module.recover(roster.pane_ids, panes, agents)
    deliveries = cast(list[dict[str, object]], plan[module.DELIVERIES_FIELD])
    expected_deliveries = [
        {
            module.PANE_ID_FIELD: pane_id,
            module.TEXT_FIELD: module.RECOVERY_INPUT,
        }
        for pane_id in roster.unoccupied_pane_ids
    ]
    if deliveries != expected_deliveries:
        failures.append("recovery plan did not preserve the source-owned atomic input")
    if any(frozenset(delivery) != module.DELIVERY_FIELDS for delivery in deliveries):
        failures.append("recovery delivery exposed non-semantic environment arguments")

    successful_results = [
        {
            module.PANE_ID_FIELD: pane_id,
            module.DELIVERED_FIELD: True,
            module.COMMAND_EXIT_CODE_FIELD: 0,
        }
        for pane_id in roster.unoccupied_pane_ids
    ]
    settled = module.settle_recovery(plan, successful_results)
    if settled[module.STATUS_FIELD] != module.ResultStatus.RESUMED:
        failures.append("successful delivery results did not preserve resumed")
    failed_results = [*successful_results]
    failed_results[-1] = {
        **failed_results[-1],
        module.DELIVERED_FIELD: False,
        module.COMMAND_EXIT_CODE_FIELD: 9,
    }
    failed = module.settle_recovery(plan, failed_results)
    if failed[module.STATUS_FIELD] != module.ResultStatus.COMMAND_FAILED:
        failures.append("failed environment delivery did not map to command-failed")

    post_panes, post_agents = _post_launch_rosters(module, roster)
    verified = module.verify(roster.pane_ids, post_panes, post_agents)
    if verified[module.STATUS_FIELD] != module.ResultStatus.VERIFIED:
        failures.append("complete post-launch roster did not map to verified")
    if verified[module.VERIFIED_FIELD] != len(roster.pane_ids):
        failures.append("verification count did not preserve the selected target count")
    correlations = cast(list[dict[str, object]], verified[module.CORRELATIONS_FIELD])
    if any(
        frozenset(correlation) != module.CORRELATION_FIELDS
        for correlation in correlations
    ):
        failures.append("correlation result omitted complete public identity fields")

    recover_stdout = StringIO()
    recover_exit = module.main(
        [
            module.Operation.RECOVER,
            *(value for pane_id in roster.pane_ids for value in ("--pane", pane_id)),
        ],
        stdin=StringIO(
            json.dumps({module.ITEMS_FIELD: panes, module.AGENTS_FIELD: agents})
        ),
        stdout=recover_stdout,
    )
    recover_output = json.loads(recover_stdout.getvalue())
    if (
        recover_exit != 0
        or recover_output[module.STATUS_FIELD] != module.ResultStatus.RESUMED
    ):
        failures.append("recover CLI did not emit the source-owned plan")

    settle_stdout = StringIO()
    settle_exit = module.main(
        [module.Operation.SETTLE],
        stdin=StringIO(
            json.dumps(
                {
                    module.PLAN_FIELD: plan,
                    module.DELIVERY_RESULTS_FIELD: successful_results,
                }
            )
        ),
        stdout=settle_stdout,
    )
    if settle_exit != 0:
        failures.append("settle CLI did not accept exact successful deliveries")

    verify_stdout = StringIO()
    verify_exit = module.main(
        [
            module.Operation.VERIFY,
            *(value for pane_id in roster.pane_ids for value in ("--pane", pane_id)),
        ],
        stdin=StringIO(
            json.dumps(
                {module.ITEMS_FIELD: post_panes, module.AGENTS_FIELD: post_agents}
            )
        ),
        stdout=verify_stdout,
    )
    verify_output = json.loads(verify_stdout.getvalue())
    if (
        verify_exit != 0
        or verify_output[module.STATUS_FIELD] != module.ResultStatus.VERIFIED
    ):
        failures.append("verify CLI did not emit complete correlation")

    pane_id = roster.pane_ids[0]
    verbatim_path = f"{roster.worktree_paths[0]}/"
    verbatim_root = f"{roster.worktree_paths[0].parent}/repository.git/"
    verbatim_cwd = f"{verbatim_path}nested/../cwd/"
    verbatim_pane = _pane_item(module, roster.worktree_paths[0], pane_id)
    cast(dict[str, object], verbatim_pane[module.WORKTREE_FIELD])[module.PATH_FIELD] = (
        verbatim_path
    )
    cast(dict[str, object], verbatim_pane[module.WORKTREE_FIELD])[
        module.ROOT_PATH_FIELD
    ] = verbatim_root
    cast(dict[str, object], verbatim_pane[module.PANE_FIELD])[module.CWD_FIELD] = (
        verbatim_cwd
    )
    verbatim_agent = _agent_item(
        module, roster.worktree_paths[0], pane_id, min(module.NATIVE_AGENT_TYPES)
    )
    cast(dict[str, object], verbatim_agent[module.WORKTREE_FIELD])[
        module.PATH_FIELD
    ] = verbatim_path
    verbatim = module.recover((pane_id,), [verbatim_pane], [verbatim_agent])
    target = cast(list[dict[str, object]], verbatim[module.TARGETS_FIELD])[0]
    if target[module.WORKTREE_PATH_FIELD] != verbatim_path:
        failures.append("worktree path identity was normalized")
    if target[module.REPOSITORY_ROOT_FIELD] != verbatim_root:
        failures.append("repository root identity was normalized")
    if target[module.CWD_FIELD] != verbatim_cwd:
        failures.append("pane cwd identity was normalized")

    relative_pane = _pane_item(module, roster.worktree_paths[0], pane_id)
    cast(dict[str, object], relative_pane[module.WORKTREE_FIELD])[module.PATH_FIELD] = (
        "relative"
    )
    relative_status = _error_status(
        module, lambda: module.recover((pane_id,), [relative_pane], [])
    )
    if relative_status != module.ResultStatus.INVALID_SCHEMA:
        failures.append("relative public path did not map to invalid-schema")
    return failures
