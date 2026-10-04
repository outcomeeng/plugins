"""Print the Director's roster of positions as Markdown.

Each watched position is matched to its live session through the same
environment view the monitor uses, so the roster and the monitor never
disagree about which pane is which position.

Usage: python3 roster.py WATCH.json
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Callable, Mapping
from datetime import datetime, timezone
from pathlib import Path

import environment
import watch_file

COLUMNS = ("Position", "Mail name", "Backend", "Worktree", "Pane", "State", "Context")
ABSENT = "absent"
INVENTORY_FAILED = "inventory failed"

# One backend's inventory: its sessions, or the adapter's message when it failed.
Inventory = list[environment.Session] | str


def _row(cells: list[str]) -> str:
    return "| " + " | ".join(cell.replace("|", "\\|") for cell in cells) + " |"


def _context(session: environment.Session) -> str:
    try:
        text = environment.BACKENDS[session.backend].read(session)
    except environment.AdapterError as error:
        return f"unread: {error}"
    used = environment.context_percent(text)
    return f"{used}%" if used is not None else "?"


def render(
    watch: dict,
    inventories: Mapping[str, Inventory],
    now: datetime,
    read_context: Callable[[environment.Session], str] = _context,
) -> str:
    lines = [
        f"# Roster of {watch['position']}, {now.strftime('%Y-%m-%d %H:%MZ')}",
        "",
        _row(list(COLUMNS)),
        _row(["---"] * len(COLUMNS)),
    ]
    for entry in watch.get("sessions", []):
        sessions = inventories.get(entry["backend"])
        cells = [
            entry["position"],
            entry.get("mail_name", "?"),
            entry["backend"],
            entry.get("cwd", ""),
        ]
        if isinstance(sessions, str):
            lines.append(_row(cells + ["?", f"{INVENTORY_FAILED}: {sessions}", "?"]))
            continue
        found = environment.find(
            sessions or [], cwd=entry.get("cwd"), handle=entry.get("handle")
        )
        if found is None:
            lines.append(_row(cells + ["-", ABSENT, "-"]))
        else:
            lines.append(_row(cells + [found.handle, found.state, read_context(found)]))
    for group in watch.get("groups", []):
        sessions = inventories.get(group["backend"])
        if isinstance(sessions, str):
            cells = [
                group["label"],
                "-",
                group["backend"],
                group["cwd_prefix"],
                "?",
                f"{INVENTORY_FAILED}: {sessions}",
                "?",
            ]
            lines.append(_row(cells))
            continue
        for member in environment.under(
            sessions or [], group["cwd_prefix"], group.get("exclude", [])
        ):
            cells = [
                f"{group['label']} {member.handle}",
                "-",
                member.backend,
                member.cwd,
                member.handle,
                member.state,
                read_context(member),
            ]
            lines.append(_row(cells))
    return "\n".join(lines) + "\n"


def inventories_for(
    watch: dict, backends: Mapping[str, environment.Backend] | None = None
) -> dict[str, Inventory]:
    """Each backend's sessions, or the error text when its inventory failed."""
    backends = environment.BACKENDS if backends is None else backends
    names = {e["backend"] for e in watch.get("sessions", [])} | {
        g["backend"] for g in watch.get("groups", [])
    }
    found: dict[str, Inventory] = {}
    for name in sorted(names):
        try:
            found[name] = backends[name].sessions()
        except environment.AdapterError as error:
            found[name] = str(error)
    return found


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="roster.py",
        description="Print one Markdown row per watched position and group member.",
    )
    parser.add_argument("watch", type=Path, help="the watch file naming the positions")
    args = parser.parse_args(argv)
    try:
        watch = watch_file.load(args.watch)
    except watch_file.WatchFileError as error:
        print(f"roster.py: {error}", file=sys.stderr)
        return 2
    sys.stdout.write(render(watch, inventories_for(watch), datetime.now(timezone.utc)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
