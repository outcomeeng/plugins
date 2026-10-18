#!/usr/bin/env python3
"""Operator configuration of the position controller, read from one TOML file."""

from __future__ import annotations

import math
import tomllib
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Final

CONFIG_DIRECTORY: Final = "outcome-engineering"
CONFIG_FILE: Final = "control-positions.toml"
XDG_CONFIG_HOME: Final = "XDG_CONFIG_HOME"
HOME_CONFIG_PARENT: Final = ".config"

DEFAULT_COMPACTION_CONTEXT_PERCENT: Final = 30
DEFAULT_COMPACTION_MULTIPLE: Final = 1.25
DEFAULT_PAUSE_MULTIPLE: Final = 2
DEFAULT_WEEKLY_CEILING_PERCENT: Final = 93
CEILING_MAXIMUM_PERCENT: Final = 95
PERCENT_MAXIMUM: Final = 100
MAX_CONFIG_BYTES: Final = 64 * 1024


class ConfigField(StrEnum):
    COMPACTION_CONTEXT_PERCENT = "compaction_context_percent"
    COMPACTION_MULTIPLE = "compaction_multiple"
    PAUSE_MULTIPLE = "pause_multiple"
    WEEKLY_CEILING_PERCENT = "weekly_ceiling_percent"
    KEY_AUTHORIZED = "key_authorized"
    STOP_AUTHORIZED = "stop_authorized"
    SKIP = "skip"
    SUBSCRIPTIONS = "subscriptions"
    PACE_TOKENS = "pace_tokens"
    POSITIONS = "positions"
    WORKTREE = "worktree"
    SUBSCRIPTION = "subscription"


class ConfigurationError(ValueError):
    """An invalid or unreadable configuration file, naming the rejected field."""

    def __init__(self, field: ConfigField, message: str) -> None:
        super().__init__(f"{field}: {message}")
        self.field = field


@dataclass(frozen=True)
class Position:
    worktree: str
    subscription: str


@dataclass(frozen=True)
class Settings:
    positions: tuple[Position, ...]
    pace: Mapping[str, float]
    skip: frozenset[str]
    compaction_context_percent: float
    compaction_multiple: float
    pause_multiple: float
    weekly_ceiling_percent: float
    key_authorized: bool
    stop_authorized: bool


def config_path(environ: Mapping[str, str], home: Path) -> Path:
    """Locate the configuration file under the XDG configuration home."""
    explicit = environ.get(XDG_CONFIG_HOME)
    base = Path(explicit) if explicit else home / HOME_CONFIG_PARENT
    return base / CONFIG_DIRECTORY / CONFIG_FILE


TOP_LEVEL: Final = "the top level of the file"
EXAMPLE_VALUES: Final = {
    ConfigField.COMPACTION_CONTEXT_PERCENT: "30",
    ConfigField.COMPACTION_MULTIPLE: "1.25",
    ConfigField.PAUSE_MULTIPLE: "2",
    ConfigField.WEEKLY_CEILING_PERCENT: "93",
    ConfigField.PACE_TOKENS: "50000",
    ConfigField.KEY_AUTHORIZED: "true",
    ConfigField.STOP_AUTHORIZED: "false",
}


def _received(value: object) -> str:
    return f"received {value!r} ({type(value).__name__})"


def _number(
    table: Mapping[str, object],
    field: ConfigField,
    default: float,
    maximum: float | None = None,
    location: str = TOP_LEVEL,
) -> float:
    value = table.get(field, default)
    example = EXAMPLE_VALUES[field]
    bound = f" no greater than {maximum}" if maximum is not None else ""
    valid = f"a finite number above zero{bound}"
    fix = f"set `{field} = {example}` in {location}"
    invalid = (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
        or value <= 0
        or (maximum is not None and value > maximum)
    )
    if invalid:
        raise ConfigurationError(
            field, f"in {location}, expected {valid}, {_received(value)}; {fix}"
        )
    return float(value)


def _boolean(table: Mapping[str, object], field: ConfigField) -> bool:
    value = table.get(field, False)
    if not isinstance(value, bool):
        raise ConfigurationError(
            field,
            f"in {TOP_LEVEL}, expected true or false, {_received(value)}; "
            f"set `{field} = {EXAMPLE_VALUES[field]}` without quotes",
        )
    return value


def _text(table: Mapping[str, object], field: ConfigField, location: str) -> str:
    value = table.get(field)
    if not isinstance(value, str) or not value:
        found = "the key is absent" if field not in table else _received(value)
        raise ConfigurationError(
            field,
            f"in {location}, expected non-empty text, {found}; "
            f'set `{field} = "..."` in {location}, for example '
            f'`[[positions]]` with `worktree = "/path/to/worktree"` and '
            f'`subscription = "name"`',
        )
    return value


def _tables(
    value: object, field: ConfigField, location: str
) -> list[Mapping[str, object]]:
    if not isinstance(value, list):
        raise ConfigurationError(
            field,
            f"expected an array of tables for `{field}`, {_received(value)}; "
            f"declare each one as a `[[{field}]]` section",
        )
    tables: list[Mapping[str, object]] = []
    for index, item in enumerate(value, start=1):
        if not isinstance(item, dict):
            raise ConfigurationError(
                field,
                f"in {location} entry {index}, expected a table, "
                f"{_received(item)}; declare it as a `[[{field}]]` section "
                f"with key = value lines beneath",
            )
        tables.append(item)
    return tables


def _skip(table: Mapping[str, object]) -> frozenset[str]:
    value = table.get(ConfigField.SKIP, [])
    if not isinstance(value, list):
        raise ConfigurationError(
            ConfigField.SKIP,
            f"expected a list of pane titles or worktree paths, "
            f'{_received(value)}; write `skip = ["pane title", "/path/to/worktree"]`',
        )
    for index, item in enumerate(value, start=1):
        if not isinstance(item, str) or not item:
            raise ConfigurationError(
                ConfigField.SKIP,
                f"in entry {index} of `skip`, expected non-empty text, "
                f"{_received(item)}; "
                f'write each entry as a quoted string, for example "pane title"',
            )
    return frozenset(value)


def _pace(table: Mapping[str, object]) -> dict[str, float]:
    value = table.get(ConfigField.SUBSCRIPTIONS, {})
    if not isinstance(value, dict):
        raise ConfigurationError(
            ConfigField.SUBSCRIPTIONS,
            f"expected one table per subscription, {_received(value)}; "
            f"declare each as `[subscriptions.NAME]` with "
            f"`pace_tokens = {EXAMPLE_VALUES[ConfigField.PACE_TOKENS]}`",
        )
    pace: dict[str, float] = {}
    for name, subscription in value.items():
        if not isinstance(subscription, dict):
            raise ConfigurationError(
                ConfigField.SUBSCRIPTIONS,
                f"in `subscriptions.{name}`, expected a table, "
                f"{_received(subscription)}; declare it as "
                f"`[subscriptions.{name}]` with "
                f"`pace_tokens = {EXAMPLE_VALUES[ConfigField.PACE_TOKENS]}`",
            )
        if ConfigField.PACE_TOKENS in subscription:
            pace[str(name)] = _number(
                subscription,
                ConfigField.PACE_TOKENS,
                0,
                location=f"[subscriptions.{name}]",
            )
    return pace


def _positions(table: Mapping[str, object]) -> tuple[Position, ...]:
    entries = _tables(
        table.get(ConfigField.POSITIONS, []), ConfigField.POSITIONS, "[[positions]]"
    )
    positions: list[Position] = []
    first_entry: dict[str, int] = {}
    for index, entry in enumerate(entries, start=1):
        location = f"[[positions]] entry {index}"
        worktree = _text(entry, ConfigField.WORKTREE, location)
        subscription = _text(entry, ConfigField.SUBSCRIPTION, location)
        if worktree in first_entry:
            raise ConfigurationError(
                ConfigField.WORKTREE,
                f"in {location}, the worktree {worktree!r} is already listed in "
                f"[[positions]] entry {first_entry[worktree]}; list each worktree "
                f"once, under one subscription",
            )
        first_entry[worktree] = index
        positions.append(Position(worktree, subscription))
    return tuple(positions)


def load_settings(path: Path) -> Settings:
    """Read and validate the configuration file; a changed file applies at the next read."""
    if path.is_symlink():
        raise ConfigurationError(
            ConfigField.POSITIONS,
            f"configuration file is symlinked: {path}; replace the link with a "
            f"regular file",
        )
    try:
        with path.open("rb") as handle:
            raw = handle.read(MAX_CONFIG_BYTES + 1)
        if len(raw) > MAX_CONFIG_BYTES:
            raise ConfigurationError(
                ConfigField.POSITIONS,
                f"configuration file is larger than {MAX_CONFIG_BYTES} bytes: "
                f"{path}; keep only the settings the controller reads",
            )
        table = tomllib.loads(raw.decode("utf-8"))
    except FileNotFoundError as error:
        raise ConfigurationError(
            ConfigField.POSITIONS,
            f"configuration file not found: {path}; create it with at least one "
            f'`[[positions]]` section holding `worktree = "..."` and '
            f'`subscription = "..."`',
        ) from error
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError) as error:
        raise ConfigurationError(
            ConfigField.POSITIONS,
            f"configuration file unreadable at {path}: {error}; fix the TOML syntax "
            f"or the file permissions named above",
        ) from error
    return Settings(
        positions=_positions(table),
        pace=_pace(table),
        skip=_skip(table),
        compaction_context_percent=_number(
            table,
            ConfigField.COMPACTION_CONTEXT_PERCENT,
            DEFAULT_COMPACTION_CONTEXT_PERCENT,
            PERCENT_MAXIMUM,
        ),
        compaction_multiple=_number(
            table, ConfigField.COMPACTION_MULTIPLE, DEFAULT_COMPACTION_MULTIPLE
        ),
        pause_multiple=_number(
            table, ConfigField.PAUSE_MULTIPLE, DEFAULT_PAUSE_MULTIPLE
        ),
        weekly_ceiling_percent=_number(
            table,
            ConfigField.WEEKLY_CEILING_PERCENT,
            DEFAULT_WEEKLY_CEILING_PERCENT,
            CEILING_MAXIMUM_PERCENT,
        ),
        key_authorized=_boolean(table, ConfigField.KEY_AUTHORIZED),
        stop_authorized=_boolean(table, ConfigField.STOP_AUTHORIZED),
    )
