"""Test infrastructure for two-phase native-agent recovery."""

from __future__ import annotations

import importlib.util
import json
import shlex
import sys
from collections.abc import Callable
from copy import deepcopy
from dataclasses import dataclass
from io import StringIO
from pathlib import Path
from types import ModuleType
from typing import cast

from hypothesis import example, given, seed, settings

from outcomeeng_testing.generators.native_agent_recovery import (
    OPERATIONAL_RECOVERY_ROSTER,
    RecoveryRosterCase,
    activation_results,
    identity_evidence,
    invalid_recovery_evidence,
    pane_read_results,
    recovery_candidates,
    recovery_delivery_results,
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
    session_id: str | None,
    *,
    status: str = "idle",
) -> dict[str, object]:
    item: dict[str, object] = {
        module.TYPE_FIELD: agent_type,
        module.STATUS_FIELD: status,
        module.WORKTREE_FIELD: {
            module.ID_FIELD: str(worktree),
            module.PATH_FIELD: str(worktree),
        },
        module.PANE_FIELD: {module.ID_FIELD: pane_id},
    }
    if session_id is not None:
        item[module.SESSION_FIELD] = {module.ID_FIELD: session_id}
    return item


def _pre_restart_rosters(
    module: ModuleType,
    roster: RecoveryRosterCase,
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    panes = [
        _pane_item(module, worktree, pane_id)
        for pane_id, worktree in zip(
            roster.original_pane_ids, roster.worktree_paths, strict=True
        )
    ]
    agents = [
        _agent_item(module, worktree, pane_id, agent_type, session_id)
        for pane_id, worktree, agent_type, session_id in zip(
            roster.original_pane_ids,
            roster.worktree_paths,
            roster.agent_types,
            roster.session_ids,
            strict=True,
        )
    ]
    return panes, agents


def _post_restart_rosters(
    module: ModuleType,
    roster: RecoveryRosterCase,
    count: int,
    *,
    exact_sessions: bool = True,
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    panes = [
        _pane_item(module, worktree, pane_id)
        for pane_id, worktree in zip(
            roster.post_restart_pane_ids[:count],
            roster.worktree_paths[:count],
            strict=True,
        )
    ]
    agents = [
        _agent_item(
            module,
            worktree,
            pane_id,
            agent_type,
            session_id if exact_sessions else None,
        )
        for pane_id, worktree, agent_type, session_id in zip(
            roster.post_restart_pane_ids[:count],
            roster.worktree_paths[:count],
            roster.agent_types[:count],
            roster.session_ids[:count],
            strict=True,
        )
    ]
    return panes, agents


def _prepared(module: ModuleType, roster: RecoveryRosterCase) -> dict[str, object]:
    panes, agents = _pre_restart_rosters(module, roster)
    return cast(
        dict[str, object],
        module.prepare(
            roster.original_pane_ids,
            panes,
            agents,
            recovery_candidates(module, roster),
            identity_evidence(module, roster, roster.original_pane_ids),
        ),
    )


def _all_bindings(
    module: ModuleType, roster: RecoveryRosterCase
) -> list[dict[str, object]]:
    return [
        {
            module.ORIGINAL_PANE_ID_FIELD: original_pane_id,
            module.PANE_ID_FIELD: post_restart_pane_id,
        }
        for original_pane_id, post_restart_pane_id in zip(
            roster.original_pane_ids,
            roster.post_restart_pane_ids,
            strict=True,
        )
    ]


def _verified_recovery(
    module: ModuleType, roster: RecoveryRosterCase
) -> dict[str, object]:
    """One verified post-restart recovery fixture shared by the mapping and compliance lanes."""
    prepared = _prepared(module, roster)
    panes, _ = _post_restart_rosters(module, roster, len(roster.original_pane_ids))
    bindings = _all_bindings(module, roster)
    agents_without_sessions = _post_restart_rosters(
        module,
        roster,
        len(roster.original_pane_ids),
        exact_sessions=False,
    )[1]
    correlations = identity_evidence(module, roster, roster.post_restart_pane_ids)
    for index, correlation in enumerate(correlations):
        if correlation[module.SOURCE_FIELD] is module.EvidenceSource.PUBLIC_AGENT:
            agents_without_sessions[index][module.SESSION_FIELD] = {
                module.ID_FIELD: roster.session_ids[index]
            }
        elif (
            correlation[module.SOURCE_FIELD] is module.EvidenceSource.OPERATOR_CONFIRMED
        ):
            correlation[module.SOURCE_FIELD] = module.EvidenceSource.PROCESS_ARGUMENT
    return {
        "prepared": prepared,
        "panes": panes,
        "bindings": bindings,
        "agents": agents_without_sessions,
        "correlations": correlations,
        "verified": module.verify(
            prepared, bindings, panes, agents_without_sessions, correlations
        ),
        "reads": pane_read_results(module, bindings),
    }


def _continuation_plan(
    module: ModuleType, roster: RecoveryRosterCase, fixture: dict[str, object]
) -> tuple[list[str], str, list[dict[str, object]]]:
    """The non-controller sessions, the one judged intact, and the restored facts for the rest."""
    continuation_sessions = [
        cast(str, candidate[module.SESSION_ID_FIELD])
        for candidate in cast(
            list[dict[str, object]],
            cast(dict[str, object], fixture["prepared"])[module.CANDIDATES_FIELD],
        )
        if candidate[module.EVIDENCE_FIELD] is not module.EvidenceSource.CURRENT_SESSION
    ]
    intact_session = continuation_sessions[-1]
    restored: list[dict[str, object]] = [
        {
            module.SESSION_ID_FIELD: session_id,
            module.TEXT_FIELD: f"The restart killed the command {session_id} was running.",
        }
        for session_id in continuation_sessions
        if session_id != intact_session
    ]
    return continuation_sessions, intact_session, restored


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
    prepared = _prepared(module, roster)
    if prepared[module.STATUS_FIELD] != module.ResultStatus.PREPARED:
        failures.append("valid pre-restart evidence did not map to prepared")
    prepared_candidates = cast(
        list[dict[str, object]], prepared[module.CANDIDATES_FIELD]
    )
    if len(prepared_candidates) != len(roster.original_pane_ids):
        failures.append("prepared manifest omitted candidates")
    for candidate, session_id in zip(
        prepared_candidates, roster.session_ids, strict=True
    ):
        if candidate[module.RESUME_LOCATOR_FIELD] != session_id:
            failures.append("prepared manifest omitted the exact resume locator")
        if module.NATIVE_HOME_FIELD not in candidate:
            failures.append("prepared manifest omitted the native home field")

    hinted_panes, hinted_agents = _pre_restart_rosters(module, roster)
    cast(dict[str, object], hinted_agents[0][module.SESSION_FIELD])[module.ID_FIELD] = (
        roster.session_ids[1]
    )
    hinted_prepared = module.prepare(
        roster.original_pane_ids,
        hinted_panes,
        hinted_agents,
        recovery_candidates(module, roster),
        identity_evidence(module, roster, roster.original_pane_ids),
    )
    if hinted_prepared[module.STATUS_FIELD] != module.ResultStatus.PREPARED:
        failures.append("non-public evidence was overridden by a public session hint")

    public_index = tuple(module.EvidenceSource).index(
        module.EvidenceSource.PUBLIC_AGENT
    )
    public_hint_agents = _pre_restart_rosters(module, roster)[1]
    cast(dict[str, object], public_hint_agents[public_index][module.SESSION_FIELD])[
        module.ID_FIELD
    ] = roster.session_ids[public_index - 1]
    public_hint_status = _error_status(
        module,
        lambda: module.prepare(
            roster.original_pane_ids,
            hinted_panes,
            public_hint_agents,
            recovery_candidates(module, roster),
            identity_evidence(module, roster, roster.original_pane_ids),
        ),
    )
    if public_hint_status != module.ResultStatus.INVALID_TARGET:
        failures.append("public-agent evidence accepted a conflicting public session")

    current_panes, current_agents = _post_restart_rosters(
        module, roster, roster.correlated_count
    )
    activation = module.plan_activation(prepared, current_panes, current_agents)
    bindings = cast(list[dict[str, object]], activation[module.BINDINGS_FIELD])
    activations = cast(list[dict[str, object]], activation[module.ACTIVATIONS_FIELD])
    if len(bindings) != roster.correlated_count:
        failures.append("exact post-restart agents did not bind as existing")
    if len(activations) != len(roster.original_pane_ids) - roster.correlated_count:
        failures.append("missing worktrees did not map to activation requests")
    if any(
        action[module.OPERATION_FIELD] != module.ACTIVATION_OPEN_OPERATION
        for action in activations
    ):
        failures.append("unique absent worktree did not map to open")

    bound = module.bind_activations(
        activation,
        activation_results(
            module,
            activations,
            roster.post_restart_pane_ids[roster.correlated_count :],
        ),
    )
    all_bindings = cast(list[dict[str, object]], bound[module.BINDINGS_FIELD])
    if len(all_bindings) != len(roster.original_pane_ids):
        failures.append("checked activation results did not bind every candidate")

    existing_target_results = activation_results(
        module,
        activations,
        roster.post_restart_pane_ids[roster.correlated_count :],
    )
    existing_target_transport = cast(
        dict[str, object], existing_target_results[0][module.TRANSPORT_FIELD]
    )
    existing_target_response = cast(
        dict[str, object], existing_target_transport[module.RESPONSE_FIELD]
    )
    existing_target_data = cast(
        dict[str, object], existing_target_response[module.DATA_FIELD]
    )
    existing_target_data[module.CREATED_TAB_FIELD] = False
    existing_target_bound = module.bind_activations(activation, existing_target_results)
    if existing_target_bound[module.STATUS_FIELD] != module.ResultStatus.READY:
        failures.append("exact existing activation target required an extra pane")

    non_exact_results = activation_results(
        module,
        activations,
        roster.post_restart_pane_ids[roster.correlated_count :],
    )
    non_exact_transport = cast(
        dict[str, object], non_exact_results[0][module.TRANSPORT_FIELD]
    )
    non_exact_response = cast(
        dict[str, object], non_exact_transport[module.RESPONSE_FIELD]
    )
    non_exact_data = cast(dict[str, object], non_exact_response[module.DATA_FIELD])
    non_exact_data[module.RESOLUTION_FIELD] = "new-root"
    non_exact_status = _error_status(
        module,
        lambda: module.bind_activations(activation, non_exact_results),
    )
    if non_exact_status != module.ResultStatus.INVALID_TARGET:
        failures.append("new-root activation was accepted for a prepared worktree")

    mixed_results = activation_results(
        module,
        activations,
        roster.post_restart_pane_ids[roster.correlated_count :],
    )
    failed_transport = cast(dict[str, object], mixed_results[0][module.TRANSPORT_FIELD])
    failed_transport[module.STATUS_FIELD] = module.TRANSPORT_COMMAND_FAILED_STATUS
    failed_transport[module.COMMAND_EXIT_CODE_FIELD] = 1
    failed_transport[module.DETAIL_FIELD] = "activation failed"
    failed_transport.pop(module.RESPONSE_FIELD)
    mixed_bound = module.bind_activations(activation, mixed_results)
    if mixed_bound[module.STATUS_FIELD] != module.ResultStatus.COMMAND_FAILED:
        failures.append("mixed activation results did not preserve command failure")
    if len(cast(list[object], mixed_bound[module.ACTIVATION_RESULTS_FIELD])) != len(
        activations
    ):
        failures.append("mixed activation results omitted checked transports")
    if (
        len(cast(list[object], mixed_bound[module.BINDINGS_FIELD]))
        != len(roster.original_pane_ids) - 1
    ):
        failures.append("mixed activation results omitted later successful bindings")

    all_panes, _ = _post_restart_rosters(module, roster, len(roster.original_pane_ids))
    recovery = module.recover(prepared, all_bindings, all_panes, current_agents)
    targets = cast(list[dict[str, object]], recovery[module.TARGETS_FIELD])
    statuses = {
        cast(str, target[module.ORIGINAL_PANE_ID_FIELD]): target[module.STATUS_FIELD]
        for target in targets
    }
    for original_pane_id in roster.original_pane_ids[: roster.correlated_count]:
        if statuses[original_pane_id] != module.Resolution.ALREADY_CORRELATED:
            failures.append("exact occupied pane did not map to already-correlated")
    for original_pane_id in roster.original_pane_ids[roster.correlated_count :]:
        if statuses[original_pane_id] != module.Resolution.RESUMED:
            failures.append("unoccupied bound pane did not map to resumed")

    panes, agents = _pre_restart_rosters(module, roster)
    candidates = recovery_candidates(module, roster)
    evidence = identity_evidence(module, roster, roster.original_pane_ids)
    for advisory_status in ("working", "idle", "blocked", "done", "unknown"):
        advisory_agents = deepcopy(agents)
        advisory_agents[0][module.STATUS_FIELD] = advisory_status
        advisory_result = module.prepare(
            roster.original_pane_ids,
            panes,
            advisory_agents,
            candidates,
            evidence,
        )
        if advisory_result[module.STATUS_FIELD] != module.ResultStatus.PREPARED:
            failures.append(
                f"advisory Prowl status {advisory_status} changed recovery eligibility"
            )

    duplicate_session_candidates = deepcopy(candidates)
    duplicate_session_candidates[1][module.SESSION_ID_FIELD] = (
        duplicate_session_candidates[0][module.SESSION_ID_FIELD]
    )
    duplicate_session_status = _error_status(
        module,
        lambda: module.prepare(
            roster.original_pane_ids,
            panes,
            _pre_restart_rosters(module, roster)[1],
            duplicate_session_candidates,
            evidence,
        ),
    )
    if duplicate_session_status != module.ResultStatus.INVALID_TARGET:
        failures.append("duplicate native session identity was prepared")

    lone_secondary = deepcopy(candidates)
    lone_secondary[1][module.ROLE_FIELD] = module.RecoveryRole.SECONDARY
    lone_secondary[1][module.SECONDARY_AUTHORIZED_FIELD] = True
    lone_secondary_status = _error_status(
        module,
        lambda: module.prepare(
            roster.original_pane_ids,
            panes,
            _pre_restart_rosters(module, roster)[1],
            lone_secondary,
            evidence,
        ),
    )
    if lone_secondary_status != module.ResultStatus.INVALID_TARGET:
        failures.append("lone secondary candidate was prepared")

    duplicate_controller_candidates = deepcopy(candidates)
    duplicate_controller_evidence = deepcopy(evidence)
    duplicate_controller_candidates[1][module.EVIDENCE_FIELD] = (
        module.EvidenceSource.CURRENT_SESSION
    )
    duplicate_controller_evidence[1][module.SOURCE_FIELD] = (
        module.EvidenceSource.CURRENT_SESSION
    )
    duplicate_controller_status = _error_status(
        module,
        lambda: module.prepare(
            roster.original_pane_ids,
            panes,
            _pre_restart_rosters(module, roster)[1],
            duplicate_controller_candidates,
            duplicate_controller_evidence,
        ),
    )
    if duplicate_controller_status != module.ResultStatus.INVALID_TARGET:
        failures.append("multiple current-session controllers were prepared")

    shared_panes, shared_agents = _pre_restart_rosters(module, roster)
    shared_candidates = recovery_candidates(module, roster)
    shared_evidence = identity_evidence(module, roster, roster.original_pane_ids)
    shared_path = shared_candidates[0][module.WORKTREE_PATH_FIELD]
    for collection in (shared_panes, shared_agents):
        cast(dict[str, object], collection[1][module.WORKTREE_FIELD])[
            module.PATH_FIELD
        ] = shared_path
    shared_candidates[1][module.WORKTREE_PATH_FIELD] = shared_path
    shared_evidence[1][module.WORKTREE_PATH_FIELD] = shared_path
    duplicate_primary_status = _error_status(
        module,
        lambda: module.prepare(
            roster.original_pane_ids,
            shared_panes,
            shared_agents,
            shared_candidates,
            shared_evidence,
        ),
    )
    if duplicate_primary_status != module.ResultStatus.INVALID_TARGET:
        failures.append("same-worktree primary candidates were prepared")
    shared_candidates[1][module.ROLE_FIELD] = module.RecoveryRole.SECONDARY
    shared_candidates[1][module.SECONDARY_AUTHORIZED_FIELD] = True
    reconciled = module.prepare(
        roster.original_pane_ids,
        shared_panes,
        shared_agents,
        shared_candidates,
        shared_evidence,
    )
    shared_activation = module.plan_activation(reconciled, [], [])
    operations = [
        action[module.OPERATION_FIELD]
        for action in cast(
            list[dict[str, object]], shared_activation[module.ACTIVATIONS_FIELD]
        )[:2]
    ]
    if operations != [
        module.ACTIVATION_OPEN_OPERATION,
        module.ACTIVATION_TAB_CREATE_OPERATION,
    ]:
        failures.append("authorized secondary did not map to open then tab-create")

    occupied_panes, occupied_agents = _post_restart_rosters(module, roster, 1)
    cast(dict[str, object], occupied_agents[0][module.SESSION_FIELD])[
        module.ID_FIELD
    ] = roster.session_ids[1]
    occupied = module.plan_activation(prepared, occupied_panes, occupied_agents)
    if occupied[module.STATUS_FIELD] != module.ResultStatus.PANE_OCCUPIED:
        failures.append("mismatched occupied pane did not block activation")

    fixture = _verified_recovery(module, roster)
    reassess_prepared = cast(dict[str, object], fixture["prepared"])
    reassess_bindings = cast(list[dict[str, object]], fixture["bindings"])
    verified = cast(dict[str, object], fixture["verified"])
    reads = cast(list[dict[str, object]], fixture["reads"])

    incomplete_barrier = _error_status(
        module,
        lambda: module.plan_reassessment(
            reassess_prepared, reassess_bindings, verified, reads[:-1]
        ),
    )
    if incomplete_barrier != module.ResultStatus.INVALID_SCHEMA:
        failures.append("incomplete pane-read barrier mapped to reassessment planning")
    blocked = module.plan_reassessment(
        reassess_prepared,
        reassess_bindings,
        verified,
        pane_read_results(
            module, reassess_bindings, failed_pane_id=roster.post_restart_pane_ids[0]
        ),
    )
    if blocked[module.STATUS_FIELD] != module.ResultStatus.COMMAND_FAILED:
        failures.append("failed pane read did not map to blocked reassessment")
    if blocked[module.DELIVERIES_FIELD]:
        failures.append("failed pane read mapped to partial continuation delivery")

    _, intact_session, restored = _continuation_plan(module, roster, fixture)
    reassessment = module.plan_reassessment(
        reassess_prepared, reassess_bindings, verified, reads, restored
    )
    reassessment_deliveries = cast(
        list[dict[str, object]], reassessment[module.DELIVERIES_FIELD]
    )
    if len(reassessment_deliveries) != len(restored):
        failures.append("supplied destroyed facts did not map one-to-one to deliveries")
    if cast(list[str], reassessment[module.NO_CONTINUATION_SESSION_IDS_FIELD]) != [
        intact_session
    ]:
        failures.append("a candidate without a destroyed fact did not map to intact")
    if any(
        delivery[module.SESSION_ID_FIELD] == intact_session
        for delivery in reassessment_deliveries
    ):
        failures.append("a judged-intact candidate mapped to a delivery")
    return failures


@dataclass(frozen=True)
class WhollyIntactSettlement:
    """Observations from planning and settling a recovery whose every pending candidate is judged intact."""

    planned_status: str
    reassessment_ready_status: str
    settled_status: str
    reassessment_sent_status: str
    deliveries: list[dict[str, object]]
    judged_intact_sessions: list[str]
    pending_sessions: list[str]
    recorded_sessions: list[str]


def observe_wholly_intact_settlement() -> WhollyIntactSettlement:
    """Plan and settle a verified recovery for which the controller supplies no destroyed fact."""
    module = _load()
    roster = OPERATIONAL_RECOVERY_ROSTER
    fixture = _verified_recovery(module, roster)
    continuation_sessions, _, _ = _continuation_plan(module, roster, fixture)
    planned = module.plan_reassessment(
        cast(dict[str, object], fixture["prepared"]),
        cast(list[dict[str, object]], fixture["bindings"]),
        cast(dict[str, object], fixture["verified"]),
        cast(list[dict[str, object]], fixture["reads"]),
        [],
    )
    settled = module.settle_recovery(planned, [])
    return WhollyIntactSettlement(
        planned_status=cast(str, planned[module.STATUS_FIELD]),
        reassessment_ready_status=module.ResultStatus.REASSESSMENT_READY,
        settled_status=cast(str, settled[module.STATUS_FIELD]),
        reassessment_sent_status=module.ResultStatus.REASSESSMENT_SENT,
        deliveries=cast(list[dict[str, object]], planned[module.DELIVERIES_FIELD]),
        judged_intact_sessions=cast(
            list[str], planned[module.NO_CONTINUATION_SESSION_IDS_FIELD]
        ),
        pending_sessions=sorted(continuation_sessions),
        recorded_sessions=cast(
            list[str],
            cast(dict[str, object], settled[module.PREPARED_FIELD])[
                module.REASSESSED_SESSION_IDS_FIELD
            ],
        ),
    )


@dataclass(frozen=True)
class AttestedControllerBinding:
    """Observations from planning and recovering while the controller attests its own pane."""

    ready_status: object
    pane_occupied_status: object
    already_correlated_status: object
    attested_pane_id: str
    unattested_activation_status: object
    attested_activation_status: object
    attested_bound_pane_ids: list[object]
    attested_controller_resolutions: list[object]


@dataclass(frozen=True)
class AttestedControllerRejections:
    """The status each attestation that fails to identify the controller candidate raises."""

    invalid_target_status: object
    absent_current_session_status: object
    absent_pane_status: object
    foreign_worktree_status: object
    multiple_agents_status: object
    foreign_agent_type_status: object
    foreign_session_status: object


def _attested_controller_fixture(
    module: ModuleType, roster: RecoveryRosterCase
) -> tuple[dict[str, object], list[dict[str, object]], list[dict[str, object]], str]:
    """A prepared recovery whose controller pane reports its agent type under no native session."""
    prepared = _prepared(module, roster)
    panes, agents = _post_restart_rosters(module, roster, len(roster.original_pane_ids))
    del agents[0][module.SESSION_FIELD]
    return prepared, panes, agents, roster.post_restart_pane_ids[0]


def observe_attested_controller_binding() -> AttestedControllerBinding:
    """Plan activation and recovery for a controller whose own pane reports no native session."""
    module = _load()
    roster = OPERATIONAL_RECOVERY_ROSTER
    prepared, panes, agents, attestation = _attested_controller_fixture(module, roster)
    controller_original_pane_id = roster.original_pane_ids[0]

    unattested = module.plan_activation(prepared, panes, agents)
    attested = module.plan_activation(prepared, panes, agents, attestation)
    attested_bindings = cast(list[dict[str, object]], attested[module.BINDINGS_FIELD])
    recovered = module.recover(prepared, attested_bindings, panes, agents, attestation)
    return AttestedControllerBinding(
        ready_status=module.ResultStatus.READY,
        pane_occupied_status=module.ResultStatus.PANE_OCCUPIED,
        already_correlated_status=module.Resolution.ALREADY_CORRELATED,
        attested_pane_id=attestation,
        unattested_activation_status=unattested[module.STATUS_FIELD],
        attested_activation_status=attested[module.STATUS_FIELD],
        attested_bound_pane_ids=[
            binding[module.PANE_ID_FIELD]
            for binding in attested_bindings
            if binding[module.ORIGINAL_PANE_ID_FIELD] == controller_original_pane_id
        ],
        attested_controller_resolutions=[
            target[module.STATUS_FIELD]
            for target in cast(list[dict[str, object]], recovered[module.TARGETS_FIELD])
            if target[module.ORIGINAL_PANE_ID_FIELD] == controller_original_pane_id
        ],
    )


def observe_attested_controller_rejections() -> AttestedControllerRejections:
    """Attest a pane that fails each way an attestation can fail to identify the controller."""
    module = _load()
    roster = OPERATIONAL_RECOVERY_ROSTER
    prepared, panes, agents, attestation = _attested_controller_fixture(module, roster)

    without_controller = deepcopy(prepared)
    cast(list[dict[str, object]], without_controller[module.CANDIDATES_FIELD])[0][
        module.EVIDENCE_FIELD
    ] = module.EvidenceSource.NATIVE_STATUS
    foreign_type_agents = deepcopy(agents)
    foreign_type_agents[0][module.TYPE_FIELD] = roster.agent_types[1]
    foreign_session_agents = deepcopy(agents)
    foreign_session_agents[0][module.SESSION_FIELD] = {
        module.ID_FIELD: roster.session_ids[1]
    }
    crowded_agents = [*agents, deepcopy(agents[0])]

    return AttestedControllerRejections(
        invalid_target_status=module.ResultStatus.INVALID_TARGET,
        absent_current_session_status=_error_status(
            module,
            lambda: module.plan_activation(
                without_controller, panes, agents, attestation
            ),
        ),
        absent_pane_status=_error_status(
            module,
            lambda: module.plan_activation(
                prepared, panes, agents, roster.unknown_pane_id
            ),
        ),
        foreign_worktree_status=_error_status(
            module,
            lambda: module.plan_activation(
                prepared, panes, agents, roster.post_restart_pane_ids[1]
            ),
        ),
        multiple_agents_status=_error_status(
            module,
            lambda: module.plan_activation(
                prepared, panes, crowded_agents, attestation
            ),
        ),
        foreign_agent_type_status=_error_status(
            module,
            lambda: module.plan_activation(
                prepared, panes, foreign_type_agents, attestation
            ),
        ),
        foreign_session_status=_error_status(
            module,
            lambda: module.plan_activation(
                prepared, panes, foreign_session_agents, attestation
            ),
        ),
    )


def verify_native_agent_recovery_properties() -> list[str]:
    module = _load()
    failures: list[str] = []

    @seed(RECOVERY_PROPERTY_SEED)
    @settings(max_examples=RECOVERY_PROPERTY_EXAMPLES, deadline=None, print_blob=True)
    @example(roster=OPERATIONAL_RECOVERY_ROSTER)
    @given(roster=roster_cases())
    def generated_idempotence(roster: RecoveryRosterCase) -> None:
        prepared = _prepared(module, roster)
        panes, agents = _post_restart_rosters(
            module, roster, len(roster.original_pane_ids)
        )
        activation = module.plan_activation(prepared, panes, agents)
        if activation[module.STATUS_FIELD] != module.ResultStatus.READY:
            failures.append("fully correlated restart did not map to ready")
        if activation[module.ACTIVATIONS_FIELD]:
            failures.append("fully correlated restart produced activation")
        recovery = module.recover(
            prepared,
            cast(list[dict[str, object]], activation[module.BINDINGS_FIELD]),
            panes,
            agents,
        )
        if recovery[module.STATUS_FIELD] != module.ResultStatus.ALREADY_CURRENT:
            failures.append("fully correlated recovery was not idempotent")
        if recovery[module.DELIVERIES_FIELD]:
            failures.append("idempotent recovery produced delivery")

    run_replayable_property(
        generated_idempotence,
        seed_value=RECOVERY_PROPERTY_SEED,
        replay_path=RECOVERY_PROPERTY_REPLAY_PATH,
    )

    @seed(RECOVERY_PROPERTY_SEED)
    @settings(max_examples=RECOVERY_PROPERTY_EXAMPLES, deadline=None, print_blob=True)
    @given(
        evidence=invalid_recovery_evidence(
            tuple(source.value for source in module.EvidenceSource)
        )
    )
    def generated_invalid_evidence(evidence: str) -> None:
        roster = OPERATIONAL_RECOVERY_ROSTER
        panes, agents = _pre_restart_rosters(module, roster)
        candidates = recovery_candidates(module, roster)
        correlations = identity_evidence(module, roster, roster.original_pane_ids)
        candidates[0][module.EVIDENCE_FIELD] = evidence
        correlations[0][module.SOURCE_FIELD] = evidence
        status = _error_status(
            module,
            lambda: module.prepare(
                roster.original_pane_ids,
                panes,
                agents,
                candidates,
                correlations,
            ),
        )
        if status != module.ResultStatus.INVALID_SCHEMA:
            failures.append("unsupported candidate evidence was accepted")

    run_replayable_property(
        generated_invalid_evidence,
        seed_value=RECOVERY_PROPERTY_SEED,
        replay_path=RECOVERY_PROPERTY_REPLAY_PATH,
    )
    return failures


def verify_native_agent_recovery_compliance() -> list[str]:
    module = _load()
    failures: list[str] = []
    roster = OPERATIONAL_RECOVERY_ROSTER
    prepared = _prepared(module, roster)
    panes, _ = _post_restart_rosters(module, roster, len(roster.original_pane_ids))
    bindings = _all_bindings(module, roster)
    plan = module.recover(prepared, bindings, panes, [])
    deliveries = cast(list[dict[str, object]], plan[module.DELIVERIES_FIELD])
    candidates_by_original = {
        candidate[module.ORIGINAL_PANE_ID_FIELD]: candidate
        for candidate in cast(
            list[dict[str, object]], prepared[module.CANDIDATES_FIELD]
        )
    }
    for delivery in deliveries:
        candidate = candidates_by_original[delivery[module.ORIGINAL_PANE_ID_FIELD]]
        expected = module.native_resume_command(
            module.prepared_candidate_from_item(candidate, "preparedCandidate")
        )
        if delivery[module.TEXT_FIELD] != expected:
            failures.append("recovery did not emit exact native resume command")
        if module.NON_CONTROLLER_BOUNDARY in cast(str, delivery[module.TEXT_FIELD]):
            failures.append("native launch transport included reassessment prose")
        if "--latest" in cast(str, delivery[module.TEXT_FIELD]):
            failures.append("recovery command used a latest-session selector")

    custom_candidates = recovery_candidates(module, roster)
    custom_candidates[0][module.RESUME_LOCATOR_FIELD] = (
        f"{roster.worktree_paths[0]}/{roster.session_ids[0]}.jsonl"
    )
    custom_candidates[1][module.NATIVE_HOME_FIELD] = str(
        roster.worktree_paths[1] / ".codex-home"
    )
    custom_prepared = module.prepare(
        roster.original_pane_ids,
        *_pre_restart_rosters(module, roster),
        custom_candidates,
        identity_evidence(module, roster, roster.original_pane_ids),
    )
    custom_values = cast(
        list[dict[str, object]], custom_prepared[module.CANDIDATES_FIELD]
    )
    claude_command = module.native_resume_command(
        module.prepared_candidate_from_item(custom_values[0], "claudeCandidate")
    )
    if (
        shlex.split(claude_command)[-1]
        != custom_candidates[0][module.RESUME_LOCATOR_FIELD]
    ):
        failures.append("Claude recovery ignored the prepared resume locator")
    codex_command = module.native_resume_command(
        module.prepared_candidate_from_item(custom_values[1], "codexCandidate")
    )
    if shlex.split(codex_command)[:2] != [
        "env",
        f"CODEX_HOME={custom_candidates[1][module.NATIVE_HOME_FIELD]}",
    ]:
        failures.append("Codex recovery ignored the prepared native home")

    successful_results = recovery_delivery_results(
        module,
        tuple(cast(str, delivery[module.PANE_ID_FIELD]) for delivery in deliveries),
    )
    settled = module.settle_recovery(plan, successful_results)
    if settled[module.STATUS_FIELD] != module.ResultStatus.RESUMED:
        failures.append("successful exact deliveries did not settle as resumed")
    unsubmitted_results = deepcopy(successful_results)
    unsubmitted_transport = cast(
        dict[str, object], unsubmitted_results[0][module.TRANSPORT_FIELD]
    )
    unsubmitted_response = cast(
        dict[str, object], unsubmitted_transport[module.RESPONSE_FIELD]
    )
    unsubmitted_data = cast(dict[str, object], unsubmitted_response[module.DATA_FIELD])
    unsubmitted_input = cast(dict[str, object], unsubmitted_data[module.INPUT_FIELD])
    unsubmitted_input[module.TRAILING_ENTER_SENT_FIELD] = False
    unsubmitted_status = _error_status(
        module,
        lambda: module.settle_recovery(plan, unsubmitted_results),
    )
    if unsubmitted_status != module.ResultStatus.INVALID_SCHEMA:
        failures.append("editor-prefilled recovery send settled as submitted")
    malformed_plan = {**plan, module.STATUS_FIELD: module.ResultStatus.INVALID_TARGET}
    malformed_status = _error_status(
        module, lambda: module.settle_recovery(malformed_plan, successful_results)
    )
    if malformed_status != module.ResultStatus.INVALID_SCHEMA:
        failures.append("settlement accepted a non-recovery plan status")

    fixture = _verified_recovery(module, roster)
    agents_without_sessions = cast(list[dict[str, object]], fixture["agents"])
    correlations = cast(list[dict[str, object]], fixture["correlations"])
    verified = cast(dict[str, object], fixture["verified"])
    if verified[module.STATUS_FIELD] != module.ResultStatus.VERIFIED:
        failures.append("exact process/native-status evidence did not verify")
    if verified[module.VERIFIED_FIELD] != len(roster.original_pane_ids):
        failures.append("verification count omitted prepared candidates")

    reads = cast(list[dict[str, object]], fixture["reads"])
    # The mapping lane proves the same two rejections as an input-output correspondence;
    # this lane proves the compliance rule that an incomplete barrier gates reassessment.
    if (
        _error_status(
            module,
            lambda: module.plan_reassessment(prepared, bindings, verified, reads[:-1]),
        )
        != module.ResultStatus.INVALID_SCHEMA
    ):
        failures.append("reassessment accepted an incomplete all-pane read barrier")
    blocked_reassessment = module.plan_reassessment(
        prepared,
        bindings,
        verified,
        pane_read_results(
            module, bindings, failed_pane_id=roster.post_restart_pane_ids[0]
        ),
    )
    if blocked_reassessment[module.STATUS_FIELD] != module.ResultStatus.COMMAND_FAILED:
        failures.append("failed pane read did not block reassessment")
    if blocked_reassessment[module.DELIVERIES_FIELD]:
        failures.append("failed pane read produced partial continuation delivery")
    _, _, restored = _continuation_plan(module, roster, fixture)
    reassessment = module.plan_reassessment(
        prepared, bindings, verified, reads, restored
    )
    reassessment_deliveries = cast(
        list[dict[str, object]], reassessment[module.DELIVERIES_FIELD]
    )
    if reassessment[module.STATUS_FIELD] != module.ResultStatus.REASSESSMENT_READY:
        failures.append("verified recovery did not prepare reassessment")
    if reassessment[module.PANE_READ_RESULTS_FIELD] != reads:
        failures.append("reassessment did not preserve the complete pane-read barrier")
    for delivery in reassessment_deliveries:
        if module.NON_CONTROLLER_BOUNDARY not in cast(str, delivery[module.TEXT_FIELD]):
            failures.append("separate reassessment delivery omitted its boundary")
        reassessment_words = shlex.split(cast(str, delivery[module.TEXT_FIELD]))
        if any(
            reassessment_words[: len(prefix)] == list(prefix)
            for prefix in module.NATIVE_RESUME_PREFIXES.values()
        ):
            failures.append("reassessment delivery included a native launch command")
    reassessment_results = recovery_delivery_results(
        module,
        tuple(
            cast(str, delivery[module.PANE_ID_FIELD])
            for delivery in reassessment_deliveries
        ),
    )
    reassessed = module.settle_recovery(reassessment, reassessment_results)
    if reassessed[module.STATUS_FIELD] != module.ResultStatus.REASSESSMENT_SENT:
        failures.append("checked reassessment transports did not settle")
    updated_prepared = reassessed[module.PREPARED_FIELD]
    repeated_reassessment = module.plan_reassessment(
        updated_prepared, bindings, verified, reads
    )
    if (
        repeated_reassessment[module.STATUS_FIELD]
        != module.ResultStatus.ALREADY_CURRENT
    ):
        failures.append("durably reassessed sessions were planned again")
    if repeated_reassessment[module.DELIVERIES_FIELD]:
        failures.append("repeated recovery emitted reassessment delivery")

    mismatched_correlations = deepcopy(correlations)
    mismatched_correlations[0][module.SESSION_ID_FIELD] = roster.session_ids[1]
    mismatched = module.verify(
        prepared,
        bindings,
        panes,
        agents_without_sessions,
        mismatched_correlations,
    )
    if mismatched[module.STATUS_FIELD] != module.ResultStatus.CORRELATION_INCOMPLETE:
        failures.append("mismatched process/native-status evidence verified")

    operator_correlations = deepcopy(correlations)
    operator_correlations[1][module.SOURCE_FIELD] = (
        module.EvidenceSource.OPERATOR_CONFIRMED
    )
    operator_verified = module.verify(
        prepared,
        bindings,
        panes,
        agents_without_sessions,
        operator_correlations,
    )
    if (
        operator_verified[module.STATUS_FIELD]
        != module.ResultStatus.CORRELATION_INCOMPLETE
    ):
        failures.append("operator-confirmed evidence verified a recovered session")

    extra_pane = _pane_item(
        module, Path("/unexpected/worktree"), roster.unknown_pane_id
    )
    extra_agent = _agent_item(
        module,
        Path("/unexpected/worktree"),
        roster.unknown_pane_id,
        "claude",
        "88888888-8888-4888-8888-888888888888",
    )
    extra = module.verify(
        prepared,
        bindings,
        [*panes, extra_pane],
        [*agents_without_sessions, extra_agent],
        correlations,
    )
    if extra[module.UNEXPECTED_AGENT_PANE_IDS_FIELD] != [roster.unknown_pane_id]:
        failures.append("verification did not reject an unprepared extra agent")

    first_candidate = cast(list[dict[str, object]], prepared[module.CANDIDATES_FIELD])[
        0
    ]
    verbatim = deepcopy(first_candidate)
    verbatim[module.WORKTREE_PATH_FIELD] = f"{roster.worktree_paths[0]}/"
    parsed = module.prepared_candidate_from_item(verbatim, "candidate")
    if parsed.worktree_path != verbatim[module.WORKTREE_PATH_FIELD]:
        failures.append("prepared worktree path was normalized")
    relative = deepcopy(first_candidate)
    relative[module.WORKTREE_PATH_FIELD] = "relative"
    relative_status = _error_status(
        module, lambda: module.prepared_candidate_from_item(relative, "candidate")
    )
    if relative_status != module.ResultStatus.INVALID_SCHEMA:
        failures.append("relative prepared worktree path was accepted")

    pre_panes, pre_agents = _pre_restart_rosters(module, roster)
    stdout = StringIO()
    exit_code = module.main(
        [
            module.Operation.PREPARE,
            *(value for pane in roster.original_pane_ids for value in ("--pane", pane)),
        ],
        stdin=StringIO(
            json.dumps(
                {
                    module.ITEMS_FIELD: pre_panes,
                    module.AGENTS_FIELD: pre_agents,
                    module.CANDIDATES_FIELD: recovery_candidates(module, roster),
                    module.CORRELATION_EVIDENCE_FIELD: identity_evidence(
                        module, roster, roster.original_pane_ids
                    ),
                }
            )
        ),
        stdout=stdout,
    )
    rendered = json.loads(stdout.getvalue())
    if exit_code != 0 or rendered[module.STATUS_FIELD] != module.ResultStatus.PREPARED:
        failures.append("prepare CLI did not emit a durable manifest")
    return failures
