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

SCHEMA_VERSION = 5
TRANSPORT_SCHEMA_VERSION = 1
TRANSPORT_SUCCEEDED_STATUS = "succeeded"
TRANSPORT_COMMAND_FAILED_STATUS = "command-failed"
TRANSPORT_SEND_OPERATION = "send"
TRANSPORT_READ_OPERATION = "read"
ACTIVATION_OPEN_OPERATION = "open"
ACTIVATION_TAB_CREATE_OPERATION = "tab-create"
EXACT_ROOT_RESOLUTION = "exact-root"

NON_CONTROLLER_BOUNDARY = (
    "You are not the recovery controller. Another session owns this restart "
    "recovery, so invoke no recovery workflow and send no text and no keys to any "
    "pane, including your own siblings."
)

SCHEMA_VERSION_FIELD = "schemaVersion"
ITEMS_FIELD = "items"
AGENTS_FIELD = "agents"
CANDIDATES_FIELD = "candidates"
CORRELATION_EVIDENCE_FIELD = "correlationEvidence"
ACTIVATION_RESULTS_FIELD = "activationResults"
PANE_READ_RESULTS_FIELD = "paneReadResults"
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
CONTROLLER_PANE_ID_FIELD = "controllerPaneId"
WORKTREE_ID_FIELD = "worktreeId"
WORKTREE_PATH_FIELD = "worktreePath"
REPOSITORY_ROOT_FIELD = "repositoryRoot"
SESSION_ID_FIELD = "sessionId"
RESUME_LOCATOR_FIELD = "resumeLocator"
NATIVE_HOME_FIELD = "nativeHome"
REASSESSED_SESSION_IDS_FIELD = "reassessedSessionIds"
RESTORED_FIELD = "restored"
NO_CONTINUATION_SESSION_IDS_FIELD = "noContinuationSessionIds"
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
DATA_FIELD = "data"
INPUT_FIELD = "input"
TRAILING_ENTER_SENT_FIELD = "trailing_enter_sent"
RESOLUTION_FIELD = "resolution"
CREATED_TAB_FIELD = "created_tab"
DELIVERED_FIELD = "delivered"
VERIFIED_FIELD = "verified"
VERIFICATION_FIELD = "verification"
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
    REASSESS = "reassess"


class ResultStatus(StrEnum):
    PREPARED = "prepared"
    ACTIVATION_REQUIRED = "activation-required"
    READY = "ready"
    RESUMED = "resumed"
    ALREADY_CURRENT = "already-current"
    VERIFIED = "verified"
    REASSESSMENT_READY = "reassessment-ready"
    REASSESSMENT_SENT = "reassessment-sent"
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


POST_RESTART_EVIDENCE_SOURCES = frozenset(
    {
        EvidenceSource.PROCESS_ARGUMENT,
        EvidenceSource.OPEN_SESSION_FILE,
        EvidenceSource.NATIVE_STATUS,
        EvidenceSource.CURRENT_SESSION,
        EvidenceSource.PUBLIC_AGENT,
    }
)

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
class AttestedController:
    pane_id: str
    candidate: "PreparedCandidate"


@dataclass(frozen=True)
class PreparedCandidate:
    original_pane_id: str
    worktree_path: str
    session_id: str
    resume_locator: str
    native_home: str | None
    agent_type: AgentType
    evidence: EvidenceSource
    role: RecoveryRole
    secondary_authorized: bool

    def result(self) -> dict[str, object]:
        return {
            ORIGINAL_PANE_ID_FIELD: self.original_pane_id,
            WORKTREE_PATH_FIELD: self.worktree_path,
            SESSION_ID_FIELD: self.session_id,
            RESUME_LOCATOR_FIELD: self.resume_locator,
            NATIVE_HOME_FIELD: self.native_home,
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


def _optional_absolute_path(value: object, location: str) -> str | None:
    if value is None:
        return None
    return _absolute_path(value, location)


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
        resume_locator=_text(
            item.get(RESUME_LOCATOR_FIELD), f"{location}.resumeLocator"
        ),
        native_home=_optional_absolute_path(
            item.get(NATIVE_HOME_FIELD), f"{location}.nativeHome"
        ),
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
        resume_locator=_text(
            item.get(RESUME_LOCATOR_FIELD), f"{location}.resumeLocator"
        ),
        native_home=_optional_absolute_path(
            item.get(NATIVE_HOME_FIELD), f"{location}.nativeHome"
        ),
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


def _attested_controller(
    value: object,
    candidates: list[PreparedCandidate],
    panes: dict[str, PaneIdentity],
    agents: dict[str, list[AgentIdentity]],
) -> AttestedController | None:
    """Bind the running controller to its post-restart pane on current-session evidence.

    A controller whose native transcript resolves under a different project root than
    its pane's working directory stays unidentified in the public agent roster, so
    activation would read the controller's own pane as a mismatched occupant and stop.
    The caller attests the exact pane it is running in; every other pane keeps the
    strict roster match, and the attested pane is never relaunched.
    """
    if value is None:
        return None
    pane_id = _text(value, CONTROLLER_PANE_ID_FIELD)
    controller = next(
        (
            candidate
            for candidate in candidates
            if candidate.evidence is EvidenceSource.CURRENT_SESSION
        ),
        None,
    )
    if controller is None:
        raise AdapterError(
            ResultStatus.INVALID_TARGET,
            "An attested controller pane requires one current-session candidate.",
        )
    pane = panes.get(pane_id)
    if pane is None:
        raise AdapterError(
            ResultStatus.INVALID_TARGET,
            f"Attested controller pane {pane_id} is absent from the post-restart panes.",
        )
    if pane.worktree_path != controller.worktree_path:
        raise AdapterError(
            ResultStatus.INVALID_TARGET,
            "Attested controller pane does not sit in the controller candidate worktree.",
        )
    matches = agents.get(pane_id, [])
    if len(matches) > 1:
        raise AdapterError(
            ResultStatus.INVALID_TARGET,
            "Attested controller pane reports more than one agent.",
        )
    for agent in matches:
        if agent.agent_type is not controller.agent_type:
            raise AdapterError(
                ResultStatus.INVALID_TARGET,
                "Attested controller pane reports another agent type.",
            )
        if agent.session_id is not None and agent.session_id != controller.session_id:
            raise AdapterError(
                ResultStatus.INVALID_TARGET,
                "Attested controller pane reports another native session.",
            )
    return AttestedController(pane_id=pane_id, candidate=controller)


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
        if candidate.agent_type is not AgentType.CLAUDE and (
            candidate.resume_locator != candidate.session_id
        ):
            raise AdapterError(
                ResultStatus.INVALID_TARGET,
                "Codex and Pi resume locators must equal their native session identity.",
            )
        if candidate.agent_type is not AgentType.CODEX and candidate.native_home:
            raise AdapterError(
                ResultStatus.INVALID_TARGET,
                "Only Codex candidates may carry a native home.",
            )
        by_worktree.setdefault(candidate.worktree_path, []).append(candidate)
    controllers = [
        candidate
        for candidate in candidates
        if candidate.evidence is EvidenceSource.CURRENT_SESSION
    ]
    if len(controllers) != 1:
        raise AdapterError(
            ResultStatus.INVALID_TARGET,
            "Recovery candidates require exactly one current-session controller.",
        )
    for worktree_path, group in by_worktree.items():
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
    reassessed = value.get(REASSESSED_SESSION_IDS_FIELD)
    if not isinstance(reassessed, list) or any(
        not isinstance(item, str) or not item for item in reassessed
    ):
        raise AdapterError(
            ResultStatus.INVALID_SCHEMA,
            "Prepared manifest reassessedSessionIds must be an array of non-empty strings.",
        )
    if len(reassessed) != len(set(reassessed)) or any(
        item not in {candidate.session_id for candidate in candidates}
        for item in reassessed
    ):
        raise AdapterError(
            ResultStatus.INVALID_TARGET,
            "Prepared manifest reassessedSessionIds must identify distinct prepared sessions.",
        )
    return candidates


def _reassessed_session_ids(prepared: object) -> set[str]:
    value = _object(prepared, PREPARED_FIELD)
    reassessed = value.get(REASSESSED_SESSION_IDS_FIELD)
    if not isinstance(reassessed, list):
        raise AdapterError(
            ResultStatus.INVALID_SCHEMA,
            "Prepared manifest reassessedSessionIds must be an array.",
        )
    return {cast(str, item) for item in reassessed}


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
            agent.worktree_path != candidate.worktree_path
            or agent.agent_type is not candidate.agent_type
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
        REASSESSED_SESSION_IDS_FIELD: [
            candidates_by_pane[pane_id].session_id
            for pane_id in selected
            if candidates_by_pane[pane_id].evidence is EvidenceSource.CURRENT_SESSION
        ],
    }


def plan_activation(
    prepared: object,
    pane_items: list[dict[str, object]],
    agent_items: list[dict[str, object]],
    controller_pane: object = None,
) -> dict[str, object]:
    candidates = _prepared_candidates(prepared)
    panes = _pane_roster(pane_items)
    agents = _agent_roster(agent_items)
    attested = _attested_controller(controller_pane, candidates, panes, agents)
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
            if attested is not None and pane.pane_id == attested.pane_id:
                bindings.append(
                    Binding(attested.candidate.original_pane_id, pane.pane_id)
                )
                remaining.remove(attested.candidate)
                continue
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


def _checked_send_transport(value: object) -> CheckedTransport:
    transport = _checked_transport(value, TRANSPORT_SEND_OPERATION)
    if not transport.delivered or transport.response is None:
        return transport
    data = _object(transport.response.get(DATA_FIELD), "transport.response.data")
    input_record = _object(data.get(INPUT_FIELD), "transport.response.data.input")
    if input_record.get(TRAILING_ENTER_SENT_FIELD) is not True:
        raise AdapterError(
            ResultStatus.INVALID_SCHEMA,
            "Successful recovery send requires public trailing_enter_sent: true evidence.",
        )
    return transport


def _checked_pane_reads(
    result_items: object,
    bindings: list[Binding],
) -> tuple[list[dict[str, object]], list[str]]:
    results = _array(result_items, PANE_READ_RESULTS_FIELD)
    if len(results) != len(bindings):
        raise AdapterError(
            ResultStatus.INVALID_SCHEMA,
            "Pane-read results must cover every verified binding exactly once.",
        )
    checked: list[dict[str, object]] = []
    failed: list[str] = []
    for index, (binding, result) in enumerate(zip(bindings, results, strict=True)):
        original = _text(
            result.get(ORIGINAL_PANE_ID_FIELD),
            f"paneReadResults[{index}].originalPaneId",
        )
        pane_id = _text(result.get(PANE_ID_FIELD), f"paneReadResults[{index}].paneId")
        if original != binding.original_pane_id or pane_id != binding.pane_id:
            raise AdapterError(
                ResultStatus.INVALID_SCHEMA,
                "Pane-read result order or identity does not match its verified binding.",
            )
        transport = _checked_transport(
            result.get(TRANSPORT_FIELD), TRANSPORT_READ_OPERATION
        )
        checked.append(
            {
                ORIGINAL_PANE_ID_FIELD: original,
                PANE_ID_FIELD: pane_id,
                TRANSPORT_FIELD: transport.raw,
            }
        )
        if not transport.delivered:
            failed.append(pane_id)
    return checked, failed


def bind_activations(plan: object, result_items: object) -> dict[str, object]:
    value = _object(plan, PLAN_FIELD)
    if value.get(SCHEMA_VERSION_FIELD) != SCHEMA_VERSION or value.get(
        STATUS_FIELD
    ) not in {ResultStatus.ACTIVATION_REQUIRED, ResultStatus.READY}:
        raise AdapterError(
            ResultStatus.INVALID_SCHEMA,
            "Activation binding requires a schema-5 activation-required or ready plan.",
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
    failed_originals: list[str] = []
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
        checked_results.append(
            {
                ORIGINAL_PANE_ID_FIELD: original,
                TRANSPORT_FIELD: transport.raw,
            }
        )
        if not transport.delivered or transport.response is None:
            failed_originals.append(original)
            continue
        data = _object(transport.response.get(DATA_FIELD), "transport.response.data")
        if (
            operation == ACTIVATION_OPEN_OPERATION
            and data.get(RESOLUTION_FIELD) != EXACT_ROOT_RESOLUTION
        ):
            raise AdapterError(
                ResultStatus.INVALID_TARGET,
                f"Activation for {original} did not lazily enter one known exact-root worktree.",
            )
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
    pane_ids = [binding.pane_id for binding in bindings]
    if len(pane_ids) != len(set(pane_ids)):
        raise AdapterError(
            ResultStatus.INVALID_TARGET,
            "Activation results produced duplicate post-restart pane identities.",
        )
    if failed_originals:
        return {
            SCHEMA_VERSION_FIELD: SCHEMA_VERSION,
            STATUS_FIELD: ResultStatus.COMMAND_FAILED,
            DETAIL_FIELD: (
                "Activation failed for original panes: "
                + ", ".join(failed_originals)
                + "."
            ),
            BINDINGS_FIELD: [binding.result() for binding in bindings],
            ACTIVATION_RESULTS_FIELD: checked_results,
        }
    return {
        SCHEMA_VERSION_FIELD: SCHEMA_VERSION,
        STATUS_FIELD: ResultStatus.READY,
        BINDINGS_FIELD: [binding.result() for binding in bindings],
        ACTIVATION_RESULTS_FIELD: checked_results,
    }


def native_resume_command(candidate: PreparedCandidate) -> str:
    prefix = NATIVE_RESUME_PREFIXES[candidate.agent_type]
    if candidate.agent_type is AgentType.CLAUDE:
        return shlex.join((*prefix, candidate.resume_locator))
    if candidate.agent_type is AgentType.CODEX and candidate.native_home is not None:
        return shlex.join(
            (
                "env",
                f"CODEX_HOME={candidate.native_home}",
                *prefix,
                candidate.session_id,
            )
        )
    return shlex.join((*prefix, candidate.session_id))


def reassessment_prompt(restored: str) -> str:
    """Carry one restored fact under the machine-enforced non-controller boundary.

    The controller supplies what this restart destroyed for this one recipient,
    having read that recipient's pane. Nothing else is added: a recipient's next
    action belongs to the recipient, which holds the conversation the controller
    cannot see.
    """
    return f"{NON_CONTROLLER_BOUNDARY} {restored}"


def recover(
    prepared: object,
    binding_items: object,
    pane_items: list[dict[str, object]],
    agent_items: list[dict[str, object]],
    controller_pane: object = None,
) -> dict[str, object]:
    candidates = _prepared_candidates(prepared)
    bindings = _validated_bindings(binding_items, candidates)
    panes = _pane_roster(pane_items)
    agents = _agent_roster(agent_items)
    attested = _attested_controller(controller_pane, candidates, panes, agents)
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
        is_attested = attested is not None and binding.pane_id == attested.pane_id
        if len(matches) > 1 or (
            matches
            and (
                matches[0].agent_type is not candidate.agent_type
                or (
                    matches[0].session_id != candidate.session_id
                    and not (is_attested and matches[0].session_id is None)
                )
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
        ResultStatus.REASSESSMENT_READY,
    }:
        raise AdapterError(
            ResultStatus.INVALID_SCHEMA,
            "Settlement requires a resumed, already-current, or reassessment-ready plan.",
        )
    _array(value.get(BINDINGS_FIELD), "plan.bindings")
    if value.get(STATUS_FIELD) != ResultStatus.REASSESSMENT_READY:
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
        transport = _checked_send_transport(result.get(TRANSPORT_FIELD))
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
            DETAIL_FIELD: "One or more planned recovery sends were not delivered.",
            DELIVERY_RESULTS_FIELD: checked,
        }
    if value.get(STATUS_FIELD) == ResultStatus.REASSESSMENT_READY:
        prepared = _object(value.get(PREPARED_FIELD), "plan.prepared")
        reassessed = _reassessed_session_ids(prepared)
        reassessed.update(
            _text(delivery.get(SESSION_ID_FIELD), "plan.delivery.sessionId")
            for delivery in deliveries
        )
        # A recipient the controller read and judged intact is settled by that
        # judgment; recording it keeps a repeated recovery from revisiting it.
        judged_none = value.get(NO_CONTINUATION_SESSION_IDS_FIELD) or []
        if not isinstance(judged_none, list):
            raise AdapterError(
                ResultStatus.INVALID_SCHEMA,
                "Plan noContinuationSessionIds must be an array.",
            )
        reassessed.update(
            _text(session_id, f"plan.noContinuationSessionIds[{index}]")
            for index, session_id in enumerate(judged_none)
        )
        updated_prepared = {
            **prepared,
            REASSESSED_SESSION_IDS_FIELD: sorted(reassessed),
        }
        _prepared_candidates(updated_prepared)
        return {
            **value,
            STATUS_FIELD: ResultStatus.REASSESSMENT_SENT,
            PREPARED_FIELD: updated_prepared,
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
            or identity.source not in POST_RESTART_EVIDENCE_SOURCES
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


def _restored_facts(items: object, pending_sessions: set[str]) -> dict[str, str]:
    """Read the controller's per-recipient judgment of what the restart destroyed.

    One entry per recipient that needs anything at all. A recipient the controller
    read and judged intact is simply absent, and receives nothing: a restart that
    destroyed nothing for a session gives that session no reason to spend a turn.
    """
    facts: dict[str, str] = {}
    for index, item in enumerate(_array(items or [], RESTORED_FIELD)):
        location = f"{RESTORED_FIELD}[{index}]"
        entry = _object(item, location)
        session_id = _text(entry.get(SESSION_ID_FIELD), f"{location}.sessionId")
        text = _text(entry.get(TEXT_FIELD), f"{location}.text").strip()
        if not text:
            raise AdapterError(
                ResultStatus.INVALID_TARGET,
                f"Restored fact for {session_id} is empty; omit the entry instead.",
            )
        if session_id not in pending_sessions:
            raise AdapterError(
                ResultStatus.INVALID_TARGET,
                f"Restored fact names {session_id}, which is not awaiting continuation.",
            )
        if session_id in facts:
            raise AdapterError(
                ResultStatus.INVALID_TARGET,
                f"Restored facts name {session_id} more than once.",
            )
        facts[session_id] = text
    return facts


def plan_reassessment(
    prepared: object,
    binding_items: object,
    verification: object,
    pane_read_items: object,
    restored_items: object = None,
) -> dict[str, object]:
    candidates = _prepared_candidates(prepared)
    bindings = _validated_bindings(binding_items, candidates)
    verified = _object(verification, "verification")
    if (
        verified.get(SCHEMA_VERSION_FIELD) != SCHEMA_VERSION
        or verified.get(STATUS_FIELD) != ResultStatus.VERIFIED
        or verified.get(TARGETS_FIELD) != len(candidates)
        or verified.get(VERIFIED_FIELD) != len(candidates)
        or verified.get(MISSING_PANE_IDS_FIELD) != []
        or verified.get(DUPLICATE_PANE_IDS_FIELD) != []
        or verified.get(UNEXPECTED_AGENT_PANE_IDS_FIELD) != []
    ):
        raise AdapterError(
            ResultStatus.INVALID_SCHEMA,
            "Reassessment requires one complete verified correlation per prepared candidate.",
        )
    correlation_items = _array(
        verified.get(CORRELATIONS_FIELD), "verification.correlations"
    )
    correlated = {
        (
            _text(item.get(ORIGINAL_PANE_ID_FIELD), "verification.originalPaneId"),
            _text(item.get(PANE_ID_FIELD), "verification.paneId"),
            _text(item.get(SESSION_ID_FIELD), "verification.sessionId"),
        )
        for item in correlation_items
    }
    expected = {
        (binding.original_pane_id, binding.pane_id, candidate.session_id)
        for binding, candidate in zip(bindings, candidates, strict=True)
    }
    if correlated != expected:
        raise AdapterError(
            ResultStatus.INVALID_TARGET,
            "Verified correlations do not match the prepared bindings and sessions.",
        )
    pane_reads, failed_panes = _checked_pane_reads(pane_read_items, bindings)
    if failed_panes:
        return {
            SCHEMA_VERSION_FIELD: SCHEMA_VERSION,
            STATUS_FIELD: ResultStatus.COMMAND_FAILED,
            DETAIL_FIELD: (
                "Context read failed before reassessment for panes: "
                + ", ".join(failed_panes)
                + "."
            ),
            PREPARED_FIELD: _object(prepared, PREPARED_FIELD),
            BINDINGS_FIELD: [binding.result() for binding in bindings],
            PANE_READ_RESULTS_FIELD: pane_reads,
            DELIVERIES_FIELD: [],
        }
    reassessed = _reassessed_session_ids(prepared)
    pending = [
        (binding, candidate)
        for binding, candidate in zip(bindings, candidates, strict=True)
        if candidate.session_id not in reassessed
    ]
    pending_sessions = {candidate.session_id for _, candidate in pending}
    restored = _restored_facts(restored_items, pending_sessions)
    deliveries = [
        {
            ORIGINAL_PANE_ID_FIELD: binding.original_pane_id,
            PANE_ID_FIELD: binding.pane_id,
            SESSION_ID_FIELD: candidate.session_id,
            TEXT_FIELD: reassessment_prompt(restored[candidate.session_id]),
        }
        for binding, candidate in pending
        if candidate.session_id in restored
    ]
    judged_none = sorted(pending_sessions - set(restored))
    return {
        SCHEMA_VERSION_FIELD: SCHEMA_VERSION,
        STATUS_FIELD: (
            ResultStatus.REASSESSMENT_READY
            if deliveries
            else ResultStatus.ALREADY_CURRENT
        ),
        PREPARED_FIELD: _object(prepared, PREPARED_FIELD),
        BINDINGS_FIELD: [binding.result() for binding in bindings],
        PANE_READ_RESULTS_FIELD: pane_reads,
        DELIVERIES_FIELD: deliveries,
        NO_CONTINUATION_SESSION_IDS_FIELD: judged_none,
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
            ResultStatus.REASSESSMENT_READY,
            ResultStatus.REASSESSMENT_SENT,
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
                value.get(CONTROLLER_PANE_ID_FIELD),
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
                value.get(CONTROLLER_PANE_ID_FIELD),
            )
        elif operation is Operation.SETTLE:
            result = settle_recovery(
                value.get(PLAN_FIELD), value.get(DELIVERY_RESULTS_FIELD)
            )
        elif operation is Operation.VERIFY:
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
        else:
            result = plan_reassessment(
                value.get(PREPARED_FIELD),
                value.get(BINDINGS_FIELD),
                value.get(VERIFICATION_FIELD),
                value.get(PANE_READ_RESULTS_FIELD),
                value.get(RESTORED_FIELD) or [],
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
