#!/usr/bin/env python3
"""Recover SPX-selected native sessions in exact live Prowl panes."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Protocol, TextIO

SCHEMA_VERSION = 2
COMMAND_TIMEOUT_SECONDS = 15
PROWL_COMMAND = "prowl"
JSON_FLAG = "--json"
PROWL_LIST_COMMAND = (PROWL_COMMAND, "list", JSON_FLAG)
PROWL_AGENTS_COMMAND = (PROWL_COMMAND, "agents", JSON_FLAG)
PROWL_SEND_PREFIX = (PROWL_COMMAND, "send")
PANE_OPTION = "--pane"
NO_WAIT_OPTION = "--no-wait"
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

OK_FIELD = "ok"
DATA_FIELD = "data"
ITEMS_FIELD = "items"
AGENTS_FIELD = "agents"
WORKTREE_FIELD = "worktree"
PANE_FIELD = "pane"
ID_FIELD = "id"
PATH_FIELD = "path"
ROOT_PATH_FIELD = "root_path"
TYPE_FIELD = "type"
STATUS_FIELD = "status"
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


class Operation(StrEnum):
    RECOVER = "recover"
    VERIFY = "verify"


class ResultStatus(StrEnum):
    RESUMED = "resumed"
    ALREADY_CURRENT = "already-current"
    VERIFIED = "verified"
    INVALID_TARGET = "invalid-target"
    PANE_OCCUPIED = "pane-occupied"
    CORRELATION_INCOMPLETE = "correlation-incomplete"
    INVALID_SCHEMA = "invalid-schema"
    PROWL_UNAVAILABLE = "prowl-unavailable"
    COMMAND_FAILED = "command-failed"


class Resolution(StrEnum):
    RESUMED = "resumed"
    ALREADY_CORRELATED = "already-correlated"


@dataclass(frozen=True)
class CommandResult:
    returncode: int
    stdout: str
    stderr: str


class CommandRunner(Protocol):
    def run(
        self,
        argv: tuple[str, ...],
        cwd: Path | None = None,
        stdin: str | None = None,
    ) -> CommandResult: ...


@dataclass(frozen=True)
class SubprocessRunner:
    timeout_seconds: int = COMMAND_TIMEOUT_SECONDS

    def run(
        self,
        argv: tuple[str, ...],
        cwd: Path | None = None,
        stdin: str | None = None,
    ) -> CommandResult:
        try:
            completed = subprocess.run(
                argv,
                cwd=cwd,
                input=stdin,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                check=False,
            )
        except FileNotFoundError as error:
            status = (
                ResultStatus.PROWL_UNAVAILABLE
                if argv[0] == PROWL_COMMAND
                else ResultStatus.COMMAND_FAILED
            )
            raise AdapterError(
                status, f"Required command is unavailable: {argv[0]}"
            ) from error
        except subprocess.TimeoutExpired as error:
            raise AdapterError(
                ResultStatus.COMMAND_FAILED,
                f"Command exceeded the {self.timeout_seconds}-second bound: {' '.join(argv)}",
            ) from error
        return CommandResult(completed.returncode, completed.stdout, completed.stderr)


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


def _checked(result: CommandResult, command: tuple[str, ...]) -> str:
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "no command detail"
        raise AdapterError(
            ResultStatus.COMMAND_FAILED,
            f"Command failed ({result.returncode}): {' '.join(command)}: {detail}",
        )
    return result.stdout


def _json_result(result: CommandResult, command: tuple[str, ...]) -> dict[str, object]:
    raw = _checked(result, command)
    try:
        payload = _object(json.loads(raw), "response")
    except json.JSONDecodeError as error:
        raise AdapterError(
            ResultStatus.INVALID_SCHEMA,
            f"Command returned invalid JSON for {' '.join(command)}: {error.msg}",
        ) from error
    if payload.get(OK_FIELD) is not True:
        raise AdapterError(
            ResultStatus.COMMAND_FAILED,
            f"Command returned a non-success response: {' '.join(command)}",
        )
    return payload


def _public_items(payload: dict[str, object], field: str) -> list[dict[str, object]]:
    data = _object(payload.get(DATA_FIELD), f"response.{DATA_FIELD}")
    return _array(data.get(field), f"response.{DATA_FIELD}.{field}")


def _runtime_rosters(
    runner: CommandRunner,
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    panes = _public_items(
        _json_result(runner.run(PROWL_LIST_COMMAND), PROWL_LIST_COMMAND), ITEMS_FIELD
    )
    agents = _public_items(
        _json_result(runner.run(PROWL_AGENTS_COMMAND), PROWL_AGENTS_COMMAND),
        AGENTS_FIELD,
    )
    return panes, agents


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
                f"Prowl returned duplicate pane identity: {identity.pane_id}",
            )
        roster[identity.pane_id] = identity
    return roster


def _agent_roster(
    items: list[dict[str, object]],
) -> dict[str, list[AgentIdentity]]:
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
    selected: tuple[str, ...],
    panes: dict[str, PaneIdentity],
) -> dict[str, PaneIdentity]:
    missing = [pane_id for pane_id in selected if pane_id not in panes]
    if missing:
        raise AdapterError(
            ResultStatus.INVALID_TARGET,
            f"Selected Prowl panes do not exist: {', '.join(missing)}",
        )
    return {pane_id: panes[pane_id] for pane_id in selected}


def recovery_send_command(pane_id: str) -> tuple[str, ...]:
    return (
        *PROWL_SEND_PREFIX,
        PANE_OPTION,
        pane_id,
        NO_WAIT_OPTION,
        JSON_FLAG,
    )


def _send_text(runner: CommandRunner, pane_id: str, text: str) -> None:
    command = recovery_send_command(pane_id)
    _json_result(runner.run(command, stdin=text), command)


def recover(
    selected_pane_ids: tuple[str, ...],
    runner: CommandRunner,
) -> dict[str, object]:
    selected = _selected_pane_ids(selected_pane_ids)
    pane_items, agent_items = _runtime_rosters(runner)
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
            "schemaVersion": SCHEMA_VERSION,
            STATUS_FIELD: ResultStatus.PANE_OCCUPIED,
            "detail": (
                "Selected panes have non-native or multiple detected-agent "
                "correlations."
            ),
            OCCUPIED_PANE_IDS_FIELD: occupied,
            TARGETS_FIELD: [
                targets[pane_id].result(ResultStatus.PANE_OCCUPIED)
                for pane_id in occupied
            ],
        }

    results: list[dict[str, object]] = []
    resumed = 0
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
        _send_text(runner, pane_id, RECOVERY_INPUT)
        resumed += 1
        result = pane.result(Resolution.RESUMED)
        result[COMMAND_FIELD] = SPX_RESUME_COMMAND
        result[REASSESSMENT_SENT_FIELD] = True
        results.append(result)

    return {
        "schemaVersion": SCHEMA_VERSION,
        STATUS_FIELD: ResultStatus.RESUMED if resumed else ResultStatus.ALREADY_CURRENT,
        TARGETS_FIELD: results,
    }


def verify(
    selected_pane_ids: tuple[str, ...],
    runner: CommandRunner,
) -> dict[str, object]:
    selected = _selected_pane_ids(selected_pane_ids)
    pane_items, agent_items = _runtime_rosters(runner)
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
        "schemaVersion": SCHEMA_VERSION,
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
        command = subparsers.add_parser(operation)
        command.add_argument("--pane", action="append", required=True)
    return parser


def main(
    argv: list[str] | None = None,
    *,
    runner: CommandRunner | None = None,
    stdout: TextIO | None = None,
) -> int:
    args = _parser().parse_args(argv)
    operation = Operation(args.operation)
    command_runner = runner if runner is not None else SubprocessRunner()
    output_stream = stdout if stdout is not None else sys.stdout
    try:
        selected = tuple(args.pane)
        result = (
            recover(selected, command_runner)
            if operation is Operation.RECOVER
            else verify(selected, command_runner)
        )
        print(json.dumps(result, sort_keys=True), file=output_stream)
        passing = {
            ResultStatus.RESUMED,
            ResultStatus.ALREADY_CURRENT,
            ResultStatus.VERIFIED,
        }
        return 0 if result[STATUS_FIELD] in passing else 2
    except AdapterError as error:
        print(
            json.dumps(
                {
                    "schemaVersion": SCHEMA_VERSION,
                    STATUS_FIELD: error.status,
                    "detail": str(error),
                },
                sort_keys=True,
            ),
            file=output_stream,
        )
        return 2


if __name__ == "__main__":
    sys.exit(main())
