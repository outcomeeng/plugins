"""A position's monitor.

Each poll reads the watch file and the state file, emits one line per new
signal, and writes the state file. With --every, the script polls in a loop
under the harness monitor facility and holds a lock so a re-arm never doubles
the signals; without it, the script polls once and exits.

Usage: python3 monitor.py WATCH.json STATE.json [--every SECONDS]
"""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import math
import os
import re
import sys
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum
from pathlib import Path

import environment
import position_mail
import watch_file

DEFAULT_BLOCKED_REMIND_MINUTES = 15


class Signal(StrEnum):
    MAIL = "MAIL"
    BLOCKED = "BLOCKED"
    WENT_IDLE = "WENT-IDLE"
    WAITING_ON_BACKGROUND = "WAITING-ON-BACKGROUND"
    STALLED = "STALLED"
    COMPACT_NOW = "COMPACT-NOW"
    COMPACT_AT_BOUNDARY = "COMPACT-AT-BOUNDARY"
    COMPACT_IDLE = "COMPACT-IDLE"
    ABSENT = "ABSENT"
    WATCH_BROKEN = "WATCH-BROKEN"
    WATCH_DUPLICATE = "WATCH-DUPLICATE"


# Context tiers, most urgent first: (threshold, applies only when the turn has ended, signal).
TIERS = (
    (85, False, Signal.COMPACT_NOW),
    (75, False, Signal.COMPACT_AT_BOUNDARY),
    (50, True, Signal.COMPACT_IDLE),
)
TIER_STEP_PERCENT = 5

Inbox = Callable[[str, str], list[position_mail.Record]]


@dataclass(frozen=True)
class Event:
    """One signal about one subject; `detail` carries its own leading separator."""

    signal: Signal
    subject: str
    detail: str = ""

    def line(self, position: str) -> str:
        return f"[{position}] {self.signal} {self.subject}{self.detail}"


def _minutes_since(stamp: str | None, now: datetime) -> float | None:
    if not stamp:
        return None
    then = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
    return (now - then).total_seconds() / 60


def _mail(watch: dict, state: dict, inbox: Inbox) -> list[Event]:
    mail = watch.get("mail")
    if not mail:
        return []
    try:
        records = inbox(mail["channel"], mail["agent"])
    except position_mail.MailError as error:
        return [Event(Signal.WATCH_BROKEN, "mail", f": {error}")]
    # A fresh state file takes the inbox as its baseline and withholds existing mail.
    baseline = "mail_last_id" not in state
    last = state.get("mail_last_id", 0)
    events = []
    for record in sorted(records, key=lambda r: r.id):
        if record.id > last and not baseline:
            events.append(
                Event(
                    Signal.MAIL,
                    str(record.id),
                    f" from {record.sender}: {record.subject}",
                )
            )
    state["mail_last_id"] = max([last] + [r.id for r in records])
    return events


def _targets(
    watch: dict, inventories: Mapping[str, list[environment.Session]]
) -> dict[str, tuple[environment.Session | None, dict]]:
    """Every watched name mapped to its live session (or None) and its watch entry."""
    targets: dict[str, tuple[environment.Session | None, dict]] = {}
    for entry in watch.get("sessions", []):
        sessions = inventories.get(entry["backend"])
        if sessions is None:
            continue
        found = environment.find(
            sessions, cwd=entry.get("cwd"), handle=entry.get("handle")
        )
        targets[entry["position"]] = (found, entry)
    for group in watch.get("groups", []):
        sessions = inventories.get(group["backend"])
        if sessions is None:
            continue
        members = environment.under(
            sessions, group["cwd_prefix"], group.get("exclude", [])
        )
        if not members and group.get("expect_members"):
            targets[group["label"]] = (None, group)
        for member in members:
            targets[f"{group['label']} {member.handle}"] = (member, group)
    return targets


def _session(
    name: str,
    session: environment.Session | None,
    entry: dict,
    previous: dict,
    now: datetime,
    backends: Mapping[str, environment.Backend],
    events: list[Event],
) -> dict:
    if session is None:
        if previous.get("state") != "absent":
            events.append(Event(Signal.ABSENT, name, ": no session"))
        return {"state": "absent"}

    text = None
    needs_text = (
        entry.get("context_percent")
        or entry.get("stall_minutes")
        or (
            session.backend != environment.Prowl.name
            and session.state in environment.ENDED
        )
    )
    if needs_text:
        try:
            text = backends[session.backend].read(session)
        except environment.AdapterError as error:
            events.append(Event(Signal.WATCH_BROKEN, f"read {name}", f": {error}"))
    used = environment.context_percent(text) if text else None
    background = environment.background_work(session, text)
    shown = f"{used}%" if used is not None else "?%"

    was = previous.get("state")
    parked = previous.get("parked", False)
    current = {
        "state": session.state,
        "changed_at": session.changed_at,
        "context": used,
    }

    if session.state == environment.State.BLOCKED:
        # Reported on first sight, baseline included, and again every remind interval.
        remind = entry.get("blocked_remind_minutes", DEFAULT_BLOCKED_REMIND_MINUTES)
        since = _minutes_since(previous.get("blocked_reported_at"), now)
        if was != environment.State.BLOCKED or since is None or since >= remind:
            held = _minutes_since(previous.get("blocked_since"), now)
            waited = (
                f" for {held:.0f} min"
                if was == environment.State.BLOCKED and held is not None
                else ""
            )
            events.append(
                Event(
                    Signal.BLOCKED,
                    name,
                    f" {shown}{waited}: waiting at an approval or question; read the pane and dispose of it",
                )
            )
            current["blocked_reported_at"] = now.isoformat()
        else:
            current["blocked_reported_at"] = previous.get("blocked_reported_at")
        current["blocked_since"] = (
            previous.get("blocked_since")
            if was == environment.State.BLOCKED
            else now.isoformat()
        )
    elif was == environment.State.WORKING and session.state in environment.ENDED:
        if background:
            # A position resting on its own monitor parks silently when its watch entry says so.
            parked = True
            if entry.get("report_background", True):
                events.append(
                    Event(
                        Signal.WAITING_ON_BACKGROUND,
                        name,
                        f" {shown}: turn ended with work still running; do not prompt",
                    )
                )
        else:
            events.append(
                Event(
                    Signal.WENT_IDLE,
                    name,
                    f" {shown}: finished a leg; needs a prompt or a disposition",
                )
            )
    elif session.state in environment.ENDED and parked and not background:
        parked = False
        events.append(
            Event(
                Signal.WENT_IDLE,
                name,
                f" {shown}: background work ended; needs a disposition",
            )
        )
    elif session.state == environment.State.WORKING:
        parked = False
    current["parked"] = parked

    # Activity is a change in the pane's text with every digit removed, so ticking
    # timers and token counters in a hung session do not count as progress.
    stall = entry.get("stall_minutes")
    if stall and text is not None:
        digest = hashlib.sha256(re.sub(r"\d", "", text).encode()).hexdigest()
        active_at = previous.get("active_at")
        if digest != previous.get("digest") or active_at is None:
            active_at = now.isoformat()
        current["digest"], current["active_at"] = digest, active_at
        quiet = _minutes_since(active_at, now)
        if (
            session.state == environment.State.WORKING
            and quiet is not None
            and quiet >= stall
        ):
            if not previous.get("stall_reported"):
                events.append(
                    Event(
                        Signal.STALLED,
                        name,
                        f": pane unchanged for {quiet:.0f} min while working",
                    )
                )
            current["stall_reported"] = True

    reported = dict(previous.get("tiers", {}))
    if used is not None and entry.get("context_percent"):
        tier = next(
            (
                t
                for t in TIERS
                if used >= t[0] and (not t[1] or session.state in environment.ENDED)
            ),
            None,
        )
        if tier:
            bucket = used // TIER_STEP_PERCENT
            if reported.get(tier[2]) != bucket:
                events.append(Event(tier[2], name, f" {used}% state={session.state}"))
            reported = {tier[2]: bucket}
        else:
            reported = {}
    current["tiers"] = reported
    return current


def poll(
    watch: dict,
    state: dict,
    now: datetime,
    *,
    backends: Mapping[str, environment.Backend] | None = None,
    inbox: Inbox | None = None,
) -> list[Event]:
    """One poll: the new signals, with `state` updated in place."""
    backends = environment.BACKENDS if backends is None else backends
    events = _mail(watch, state, position_mail.inbox if inbox is None else inbox)

    names = {e["backend"] for e in watch.get("sessions", [])} | {
        g["backend"] for g in watch.get("groups", [])
    }
    inventories: dict[str, list[environment.Session]] = {}
    for name in sorted(names):
        try:
            inventories[name] = backends[name].sessions()
        except environment.AdapterError as error:
            events.append(Event(Signal.WATCH_BROKEN, f"{name} inventory", f": {error}"))

    seen = state.setdefault("sessions", {})
    targets = _targets(watch, inventories)
    for name, (session, entry) in targets.items():
        seen[name] = _session(
            name, session, entry, seen.get(name, {}), now, backends, events
        )
    # A group member that disappeared since the last poll.
    for name in [
        n for n in seen if n not in targets and seen[n].get("state") != "absent"
    ]:
        if any(name.startswith(g["label"] + " ") for g in watch.get("groups", [])):
            events.append(Event(Signal.ABSENT, name, ": session ended"))
            seen[name] = {"state": "absent"}
    return events


def load_state(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        state = json.loads(path.read_text())
    except json.JSONDecodeError as error:
        raise watch_file.WatchFileError(f"{path} is not JSON: {error}") from error
    if not isinstance(state, dict):
        raise watch_file.WatchFileError(f"{path} must hold a JSON object")
    return state


def poll_once(watch_path: Path, state_path: Path) -> None:
    watch = watch_file.load(watch_path)
    state = load_state(state_path)
    events = poll(watch, state, datetime.now(timezone.utc))
    state_path.write_text(json.dumps(state, indent=2))
    for event in events:
        print(event.line(watch["position"]), flush=True)


def _positive_seconds(text: str) -> float:
    try:
        seconds = float(text)
    except ValueError as error:
        raise argparse.ArgumentTypeError(
            f"{text!r} is not a number of seconds"
        ) from error
    if not (math.isfinite(seconds) and seconds > 0):
        raise argparse.ArgumentTypeError(
            f"{text!r} must be a positive, finite number of seconds"
        )
    return seconds


def take_lock(path: Path):
    """The open lock file this process holds, or None when another loop holds it.

    The kernel releases the lock when its holder ends, so a lock file left by
    a dead process is taken over by the next loop.
    """
    handle = path.open("a+")
    try:
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        handle.close()
        return None
    handle.seek(0)
    handle.truncate()
    handle.write(str(os.getpid()))
    handle.flush()
    return handle


def _holder(path: Path) -> str:
    try:
        return path.read_text().strip() or "?"
    except OSError:
        return "?"


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="monitor.py",
        description="Emit one line per new signal about the watched positions.",
    )
    parser.add_argument("watch", type=Path, help="the watch file naming the positions")
    parser.add_argument("state", type=Path, help="the state file the monitor writes")
    parser.add_argument(
        "--every",
        type=_positive_seconds,
        help="poll in a loop at this interval instead of once",
    )
    args = parser.parse_args(argv)
    try:
        watch_file.load(args.watch)
        load_state(args.state)
    except watch_file.WatchFileError as error:
        print(f"monitor.py: {error}", file=sys.stderr)
        return 2
    if args.every is None:
        poll_once(args.watch, args.state)
        return 0
    lock = Path(f"{args.state}.lock")
    held = take_lock(lock)
    if held is None:
        print(
            f"{Signal.WATCH_DUPLICATE} another loop ({_holder(lock)}) already watches {args.state}; this copy exits",
            flush=True,
        )
        return 0
    with held:
        while True:
            try:
                poll_once(args.watch, args.state)
            except Exception as error:  # a broken poll reports and the loop goes on
                print(
                    f"{Signal.WATCH_BROKEN} monitor.py poll failed: {error}", flush=True
                )
            time.sleep(args.every)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
