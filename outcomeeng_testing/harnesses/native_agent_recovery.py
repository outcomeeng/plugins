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


@dataclass(frozen=True)
class IdempotentRecovery:
    """One generated roster's activation and recovery result when every candidate already correlates."""

    ready_status: object
    already_current_status: object
    activation_status: object
    activations: list[object]
    recovery_status: object
    deliveries: list[object]


@dataclass(frozen=True)
class UnsupportedEvidence:
    """The status preparation raises for one generated evidence value outside the source contract."""

    invalid_schema_status: object
    prepare_status: object


def _observe_idempotent_recovery(
    module: ModuleType, roster: RecoveryRosterCase
) -> IdempotentRecovery:
    prepared = _prepared(module, roster)
    panes, agents = _post_restart_rosters(module, roster, len(roster.original_pane_ids))
    activation = module.plan_activation(prepared, panes, agents)
    recovery = module.recover(
        prepared,
        cast(list[dict[str, object]], activation[module.BINDINGS_FIELD]),
        panes,
        agents,
    )
    return IdempotentRecovery(
        ready_status=module.ResultStatus.READY,
        already_current_status=module.ResultStatus.ALREADY_CURRENT,
        activation_status=activation[module.STATUS_FIELD],
        activations=cast(list[object], activation[module.ACTIVATIONS_FIELD]),
        recovery_status=recovery[module.STATUS_FIELD],
        deliveries=cast(list[object], recovery[module.DELIVERIES_FIELD]),
    )


def _observe_unsupported_evidence(
    module: ModuleType, evidence: str
) -> UnsupportedEvidence:
    roster = OPERATIONAL_RECOVERY_ROSTER
    panes, agents = _pre_restart_rosters(module, roster)
    candidates = recovery_candidates(module, roster)
    correlations = identity_evidence(module, roster, roster.original_pane_ids)
    candidates[0][module.EVIDENCE_FIELD] = evidence
    correlations[0][module.SOURCE_FIELD] = evidence
    return UnsupportedEvidence(
        invalid_schema_status=module.ResultStatus.INVALID_SCHEMA,
        prepare_status=_error_status(
            module,
            lambda: module.prepare(
                roster.original_pane_ids, panes, agents, candidates, correlations
            ),
        ),
    )


def drive_idempotent_recovery_property(
    check: Callable[[IdempotentRecovery], None],
) -> None:
    """Drive the repeated-recovery invariant over generated rosters under harness-owned replay settings."""
    module = _load()

    @seed(RECOVERY_PROPERTY_SEED)
    @settings(max_examples=RECOVERY_PROPERTY_EXAMPLES, deadline=None, print_blob=True)
    @example(roster=OPERATIONAL_RECOVERY_ROSTER)
    @given(roster=roster_cases())
    def property_case(roster: RecoveryRosterCase) -> None:
        check(_observe_idempotent_recovery(module, roster))

    run_replayable_property(
        property_case,
        seed_value=RECOVERY_PROPERTY_SEED,
        replay_path=RECOVERY_PROPERTY_REPLAY_PATH,
    )


def drive_unsupported_evidence_property(
    check: Callable[[UnsupportedEvidence], None],
) -> None:
    """Drive the evidence-contract invariant over generated values under harness-owned replay settings."""
    module = _load()

    @seed(RECOVERY_PROPERTY_SEED)
    @settings(max_examples=RECOVERY_PROPERTY_EXAMPLES, deadline=None, print_blob=True)
    @given(
        evidence=invalid_recovery_evidence(
            tuple(source.value for source in module.EvidenceSource)
        )
    )
    def property_case(evidence: str) -> None:
        check(_observe_unsupported_evidence(module, evidence))

    run_replayable_property(
        property_case,
        seed_value=RECOVERY_PROPERTY_SEED,
        replay_path=RECOVERY_PROPERTY_REPLAY_PATH,
    )


@dataclass(frozen=True)
class NativeLaunchTransport:
    """The native resume commands one recovery emits, beside the commands its manifest implies."""

    delivery_texts: list[str]
    expected_resume_commands: list[str]
    deliveries_carrying_boundary: list[str]
    deliveries_using_latest_selector: list[str]
    claude_command_tail: str
    prepared_claude_locator: object
    codex_command_head: list[str]
    expected_codex_head: list[str]


@dataclass(frozen=True)
class LaunchSettlement:
    """Settlement of native-launch deliveries under submitted, prefilled, and non-recovery plans."""

    resumed_status: object
    invalid_schema_status: object
    submitted_status: object
    prefilled_status: object
    non_recovery_plan_status: object


@dataclass(frozen=True)
class CorrelationVerification:
    """Verification of one recovery under exact, mismatched, operator-confirmed, and extra evidence."""

    verified_status: object
    correlation_incomplete_status: object
    exact_status: object
    verified_count: object
    candidate_count: int
    mismatched_status: object
    operator_confirmed_status: object
    unexpected_agent_pane_ids: object
    unprepared_pane_ids: list[str]


@dataclass(frozen=True)
class PaneReadBarrier:
    """Reassessment planning under an incomplete, failed, and complete stable-screen barrier."""

    invalid_schema_status: object
    command_failed_status: object
    reassessment_ready_status: object
    incomplete_barrier_status: object
    failed_read_status: object
    failed_read_deliveries: list[object]
    complete_barrier_status: object
    preserved_reads: object
    supplied_reads: list[dict[str, object]]


@dataclass(frozen=True)
class ContinuationBoundary:
    """Every emitted continuation instruction, checked for its boundary and for launch prose."""

    delivery_texts: list[str]
    boundary: str
    deliveries_missing_boundary: list[str]
    deliveries_carrying_launch_prefix: list[str]


@dataclass(frozen=True)
class ReassessmentSettlement:
    """Settling checked reassessment transports, then planning the same recovery again."""

    reassessment_sent_status: object
    already_current_status: object
    settled_status: object
    repeated_status: object
    repeated_deliveries: list[object]


@dataclass(frozen=True)
class PathIdentity:
    """A prepared worktree path parsed verbatim, and a relative path offered to the same parser."""

    supplied_worktree_path: object
    parsed_worktree_path: object
    invalid_schema_status: object
    relative_path_status: object


@dataclass(frozen=True)
class PrepareCommandLine:
    """The prepare CLI's exit code and rendered manifest status."""

    exit_code: int
    rendered_status: object
    prepared_status: object


def _compliance_fixture(
    module: ModuleType, roster: RecoveryRosterCase
) -> tuple[
    dict[str, object],
    list[dict[str, object]],
    list[dict[str, object]],
    dict[str, object],
    list[dict[str, object]],
]:
    """One prepared recovery, its panes and bindings, and the launch plan with its deliveries."""
    prepared = _prepared(module, roster)
    panes, _ = _post_restart_rosters(module, roster, len(roster.original_pane_ids))
    bindings = _all_bindings(module, roster)
    plan = cast(dict[str, object], module.recover(prepared, bindings, panes, []))
    deliveries = cast(list[dict[str, object]], plan[module.DELIVERIES_FIELD])
    return prepared, panes, bindings, plan, deliveries


def observe_native_launch_transport() -> NativeLaunchTransport:
    """Emit native launches for one recovery and derive each command from the prepared manifest."""
    module = _load()
    roster = OPERATIONAL_RECOVERY_ROSTER
    prepared, _, _, _, deliveries = _compliance_fixture(module, roster)
    candidates_by_original = {
        candidate[module.ORIGINAL_PANE_ID_FIELD]: candidate
        for candidate in cast(
            list[dict[str, object]], prepared[module.CANDIDATES_FIELD]
        )
    }
    texts = [cast(str, delivery[module.TEXT_FIELD]) for delivery in deliveries]

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
    codex_command = module.native_resume_command(
        module.prepared_candidate_from_item(custom_values[1], "codexCandidate")
    )
    return NativeLaunchTransport(
        delivery_texts=texts,
        expected_resume_commands=[
            module.native_resume_command(
                module.prepared_candidate_from_item(
                    candidates_by_original[delivery[module.ORIGINAL_PANE_ID_FIELD]],
                    "preparedCandidate",
                )
            )
            for delivery in deliveries
        ],
        deliveries_carrying_boundary=[
            text for text in texts if module.NON_CONTROLLER_BOUNDARY in text
        ],
        deliveries_using_latest_selector=[text for text in texts if "--latest" in text],
        claude_command_tail=shlex.split(claude_command)[-1],
        prepared_claude_locator=custom_candidates[0][module.RESUME_LOCATOR_FIELD],
        codex_command_head=shlex.split(codex_command)[:2],
        expected_codex_head=[
            "env",
            f"CODEX_HOME={custom_candidates[1][module.NATIVE_HOME_FIELD]}",
        ],
    )


def observe_launch_settlement() -> LaunchSettlement:
    """Settle native-launch deliveries submitted, left in the editor, and under a non-recovery plan."""
    module = _load()
    roster = OPERATIONAL_RECOVERY_ROSTER
    _, _, _, plan, deliveries = _compliance_fixture(module, roster)
    submitted_results = recovery_delivery_results(
        module,
        tuple(cast(str, delivery[module.PANE_ID_FIELD]) for delivery in deliveries),
    )
    prefilled_results = deepcopy(submitted_results)
    prefilled_transport = cast(
        dict[str, object], prefilled_results[0][module.TRANSPORT_FIELD]
    )
    prefilled_response = cast(
        dict[str, object], prefilled_transport[module.RESPONSE_FIELD]
    )
    prefilled_data = cast(dict[str, object], prefilled_response[module.DATA_FIELD])
    prefilled_input = cast(dict[str, object], prefilled_data[module.INPUT_FIELD])
    prefilled_input[module.TRAILING_ENTER_SENT_FIELD] = False
    non_recovery_plan = {
        **plan,
        module.STATUS_FIELD: module.ResultStatus.INVALID_TARGET,
    }
    return LaunchSettlement(
        resumed_status=module.ResultStatus.RESUMED,
        invalid_schema_status=module.ResultStatus.INVALID_SCHEMA,
        submitted_status=cast(
            dict[str, object], module.settle_recovery(plan, submitted_results)
        )[module.STATUS_FIELD],
        prefilled_status=_error_status(
            module, lambda: module.settle_recovery(plan, prefilled_results)
        ),
        non_recovery_plan_status=_error_status(
            module,
            lambda: module.settle_recovery(non_recovery_plan, submitted_results),
        ),
    )


def observe_correlation_verification() -> CorrelationVerification:
    """Verify one recovery under exact, mismatched, operator-confirmed, and unprepared evidence."""
    module = _load()
    roster = OPERATIONAL_RECOVERY_ROSTER
    fixture = _verified_recovery(module, roster)
    prepared = cast(dict[str, object], fixture["prepared"])
    bindings = cast(list[dict[str, object]], fixture["bindings"])
    panes = cast(list[dict[str, object]], fixture["panes"])
    agents = cast(list[dict[str, object]], fixture["agents"])
    correlations = cast(list[dict[str, object]], fixture["correlations"])
    verified = cast(dict[str, object], fixture["verified"])

    mismatched_correlations = deepcopy(correlations)
    mismatched_correlations[0][module.SESSION_ID_FIELD] = roster.session_ids[1]
    operator_correlations = deepcopy(correlations)
    operator_correlations[1][module.SOURCE_FIELD] = (
        module.EvidenceSource.OPERATOR_CONFIRMED
    )
    unexpected_worktree = Path("/unexpected/worktree")
    extra = module.verify(
        prepared,
        bindings,
        [*panes, _pane_item(module, unexpected_worktree, roster.unknown_pane_id)],
        [
            *agents,
            _agent_item(
                module,
                unexpected_worktree,
                roster.unknown_pane_id,
                "claude",
                "88888888-8888-4888-8888-888888888888",
            ),
        ],
        correlations,
    )
    return CorrelationVerification(
        verified_status=module.ResultStatus.VERIFIED,
        correlation_incomplete_status=module.ResultStatus.CORRELATION_INCOMPLETE,
        exact_status=verified[module.STATUS_FIELD],
        verified_count=verified[module.VERIFIED_FIELD],
        candidate_count=len(roster.original_pane_ids),
        mismatched_status=cast(
            dict[str, object],
            module.verify(prepared, bindings, panes, agents, mismatched_correlations),
        )[module.STATUS_FIELD],
        operator_confirmed_status=cast(
            dict[str, object],
            module.verify(prepared, bindings, panes, agents, operator_correlations),
        )[module.STATUS_FIELD],
        unexpected_agent_pane_ids=extra[module.UNEXPECTED_AGENT_PANE_IDS_FIELD],
        unprepared_pane_ids=[roster.unknown_pane_id],
    )


def observe_pane_read_barrier() -> PaneReadBarrier:
    """Plan reassessment under an incomplete, a failed, and a complete stable-screen barrier."""
    module = _load()
    roster = OPERATIONAL_RECOVERY_ROSTER
    fixture = _verified_recovery(module, roster)
    prepared = cast(dict[str, object], fixture["prepared"])
    bindings = cast(list[dict[str, object]], fixture["bindings"])
    verified = cast(dict[str, object], fixture["verified"])
    reads = cast(list[dict[str, object]], fixture["reads"])
    _, _, restored = _continuation_plan(module, roster, fixture)
    failed = cast(
        dict[str, object],
        module.plan_reassessment(
            prepared,
            bindings,
            verified,
            pane_read_results(
                module, bindings, failed_pane_id=roster.post_restart_pane_ids[0]
            ),
        ),
    )
    complete = cast(
        dict[str, object],
        module.plan_reassessment(prepared, bindings, verified, reads, restored),
    )
    return PaneReadBarrier(
        invalid_schema_status=module.ResultStatus.INVALID_SCHEMA,
        command_failed_status=module.ResultStatus.COMMAND_FAILED,
        reassessment_ready_status=module.ResultStatus.REASSESSMENT_READY,
        incomplete_barrier_status=_error_status(
            module,
            lambda: module.plan_reassessment(prepared, bindings, verified, reads[:-1]),
        ),
        failed_read_status=failed[module.STATUS_FIELD],
        failed_read_deliveries=cast(list[object], failed[module.DELIVERIES_FIELD]),
        complete_barrier_status=complete[module.STATUS_FIELD],
        preserved_reads=complete[module.PANE_READ_RESULTS_FIELD],
        supplied_reads=reads,
    )


def observe_continuation_boundary() -> ContinuationBoundary:
    """Every continuation instruction one verified recovery emits."""
    module = _load()
    roster = OPERATIONAL_RECOVERY_ROSTER
    fixture = _verified_recovery(module, roster)
    _, _, restored = _continuation_plan(module, roster, fixture)
    reassessment = cast(
        dict[str, object],
        module.plan_reassessment(
            cast(dict[str, object], fixture["prepared"]),
            cast(list[dict[str, object]], fixture["bindings"]),
            cast(dict[str, object], fixture["verified"]),
            cast(list[dict[str, object]], fixture["reads"]),
            restored,
        ),
    )
    texts = [
        cast(str, delivery[module.TEXT_FIELD])
        for delivery in cast(
            list[dict[str, object]], reassessment[module.DELIVERIES_FIELD]
        )
    ]
    return ContinuationBoundary(
        delivery_texts=texts,
        boundary=module.NON_CONTROLLER_BOUNDARY,
        deliveries_missing_boundary=[
            text for text in texts if module.NON_CONTROLLER_BOUNDARY not in text
        ],
        deliveries_carrying_launch_prefix=[
            text
            for text in texts
            if any(
                shlex.split(text)[: len(prefix)] == list(prefix)
                for prefix in module.NATIVE_RESUME_PREFIXES.values()
            )
        ],
    )


def observe_reassessment_settlement() -> ReassessmentSettlement:
    """Settle checked reassessment transports, then plan the same recovery from the updated manifest."""
    module = _load()
    roster = OPERATIONAL_RECOVERY_ROSTER
    fixture = _verified_recovery(module, roster)
    prepared = cast(dict[str, object], fixture["prepared"])
    bindings = cast(list[dict[str, object]], fixture["bindings"])
    verified = cast(dict[str, object], fixture["verified"])
    reads = cast(list[dict[str, object]], fixture["reads"])
    _, _, restored = _continuation_plan(module, roster, fixture)
    reassessment = cast(
        dict[str, object],
        module.plan_reassessment(prepared, bindings, verified, reads, restored),
    )
    settled = cast(
        dict[str, object],
        module.settle_recovery(
            reassessment,
            recovery_delivery_results(
                module,
                tuple(
                    cast(str, delivery[module.PANE_ID_FIELD])
                    for delivery in cast(
                        list[dict[str, object]],
                        reassessment[module.DELIVERIES_FIELD],
                    )
                ),
            ),
        ),
    )
    repeated = cast(
        dict[str, object],
        module.plan_reassessment(
            settled[module.PREPARED_FIELD], bindings, verified, reads
        ),
    )
    return ReassessmentSettlement(
        reassessment_sent_status=module.ResultStatus.REASSESSMENT_SENT,
        already_current_status=module.ResultStatus.ALREADY_CURRENT,
        settled_status=settled[module.STATUS_FIELD],
        repeated_status=repeated[module.STATUS_FIELD],
        repeated_deliveries=cast(list[object], repeated[module.DELIVERIES_FIELD]),
    )


def observe_path_identity() -> PathIdentity:
    """Parse a prepared candidate carrying a trailing-slash path, and one carrying a relative path."""
    module = _load()
    roster = OPERATIONAL_RECOVERY_ROSTER
    first_candidate = cast(
        list[dict[str, object]], _prepared(module, roster)[module.CANDIDATES_FIELD]
    )[0]
    verbatim = deepcopy(first_candidate)
    verbatim[module.WORKTREE_PATH_FIELD] = f"{roster.worktree_paths[0]}/"
    relative = deepcopy(first_candidate)
    relative[module.WORKTREE_PATH_FIELD] = "relative"
    return PathIdentity(
        supplied_worktree_path=verbatim[module.WORKTREE_PATH_FIELD],
        parsed_worktree_path=module.prepared_candidate_from_item(
            verbatim, "candidate"
        ).worktree_path,
        invalid_schema_status=module.ResultStatus.INVALID_SCHEMA,
        relative_path_status=_error_status(
            module,
            lambda: module.prepared_candidate_from_item(relative, "candidate"),
        ),
    )


def observe_prepare_command_line() -> PrepareCommandLine:
    """Drive the prepare CLI over the pre-restart rosters and read its rendered manifest."""
    module = _load()
    roster = OPERATIONAL_RECOVERY_ROSTER
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
    return PrepareCommandLine(
        exit_code=cast(int, exit_code),
        rendered_status=json.loads(stdout.getvalue())[module.STATUS_FIELD],
        prepared_status=module.ResultStatus.PREPARED,
    )
