"""Load and check the watch file the roster and the monitor read.

One check serves both scripts, so a malformed watch file fails the same way in
each and the message names the defect and its field path.
"""

from __future__ import annotations

import json
from pathlib import Path

import environment

THRESHOLDS = ("stall_minutes", "context_percent", "blocked_remind_minutes")
FLAGS = ("report_background", "expect_members")


class WatchFileError(ValueError):
    pass


def _text(entry: dict, field: str, where: str) -> None:
    value = entry.get(field)
    if not isinstance(value, str) or not value:
        raise WatchFileError(f"{where}.{field}: required, a non-empty string")


def _object(value: object, where: str) -> dict:
    if not isinstance(value, dict):
        raise WatchFileError(f"{where}: must be an object")
    return value


def _entry(entry: dict, where: str) -> None:
    backend = entry.get("backend")
    if backend not in environment.BACKENDS:
        known = ", ".join(sorted(environment.BACKENDS))
        raise WatchFileError(f"{where}.backend: {backend!r} is not one of {known}")
    for field in THRESHOLDS:
        if field in entry:
            value = entry[field]
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or value <= 0
            ):
                raise WatchFileError(f"{where}.{field}: must be a positive number")
    for field in FLAGS:
        if field in entry and not isinstance(entry[field], bool):
            raise WatchFileError(f"{where}.{field}: must be true or false")


def load(path: Path) -> dict:
    """The watch file's content, or WatchFileError naming the first defect."""
    try:
        watch = json.loads(path.read_text())
    except FileNotFoundError as error:
        raise WatchFileError(
            f"no watch file at {path}; create it with one entry per position"
        ) from error
    except json.JSONDecodeError as error:
        raise WatchFileError(f"{path} is not JSON: {error}") from error
    except OSError as error:
        raise WatchFileError(f"{path} cannot be read: {error}") from error
    watch = _object(watch, str(path))
    if not isinstance(watch.get("position"), str) or not watch["position"]:
        raise WatchFileError(
            f"{path} lacks the top-level 'position' naming the watching position"
        )
    if "mail" in watch:
        mail = _object(watch["mail"], "mail")
        _text(mail, "channel", "mail")
        _text(mail, "agent", "mail")
    for index, session in enumerate(watch.get("sessions", [])):
        where = f"sessions[{index}]"
        session = _object(session, where)
        _text(session, "position", where)
        _entry(session, where)
        if not isinstance(session.get("cwd") or session.get("handle"), str):
            raise WatchFileError(f"{where}: needs a 'cwd' or a 'handle'")
    for index, group in enumerate(watch.get("groups", [])):
        where = f"groups[{index}]"
        group = _object(group, where)
        _text(group, "label", where)
        _text(group, "cwd_prefix", where)
        _entry(group, where)
        exclude = group.get("exclude", [])
        if not isinstance(exclude, list) or not all(
            isinstance(x, str) for x in exclude
        ):
            raise WatchFileError(f"{where}.exclude: must be a list of paths")
    return watch
