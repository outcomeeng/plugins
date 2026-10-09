"""Print the Director's roster of positions as Markdown on standard output.

Each watched position is matched to its live session through the same
environment view the monitor uses, so the roster and the monitor never
disagree about which pane is which position.

Usage: python3 roster.py WATCH.json
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Callable, Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import cast

import environment
import watch_file

COLUMNS = ("Position", "Mail name", "Backend", "Worktree", "Pane", "State", "Context")
ABSENT = "absent"
INVENTORY_FAILED = "inventory failed"
UNKNOWN_CELL = "?"
EMPTY_CELL = "-"
EXIT_INVALID = 2

# A backend's sessions, or the error text when its inventory failed.
type Inventory = Sequence[environment.Session] | str
type ReadContext = Callable[[environment.Session], str]


def _row(cells: Sequence[str]) -> str:
    return "| " + " | ".join(cell.replace("|", "\\|") for cell in cells) + " |"


def _context(session: environment.Session) -> str:
    try:
        text = environment.BACKENDS[session.backend].read(session)
    except environment.AdapterError as error:
        return f"unread: {error}"
    used = environment.context_percent(text)
    return f"{used}%" if used is not None else UNKNOWN_CELL


def _entries(watch: Mapping[str, object], key: str) -> list[Mapping[str, str]]:
    return cast(list[Mapping[str, str]], watch.get(key, []))


def render(
    watch: Mapping[str, object],
    inventories: Mapping[str, Inventory],
    now: datetime,
    read_context: ReadContext = _context,
) -> str:
    lines = [
        f"# Roster of {watch[watch_file.POSITION]}, {now.strftime('%Y-%m-%d %H:%MZ')}",
        "",
        _row(COLUMNS),
        _row(["---"] * len(COLUMNS)),
    ]
    for entry in _entries(watch, watch_file.SESSIONS):
        backend = entry[watch_file.BACKEND]
        sessions = inventories.get(backend, [])
        cells = [
            entry[watch_file.POSITION],
            entry.get(watch_file.MAIL_NAME, UNKNOWN_CELL),
            backend,
            entry.get(watch_file.CWD, ""),
        ]
        if isinstance(sessions, str):
            failed = f"{INVENTORY_FAILED}: {sessions}"
            lines.append(_row([*cells, UNKNOWN_CELL, failed, UNKNOWN_CELL]))
            continue
        found = environment.find(
            sessions, cwd=entry.get(watch_file.CWD), handle=entry.get(watch_file.HANDLE)
        )
        if found is None:
            lines.append(_row([*cells, EMPTY_CELL, ABSENT, EMPTY_CELL]))
        else:
            row = [*cells, found.handle, str(found.state), read_context(found)]
            lines.append(_row(row))
    for group in _entries(watch, watch_file.GROUPS):
        label = group[watch_file.LABEL]
        backend = group[watch_file.BACKEND]
        prefix = group[watch_file.CWD_PREFIX]
        sessions = inventories.get(backend, [])
        if isinstance(sessions, str):
            failed = f"{INVENTORY_FAILED}: {sessions}"
            cells = [label, EMPTY_CELL, backend, prefix, UNKNOWN_CELL, failed]
            lines.append(_row([*cells, UNKNOWN_CELL]))
            continue
        exclude = cast(Sequence[str], group.get(watch_file.EXCLUDE, []))
        for member in environment.under(sessions, prefix, exclude):
            lines.append(
                _row(
                    [
                        f"{label} {member.handle}",
                        EMPTY_CELL,
                        member.backend,
                        member.cwd,
                        member.handle,
                        str(member.state),
                        read_context(member),
                    ]
                )
            )
    return "\n".join(lines) + "\n"


def inventories_for(watch: Mapping[str, object]) -> dict[str, Inventory]:
    """Each watched backend's sessions, or the error text when its inventory failed."""
    entries = [
        *_entries(watch, watch_file.SESSIONS),
        *_entries(watch, watch_file.GROUPS),
    ]
    found: dict[str, Inventory] = {}
    for name in sorted({entry[watch_file.BACKEND] for entry in entries}):
        try:
            found[name] = environment.BACKENDS[name].sessions()
        except environment.AdapterError as error:
            found[name] = str(error)
    return found


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="roster.py", description="Print the Director's roster of positions."
    )
    parser.add_argument("watch", type=Path, help="the watch file naming the positions")
    return parser


def main(argv: Sequence[str]) -> int:
    arguments = _parser().parse_args(argv)
    try:
        watch = watch_file.load(arguments.watch)
    except watch_file.InputError as error:
        print(f"roster.py: {error}", file=sys.stderr)
        return EXIT_INVALID
    sys.stdout.write(render(watch, inventories_for(watch), datetime.now(UTC)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
