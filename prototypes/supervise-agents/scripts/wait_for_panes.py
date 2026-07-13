#!/usr/bin/env python3
"""Block until a Prowl agent pane meaningfully changes."""

import fcntl
import json
import subprocess
import time
from pathlib import Path
from typing import cast

type Json = dict[str, object]
type Snapshot = dict[str, tuple[str, int]]


def _prowl(*args: str) -> Json:
    output = subprocess.check_output(["prowl", *args, "--json"], text=True, timeout=15)
    return cast(Json, cast(Json, json.loads(output))["data"])


def _snapshot() -> Snapshot:
    agents = cast(list[Json], _prowl("agents")["agents"])
    panes: Snapshot = {}
    for agent in agents:
        pane = cast(Json, agent["pane"])
        status, pane_id = cast(str, agent["status"]), cast(str, pane["id"])
        fingerprint = 0
        if status != "working":
            text = cast(str, _prowl("read", "--pane", pane_id, "--last", "200")["text"])
            fingerprint = hash(text)
        panes[pane_id] = (status, fingerprint)
    return panes


with Path("/tmp/outcomeeng-pane-wait.lock").open("a+", encoding="utf-8") as lock:
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    previous = _snapshot()
    while True:
        time.sleep(2)
        current = _snapshot()
        removed = [pane for pane in previous if pane not in current]
        changed = [pane for pane in current if previous.get(pane) != current[pane]]
        if changed or removed:
            terminal = bool(current) and all(
                item[0] == "done" for item in current.values()
            )
            event = {"event": "pane-change", "allTerminal": terminal}
            event["panes"], event["removed"] = changed, removed
            print(json.dumps(event))
            break
        previous = current
