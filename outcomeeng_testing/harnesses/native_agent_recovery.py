"""Test infrastructure for two-phase native-agent recovery."""

from __future__ import annotations

import importlib.util
import json
import sys
from collections.abc import Callable
from copy import deepcopy
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
) -> list[dict[str, str]]:
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
    agents[0][module.STATUS_FIELD] = module.DONE_STATUS
    stale_status = _error_status(
        module,
        lambda: module.prepare(
            roster.original_pane_ids, panes, agents, candidates, evidence
        ),
    )
    if stale_status != module.ResultStatus.INVALID_TARGET:
        failures.append("done pre-restart agent was prepared")

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
    return failures


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
        if "--latest" in cast(str, delivery[module.TEXT_FIELD]):
            failures.append("recovery command used a latest-session selector")

    successful_results = recovery_delivery_results(
        module,
        tuple(cast(str, delivery[module.PANE_ID_FIELD]) for delivery in deliveries),
    )
    settled = module.settle_recovery(plan, successful_results)
    if settled[module.STATUS_FIELD] != module.ResultStatus.RESUMED:
        failures.append("successful exact deliveries did not settle as resumed")
    malformed_plan = {**plan, module.STATUS_FIELD: module.ResultStatus.INVALID_TARGET}
    malformed_status = _error_status(
        module, lambda: module.settle_recovery(malformed_plan, successful_results)
    )
    if malformed_status != module.ResultStatus.INVALID_SCHEMA:
        failures.append("settlement accepted a non-recovery plan status")

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
    verified = module.verify(
        prepared,
        bindings,
        panes,
        agents_without_sessions,
        correlations,
    )
    if verified[module.STATUS_FIELD] != module.ResultStatus.VERIFIED:
        failures.append("exact process/native-status evidence did not verify")
    if verified[module.VERIFIED_FIELD] != len(roster.original_pane_ids):
        failures.append("verification count omitted prepared candidates")

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
