"""A position's monitor.

Each poll reads the watch file and the state file, emits one line per new
signal, and writes the state file. With --every, the script polls in a loop
under the harness monitor facility and holds a lock so a re-arm never doubles
the signals; without it, the script polls once and exits.

Usage: python3 monitor.py WATCH.json STATE.json [--every SECONDS]
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import environment
import position_mail

# Context tiers, most urgent first: (threshold, applies only when the turn has ended, signal).
TIERS = (
    (85, False, "COMPACT-NOW"),
    (75, False, "COMPACT-AT-BOUNDARY"),
    (50, True, "COMPACT-IDLE"),
)
ENDED = ("idle", "done")


def _minutes_since(stamp: str | None, now: datetime) -> float | None:
    if not stamp:
        return None
    then = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
    return (now - then).total_seconds() / 60


def _mail(watch: dict, state: dict, emit) -> None:
    mail = watch.get("mail")
    if not mail:
        return
    try:
        records = position_mail.inbox(mail["channel"], mail["agent"])
    except position_mail.MailError as error:
        emit(f"WATCH-BROKEN mail: {error}")
        return
    last = state.get("mail_last_id", 0)
    for record in sorted(records, key=lambda r: r.id):
        if record.id > last:
            emit(f"MAIL {record.id} from {record.sender}: {record.subject}")
    state["mail_last_id"] = max([last] + [r.id for r in records])


def _targets(
    watch: dict, inventories: dict
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
            targets[f"{group['label']}"] = (None, group)
        for member in members:
            targets[f"{group['label']} {member.handle}"] = (member, group)
    return targets


def _session(
    name: str, session, entry: dict, previous: dict, now: datetime, emit
) -> dict:
    if session is None:
        if previous.get("state") != "absent":
            emit(f"ABSENT {name}: no session")
        return {"state": "absent"}

    backend = environment.BACKENDS[session.backend]
    text = None
    needs_text = (
        entry.get("context_percent")
        or entry.get("stall_minutes")
        or (session.backend != "prowl" and session.state in ENDED)
    )
    if needs_text:
        try:
            text = backend.read(session)
        except environment.AdapterError as error:
            emit(f"WATCH-BROKEN read {name}: {error}")
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

    if session.state == "blocked":
        # Reported on first sight, baseline included, and again every remind interval.
        remind = entry.get("blocked_remind_minutes", 15)
        since = _minutes_since(previous.get("blocked_reported_at"), now)
        if was != "blocked" or since is None or since >= remind:
            held = _minutes_since(previous.get("blocked_since"), now)
            waited = (
                f" for {held:.0f} min" if was == "blocked" and held is not None else ""
            )
            emit(
                f"BLOCKED {name} {shown}{waited}: waiting at an approval or question; read the pane and dispose of it"
            )
            current["blocked_reported_at"] = now.isoformat()
        else:
            current["blocked_reported_at"] = previous.get("blocked_reported_at")
        current["blocked_since"] = (
            previous.get("blocked_since") if was == "blocked" else now.isoformat()
        )
    elif was == "working" and session.state in ENDED:
        if background:
            # A position resting on its own monitor parks silently when its watch entry says so.
            parked = True
            if entry.get("report_background", True):
                emit(
                    f"WAITING-ON-BACKGROUND {name} {shown}: turn ended with work still running; do not prompt"
                )
        else:
            emit(
                f"WENT-IDLE {name} {shown}: finished a leg; needs a prompt or a disposition"
            )
    elif session.state in ENDED and parked and not background:
        parked = False
        emit(f"WENT-IDLE {name} {shown}: background work ended; needs a disposition")
    elif session.state == "working":
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
        if session.state == "working" and quiet is not None and quiet >= stall:
            if not previous.get("stall_reported"):
                emit(
                    f"STALLED {name}: pane unchanged for {quiet:.0f} min while working"
                )
            current["stall_reported"] = True

    reported = dict(previous.get("tiers", {}))
    if used is not None and entry.get("context_percent"):
        tier = next(
            (t for t in TIERS if used >= t[0] and (not t[1] or session.state in ENDED)),
            None,
        )
        if tier:
            bucket = used // 5
            if reported.get(tier[2]) != bucket:
                emit(f"{tier[2]} {name} {used}% state={session.state}")
            reported = {tier[2]: bucket}
        else:
            reported = {}
    current["tiers"] = reported
    return current


def poll(watch: dict, state: dict, now: datetime) -> list[str]:
    lines: list[str] = []
    me = watch["position"]

    def emit(text: str) -> None:
        lines.append(f"[{me}] {text}")

    _mail(watch, state, emit)

    backends = {e["backend"] for e in watch.get("sessions", [])} | {
        g["backend"] for g in watch.get("groups", [])
    }
    inventories: dict[str, list[environment.Session]] = {}
    for name in sorted(backends):
        try:
            inventories[name] = environment.BACKENDS[name].sessions()
        except environment.AdapterError as error:
            emit(f"WATCH-BROKEN {name} inventory: {error}")

    seen = state.setdefault("sessions", {})
    targets = _targets(watch, inventories)
    for name, (session, entry) in targets.items():
        seen[name] = _session(name, session, entry, seen.get(name, {}), now, emit)
    # A group member that disappeared since the last poll.
    for name in [
        n for n in seen if n not in targets and seen[n].get("state") != "absent"
    ]:
        if any(name.startswith(g["label"] + " ") for g in watch.get("groups", [])):
            emit(f"ABSENT {name}: session ended")
            seen[name] = {"state": "absent"}
    return lines


def poll_once(watch_path: Path, state_path: Path) -> None:
    watch = json.loads(watch_path.read_text())
    state = json.loads(state_path.read_text()) if state_path.exists() else {}
    first_run = not state
    lines = poll(watch, state, datetime.now(timezone.utc))
    state_path.write_text(json.dumps(state, indent=2))
    for line in lines:
        # The baseline run withholds existing mail; every session signal shows at once.
        if first_run and "] MAIL " in line:
            continue
        print(line, flush=True)


def holder(lock: Path) -> int | None:
    """The live process id holding the lock, or None."""
    try:
        pid = int(lock.read_text())
        os.kill(pid, 0)
        return pid
    except (FileNotFoundError, ValueError, ProcessLookupError, PermissionError):
        return None


def main(argv: list[str]) -> int:
    watch_path, state_path = Path(argv[0]), Path(argv[1])
    if "--every" not in argv:
        poll_once(watch_path, state_path)
        return 0
    interval = float(argv[argv.index("--every") + 1])
    lock = Path(f"{state_path}.lock")
    other = holder(lock)
    if other is not None:
        print(
            f"WATCH-DUPLICATE another loop ({other}) already watches {state_path}; this copy exits",
            flush=True,
        )
        return 0
    lock.write_text(str(os.getpid()))
    try:
        while True:
            try:
                poll_once(watch_path, state_path)
            except Exception as error:  # a broken poll reports and the loop goes on
                print(f"WATCH-BROKEN monitor.py poll failed: {error}", flush=True)
            time.sleep(interval)
    finally:
        if holder(lock) == os.getpid():
            lock.unlink(missing_ok=True)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
