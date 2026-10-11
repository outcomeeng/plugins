"""Compact an idle Claude pane and send it the resume line once its context has dropped.

Sends /compact to the pane unless a compaction is already under way, waits for
the status line's context to drop by 30 points (or below 10%) after it sent
/compact, then sends the resume line. A pane under 60% is refused, so a fresh
pane never gets the resume line.

Usage: python3 compact_pane.py PANE RESUME_TEXT
"""

from __future__ import annotations

import sys
import time
from collections.abc import Callable, Sequence

import environment

COMPACT_COMMAND = "/compact"
COMPACTING = "Compacting conversation"
COMPACT_FLOOR = 60  # percent of context below which a pane is not compacted
DROP_POINTS = 30
DROP_CEILING = 10  # a context below this many percent counts as dropped
READ_LINES = 14
POLL_SECONDS = 15
SETTLE_SECONDS = 5
DEADLINE_SECONDS = 900
EXIT_OK = 0
EXIT_TIMED_OUT = 1
EXIT_NOT_HIGH = 2
EXIT_USAGE = 2


def compact(
    backend: environment.Prowl,
    session: environment.Session,
    resume: str,
    now: Callable[[], float] = time.time,
    sleep: Callable[[float], None] = time.sleep,
) -> int:
    deadline = now() + DEADLINE_SECONDS
    sent = False
    start: int | None = None
    context: int | None = None
    while now() < deadline:
        try:
            text = backend.read(session, READ_LINES)
        except environment.AdapterError:
            sleep(POLL_SECONDS)
            continue
        context = environment.context_percent(text)
        if start is None and context is not None:
            start = context
        dropped = (
            context is not None
            and start is not None
            and (start - context >= DROP_POINTS or context < DROP_CEILING)
        )
        if sent and dropped and COMPACTING not in text:
            sleep(SETTLE_SECONDS)
            backend.send(session, resume)
            print(f"compacted to {context}%; resume sent")
            return EXIT_OK
        if COMPACTING in text or COMPACT_COMMAND in text:
            sent = True
        elif not sent:
            if context is None or context < COMPACT_FLOOR:
                print(f"context {context}% is not high; no {COMPACT_COMMAND} sent")
                return EXIT_NOT_HIGH
            backend.send(session, COMPACT_COMMAND)
            print(f"{COMPACT_COMMAND} sent")
            sent = True
        sleep(POLL_SECONDS)
    print(f"timed out; last context {context}%")
    return EXIT_TIMED_OUT


def main(argv: Sequence[str]) -> int:
    if len(argv) != 2:
        print("usage: compact_pane.py PANE RESUME_TEXT", file=sys.stderr)
        return EXIT_USAGE
    pane, resume = argv
    backend = environment.Prowl()
    session = environment.Session(
        backend=environment.Prowl.name,
        handle=pane,
        cwd="",
        state=environment.State.UNKNOWN,
        changed_at=None,
        detail="",
    )
    try:
        return compact(backend, session, resume)
    except environment.AdapterError as error:
        print(f"compact_pane.py: {error}", file=sys.stderr)
        return EXIT_TIMED_OUT


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
