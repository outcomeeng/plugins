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
    (75, True, "COMPACT-IDLE"),
    (75, False, "COMPACT-AT-BOUNDARY"),
)
ENDED = ("idle", "done")

# The disposition each signal calls for, from the authority map and the Spec Tree foundation.
GATE = (
    "before any ruling, read the malleability of every node the changeset touches: "
    "spec = Validate, reachability tests, tagged results; verification adds Review; "
    "only implementation adds evidence audits. A gate the nodes do not require never launches"
)
RULES = {
    "note": "compact it now: /compact, wait for its context to drop, send its resume line",
    "shape": "forward it to SnowyHeron with forward.py, then receipt; judge nothing in it",
    "status": "read its blocked and next lines; act only on a step-in trigger; a reported rejection: check the gate applied",
    "gate": GATE,
    "question": (
        "find the owner: inside one Product it is the Maintainer's (answer 'the decision is yours'); "
        "delivery mechanics are the Orchestrator's; only order across Products, the operating model and the board are yours"
    ),
    "other": "verify it against the store or git before acting; receipt after handling",
    "blocked": (
        "read the pane: a read a higher rank ordered, approve; a guard or destructive prompt, "
        "Escape and a redirect (one command at a time, trash for rm); never allow"
    ),
    "idle": "read its last lines: a finished leg its skill continues is left alone; open work gets its next step; a question to the operator it waits on is answered by its owner within 15 minutes, or asked through AskUserQuestion when none can",
    "executor": "its Orchestrator owns it: check the Orchestrator is disposing of it; never prompt an Executor",
    "COMPACT-NOW": "order its note now; compact on 'note written'",
    "COMPACT-IDLE": "order its note now; compact on 'note written'",
    "COMPACT-AT-BOUNDARY": "order its note for the end of its current step",
}
_GATE_WORDS = re.compile(
    r"\b(audits?|auditor|reviews?|reviewer|gates?|reject\w*|verdicts?|verifier|fixer|evidence|runs?)\b",
    re.IGNORECASE,
)


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


def _broken(state: dict, key: str, error: object, emit) -> None:
    """Report an adapter failure only when it repeats on the next poll."""
    counts = state.setdefault("broken", {})
    counts[key] = counts.get(key, 0) + 1
    if counts[key] == 2:
        emit(f"WATCH-BROKEN {key}: {error} (twice in a row)")


def _healthy(state: dict, key: str) -> None:
    state.setdefault("broken", {}).pop(key, None)


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
        _broken(state, "mail", error, emit)
        return
    _healthy(state, "mail")
    last = state.get("mail_last_id", 0)
    for record in sorted(records, key=lambda r: r.id):
        if record.id > last:
            emit(
                f"MAIL {record.id} from {record.sender}: {record.subject} → {mail_rule(record.subject)}"
            )
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
    name: str, session, entry: dict, previous: dict, now: datetime, emit, state: dict
) -> dict:
    # A group member is an Executor its Orchestrator owns: only a long block reaches the Director.
    member = "cwd_prefix" in entry
    if session is None:
        if previous.get("state") != "absent" and not member:
            emit(f"ABSENT {name}: no session → open work goes to restart.md")
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
            _healthy(state, f"read {name}")
        except environment.AdapterError as error:
            _broken(state, f"read {name}", error, emit)
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
        held = _minutes_since(previous.get("blocked_since"), now)
        due = was != "blocked" or since is None or since >= remind
        if member:
            # An Executor's prompt is its Orchestrator's; the Director checks only a long one.
            due = (
                was == "blocked"
                and held is not None
                and held >= remind
                and (since is None or since >= remind)
            )
        if due:
            waited = (
                f" for {held:.0f} min" if was == "blocked" and held is not None else ""
            )
            rule = RULES["executor"] if member else RULES["blocked"]
            emit(f"BLOCKED {name} {shown}{waited} → {rule}")
            current["blocked_reported_at"] = now.isoformat()
        else:
            current["blocked_reported_at"] = previous.get("blocked_reported_at")
        current["blocked_since"] = (
            previous.get("blocked_since") if was == "blocked" else now.isoformat()
        )
    elif was == "working" and session.state in ENDED:
        if background:
            # A position resting on its own monitor parks silently when its watch entry says so.
            # The harness re-invokes the session when its work ends: nothing to do.
            parked = True
        elif not member:
            emit(f"WENT-IDLE {name} {shown} → {RULES['idle']}")
    elif session.state in ENDED and parked and not background:
        parked = False
        if not member:
            emit(f"WENT-IDLE {name} {shown} after background work → {RULES['idle']}")
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
                rule = (
                    RULES["executor"]
                    if member
                    else "read the pane and the transcript; a stall over 15 min is a step-in trigger"
                )
                emit(
                    f"STALLED {name}: pane unchanged for {quiet:.0f} min while working → {rule}"
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
                emit(
                    f"{tier[2]} {name} {used}% state={session.state} → {RULES[tier[2]]}"
                )
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
            _healthy(state, f"{name} inventory")
        except environment.AdapterError as error:
            _broken(state, f"{name} inventory", error, emit)

    seen = state.setdefault("sessions", {})
    targets = _targets(watch, inventories)
    for name, (session, entry) in targets.items():
        seen[name] = _session(
            name, session, entry, seen.get(name, {}), now, emit, state
        )
    # A group member that disappeared since the last poll.
    for name in [
        n for n in seen if n not in targets and seen[n].get("state") != "absent"
    ]:
        if any(name.startswith(g["label"] + " ") for g in watch.get("groups", [])):
            # An Executor ending is its Orchestrator's to dispose of; recorded silently.
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
