#!/usr/bin/env python3
"""Prepare, activate, launch, settle, and verify exact native-session recovery."""

from __future__ import annotations

import argparse
import json
import os
import shlex
import sys
from dataclasses import dataclass
from enum import StrEnum
from typing import TextIO, cast

SCHEMA_VERSION = 4
TRANSPORT_SCHEMA_VERSION = 1
TRANSPORT_SUCCEEDED_STATUS = "succeeded"
TRANSPORT_COMMAND_FAILED_STATUS = "command-failed"
TRANSPORT_SEND_OPERATION = "send"
ACTIVATION_OPEN_OPERATION = "open"
ACTIVATION_TAB_CREATE_OPERATION = "tab-create"
DONE_STATUS = "done"

RECOVERY_REASSESSMENT_PROMPT = (
    "Recovery check: Prowl restored this pane with the expected native session "
    "identity. Before acting, inspect the prior conversation and authoritative "
    "current repository and SPX state. Continue only when concrete unfinished work "
    "remains and continuation is still authorized. If the prior workflow completed, "
    "the session was deliberately stopped, or continuation is unclear, exit now "
    "without modifying files or starting background work. Do not remain active "
    "merely because recovery resumed the session."
)

SCHEMA_VERSION_FIELD = "schemaVersion"
ITEMS_FIELD = "items"
AGENTS_FIELD = "agents"
CANDIDATES_FIELD = "candidates"
CORRELATION_EVIDENCE_FIELD = "correlationEvidence"
ACTIVATION_RESULTS_FIELD = "activationResults"
DELIVERY_RESULTS_FIELD = "deliveryResults"
PLAN_FIELD = "plan"
PREPARED_FIELD = "prepared"
BINDINGS_FIELD = "bindings"
ACTIVATIONS_FIELD = "activations"
TARGETS_FIELD = "targets"
DELIVERIES_FIELD = "deliveries"
CORRELATIONS_FIELD = "correlations"
WORKTREE_FIELD = "worktree"
PANE_FIELD = "pane"
SESSION_FIELD = "session"
ID_FIELD = "id"
PATH_FIELD = "path"
ROOT_PATH_FIELD = "root_path"
CWD_FIELD = "cwd"
TYPE_FIELD = "type"
STATUS_FIELD = "status"
DETAIL_FIELD = "detail"
PANE_ID_FIELD = "paneId"
ORIGINAL_PANE_ID_FIELD = "originalPaneId"
WORKTREE_ID_FIELD = "worktreeId"
WORKTREE_PATH_FIELD = "worktreePath"
REPOSITORY_ROOT_FIELD = "repositoryRoot"
SESSION_ID_FIELD = "sessionId"
AGENT_TYPE_FIELD = "agentType"
EVIDENCE_FIELD = "evidence"
SOURCE_FIELD = "source"
ROLE_FIELD = "role"
SECONDARY_AUTHORIZED_FIELD = "secondaryAuthorized"
OPERATION_FIELD = "operation"
TEXT_FIELD = "text"
TRANSPORT_FIELD = "transport"
COMMAND_EXIT_CODE_FIELD = "commandExitCode"
RESPONSE_FIELD = "response"
DELIVERED_FIELD = "delivered"
VERIFIED_FIELD = "verified"
MISSING_PANE_IDS_FIELD = "missingPaneIds"
DUPLICATE_PANE_IDS_FIELD = "duplicatePaneIds"
UNEXPECTED_AGENT_PANE_IDS_FIELD = "unexpectedAgentPaneIds"


class Operation(StrEnum):
    PREPARE = "prepare"
    ACTIVATE = "activate"
    BIND = "bind"
    RECOVER = "recover"
    SETTLE = "settle"
    VERIFY = "verify"


class ResultStatus(StrEnum):
    PREPARED = "prepared"
    ACTIVATION_REQUIRED = "activation-required"
    READY = "ready"
    RESUMED = "resumed"
    ALREADY_CURRENT = "already-current"
    VERIFIED = "verified"
    INVALID_TARGET = "invalid-target"
    PANE_OCCUPIED = "pane-occupied"
    CORRELATION_INCOMPLETE = "correlation-incomplete"
    INVALID_SCHEMA = "invalid-schema"
    COMMAND_FAILED = "command-failed"


class Resolution(StrEnum):
    RESUMED = "resumed"
    ALREADY_CORRELATED = "already-correlated"


class AgentType(StrEnum):
    CLAUDE = "claude"
    CODEX = "codex"
    PI = "pi"


class EvidenceSource(StrEnum):
    PROCESS_ARGUMENT = "process-argument"
    OPEN_SESSION_FILE = "open-session-file"
    NATIVE_STATUS = "native-status"
    CURRENT_SESSION = "current-session"
    PUBLIC_AGENT = "public-agent"
    OPERATOR_CONFIRMED = "operator-confirmed"


class RecoveryRole(StrEnum):
    PRIMARY = "primary"
    SECONDARY = "secondary"


NATIVE_RESUME_PREFIXES: dict[AgentType, tuple[str, ...]] = {
    AgentType.CLAUDE: ("claude", "--resume"),
    AgentType.CODEX: ("codex", "resume"),
    AgentType.PI: ("pi", "--session"),
}


class AdapterError(RuntimeError):
    def __init__(self, status: ResultStatus, message: str) -> None:
        super().__init__(message)
        self.status = status


@dataclass(frozen=True)
class PaneIdentity:
    pane_id: str
    worktree_id: str
    worktree_path: str
    repository_root: str
    cwd: str


@dataclass(frozen=True)
class AgentIdentity:
    pane_id: str
    worktree_path: str
    agent_type: AgentType
    status: str
    session_id: str | None


@dataclass(frozen=True)
class PreparedCandidate:
    original_pane_id: str
    worktree_path: str
    session_id: str
    agent_type: AgentType
    evidence: EvidenceSource
    role: RecoveryRole
    secondary_authorized: bool

    def result(self) -> dict[str, object]:
        return {
            ORIGINAL_PANE_ID_FIELD: self.original_pane_id,
            WORKTREE_PATH_FIELD: self.worktree_path,
            SESSION_ID_FIELD: self.session_id,
            AGENT_TYPE_FIELD: self.agent_type,
            EVIDENCE_FIELD: self.evidence,
            ROLE_FIELD: self.role,
            SECONDARY_AUTHORIZED_FIELD: self.secondary_authorized,
        }


@dataclass(frozen=True)
class Binding:
    original_pane_id: str
    pane_id: str

    def result(self) -> dict[str, str]:
        return {
            ORIGINAL_PANE_ID_FIELD: self.original_pane_id,
            PANE_ID_FIELD: self.pane_id,
        }


@dataclass(frozen=True)
class IdentityEvidence:
    pane_id: str
    worktree_path: str
    session_id: str
    agent_type: AgentType
    source: EvidenceSource


@dataclass(frozen=True)
class CheckedTransport:
    operation: str
    exit_code: int | None
    response: dict[str, object] | None
    delivered: bool
    raw: dict[str, object]


def _object(value: object, location: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise AdapterError(
            ResultStatus.INVALID_SCHEMA, f"Expected an object at {location}."
        )
    return value


def _array(value: object, location: str) -> list[dict[str, object]]:
    if not isinstance(value, list):
        raise AdapterError(
            ResultStatus.INVALID_SCHEMA, f"Expected an array at {location}."
        )
    return [_object(item, f"{location}[{index}]") for index, item in enumerate(value)]


def _text(value: object, location: str) -> str:
    if not isinstance(value, str) or not value:
        raise AdapterError(
            ResultStatus.INVALID_SCHEMA,
            f"Expected a non-empty string at {location}.",
        )
    return value


def _boolean(value: object, location: str) -> bool:
    if not isinstance(value, bool):
        raise AdapterError(
            ResultStatus.INVALID_SCHEMA, f"Expected a boolean at {location}."
        )
    return value


def _absolute_path(value: object, location: str) -> str:
    path = _text(value, location)
    if not os.path.isabs(path):
        raise AdapterError(
            ResultStatus.INVALID_SCHEMA,
            f"Expected an absolute path at {location}; received {path!r}.",
        )
    return path


def _enum(enum_type: type[StrEnum], value: object, location: str) -> StrEnum:
    raw = _text(value, location)
    try:
        return enum_type(raw)
    except ValueError as error:
        valid = ", ".join(item.value for item in enum_type)
        raise AdapterError(
            ResultStatus.INVALID_SCHEMA,
            f"Unsupported {location} {raw!r}; expected one of: {valid}.",
        ) from error


def _pane_identity(item: dict[str, object], location: str) -> PaneIdentity:
    pane = _object(item.get(PANE_FIELD), f"{location}.pane")
    worktree = _object(item.get(WORKTREE_FIELD), f"{location}.worktree")
    return PaneIdentity(
        pane_id=_text(pane.get(ID_FIELD), f"{location}.pane.id"),
        worktree_id=_text(worktree.get(ID_FIELD), f"{location}.worktree.id"),
        worktree_path=_absolute_path(
            worktree.get(PATH_FIELD), f"{location}.worktree.path"
        ),
        repository_root=_absolute_path(
            worktree.get(ROOT_PATH_FIELD), f"{location}.worktree.root_path"
        ),
        cwd=_absolute_path(pane.get(CWD_FIELD), f"{location}.pane.cwd"),
    )


def _agent_identity(item: dict[str, object], location: str) -> AgentIdentity:
    pane = _object(item.get(PANE_FIELD), f"{location}.pane")
    worktree = _object(item.get(WORKTREE_FIELD), f"{location}.worktree")
    session_value = item.get(SESSION_FIELD)
    session_id = None
    if session_value is not None:
        session_id = _text(
            _object(session_value, f"{location}.session").get(ID_FIELD),
            f"{location}.session.id",
        )
    return AgentIdentity(
        pane_id=_text(pane.get(ID_FIELD), f"{location}.pane.id"),
        worktree_path=_absolute_path(
            worktree.get(PATH_FIELD), f"{location}.worktree.path"
        ),
        agent_type=cast(
            AgentType, _enum(AgentType, item.get(TYPE_FIELD), f"{location}.type")
        ),
        status=_text(item.get(STATUS_FIELD), f"{location}.status"),
        session_id=session_id,
    )


def _candidate_from_item(item: dict[str, object], location: str) -> PreparedCandidate:
    return PreparedCandidate(
        original_pane_id=_text(item.get(PANE_ID_FIELD), f"{location}.paneId"),
        worktree_path=_absolute_path(
            item.get(WORKTREE_PATH_FIELD), f"{location}.worktreePath"
        ),
        session_id=_text(item.get(SESSION_ID_FIELD), f"{location}.sessionId"),
        agent_type=cast(
            AgentType,
            _enum(AgentType, item.get(AGENT_TYPE_FIELD), f"{location}.agentType"),
        ),
        evidence=cast(
            EvidenceSource,
            _enum(EvidenceSource, item.get(EVIDENCE_FIELD), f"{location}.evidence"),
        ),
        role=cast(
            RecoveryRole,
            _enum(RecoveryRole, item.get(ROLE_FIELD), f"{location}.role"),
        ),
        secondary_authorized=_boolean(
            item.get(SECONDARY_AUTHORIZED_FIELD),
            f"{location}.secondaryAuthorized",
        ),
    )


def prepared_candidate_from_item(
    item: dict[str, object], location: str
) -> PreparedCandidate:
    return PreparedCandidate(
        original_pane_id=_text(
            item.get(ORIGINAL_PANE_ID_FIELD), f"{location}.originalPaneId"
        ),
        worktree_path=_absolute_path(
            item.get(WORKTREE_PATH_FIELD), f"{location}.worktreePath"
        ),
        session_id=_text(item.get(SESSION_ID_FIELD), f"{location}.sessionId"),
        agent_type=cast(
            AgentType,
            _enum(AgentType, item.get(AGENT_TYPE_FIELD), f"{location}.agentType"),
        ),
        evidence=cast(
            EvidenceSource,
            _enum(EvidenceSource, item.get(EVIDENCE_FIELD), f"{location}.evidence"),
        ),
        role=cast(
            RecoveryRole,
            _enum(RecoveryRole, item.get(ROLE_FIELD), f"{location}.role"),
        ),
        secondary_authorized=_boolean(
            item.get(SECONDARY_AUTHORIZED_FIELD),
            f"{location}.secondaryAuthorized",
        ),
    )


def _evidence_from_item(item: dict[str, object], location: str) -> IdentityEvidence:
    return IdentityEvidence(
        pane_id=_text(item.get(PANE_ID_FIELD), f"{location}.paneId"),
        worktree_path=_absolute_path(
            item.get(WORKTREE_PATH_FIELD), f"{location}.worktreePath"
        ),
        session_id=_text(item.get(SESSION_ID_FIELD), f"{location}.sessionId"),
        agent_type=cast(
            AgentType,
            _enum(AgentType, item.get(AGENT_TYPE_FIELD), f"{location}.agentType"),
        ),
        source=cast(
            EvidenceSource,
            _enum(EvidenceSource, item.get(SOURCE_FIELD), f"{location}.source"),
        ),
    )


def _binding_from_item(item: dict[str, object], location: str) -> Binding:
    return Binding(
        original_pane_id=_text(
            item.get(ORIGINAL_PANE_ID_FIELD), f"{location}.originalPaneId"
        ),
        pane_id=_text(item.get(PANE_ID_FIELD), f"{location}.paneId"),
    )


def _pane_roster(items: list[dict[str, object]]) -> dict[str, PaneIdentity]:
    roster: dict[str, PaneIdentity] = {}
    for index, item in enumerate(items):
        pane = _pane_identity(item, f"items[{index}]")
        if pane.pane_id in roster:
            raise AdapterError(
                ResultStatus.INVALID_SCHEMA,
                f"Public evidence returned duplicate pane identity: {pane.pane_id}.",
            )
        roster[pane.pane_id] = pane
    return roster


def _agent_roster(items: list[dict[str, object]]) -> dict[str, list[AgentIdentity]]:
    roster: dict[str, list[AgentIdentity]] = {}
    for index, item in enumerate(items):
        agent = _agent_identity(item, f"agents[{index}]")
        roster.setdefault(agent.pane_id, []).append(agent)
    return roster


def _validate_candidate_set(candidates: list[PreparedCandidate]) -> None:
    pane_ids = [candidate.original_pane_id for candidate in candidates]
    session_ids = [candidate.session_id for candidate in candidates]
    if len(pane_ids) != len(set(pane_ids)):
        raise AdapterError(
            ResultStatus.INVALID_TARGET,
            "Recovery candidates contain duplicate original pane identities.",
        )
    if len(session_ids) != len(set(session_ids)):
        raise AdapterError(
            ResultStatus.INVALID_TARGET,
            "Recovery candidates contain duplicate native session identities.",
        )
    by_worktree: dict[str, list[PreparedCandidate]] = {}
    for candidate in candidates:
        by_worktree.setdefault(candidate.worktree_path, []).append(candidate)
    for worktree_path, group in by_worktree.items():
        if len(group) == 1:
            continue
        primaries = [item for item in group if item.role is RecoveryRole.PRIMARY]
        secondaries = [item for item in group if item.role is RecoveryRole.SECONDARY]
        if len(primaries) != 1 or len(secondaries) != len(group) - 1:
            raise AdapterError(
                ResultStatus.INVALID_TARGET,
                f"Worktree {worktree_path} requires exactly one primary candidate.",
            )
        if any(not item.secondary_authorized for item in secondaries):
            raise AdapterError(
                ResultStatus.INVALID_TARGET,
                f"Worktree {worktree_path} contains an unauthorized secondary candidate.",
            )


def _prepared_candidates(prepared: object) -> list[PreparedCandidate]:
    value = _object(prepared, PREPARED_FIELD)
    if value.get(SCHEMA_VERSION_FIELD) != SCHEMA_VERSION:
        raise AdapterError(
            ResultStatus.INVALID_SCHEMA,
            f"Prepared manifest schema version must be {SCHEMA_VERSION}.",
        )
    if value.get(STATUS_FIELD) != ResultStatus.PREPARED:
        raise AdapterError(
            ResultStatus.INVALID_SCHEMA,
            "Prepared manifest status must be prepared.",
        )
    candidates = [
        prepared_candidate_from_item(item, f"prepared.candidates[{index}]")
        for index, item in enumerate(
            _array(value.get(CANDIDATES_FIELD), "prepared.candidates")
        )
    ]
    _validate_candidate_set(candidates)
    return candidates


def _validated_bindings(
    binding_items: object, candidates: list[PreparedCandidate]
) -> list[Binding]:
    bindings = [
        _binding_from_item(item, f"bindings[{index}]")
        for index, item in enumerate(_array(binding_items, BINDINGS_FIELD))
    ]
    originals = [binding.original_pane_id for binding in bindings]
    panes = [binding.pane_id for binding in bindings]
    expected = [candidate.original_pane_id for candidate in candidates]
    if set(originals) != set(expected) or len(originals) != len(expected):
        raise AdapterError(
            ResultStatus.INVALID_TARGET,
            "Bindings must identify every prepared original pane exactly once.",
        )
    if len(panes) != len(set(panes)):
        raise AdapterError(
            ResultStatus.INVALID_TARGET,
            "Bindings must carry distinct post-restart pane identities.",
        )
    by_original = {binding.original_pane_id: binding for binding in bindings}
    return [by_original[original] for original in expected]


def _selected(values: tuple[str, ...]) -> tuple[str, ...]:
    if not values or len(values) != len(set(values)):
        raise AdapterError(
            ResultStatus.INVALID_TARGET,
            "Preparation requires one or more distinct original pane identities.",
        )
    return tuple(_text(value, "selected pane identity") for value in values)


def prepare(
    selected_pane_ids: tuple[str, ...],
    pane_items: list[dict[str, object]],
    agent_items: list[dict[str, object]],
    candidate_items: list[dict[str, object]],
    evidence_items: list[dict[str, object]],
) -> dict[str, object]:
    selected = _selected(selected_pane_ids)
    panes = _pane_roster(pane_items)
    agents = _agent_roster(agent_items)
    candidates = [
        _candidate_from_item(item, f"candidates[{index}]")
        for index, item in enumerate(candidate_items)
    ]
    _validate_candidate_set(candidates)
    if {candidate.original_pane_id for candidate in candidates} != set(selected):
        raise AdapterError(
            ResultStatus.INVALID_TARGET,
            "Candidates must identify every selected pre-restart pane exactly once.",
        )
    evidence = [
        _evidence_from_item(item, f"correlationEvidence[{index}]")
        for index, item in enumerate(evidence_items)
    ]
    if len(evidence) != len(selected) or {item.pane_id for item in evidence} != set(
        selected
    ):
        raise AdapterError(
            ResultStatus.INVALID_TARGET,
            "Identity evidence must identify every selected pre-restart pane exactly once.",
        )
    candidates_by_pane = {item.original_pane_id: item for item in candidates}
    evidence_by_pane = {item.pane_id: item for item in evidence}
    for pane_id in selected:
        candidate = candidates_by_pane[pane_id]
        pane = panes.get(pane_id)
        if pane is None or pane.worktree_path != candidate.worktree_path:
            raise AdapterError(
                ResultStatus.INVALID_TARGET,
                f"Candidate {pane_id} does not match one pre-restart pane and worktree.",
            )
        matches = agents.get(pane_id, [])
        if len(matches) != 1:
            raise AdapterError(
                ResultStatus.INVALID_TARGET,
                f"Candidate {pane_id} requires one live pre-restart agent.",
            )
        agent = matches[0]
        if (
            agent.status == DONE_STATUS
            or agent.worktree_path != candidate.worktree_path
            or agent.agent_type is not candidate.agent_type
            or (
                agent.session_id is not None
                and agent.session_id != candidate.session_id
            )
        ):
            raise AdapterError(
                ResultStatus.INVALID_TARGET,
                f"Candidate {pane_id} does not match the live pre-restart agent identity.",
            )
        identity = evidence_by_pane[pane_id]
        if (
            identity.worktree_path != candidate.worktree_path
            or identity.session_id != candidate.session_id
            or identity.agent_type is not candidate.agent_type
            or identity.source is not candidate.evidence
        ):
            raise AdapterError(
                ResultStatus.INVALID_TARGET,
                f"Candidate {pane_id} does not match its exact identity evidence.",
            )
        if (
            identity.source is EvidenceSource.PUBLIC_AGENT
            and agent.session_id != candidate.session_id
        ):
            raise AdapterError(
                ResultStatus.INVALID_TARGET,
                f"Candidate {pane_id} uses public-agent evidence without an exact public session.",
            )
    return {
        SCHEMA_VERSION_FIELD: SCHEMA_VERSION,
        STATUS_FIELD: ResultStatus.PREPARED,
        CANDIDATES_FIELD: [
            candidates_by_pane[pane_id].result() for pane_id in selected
        ],
    }


def plan_activation(
    prepared: object,
    pane_items: list[dict[str, object]],
    agent_items: list[dict[str, object]],
) -> dict[str, object]:
    candidates = _prepared_candidates(prepared)
    panes = _pane_roster(pane_items)
    agents = _agent_roster(agent_items)
    by_worktree: dict[str, list[PreparedCandidate]] = {}
    panes_by_worktree: dict[str, list[PaneIdentity]] = {}
    for candidate in candidates:
        by_worktree.setdefault(candidate.worktree_path, []).append(candidate)
    for pane in panes.values():
        panes_by_worktree.setdefault(pane.worktree_path, []).append(pane)

    bindings: list[Binding] = []
    activations: list[dict[str, object]] = []
    occupied: list[str] = []
    for worktree_path, group in by_worktree.items():
        remaining = sorted(
            group,
            key=lambda item: (
                item.role is RecoveryRole.SECONDARY,
                item.original_pane_id,
            ),
        )
        current = sorted(
            panes_by_worktree.get(worktree_path, []), key=lambda item: item.pane_id
        )
        unoccupied: list[PaneIdentity] = []
        for pane in current:
            matches = agents.get(pane.pane_id, [])
            if not matches:
                unoccupied.append(pane)
                continue
            if len(matches) != 1:
                occupied.append(pane.pane_id)
                continue
            agent = matches[0]
            exact = next(
                (
                    candidate
                    for candidate in remaining
                    if candidate.agent_type is agent.agent_type
                    and candidate.session_id == agent.session_id
                ),
                None,
            )
            if exact is None:
                occupied.append(pane.pane_id)
                continue
            bindings.append(Binding(exact.original_pane_id, pane.pane_id))
            remaining.remove(exact)
        if occupied:
            continue
        for pane, candidate in zip(unoccupied, remaining, strict=False):
            bindings.append(Binding(candidate.original_pane_id, pane.pane_id))
        remaining = remaining[len(unoccupied) :]
        for index, candidate in enumerate(remaining):
            operation = (
                ACTIVATION_OPEN_OPERATION
                if not current and index == 0
                else ACTIVATION_TAB_CREATE_OPERATION
            )
            activations.append(
                {
                    ORIGINAL_PANE_ID_FIELD: candidate.original_pane_id,
                    OPERATION_FIELD: operation,
                    WORKTREE_PATH_FIELD: candidate.worktree_path,
                }
            )
    if occupied:
        return {
            SCHEMA_VERSION_FIELD: SCHEMA_VERSION,
            STATUS_FIELD: ResultStatus.PANE_OCCUPIED,
            DETAIL_FIELD: "Post-restart worktrees contain mismatched or duplicate agents.",
            BINDINGS_FIELD: [],
            ACTIVATIONS_FIELD: [],
            "occupiedPaneIds": occupied,
        }
    return {
        SCHEMA_VERSION_FIELD: SCHEMA_VERSION,
        STATUS_FIELD: (
            ResultStatus.ACTIVATION_REQUIRED if activations else ResultStatus.READY
        ),
        BINDINGS_FIELD: [binding.result() for binding in bindings],
        ACTIVATIONS_FIELD: activations,
    }


def _checked_transport(value: object, expected_operation: str) -> CheckedTransport:
    transport = _object(value, TRANSPORT_FIELD)
    if transport.get(SCHEMA_VERSION_FIELD) != TRANSPORT_SCHEMA_VERSION:
        raise AdapterError(
            ResultStatus.INVALID_SCHEMA,
            f"Transport schema version must be {TRANSPORT_SCHEMA_VERSION}.",
        )
    operation = _text(transport.get(OPERATION_FIELD), "transport.operation")
    if operation != expected_operation:
        raise AdapterError(
            ResultStatus.INVALID_SCHEMA,
            f"Transport operation {operation!r} does not match {expected_operation!r}.",
        )
    status = _text(transport.get(STATUS_FIELD), "transport.status")
    exit_code = transport.get(COMMAND_EXIT_CODE_FIELD)
    if exit_code is not None and (
        not isinstance(exit_code, int) or isinstance(exit_code, bool)
    ):
        raise AdapterError(
            ResultStatus.INVALID_SCHEMA,
            "Transport commandExitCode must be an integer when present.",
        )
    if status == TRANSPORT_SUCCEEDED_STATUS:
        if exit_code != 0:
            raise AdapterError(
                ResultStatus.INVALID_SCHEMA,
                "Successful transport requires commandExitCode 0.",
            )
        response = _object(transport.get(RESPONSE_FIELD), "transport.response")
        return CheckedTransport(operation, exit_code, response, True, transport)
    _text(transport.get(DETAIL_FIELD), "transport.detail")
    return CheckedTransport(
        operation, cast(int | None, exit_code), None, False, transport
    )


def bind_activations(plan: object, result_items: object) -> dict[str, object]:
    value = _object(plan, PLAN_FIELD)
    if value.get(SCHEMA_VERSION_FIELD) != SCHEMA_VERSION or value.get(
        STATUS_FIELD
    ) not in {ResultStatus.ACTIVATION_REQUIRED, ResultStatus.READY}:
        raise AdapterError(
            ResultStatus.INVALID_SCHEMA,
            "Activation binding requires a schema-4 activation-required or ready plan.",
        )
    bindings = [
        _binding_from_item(item, f"plan.bindings[{index}]")
        for index, item in enumerate(_array(value.get(BINDINGS_FIELD), "plan.bindings"))
    ]
    activations = _array(value.get(ACTIVATIONS_FIELD), "plan.activations")
    results = _array(result_items, ACTIVATION_RESULTS_FIELD)
    if len(results) != len(activations):
        raise AdapterError(
            ResultStatus.INVALID_SCHEMA,
            "Activation results must match planned activations exactly.",
        )
    checked_results: list[dict[str, object]] = []
    for index, (action, result) in enumerate(zip(activations, results, strict=True)):
        original = _text(
            action.get(ORIGINAL_PANE_ID_FIELD),
            f"plan.activations[{index}].originalPaneId",
        )
        if result.get(ORIGINAL_PANE_ID_FIELD) != original:
            raise AdapterError(
                ResultStatus.INVALID_SCHEMA,
                "Activation result order or original pane identity does not match its plan.",
            )
        operation = _text(
            action.get(OPERATION_FIELD), f"plan.activations[{index}].operation"
        )
        transport = _checked_transport(result.get(TRANSPORT_FIELD), operation)
        if not transport.delivered or transport.response is None:
            return {
                SCHEMA_VERSION_FIELD: SCHEMA_VERSION,
                STATUS_FIELD: ResultStatus.COMMAND_FAILED,
                DETAIL_FIELD: f"Activation failed for original pane {original}.",
                BINDINGS_FIELD: [binding.result() for binding in bindings],
                ACTIVATION_RESULTS_FIELD: checked_results,
            }
        data = _object(transport.response.get("data"), "transport.response.data")
        target = _object(data.get("target"), "transport.response.data.target")
        pane = _object(target.get("pane"), "transport.response.data.target.pane")
        worktree = _object(
            target.get("worktree"), "transport.response.data.target.worktree"
        )
        expected_path = _absolute_path(
            action.get(WORKTREE_PATH_FIELD),
            f"plan.activations[{index}].worktreePath",
        )
        actual_path = _absolute_path(
            worktree.get(PATH_FIELD), "transport.response.data.target.worktree.path"
        )
        if actual_path != expected_path:
            raise AdapterError(
                ResultStatus.INVALID_SCHEMA,
                f"Activation for {original} returned a different worktree path.",
            )
        bindings.append(
            Binding(
                original,
                _text(pane.get(ID_FIELD), "transport.response.data.target.pane.id"),
            )
        )
        checked_results.append(
            {
                ORIGINAL_PANE_ID_FIELD: original,
                TRANSPORT_FIELD: transport.raw,
            }
        )
    pane_ids = [binding.pane_id for binding in bindings]
    if len(pane_ids) != len(set(pane_ids)):
        raise AdapterError(
            ResultStatus.INVALID_TARGET,
            "Activation results produced duplicate post-restart pane identities.",
        )
    return {
        SCHEMA_VERSION_FIELD: SCHEMA_VERSION,
        STATUS_FIELD: ResultStatus.READY,
        BINDINGS_FIELD: [binding.result() for binding in bindings],
        ACTIVATION_RESULTS_FIELD: checked_results,
    }


def native_resume_command(candidate: PreparedCandidate) -> str:
    prompt = (
        f"Expected native session identity: {candidate.session_id}. "
        f"Recovery role: {candidate.role.value}. {RECOVERY_REASSESSMENT_PROMPT}"
    )
    return shlex.join(
        (*NATIVE_RESUME_PREFIXES[candidate.agent_type], candidate.session_id, prompt)
    )


def recover(
    prepared: object,
    binding_items: object,
    pane_items: list[dict[str, object]],
    agent_items: list[dict[str, object]],
) -> dict[str, object]:
    candidates = _prepared_candidates(prepared)
    bindings = _validated_bindings(binding_items, candidates)
    panes = _pane_roster(pane_items)
    agents = _agent_roster(agent_items)
    candidates_by_original = {
        candidate.original_pane_id: candidate for candidate in candidates
    }
    targets: list[dict[str, object]] = []
    deliveries: list[dict[str, object]] = []
    occupied: list[str] = []
    for binding in bindings:
        candidate = candidates_by_original[binding.original_pane_id]
        pane = panes.get(binding.pane_id)
        if pane is None or pane.worktree_path != candidate.worktree_path:
            raise AdapterError(
                ResultStatus.INVALID_TARGET,
                f"Binding for {binding.original_pane_id} does not match one post-restart pane and worktree.",
            )
        matches = agents.get(binding.pane_id, [])
        if len(matches) > 1 or (
            matches
            and (
                matches[0].agent_type is not candidate.agent_type
                or matches[0].session_id != candidate.session_id
            )
        ):
            occupied.append(binding.pane_id)
            continue
        resolution = Resolution.ALREADY_CORRELATED if matches else Resolution.RESUMED
        target = {
            **binding.result(),
            WORKTREE_ID_FIELD: pane.worktree_id,
            WORKTREE_PATH_FIELD: pane.worktree_path,
            REPOSITORY_ROOT_FIELD: pane.repository_root,
            CWD_FIELD: pane.cwd,
            SESSION_ID_FIELD: candidate.session_id,
            AGENT_TYPE_FIELD: candidate.agent_type,
            EVIDENCE_FIELD: candidate.evidence,
            ROLE_FIELD: candidate.role,
            STATUS_FIELD: resolution,
        }
        targets.append(target)
        if not matches:
            deliveries.append(
                {
                    ORIGINAL_PANE_ID_FIELD: binding.original_pane_id,
                    PANE_ID_FIELD: binding.pane_id,
                    TEXT_FIELD: native_resume_command(candidate),
                }
            )
    if occupied:
        return {
            SCHEMA_VERSION_FIELD: SCHEMA_VERSION,
            STATUS_FIELD: ResultStatus.PANE_OCCUPIED,
            DETAIL_FIELD: "Bound panes contain mismatched or duplicate agents.",
            "occupiedPaneIds": occupied,
            BINDINGS_FIELD: [binding.result() for binding in bindings],
            TARGETS_FIELD: [],
            DELIVERIES_FIELD: [],
        }
    return {
        SCHEMA_VERSION_FIELD: SCHEMA_VERSION,
        STATUS_FIELD: (
            ResultStatus.RESUMED if deliveries else ResultStatus.ALREADY_CURRENT
        ),
        BINDINGS_FIELD: [binding.result() for binding in bindings],
        TARGETS_FIELD: targets,
        DELIVERIES_FIELD: deliveries,
    }


def _validated_recovery_plan(plan: object) -> dict[str, object]:
    value = _object(plan, PLAN_FIELD)
    if value.get(SCHEMA_VERSION_FIELD) != SCHEMA_VERSION:
        raise AdapterError(
            ResultStatus.INVALID_SCHEMA,
            f"Recovery plan schema version must be {SCHEMA_VERSION}.",
        )
    if value.get(STATUS_FIELD) not in {
        ResultStatus.RESUMED,
        ResultStatus.ALREADY_CURRENT,
    }:
        raise AdapterError(
            ResultStatus.INVALID_SCHEMA,
            "Settlement requires a resumed or already-current recovery plan.",
        )
    _array(value.get(BINDINGS_FIELD), "plan.bindings")
    _array(value.get(TARGETS_FIELD), "plan.targets")
    _array(value.get(DELIVERIES_FIELD), "plan.deliveries")
    return value


def settle_recovery(plan: object, result_items: object) -> dict[str, object]:
    value = _validated_recovery_plan(plan)
    deliveries = _array(value.get(DELIVERIES_FIELD), "plan.deliveries")
    results = _array(result_items, DELIVERY_RESULTS_FIELD)
    if len(results) != len(deliveries):
        raise AdapterError(
            ResultStatus.INVALID_SCHEMA,
            "Delivery results must match planned deliveries exactly.",
        )
    checked: list[dict[str, object]] = []
    for index, (delivery, result) in enumerate(zip(deliveries, results, strict=True)):
        pane_id = _text(delivery.get(PANE_ID_FIELD), f"plan.deliveries[{index}].paneId")
        if result.get(PANE_ID_FIELD) != pane_id:
            raise AdapterError(
                ResultStatus.INVALID_SCHEMA,
                "Delivery result order or pane identity does not match its plan.",
            )
        transport = _checked_transport(
            result.get(TRANSPORT_FIELD), TRANSPORT_SEND_OPERATION
        )
        checked.append(
            {
                PANE_ID_FIELD: pane_id,
                DELIVERED_FIELD: transport.delivered,
                COMMAND_EXIT_CODE_FIELD: transport.exit_code,
                TRANSPORT_FIELD: transport.raw,
            }
        )
    if any(item[DELIVERED_FIELD] is not True for item in checked):
        return {
            **value,
            STATUS_FIELD: ResultStatus.COMMAND_FAILED,
            DETAIL_FIELD: "One or more exact native recovery commands were not delivered.",
            DELIVERY_RESULTS_FIELD: checked,
        }
    return {**value, DELIVERY_RESULTS_FIELD: checked}


def verify(
    prepared: object,
    binding_items: object,
    pane_items: list[dict[str, object]],
    agent_items: list[dict[str, object]],
    evidence_items: list[dict[str, object]],
) -> dict[str, object]:
    candidates = _prepared_candidates(prepared)
    bindings = _validated_bindings(binding_items, candidates)
    panes = _pane_roster(pane_items)
    agents = _agent_roster(agent_items)
    evidence = [
        _evidence_from_item(item, f"correlationEvidence[{index}]")
        for index, item in enumerate(evidence_items)
    ]
    evidence_by_pane: dict[str, list[IdentityEvidence]] = {}
    for item in evidence:
        evidence_by_pane.setdefault(item.pane_id, []).append(item)
    binding_panes = {binding.pane_id for binding in bindings}
    unexpected = sorted(pane_id for pane_id in agents if pane_id not in binding_panes)
    candidates_by_original = {
        candidate.original_pane_id: candidate for candidate in candidates
    }
    missing: list[str] = []
    duplicates: list[str] = []
    correlations: list[dict[str, object]] = []
    for binding in bindings:
        candidate = candidates_by_original[binding.original_pane_id]
        pane = panes.get(binding.pane_id)
        if pane is None or pane.worktree_path != candidate.worktree_path:
            missing.append(binding.pane_id)
            continue
        observed = evidence_by_pane.get(binding.pane_id, [])
        if not observed:
            missing.append(binding.pane_id)
            continue
        if len(observed) > 1:
            duplicates.append(binding.pane_id)
            continue
        identity = observed[0]
        matches = agents.get(binding.pane_id, [])
        if len(matches) > 1:
            duplicates.append(binding.pane_id)
            continue
        agent = matches[0] if matches else None
        if (
            identity.worktree_path != candidate.worktree_path
            or identity.session_id != candidate.session_id
            or identity.agent_type is not candidate.agent_type
            or (
                agent is not None
                and (
                    agent.agent_type is not candidate.agent_type
                    or (
                        agent.session_id is not None
                        and agent.session_id != candidate.session_id
                    )
                )
            )
            or (
                identity.source is EvidenceSource.PUBLIC_AGENT
                and (agent is None or agent.session_id != candidate.session_id)
            )
        ):
            unexpected.append(binding.pane_id)
            continue
        correlations.append(
            {
                **binding.result(),
                WORKTREE_ID_FIELD: pane.worktree_id,
                WORKTREE_PATH_FIELD: pane.worktree_path,
                REPOSITORY_ROOT_FIELD: pane.repository_root,
                CWD_FIELD: pane.cwd,
                SESSION_ID_FIELD: candidate.session_id,
                AGENT_TYPE_FIELD: candidate.agent_type,
                SOURCE_FIELD: identity.source,
                STATUS_FIELD: agent.status if agent is not None else "process-backed",
            }
        )
    unexpected = sorted(set(unexpected))
    status = (
        ResultStatus.VERIFIED
        if not missing and not duplicates and not unexpected
        else ResultStatus.CORRELATION_INCOMPLETE
    )
    return {
        SCHEMA_VERSION_FIELD: SCHEMA_VERSION,
        STATUS_FIELD: status,
        TARGETS_FIELD: len(candidates),
        VERIFIED_FIELD: len(correlations),
        CORRELATIONS_FIELD: correlations,
        MISSING_PANE_IDS_FIELD: missing,
        DUPLICATE_PANE_IDS_FIELD: duplicates,
        UNEXPECTED_AGENT_PANE_IDS_FIELD: unexpected,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="operation", required=True)
    for operation in Operation:
        command = subparsers.add_parser(operation.value)
        if operation is Operation.PREPARE:
            command.add_argument("--pane", action="append", required=True)
    return parser


def _input(stream: TextIO) -> dict[str, object]:
    try:
        return _object(json.load(stream), "stdin")
    except json.JSONDecodeError as error:
        raise AdapterError(
            ResultStatus.INVALID_SCHEMA,
            f"Recovery input on stdin is invalid JSON: {error.msg}.",
        ) from error


def command_exit_code(result: object) -> int:
    status = _object(result, "result").get(STATUS_FIELD)
    return (
        0
        if status
        in {
            ResultStatus.PREPARED,
            ResultStatus.ACTIVATION_REQUIRED,
            ResultStatus.READY,
            ResultStatus.RESUMED,
            ResultStatus.ALREADY_CURRENT,
            ResultStatus.VERIFIED,
        }
        else 2
    )


def main(
    argv: list[str] | None = None,
    *,
    stdin: TextIO | None = None,
    stdout: TextIO | None = None,
) -> int:
    args = _parser().parse_args(argv)
    operation = Operation(args.operation)
    input_stream = stdin if stdin is not None else sys.stdin
    output_stream = stdout if stdout is not None else sys.stdout
    try:
        value = _input(input_stream)
        if operation is Operation.PREPARE:
            result = prepare(
                tuple(cast(list[str], args.pane)),
                _array(value.get(ITEMS_FIELD), ITEMS_FIELD),
                _array(value.get(AGENTS_FIELD), AGENTS_FIELD),
                _array(value.get(CANDIDATES_FIELD), CANDIDATES_FIELD),
                _array(
                    value.get(CORRELATION_EVIDENCE_FIELD),
                    CORRELATION_EVIDENCE_FIELD,
                ),
            )
        elif operation is Operation.ACTIVATE:
            result = plan_activation(
                value.get(PREPARED_FIELD),
                _array(value.get(ITEMS_FIELD), ITEMS_FIELD),
                _array(value.get(AGENTS_FIELD), AGENTS_FIELD),
            )
        elif operation is Operation.BIND:
            result = bind_activations(
                value.get(PLAN_FIELD),
                value.get(ACTIVATION_RESULTS_FIELD),
            )
        elif operation is Operation.RECOVER:
            result = recover(
                value.get(PREPARED_FIELD),
                value.get(BINDINGS_FIELD),
                _array(value.get(ITEMS_FIELD), ITEMS_FIELD),
                _array(value.get(AGENTS_FIELD), AGENTS_FIELD),
            )
        elif operation is Operation.SETTLE:
            result = settle_recovery(
                value.get(PLAN_FIELD), value.get(DELIVERY_RESULTS_FIELD)
            )
        else:
            result = verify(
                value.get(PREPARED_FIELD),
                value.get(BINDINGS_FIELD),
                _array(value.get(ITEMS_FIELD), ITEMS_FIELD),
                _array(value.get(AGENTS_FIELD), AGENTS_FIELD),
                _array(
                    value.get(CORRELATION_EVIDENCE_FIELD),
                    CORRELATION_EVIDENCE_FIELD,
                ),
            )
        print(json.dumps(result, sort_keys=True), file=output_stream)
        return command_exit_code(result)
    except AdapterError as error:
        result = {
            SCHEMA_VERSION_FIELD: SCHEMA_VERSION,
            STATUS_FIELD: error.status,
            DETAIL_FIELD: str(error),
        }
        print(json.dumps(result, sort_keys=True), file=output_stream)
        return 2


if __name__ == "__main__":
    sys.exit(main())
