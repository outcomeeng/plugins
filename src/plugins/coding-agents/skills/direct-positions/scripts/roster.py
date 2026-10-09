"""Print the Director's roster of positions as Markdown.

Each watched position is matched to its live session through the same
environment view the monitor uses, so the roster and the monitor never
disagree about which pane is which position.

Usage: python3 roster.py WATCH.json
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import environment

COLUMNS = ("Position", "Mail name", "Backend", "Worktree", "Pane", "State", "Context")


def _row(cells: list[str]) -> str:
    return "| " + " | ".join(cell.replace("|", "\\|") for cell in cells) + " |"


def _context(session: environment.Session) -> str:
    try:
        text = environment.BACKENDS[session.backend].read(session)
    except environment.AdapterError as error:
        return f"unread: {error}"
    used = environment.context_percent(text)
    return f"{used}%" if used is not None else "?"


def render(watch: dict, inventories: dict, now: datetime, read_context=_context) -> str:
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
            lines.append(_row(cells + ["?", f"inventory failed: {sessions}", "?"]))
            continue
        found = environment.find(
            sessions, cwd=entry.get("cwd"), handle=entry.get("handle")
        )
        if found is None:
            lines.append(_row(cells + ["-", "absent", "-"]))
        else:
            lines.append(_row(cells + [found.handle, found.state, read_context(found)]))
    for group in watch.get("groups", []):
        sessions = inventories.get(group["backend"])
        if isinstance(sessions, str):
            lines.append(
                _row(
                    [
                        group["label"],
                        "-",
                        group["backend"],
                        group["cwd_prefix"],
                        "?",
                        f"inventory failed: {sessions}",
                        "?",
                    ]
                )
            )
            continue
        for member in environment.under(
            sessions, group["cwd_prefix"], group.get("exclude", [])
        ):
            lines.append(
                _row(
                    [
                        f"{group['label']} {member.handle}",
                        "-",
                        member.backend,
                        member.cwd,
                        member.handle,
                        member.state,
                        read_context(member),
                    ]
                )
            )
    return "\n".join(lines) + "\n"


def inventories_for(watch: dict) -> dict:
    """Each backend's sessions, or the error text when its inventory failed."""
    backends = {e["backend"] for e in watch.get("sessions", [])} | {
        g["backend"] for g in watch.get("groups", [])
    }
    found: dict = {}
    for name in sorted(backends):
        try:
            found[name] = environment.BACKENDS[name].sessions()
        except environment.AdapterError as error:
            found[name] = str(error)
    return found


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print(
            "usage: roster.py WATCH.json — WATCH.json names the watched positions",
            file=sys.stderr,
        )
        return 2
    path = Path(argv[0])
    try:
        watch = json.loads(path.read_text())
    except FileNotFoundError:
        print(
            f"roster.py: no watch file at {path}; create it with one entry per position",
            file=sys.stderr,
        )
        return 2
    except json.JSONDecodeError as error:
        print(f"roster.py: {path} is not JSON: {error}", file=sys.stderr)
        return 2
    if "position" not in watch:
        print(
            f"roster.py: {path} lacks the top-level 'position' naming the watching position",
            file=sys.stderr,
        )
        return 2
    sys.stdout.write(render(watch, inventories_for(watch), datetime.now(timezone.utc)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
