"""A position's monitor.

Each poll reads the watch file and the state file, emits one line per new
signal, and writes the state file. With --every and --deadline, the script
polls in a loop until the deadline, measured from its start, and holds a lock
so a re-arm never doubles the signals; with neither, it polls once and exits.

Usage: python3 monitor.py WATCH.json STATE.json [--every SECONDS --deadline SECONDS]
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
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import cast

import environment
import position_mail
import watch_file


class Signal(StrEnum):
    MAIL = "MAIL"
    BLOCKED = "BLOCKED"
    WENT_IDLE = "WENT-IDLE"
    WAITING_ON_BACKGROUND = "WAITING-ON-BACKGROUND"
    STALLED = "STALLED"
    ABSENT = "ABSENT"
    WATCH_BROKEN = "WATCH-BROKEN"
    WATCH_DUPLICATE = "WATCH-DUPLICATE"
    COMPACT_NOW = "COMPACT-NOW"
    COMPACT_IDLE = "COMPACT-IDLE"
    COMPACT_AT_BOUNDARY = "COMPACT-AT-BOUNDARY"


# Context tiers, most urgent first: (threshold, applies only when the turn has ended, signal).
TIERS = (
    (85, False, Signal.COMPACT_NOW),
    (75, True, Signal.COMPACT_IDLE),
    (75, False, Signal.COMPACT_AT_BOUNDARY),
)
# A tier is reported once per step of this many percentage points.
TIER_STEP_PERCENT = 5
DEFAULT_BLOCKED_REMIND_MINUTES = 15
# A failing source is reported when it fails on this many polls in a row.
BROKEN_AFTER_POLLS = 2

EVERY_OPTION = "--every"
DEADLINE_OPTION = "--deadline"
EXIT_INVALID = 2
LOCK_SUFFIX = ".lock"
MAIL_SOURCE = "mail"

# The disposition each signal calls for, from the authority map and the Spec Tree foundation.
GATE = (
    "before any ruling, read the malleability of every node the changeset touches: "
    "spec = Validate, reachability tests, tagged results; verification adds Review; "
    "only implementation adds evidence audits. A gate the nodes do not require never launches"
)
RULES = {
    "note": "compact it now: /compact, wait for its context to drop, send its resume line",
    "shape": "forward it to the owner its authority map names, then receipt; judge nothing in it",
    "status": "read its blocked and next lines; act only on a step-in trigger; a reported rejection: check the gate applied",
    "gate": GATE,
    "question": (
        "find the owner: inside one Product it is the Maintainer's (answer 'the decision is yours'); "
        "delivery mechanics are the Orchestrator's; only order across Products, the operating model and the board are yours"
    ),
    "other": "verify it against the store or git before acting; receipt after handling",
    "blocked": (
        "read the pane: a read a higher rank ordered, approve; a guard or destructive prompt, "
        "Escape; never allow"
    ),
    "idle": "read its last lines: a finished leg its skill continues is left alone; open work gets its next step; a question to the operator it waits on is answered by its owner within 15 minutes, or asked through AskUserQuestion when none can",
    "background": "its turn ended with work still running; the harness re-invokes it when that work ends",
    "stalled": "read the pane and the transcript; a stall over 15 min is a step-in trigger",
    "absent": "open work goes to restart.md",
    "executor": "its Orchestrator owns it: check the Orchestrator is disposing of it; never prompt an Executor",
    Signal.COMPACT_NOW: "order its note now; compact on 'note written'",
    Signal.COMPACT_IDLE: "order its note now; compact on 'note written'",
    Signal.COMPACT_AT_BOUNDARY: "order its note for the end of its current step",
}
_GATE_WORDS = re.compile(
    r"\b(audits?|auditor|reviews?|reviewer|gates?|reject\w*|verdicts?|verifier|fixer|evidence|runs?)\b",
    re.IGNORECASE,
)

# Keys of the state file.
MAIL_LAST_ID = "mail_last_id"
BROKEN = "broken"
SESSIONS = "sessions"
STATE = "state"
CHANGED_AT = "changed_at"
CONTEXT = "context"
PARKED = "parked"
BLOCKED_SINCE = "blocked_since"
BLOCKED_REPORTED_AT = "blocked_reported_at"
DIGEST = "digest"
ACTIVE_AT = "active_at"
STALL_REPORTED = "stall_reported"
REPORTED_TIERS = "tiers"
ABSENT_STATE = "absent"

type Entry = Mapping[str, object]
type SessionState = dict[str, object]
type Inbox = Callable[[str, str], list[position_mail.Record]]


@dataclass(frozen=True)
class Event:
    signal: Signal
    subject: str
    detail: str

    def line(self, watcher: str) -> str:
        return f"[{watcher}] {self.signal} {self.subject}: {self.detail}"


def mail_rule(subject: str) -> str:
    """The disposition a position mail calls for, read from its subject."""
    lowered = subject.lower()
    if "note written" in lowered:
        return RULES["note"]
    if lowered.lstrip("[").startswith("status"):
        return RULES["status"]
    answers = lowered.startswith(("re ", "re:", "correction"))
    if not answers and (
        lowered.lstrip("[").startswith(("shape review", "review"))
        or re.search(r"\bdraft\b", lowered)
    ):
        return RULES["shape"]
    if _GATE_WORDS.search(subject):
        return RULES["gate"]
    if "?" in subject or "question" in lowered:
        return RULES["question"]
    return RULES["other"]


class _Poll:
    """One poll's state, clock, and the events it emits."""

    def __init__(self, state: dict[str, object], now: datetime) -> None:
        self.state = state
        self.now = now
        self.events: list[Event] = []

    def emit(self, signal: Signal, subject: str, detail: str) -> None:
        self.events.append(Event(signal, subject, detail))

    def broken(self, source: str, error: Exception) -> None:
        """Report a failing source only when it fails again on the next poll."""
        counts = cast(dict[str, int], self.state.setdefault(BROKEN, {}))
        counts[source] = counts.get(source, 0) + 1
        if counts[source] == BROKEN_AFTER_POLLS:
            detail = f"{error} ({BROKEN_AFTER_POLLS} polls in a row; polling goes on)"
            self.emit(Signal.WATCH_BROKEN, source, detail)

    def healthy(self, source: str) -> None:
        cast(dict[str, int], self.state.setdefault(BROKEN, {})).pop(source, None)

    def minutes_since(self, stamp: object) -> float | None:
        if not isinstance(stamp, str) or not stamp:
            return None
        then = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
        return (self.now - then).total_seconds() / 60


def _mail(watch: Mapping[str, object], run: _Poll, inbox: Inbox) -> None:
    mail = cast(Mapping[str, str] | None, watch.get(watch_file.MAIL))
    if not mail:
        return
    try:
        records = inbox(mail[watch_file.CHANNEL], mail[watch_file.AGENT])
    except position_mail.MailError as error:
        run.broken(MAIL_SOURCE, error)
        return
    run.healthy(MAIL_SOURCE)
    newest = max((record.id for record in records), default=0)
    if MAIL_LAST_ID not in run.state:
        # A fresh state file withholds the mail that existed before it.
        run.state[MAIL_LAST_ID] = newest
        return
    last = cast(int, run.state[MAIL_LAST_ID])
    for record in sorted(records, key=lambda r: r.id):
        if record.id > last:
            detail = (
                f"from {record.sender}: {record.subject} → {mail_rule(record.subject)}"
            )
            run.emit(Signal.MAIL, str(record.id), detail)
    run.state[MAIL_LAST_ID] = max(last, newest)


def _targets(
    watch: Mapping[str, object],
    inventories: Mapping[str, list[environment.Session]],
) -> dict[str, tuple[environment.Session | None, Entry]]:
    """Every watched name mapped to its live session (or None) and its watch entry."""
    targets: dict[str, tuple[environment.Session | None, Entry]] = {}
    for entry in cast(list[Entry], watch.get(watch_file.SESSIONS, [])):
        sessions = inventories.get(cast(str, entry[watch_file.BACKEND]))
        if sessions is None:
            continue
        found = environment.find(
            sessions,
            cwd=cast(str | None, entry.get(watch_file.CWD)),
            handle=cast(str | None, entry.get(watch_file.HANDLE)),
        )
        targets[cast(str, entry[watch_file.POSITION])] = (found, entry)
    for group in cast(list[Entry], watch.get(watch_file.GROUPS, [])):
        sessions = inventories.get(cast(str, group[watch_file.BACKEND]))
        if sessions is None:
            continue
        label = cast(str, group[watch_file.LABEL])
        members = environment.under(
            sessions,
            cast(str, group[watch_file.CWD_PREFIX]),
            cast(list[str], group.get(watch_file.EXCLUDE, [])),
        )
        if not members and group.get(watch_file.EXPECT_MEMBERS):
            targets[label] = (None, group)
        for member in members:
            targets[f"{label} {member.handle}"] = (member, group)
    return targets


def _blocked(
    name: str,
    entry: Entry,
    previous: SessionState,
    current: SessionState,
    shown: str,
    run: _Poll,
) -> None:
    """Report a block at once and again every remind interval; a group member only once it has lasted."""
    member = watch_file.CWD_PREFIX in entry
    was = previous.get(STATE)
    remind = cast(
        float,
        entry.get(watch_file.BLOCKED_REMIND_MINUTES, DEFAULT_BLOCKED_REMIND_MINUTES),
    )
    since = run.minutes_since(previous.get(BLOCKED_REPORTED_AT))
    held = run.minutes_since(previous.get(BLOCKED_SINCE))
    due = was != environment.State.BLOCKED or since is None or since >= remind
    if member:
        # An Executor's prompt is its Orchestrator's; the Director checks only a long one.
        due = (
            was == environment.State.BLOCKED
            and held is not None
            and held >= remind
            and (since is None or since >= remind)
        )
    if due:
        lasted = held is not None and was == environment.State.BLOCKED
        waited = f" for {held:.0f} min" if lasted else ""
        rule = RULES["executor"] if member else RULES["blocked"]
        run.emit(Signal.BLOCKED, name, f"{shown}{waited} → {rule}")
        current[BLOCKED_REPORTED_AT] = run.now.isoformat()
    else:
        current[BLOCKED_REPORTED_AT] = previous.get(BLOCKED_REPORTED_AT)
    current[BLOCKED_SINCE] = (
        previous.get(BLOCKED_SINCE)
        if was == environment.State.BLOCKED
        else run.now.isoformat()
    )


def _turn(
    name: str,
    session: environment.Session,
    entry: Entry,
    previous: SessionState,
    background: bool,
    shown: str,
    run: _Poll,
) -> bool:
    """Report a turn's end; whether the session is parked on background work afterwards."""
    member = watch_file.CWD_PREFIX in entry
    was = previous.get(STATE)
    parked = bool(previous.get(PARKED, False))
    if was == environment.State.WORKING and session.state in environment.ENDED:
        if background:
            # The harness re-invokes the session when its work ends.
            if entry.get(watch_file.REPORT_BACKGROUND, False) and not member:
                detail = f"{shown} → {RULES['background']}"
                run.emit(Signal.WAITING_ON_BACKGROUND, name, detail)
            return True
        if not member:
            run.emit(Signal.WENT_IDLE, name, f"{shown} → {RULES['idle']}")
        return False
    if session.state in environment.ENDED and parked and not background:
        if not member:
            detail = f"{shown} after background work → {RULES['idle']}"
            run.emit(Signal.WENT_IDLE, name, detail)
        return False
    if session.state == environment.State.WORKING:
        return False
    return parked


def _stall(
    name: str,
    session: environment.Session,
    entry: Entry,
    previous: SessionState,
    current: SessionState,
    text: str | None,
    run: _Poll,
) -> None:
    """Report a working pane whose text, digits removed, has not changed for `stall_minutes`.

    Ticking timers and token counters in a hung session do not count as progress.
    """
    stall = cast(float | None, entry.get(watch_file.STALL_MINUTES))
    if not stall or text is None:
        return
    digest = hashlib.sha256(re.sub(r"\d", "", text).encode()).hexdigest()
    active_at = previous.get(ACTIVE_AT)
    if digest != previous.get(DIGEST) or active_at is None:
        active_at = run.now.isoformat()
    current[DIGEST], current[ACTIVE_AT] = digest, active_at
    quiet = run.minutes_since(active_at)
    if (
        session.state == environment.State.WORKING
        and quiet is not None
        and quiet >= stall
    ):
        if not previous.get(STALL_REPORTED):
            member = watch_file.CWD_PREFIX in entry
            rule = RULES["executor"] if member else RULES["stalled"]
            detail = f"pane unchanged for {quiet:.0f} min while working → {rule}"
            run.emit(Signal.STALLED, name, detail)
        current[STALL_REPORTED] = True


def _tiers(
    name: str,
    session: environment.Session,
    entry: Entry,
    previous: SessionState,
    used: int | None,
    run: _Poll,
) -> dict[str, int]:
    """Report the most urgent compaction tier due, once per step; the tiers reported in this step."""
    if used is None or not entry.get(watch_file.CONTEXT_PERCENT):
        return {}
    reported = cast(dict[str, int], previous.get(REPORTED_TIERS, {}))
    for threshold, ended_only, signal in TIERS:
        if used >= threshold and (not ended_only or session.state in environment.ENDED):
            step = used // TIER_STEP_PERCENT
            if reported.get(str(signal)) != step:
                detail = f"{used}% state={session.state} → {RULES[signal]}"
                run.emit(signal, name, detail)
            return {str(signal): step}
    return {}


def _session(
    name: str,
    session: environment.Session | None,
    entry: Entry,
    previous: SessionState,
    backends: Mapping[str, environment.Backend],
    run: _Poll,
) -> SessionState:
    member = watch_file.CWD_PREFIX in entry
    if session is None:
        if previous.get(STATE) != ABSENT_STATE and not member:
            run.emit(Signal.ABSENT, name, f"no session → {RULES['absent']}")
        return {STATE: ABSENT_STATE}

    text = None
    needs_text = (
        entry.get(watch_file.CONTEXT_PERCENT)
        or entry.get(watch_file.STALL_MINUTES)
        or (
            session.backend != environment.Prowl.name
            and session.state in environment.ENDED
        )
    )
    if needs_text:
        try:
            text = backends[session.backend].read(session)
            run.healthy(name)
        except environment.AdapterError as error:
            run.broken(name, error)
    used = environment.context_percent(text) if text else None
    background = environment.background_work(session, text)
    shown = f"{used}%" if used is not None else "?%"

    current: SessionState = {
        STATE: str(session.state),
        CHANGED_AT: session.changed_at,
        CONTEXT: used,
    }
    if session.state == environment.State.BLOCKED:
        _blocked(name, entry, previous, current, shown, run)
    current[PARKED] = _turn(name, session, entry, previous, background, shown, run)
    _stall(name, session, entry, previous, current, text, run)
    current[REPORTED_TIERS] = _tiers(name, session, entry, previous, used, run)
    return current


def poll(
    watch: Mapping[str, object],
    state: dict[str, object],
    now: datetime,
    backends: Mapping[str, environment.Backend] | None = None,
    inbox: Inbox | None = None,
) -> list[Event]:
    """Poll every watched source once, updating `state`; the events this poll emits."""
    backends = environment.BACKENDS if backends is None else backends
    run = _Poll(state, now)
    _mail(watch, run, position_mail.inbox if inbox is None else inbox)

    entries = [
        *cast(list[Entry], watch.get(watch_file.SESSIONS, [])),
        *cast(list[Entry], watch.get(watch_file.GROUPS, [])),
    ]
    inventories: dict[str, list[environment.Session]] = {}
    for name in sorted({cast(str, entry[watch_file.BACKEND]) for entry in entries}):
        try:
            inventories[name] = backends[name].sessions()
            run.healthy(name)
        except environment.AdapterError as error:
            run.broken(name, error)

    seen = cast(dict[str, SessionState], state.setdefault(SESSIONS, {}))
    targets = _targets(watch, inventories)
    for name, (session, entry) in targets.items():
        seen[name] = _session(name, session, entry, seen.get(name, {}), backends, run)
    # A group member that ended since the last poll is its Orchestrator's to dispose of.
    labels = [
        cast(str, group[watch_file.LABEL])
        for group in cast(list[Entry], watch.get(watch_file.GROUPS, []))
    ]
    for name in list(seen):
        gone = name not in targets and seen[name].get(STATE) != ABSENT_STATE
        if gone and any(name.startswith(f"{label} ") for label in labels):
            seen[name] = {STATE: ABSENT_STATE}
    return run.events


def poll_once(watch_path: Path, state_path: Path) -> None:
    """Poll once from the files, print every event, and write the state file."""
    watch = watch_file.load(watch_path)
    state = watch_file.load_state(state_path)
    events = poll(watch, state, datetime.now(UTC))
    state_path.write_text(json.dumps(state, indent=2))
    watcher = cast(str, watch[watch_file.POSITION])
    for event in events:
        print(event.line(watcher), flush=True)


def _lock_holder(lock: Path) -> str:
    try:
        return lock.read_text().strip()
    except OSError:
        return ""


def take_lock(state_path: Path) -> int | None:
    """Hold the state file's lock; its descriptor, or None when a live loop holds it.

    The kernel releases the lock when its process ends however it ends, so a
    lock file whose process is gone is taken over by the next loop.
    """
    lock = Path(f"{state_path}{LOCK_SUFFIX}")
    descriptor = os.open(lock, os.O_RDWR | os.O_CREAT, 0o644)
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        os.close(descriptor)
        return None
    os.ftruncate(descriptor, 0)
    os.write(descriptor, str(os.getpid()).encode())
    return descriptor


def loop(watch_path: Path, state_path: Path, every: float, deadline: float) -> int:
    """Poll every `every` seconds until `deadline` seconds after the start, holding the lock."""
    end = time.monotonic() + deadline
    descriptor = take_lock(state_path)
    if descriptor is None:
        holder = _lock_holder(Path(f"{state_path}{LOCK_SUFFIX}")) or "unknown"
        print(
            f"{Signal.WATCH_DUPLICATE} another loop ({holder}) already watches "
            f"{state_path}; this copy exits",
            flush=True,
        )
        return 0
    try:
        while True:
            try:
                poll_once(watch_path, state_path)
            except (OSError, ValueError) as error:
                # A broken poll reports and the loop goes on.
                print(
                    f"{Signal.WATCH_BROKEN} monitor.py poll failed: {error}", flush=True
                )
            remaining = end - time.monotonic()
            if remaining <= 0:
                return 0
            time.sleep(min(every, remaining))
    finally:
        os.close(descriptor)


def _seconds(text: str) -> float:
    """A positive finite number of seconds."""
    try:
        value = float(text)
    except ValueError as error:
        raise argparse.ArgumentTypeError(
            f"{text!r} is not a number of seconds"
        ) from error
    if not math.isfinite(value) or value <= 0:
        raise argparse.ArgumentTypeError(
            f"{text!r} is not a positive finite number of seconds"
        )
    return value


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="monitor.py",
        description="Poll the watched positions once, or in a loop that ends at a deadline.",
    )
    parser.add_argument("watch", type=Path, help="the watch file naming the positions")
    parser.add_argument("state", type=Path, help="the state file this monitor writes")
    parser.add_argument(
        EVERY_OPTION,
        type=_seconds,
        metavar="SECONDS",
        help="poll in a loop at this interval",
    )
    parser.add_argument(
        DEADLINE_OPTION,
        type=_seconds,
        metavar="SECONDS",
        help="end the loop this many seconds after the monitor starts",
    )
    return parser


def main(argv: Sequence[str]) -> int:
    parser = _parser()
    arguments = parser.parse_args(argv)
    every, deadline = arguments.every, arguments.deadline
    if (every is None) != (deadline is None):
        parser.error(
            f"{EVERY_OPTION} and {DEADLINE_OPTION} go together: a loop needs a deadline"
        )
    try:
        watch_file.load(arguments.watch)
        watch_file.load_state(arguments.state)
    except watch_file.InputError as error:
        print(f"monitor.py: {error}", file=sys.stderr)
        return EXIT_INVALID
    if every is None:
        poll_once(arguments.watch, arguments.state)
        return 0
    return loop(arguments.watch, arguments.state, every, deadline)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
