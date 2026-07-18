#!/usr/bin/env python3
"""Plan and verify native-session recovery from public Prowl evidence."""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from enum import StrEnum
from typing import TextIO, cast

SCHEMA_VERSION = 3
SPX_RESUME_COMMAND = "spx agent resume --latest"
RECOVERY_REASSESSMENT_PROMPT = (
    "Recovery check: Prowl restored this pane and SPX selected this native session. "
    "Before acting, inspect the prior conversation and authoritative current repository "
    "and SPX state. Continue only when concrete unfinished work remains and continuation "
    "is still authorized. If the prior workflow completed, the session was deliberately "
    "stopped, or continuation is unclear, exit now without modifying files or starting "
    "background work. Do not remain active merely because recovery resumed the session."
)
RECOVERY_INPUT = f"{SPX_RESUME_COMMAND}\n{RECOVERY_REASSESSMENT_PROMPT}"
NATIVE_AGENT_TYPES = frozenset({"claude", "codex"})

SCHEMA_VERSION_FIELD = "schemaVersion"
ITEMS_FIELD = "items"
AGENTS_FIELD = "agents"
WORKTREE_FIELD = "worktree"
PANE_FIELD = "pane"
ID_FIELD = "id"
PATH_FIELD = "path"
ROOT_PATH_FIELD = "root_path"
TYPE_FIELD = "type"
STATUS_FIELD = "status"
DETAIL_FIELD = "detail"
TARGETS_FIELD = "targets"
CORRELATIONS_FIELD = "correlations"
CWD_FIELD = "cwd"
PANE_ID_FIELD = "paneId"
WORKTREE_ID_FIELD = "worktreeId"
WORKTREE_PATH_FIELD = "worktreePath"
REPOSITORY_ROOT_FIELD = "repositoryRoot"
VERIFIED_FIELD = "verified"
MISSING_PANE_IDS_FIELD = "missingPaneIds"
DUPLICATE_PANE_IDS_FIELD = "duplicatePaneIds"
OCCUPIED_PANE_IDS_FIELD = "occupiedPaneIds"
UNEXPECTED_AGENT_PANE_IDS_FIELD = "unexpectedAgentPaneIds"
COMMAND_FIELD = "command"
REASSESSMENT_SENT_FIELD = "reassessmentSent"
DELIVERIES_FIELD = "deliveries"
DELIVERY_RESULTS_FIELD = "deliveryResults"
PLAN_FIELD = "plan"
TEXT_FIELD = "text"
DELIVERED_FIELD = "delivered"
COMMAND_EXIT_CODE_FIELD = "commandExitCode"
PANE_RESULT_FIELDS = frozenset(
    {
        PANE_ID_FIELD,
        WORKTREE_ID_FIELD,
        WORKTREE_PATH_FIELD,
        REPOSITORY_ROOT_FIELD,
        CWD_FIELD,
        STATUS_FIELD,
    }
)
CORRELATION_FIELDS = frozenset(
    {
        PANE_ID_FIELD,
        WORKTREE_ID_FIELD,
        WORKTREE_PATH_FIELD,
        REPOSITORY_ROOT_FIELD,
        CWD_FIELD,
        TYPE_FIELD,
        STATUS_FIELD,
    }
)
DELIVERY_FIELDS = frozenset({PANE_ID_FIELD, TEXT_FIELD})


class Operation(StrEnum):
    RECOVER = "recover"
    VERIFY = "verify"
    SETTLE = "settle"


class ResultStatus(StrEnum):
    RESUMED = "resumed"
    ALREADY_CURRENT = "already-current"
    VERIFIED = "verified"
    INVALID_TARGET = "invalid-target"
    PANE_OCCUPIED = "pane-occupied"
    CORRELATION_INCOMPLETE = "correlation-incomplete"
    INVALID_SCHEMA = "invalid-schema"
    ENVIRONMENT_UNAVAILABLE = "environment-unavailable"
    COMMAND_FAILED = "command-failed"


class Resolution(StrEnum):
    RESUMED = "resumed"
    ALREADY_CORRELATED = "already-correlated"


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

    def result(self, resolution: Resolution | ResultStatus) -> dict[str, object]:
        return {
            PANE_ID_FIELD: self.pane_id,
            WORKTREE_ID_FIELD: self.worktree_id,
            WORKTREE_PATH_FIELD: self.worktree_path,
            REPOSITORY_ROOT_FIELD: self.repository_root,
            CWD_FIELD: self.cwd,
            STATUS_FIELD: resolution,
        }


@dataclass(frozen=True)
class AgentIdentity:
    pane_id: str
    worktree_path: str
    agent_type: str
    status: str


def _object(value: object, location: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise AdapterError(
            ResultStatus.INVALID_SCHEMA, f"Expected an object at {location}."
        )
    return value


def _text(value: object, location: str) -> str:
    if not isinstance(value, str) or not value:
        raise AdapterError(
            ResultStatus.INVALID_SCHEMA,
            f"Expected a non-empty string at {location}.",
        )
    return value


def _array(value: object, location: str) -> list[dict[str, object]]:
    if not isinstance(value, list):
        raise AdapterError(
            ResultStatus.INVALID_SCHEMA, f"Expected an array at {location}."
        )
    return [_object(item, f"{location}[{index}]") for index, item in enumerate(value)]


def _absolute_path(value: object, location: str) -> str:
    path = _text(value, location)
    if not os.path.isabs(path):
        raise AdapterError(
            ResultStatus.INVALID_SCHEMA,
            f"Expected an absolute path at {location}.",
        )
    return path


def _pane_identity(item: dict[str, object], location: str) -> PaneIdentity:
    worktree = _object(item.get(WORKTREE_FIELD), f"{location}.worktree")
    pane = _object(item.get(PANE_FIELD), f"{location}.pane")
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
    worktree = _object(item.get(WORKTREE_FIELD), f"{location}.worktree")
    pane = _object(item.get(PANE_FIELD), f"{location}.pane")
    return AgentIdentity(
        pane_id=_text(pane.get(ID_FIELD), f"{location}.pane.id"),
        worktree_path=_absolute_path(
            worktree.get(PATH_FIELD), f"{location}.worktree.path"
        ),
        agent_type=_text(item.get(TYPE_FIELD), f"{location}.type"),
        status=_text(item.get(STATUS_FIELD), f"{location}.status"),
    )


def _pane_roster(items: list[dict[str, object]]) -> dict[str, PaneIdentity]:
    roster: dict[str, PaneIdentity] = {}
    for index, item in enumerate(items):
        identity = _pane_identity(item, f"panes[{index}]")
        if identity.pane_id in roster:
            raise AdapterError(
                ResultStatus.INVALID_SCHEMA,
                f"Public evidence returned duplicate pane identity: {identity.pane_id}",
            )
        roster[identity.pane_id] = identity
    return roster


def _agent_roster(items: list[dict[str, object]]) -> dict[str, list[AgentIdentity]]:
    roster: dict[str, list[AgentIdentity]] = {}
    for index, item in enumerate(items):
        identity = _agent_identity(item, f"agents[{index}]")
        roster.setdefault(identity.pane_id, []).append(identity)
    return roster


def _selected_pane_ids(values: tuple[str, ...]) -> tuple[str, ...]:
    if not values:
        raise AdapterError(
            ResultStatus.INVALID_TARGET,
            "At least one exact Prowl pane UUID is required.",
        )
    selected = tuple(_text(value, "selected pane identity") for value in values)
    if len(selected) != len(set(selected)):
        raise AdapterError(
            ResultStatus.INVALID_TARGET,
            "Selected Prowl pane identities must be unique.",
        )
    return selected


def _validate_targets(
    selected: tuple[str, ...], panes: dict[str, PaneIdentity]
) -> dict[str, PaneIdentity]:
    missing = [pane_id for pane_id in selected if pane_id not in panes]
    if missing:
        raise AdapterError(
            ResultStatus.INVALID_TARGET,
            f"Selected Prowl panes do not exist: {', '.join(missing)}",
        )
    return {pane_id: panes[pane_id] for pane_id in selected}


def recover(
    selected_pane_ids: tuple[str, ...],
    pane_items: list[dict[str, object]],
    agent_items: list[dict[str, object]],
) -> dict[str, object]:
    selected = _selected_pane_ids(selected_pane_ids)
    panes = _pane_roster(pane_items)
    targets = _validate_targets(selected, panes)
    agents = _agent_roster(agent_items)

    occupied: list[str] = []
    for pane_id in selected:
        matches = agents.get(pane_id, [])
        if len(matches) > 1 or (
            matches and matches[0].agent_type not in NATIVE_AGENT_TYPES
        ):
            occupied.append(pane_id)
    if occupied:
        return {
            SCHEMA_VERSION_FIELD: SCHEMA_VERSION,
            STATUS_FIELD: ResultStatus.PANE_OCCUPIED,
            DETAIL_FIELD: (
                "Selected panes have non-native or multiple detected-agent correlations."
            ),
            OCCUPIED_PANE_IDS_FIELD: occupied,
            TARGETS_FIELD: [
                targets[pane_id].result(ResultStatus.PANE_OCCUPIED)
                for pane_id in occupied
            ],
            DELIVERIES_FIELD: [],
        }

    results: list[dict[str, object]] = []
    deliveries: list[dict[str, object]] = []
    for pane_id in selected:
        pane = targets[pane_id]
        matches = agents.get(pane_id, [])
        if matches:
            agent = matches[0]
            if agent.worktree_path != pane.worktree_path:
                raise AdapterError(
                    ResultStatus.INVALID_SCHEMA,
                    f"Detected agent worktree does not match pane {pane_id}.",
                )
            results.append(pane.result(Resolution.ALREADY_CORRELATED))
            continue
        result = pane.result(Resolution.RESUMED)
        result[COMMAND_FIELD] = SPX_RESUME_COMMAND
        result[REASSESSMENT_SENT_FIELD] = True
        results.append(result)
        deliveries.append({PANE_ID_FIELD: pane_id, TEXT_FIELD: RECOVERY_INPUT})

    return {
        SCHEMA_VERSION_FIELD: SCHEMA_VERSION,
        STATUS_FIELD: (
            ResultStatus.RESUMED if deliveries else ResultStatus.ALREADY_CURRENT
        ),
        TARGETS_FIELD: results,
        DELIVERIES_FIELD: deliveries,
    }


def settle_recovery(plan: object, delivery_results: object) -> dict[str, object]:
    value = _object(plan, PLAN_FIELD)
    deliveries = _array(value.get(DELIVERIES_FIELD), f"{PLAN_FIELD}.{DELIVERIES_FIELD}")
    results = _array(delivery_results, DELIVERY_RESULTS_FIELD)
    expected_panes = [
        _text(delivery.get(PANE_ID_FIELD), f"delivery.{PANE_ID_FIELD}")
        for delivery in deliveries
    ]
    observed_panes = [
        _text(result.get(PANE_ID_FIELD), f"deliveryResult.{PANE_ID_FIELD}")
        for result in results
    ]
    if expected_panes != observed_panes:
        raise AdapterError(
            ResultStatus.INVALID_SCHEMA,
            "Delivery results must match planned pane identities in order.",
        )
    failures = [result for result in results if result.get(DELIVERED_FIELD) is not True]
    if failures:
        return {
            SCHEMA_VERSION_FIELD: SCHEMA_VERSION,
            STATUS_FIELD: ResultStatus.COMMAND_FAILED,
            DETAIL_FIELD: "One or more planned recovery inputs were not delivered.",
            DELIVERY_RESULTS_FIELD: results,
            TARGETS_FIELD: value.get(TARGETS_FIELD),
        }
    return {**value, DELIVERY_RESULTS_FIELD: results}


def verify(
    selected_pane_ids: tuple[str, ...],
    pane_items: list[dict[str, object]],
    agent_items: list[dict[str, object]],
) -> dict[str, object]:
    selected = _selected_pane_ids(selected_pane_ids)
    panes = _pane_roster(pane_items)
    targets = _validate_targets(selected, panes)
    agents = _agent_roster(agent_items)

    correlations: list[dict[str, object]] = []
    missing: list[str] = []
    duplicates: list[str] = []
    unexpected: list[str] = []
    for pane_id in selected:
        pane = targets[pane_id]
        matches = agents.get(pane_id, [])
        if not matches:
            missing.append(pane_id)
            continue
        if len(matches) > 1:
            duplicates.append(pane_id)
            continue
        agent = matches[0]
        if (
            agent.agent_type not in NATIVE_AGENT_TYPES
            or agent.worktree_path != pane.worktree_path
        ):
            unexpected.append(pane_id)
            continue
        correlation = pane.result(Resolution.ALREADY_CORRELATED)
        correlation[TYPE_FIELD] = agent.agent_type
        correlation[STATUS_FIELD] = agent.status
        correlations.append(correlation)

    result_status = (
        ResultStatus.VERIFIED
        if not missing and not duplicates and not unexpected
        else ResultStatus.CORRELATION_INCOMPLETE
    )
    return {
        SCHEMA_VERSION_FIELD: SCHEMA_VERSION,
        STATUS_FIELD: result_status,
        TARGETS_FIELD: len(selected),
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
        if operation is not Operation.SETTLE:
            command.add_argument("--pane", action="append", required=True)
    return parser


def _input(stream: TextIO) -> dict[str, object]:
    try:
        return _object(json.load(stream), "stdin")
    except json.JSONDecodeError as error:
        raise AdapterError(
            ResultStatus.INVALID_SCHEMA,
            f"Recovery input on stdin is invalid JSON: {error.msg}",
        ) from error


def command_exit_code(result: object) -> int:
    status = _object(result, "result").get(STATUS_FIELD)
    return (
        0
        if status
        in {
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
        if operation is Operation.SETTLE:
            result = settle_recovery(
                value.get(PLAN_FIELD), value.get(DELIVERY_RESULTS_FIELD)
            )
        else:
            pane_items = _array(value.get(ITEMS_FIELD), ITEMS_FIELD)
            agent_items = _array(value.get(AGENTS_FIELD), AGENTS_FIELD)
            selected = tuple(cast(list[str], args.pane))
            result = (
                recover(selected, pane_items, agent_items)
                if operation is Operation.RECOVER
                else verify(selected, pane_items, agent_items)
            )
        print(json.dumps(result, sort_keys=True), file=output_stream)
        return command_exit_code(result)
    except AdapterError as error:
        print(
            json.dumps(
                {
                    SCHEMA_VERSION_FIELD: SCHEMA_VERSION,
                    STATUS_FIELD: error.status,
                    DETAIL_FIELD: str(error),
                },
                sort_keys=True,
            ),
            file=output_stream,
        )
        return 2


if __name__ == "__main__":
    sys.exit(main())
