"""Load and check the Director's watch file and the monitor's state file.

Every defect raises InputError naming the file and the field at fault, so the
roster and the monitor exit nonzero before reading a session or writing state.
"""

from __future__ import annotations

import json
import math
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import cast

import environment

# Top-level fields.
POSITION = "position"
MAIL = "mail"
SESSIONS = "sessions"
GROUPS = "groups"
# Fields of the mail entry.
CHANNEL = "channel"
AGENT = "agent"
# Fields of a session or group entry.
BACKEND = "backend"
CWD = "cwd"
HANDLE = "handle"
MAIL_NAME = "mail_name"
LABEL = "label"
CWD_PREFIX = "cwd_prefix"
EXCLUDE = "exclude"
STALL_MINUTES = "stall_minutes"
CONTEXT_PERCENT = "context_percent"
BLOCKED_REMIND_MINUTES = "blocked_remind_minutes"
REPORT_BACKGROUND = "report_background"
EXPECT_MEMBERS = "expect_members"

# Thresholds an entry may set; each is a positive number.
THRESHOLDS = (STALL_MINUTES, CONTEXT_PERCENT, BLOCKED_REMIND_MINUTES)

type Watch = dict[str, object]
type Check = Callable[[object, str], None]


class InputError(ValueError):
    """A watch or state file the scripts refuse, with the defect named."""


def _text(value: object, where: str) -> None:
    if not isinstance(value, str) or not value:
        raise InputError(f"{where} must be a non-empty string")


def _positive(value: object, where: str) -> None:
    number = isinstance(value, int | float) and not isinstance(value, bool)
    if not number or not math.isfinite(cast(float, value)) or cast(float, value) <= 0:
        raise InputError(f"{where} must be a positive number")


def _flag(value: object, where: str) -> None:
    if not isinstance(value, bool):
        raise InputError(f"{where} must be true or false")


def _backend(value: object, where: str) -> None:
    if value not in environment.BACKENDS:
        raise InputError(
            f"{where} must be one of {', '.join(sorted(environment.BACKENDS))}"
        )


def _paths(value: object, where: str) -> None:
    if not isinstance(value, list):
        raise InputError(f"{where} must be a list of paths")
    for index, item in enumerate(value):
        _text(item, f"{where}[{index}]")


_SESSION_FIELDS: Mapping[str, Check] = {
    POSITION: _text,
    BACKEND: _backend,
    CWD: _text,
    HANDLE: _text,
    MAIL_NAME: _text,
    REPORT_BACKGROUND: _flag,
    **dict.fromkeys(THRESHOLDS, _positive),
}
_SESSION_REQUIRED = (POSITION, BACKEND)

_GROUP_FIELDS: Mapping[str, Check] = {
    LABEL: _text,
    BACKEND: _backend,
    CWD_PREFIX: _text,
    EXCLUDE: _paths,
    EXPECT_MEMBERS: _flag,
    REPORT_BACKGROUND: _flag,
    **dict.fromkeys(THRESHOLDS, _positive),
}
_GROUP_REQUIRED = (LABEL, BACKEND, CWD_PREFIX)

_MAIL_FIELDS: Mapping[str, Check] = {CHANNEL: _text, AGENT: _text}


def _entry(
    value: object,
    where: str,
    fields: Mapping[str, Check],
    required: tuple[str, ...],
) -> Mapping[str, object]:
    if not isinstance(value, dict):
        raise InputError(f"{where} must be an object")
    entry = cast(Mapping[str, object], value)
    for name in required:
        if name not in entry:
            raise InputError(f"{where}.{name} is required")
    for name, item in entry.items():
        check = fields.get(name)
        if check is None:
            raise InputError(f"{where}.{name} is not a watch field")
        check(item, f"{where}.{name}")
    return entry


def _entries(watch: Mapping[str, object], key: str) -> list[object]:
    value = watch.get(key, [])
    if not isinstance(value, list):
        raise InputError(f"{key} must be a list")
    return cast(list[object], value)


def check(watch: object) -> Watch:
    """The watch document when it keeps the contract; InputError naming the defect otherwise."""
    if not isinstance(watch, dict):
        raise InputError("the watch file must be an object")
    document = cast(Watch, watch)
    if POSITION not in document:
        raise InputError(f"{POSITION} is required: the watching position's name")
    _text(document[POSITION], POSITION)
    for name in document:
        if name not in (POSITION, MAIL, SESSIONS, GROUPS):
            raise InputError(f"{name} is not a watch field")
    if MAIL in document:
        _entry(document[MAIL], MAIL, _MAIL_FIELDS, (CHANNEL, AGENT))
    for index, item in enumerate(_entries(document, SESSIONS)):
        where = f"{SESSIONS}[{index}]"
        entry = _entry(item, where, _SESSION_FIELDS, _SESSION_REQUIRED)
        if CWD not in entry and HANDLE not in entry:
            raise InputError(f"{where} names neither {CWD} nor {HANDLE}")
    for index, item in enumerate(_entries(document, GROUPS)):
        _entry(item, f"{GROUPS}[{index}]", _GROUP_FIELDS, _GROUP_REQUIRED)
    return document


def _json(path: Path) -> object:
    try:
        text = path.read_text()
    except FileNotFoundError as error:
        raise InputError(f"{path}: no such file") from error
    except OSError as error:
        raise InputError(f"{path}: unreadable: {error}") from error
    try:
        return json.loads(text)
    except json.JSONDecodeError as error:
        raise InputError(f"{path} is not JSON: {error}") from error


def load(path: Path) -> Watch:
    """The checked watch file at `path`."""
    try:
        return check(_json(path))
    except InputError as error:
        message = str(error)
        raise InputError(
            message if message.startswith(str(path)) else f"{path}: {message}"
        ) from error


def load_state(path: Path) -> dict[str, object]:
    """The monitor's state file at `path`, or an empty state when it does not exist yet."""
    if not path.exists():
        return {}
    state = _json(path)
    if not isinstance(state, dict):
        raise InputError(f"{path}: the state file must be an object")
    return cast(dict[str, object], state)
