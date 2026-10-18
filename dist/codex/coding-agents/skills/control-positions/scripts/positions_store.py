#!/usr/bin/env python3
"""Durable action records and cross-pass state of the position controller."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Final

from positions_siblings import publish

POSITIONS_DIRECTORY: Final = "positions"
RECORD_SUFFIX: Final = ".json"
RECORD_NUMBER_WIDTH: Final = 8
STATE_FILE: Final = "control-positions-state.json"
FIRST_RECORD_NUMBER: Final = 1


class Action(StrEnum):
    COMPACT = "compact"
    PAUSE = "pause"
    RESUME = "resume"
    STOP = "stop"


class RecordField(StrEnum):
    RECORDED_UTC = "recorded_utc"
    ACTION = "action"
    POSITION = "position"
    MEASUREMENT = "measurement"
    THRESHOLD = "threshold"
    REASON = "reason"


class StateField(StrEnum):
    STREAKS = "streaks"
    PAUSED = "paused"
    UNFINISHED = "unfinished"


class StoreError(ValueError):
    """A record or state file the controller refuses to read or replace."""


def _record_path(data_root: Path, number: int) -> Path:
    name = f"{number:0{RECORD_NUMBER_WIDTH}d}{RECORD_SUFFIX}"
    return data_root / POSITIONS_DIRECTORY / name


def _record_files(data_root: Path) -> list[Path]:
    """Every numbered record file, links included, in number order."""
    directory = data_root / POSITIONS_DIRECTORY
    if not directory.is_dir():
        return []
    return sorted(
        item
        for item in directory.iterdir()
        if item.suffix == RECORD_SUFFIX and item.stem.isdecimal()
    )


def _refuse_link(path: Path, what: str) -> None:
    if path.is_symlink():
        raise StoreError(
            f"{what} is symlinked: {path}; inspect the link target and remove the "
            "link before the next pass"
        )


def read_records(data_root: Path) -> list[dict[str, object]]:
    """Return every durable record, oldest first.

    A symlinked, unreadable, or malformed record is refused.
    """
    records: list[dict[str, object]] = []
    for path in _record_files(data_root):
        _refuse_link(path, "Record")
        if not path.is_file():
            continue
        try:
            loaded = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as error:
            raise StoreError(
                f"Record is unreadable or not valid JSON: {path}: {error}; inspect "
                "the file and correct or remove it"
            ) from error
        if isinstance(loaded, dict):
            records.append(loaded)
    return records


def append_record(data_root: Path, record: dict[str, object]) -> Path:
    """Publish one record as the next numbered file; an existing file is never reused."""
    (data_root / POSITIONS_DIRECTORY).mkdir(parents=True, exist_ok=True)
    taken = [int(item.stem) for item in _record_files(data_root)]
    number = max(taken, default=FIRST_RECORD_NUMBER - 1) + 1
    while (path := _record_path(data_root, number)).is_symlink() or path.exists():
        number += 1
    publish(path, json.dumps(record, indent=2, sort_keys=True) + "\n")
    return path


@dataclass
class PassState:
    streaks: dict[str, int] = field(default_factory=dict)
    paused: set[str] = field(default_factory=set)
    unfinished: list[str] = field(default_factory=list)


def load_state(data_root: Path) -> PassState:
    """Read the cross-pass state; an absent file is a first pass and reads as empty.

    A symlinked, unreadable, or malformed file is refused: reading it as empty would
    forget a paused position.
    """
    path = data_root / STATE_FILE
    _refuse_link(path, "State file")
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return PassState()
    except (OSError, ValueError) as error:
        raise StoreError(
            f"State file is unreadable or not valid JSON: {path}: {error}; inspect "
            "the file and correct or remove it"
        ) from error
    if not isinstance(loaded, dict):
        raise StoreError(
            f"State file does not hold a JSON object: {path}; inspect the file and "
            "correct or remove it"
        )
    streaks = loaded.get(StateField.STREAKS, {})
    paused = loaded.get(StateField.PAUSED, [])
    unfinished = loaded.get(StateField.UNFINISHED, [])
    return PassState(
        streaks={
            str(key): int(value)
            for key, value in (streaks.items() if isinstance(streaks, dict) else ())
            if isinstance(value, int)
        },
        paused={str(item) for item in paused} if isinstance(paused, list) else set(),
        unfinished=[str(item) for item in unfinished]
        if isinstance(unfinished, list)
        else [],
    )


def save_state(data_root: Path, state: PassState) -> None:
    data_root.mkdir(parents=True, exist_ok=True)
    path = data_root / STATE_FILE
    _refuse_link(path, "State file")
    document = {
        StateField.STREAKS: state.streaks,
        StateField.PAUSED: sorted(state.paused),
        StateField.UNFINISHED: state.unfinished,
    }
    publish(path, json.dumps(document, indent=2))
