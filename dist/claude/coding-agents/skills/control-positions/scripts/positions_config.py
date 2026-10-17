#!/usr/bin/env python3
"""Operator configuration of the position controller, read from one TOML file."""

from __future__ import annotations

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


def _number(
    table: Mapping[str, object],
    field: ConfigField,
    default: float,
    maximum: float | None = None,
) -> float:
    value = table.get(field, default)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ConfigurationError(field, "expected a number")
    if value <= 0:
        raise ConfigurationError(field, "expected a number above zero")
    if maximum is not None and value > maximum:
        raise ConfigurationError(field, f"expected a number no greater than {maximum}")
    return float(value)


def _boolean(table: Mapping[str, object], field: ConfigField) -> bool:
    value = table.get(field, False)
    if not isinstance(value, bool):
        raise ConfigurationError(field, "expected true or false")
    return value


def _text(table: Mapping[str, object], field: ConfigField, location: str) -> str:
    value = table.get(field)
    if not isinstance(value, str) or not value:
        raise ConfigurationError(field, f"expected text in {location}")
    return value


def _tables(
    value: object, field: ConfigField, location: str
) -> list[Mapping[str, object]]:
    if not isinstance(value, list):
        raise ConfigurationError(field, f"expected a list of tables in {location}")
    tables: list[Mapping[str, object]] = []
    for item in value:
        if not isinstance(item, dict):
            raise ConfigurationError(field, f"expected a table in {location}")
        tables.append(item)
    return tables


def _skip(table: Mapping[str, object]) -> frozenset[str]:
    value = table.get(ConfigField.SKIP, [])
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ConfigurationError(
            ConfigField.SKIP, "expected a list of pane titles or worktree paths"
        )
    return frozenset(str(item) for item in value)


def _pace(table: Mapping[str, object]) -> dict[str, float]:
    value = table.get(ConfigField.SUBSCRIPTIONS, {})
    if not isinstance(value, dict):
        raise ConfigurationError(
            ConfigField.SUBSCRIPTIONS, "expected one table per subscription"
        )
    pace: dict[str, float] = {}
    for name, subscription in value.items():
        if not isinstance(subscription, dict):
            raise ConfigurationError(
                ConfigField.SUBSCRIPTIONS, f"expected a table for {name}"
            )
        if ConfigField.PACE_TOKENS in subscription:
            pace[str(name)] = _number(subscription, ConfigField.PACE_TOKENS, 0)
    return pace


def _positions(table: Mapping[str, object]) -> tuple[Position, ...]:
    entries = _tables(
        table.get(ConfigField.POSITIONS, []), ConfigField.POSITIONS, "positions"
    )
    return tuple(
        Position(
            _text(entry, ConfigField.WORKTREE, "a position"),
            _text(entry, ConfigField.SUBSCRIPTION, "a position"),
        )
        for entry in entries
    )


def load_settings(path: Path) -> Settings:
    """Read and validate the configuration file; a changed file applies at the next read."""
    try:
        with path.open("rb") as handle:
            table = tomllib.load(handle)
    except FileNotFoundError as error:
        raise ConfigurationError(
            ConfigField.POSITIONS, f"configuration file not found: {path}"
        ) from error
    except (OSError, tomllib.TOMLDecodeError) as error:
        raise ConfigurationError(
            ConfigField.POSITIONS, f"configuration file unreadable: {error}"
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
