#!/usr/bin/env python3
"""Durable action records and cross-pass state of the position controller."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Final

POSITIONS_DIRECTORY: Final = "positions"
RECORD_SUFFIX: Final = ".json"
RECORD_NUMBER_WIDTH: Final = 8
STATE_FILE: Final = "control-positions-state.json"
STATE_TEMPORARY_SUFFIX: Final = ".tmp"
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


def _record_path(data_root: Path, number: int) -> Path:
    name = f"{number:0{RECORD_NUMBER_WIDTH}d}{RECORD_SUFFIX}"
    return data_root / POSITIONS_DIRECTORY / name


def read_records(data_root: Path) -> list[dict[str, object]]:
    """Return every durable record, oldest first."""
    records: list[dict[str, object]] = []
    number = FIRST_RECORD_NUMBER
    while (path := _record_path(data_root, number)).is_file():
        loaded = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(loaded, dict):
            records.append(loaded)
        number += 1
    return records


def append_record(data_root: Path, record: dict[str, object]) -> Path:
    """Write one record as the next numbered file; an existing file is never replaced."""
    (data_root / POSITIONS_DIRECTORY).mkdir(parents=True, exist_ok=True)
    number = FIRST_RECORD_NUMBER
    while True:
        path = _record_path(data_root, number)
        try:
            with path.open("x", encoding="utf-8") as handle:
                json.dump(record, handle, indent=2, sort_keys=True)
                handle.write("\n")
        except FileExistsError:
            number += 1
            continue
        return path


@dataclass
class PassState:
    streaks: dict[str, int] = field(default_factory=dict)
    paused: set[str] = field(default_factory=set)
    unfinished: list[str] = field(default_factory=list)


def load_state(data_root: Path) -> PassState:
    path = data_root / STATE_FILE
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return PassState()
    if not isinstance(loaded, dict):
        return PassState()
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
    temporary = path.with_suffix(STATE_TEMPORARY_SUFFIX)
    document = {
        StateField.STREAKS: state.streaks,
        StateField.PAUSED: sorted(state.paused),
        StateField.UNFINISHED: state.unfinished,
    }
    temporary.write_text(json.dumps(document, indent=2), encoding="utf-8")
    os.replace(temporary, path)
