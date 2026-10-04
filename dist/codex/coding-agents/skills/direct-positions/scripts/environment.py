"""One view of watched sessions across Prowl (local) and herdr (cloud).

Each backend is reached only through its coding-agents adapter script, so
this module owns no Prowl or herdr command grammar.
"""

from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Protocol

# The adapters ship in sibling skills of this plugin.
ADAPTERS = Path(__file__).resolve().parents[2]
PROWL = ADAPTERS / "operate-prowl/scripts/prowl_environment.py"
HERDR = ADAPTERS / "operate-herdr/scripts/herdr_environment.py"

ADAPTER_TIMEOUT_SECONDS = 30
PANE_LINES = 15

# Marks a Prowl session whose status stays `working` while its screen is idle.
BACKGROUND_MARKER = "backgroundWork"


class State(StrEnum):
    """One state set for every backend."""

    WORKING = "working"
    IDLE = "idle"
    BLOCKED = "blocked"
    DONE = "done"
    UNKNOWN = "unknown"


ENDED = (State.IDLE, State.DONE)

_PROWL_STATES = {
    "working": State.WORKING,
    "idle": State.IDLE,
    "waiting": State.BLOCKED,
    "blocked": State.BLOCKED,
    "done": State.DONE,
}
_HERDR_STATES = {
    "working": State.WORKING,
    "idle": State.IDLE,
    "blocked": State.BLOCKED,
    "done": State.DONE,
}

# "(659k/1M tokens) 66%" and "(0/1M tokens) 0%": the unit is optional on both sides.
_CONTEXT = re.compile(
    r"\(\s*[\d.]+\s*[kKmM]?\s*/\s*[\d.]+\s*[kKmM]?\s*tokens\s*\)\s*(\d{1,3})\s*%"
)

# A turn that ended while a shell or background agent still runs; the harness re-invokes it.
_BACKGROUND = re.compile(
    r"\d+ shells? still running|·\s*\d+ shell|background agents? to finish|Waiting for \d+ background"
)


@dataclass(frozen=True)
class Session:
    backend: str  # a key of BACKENDS
    handle: str  # pane id for prowl, agent name for herdr
    cwd: str
    state: State
    changed_at: str | None
    detail: str


class AdapterError(RuntimeError):
    pass


class Backend(Protocol):
    """What the monitor and the roster read from one environment."""

    name: str

    def sessions(self) -> list[Session]: ...

    def read(self, session: Session, lines: int = PANE_LINES) -> str: ...


def _run(adapter: Path, request: dict, timeout: float) -> dict:
    try:
        completed = subprocess.run(
            ["python3", str(adapter), "run"],
            input=json.dumps(request),
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as error:
        raise AdapterError(
            f"{adapter.name}: no answer within {timeout:.0f}s"
        ) from error
    try:
        result = json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        raise AdapterError(
            f"{adapter.name}: unreadable result: {completed.stderr.strip()[:200]}"
        ) from error
    if result.get("status") != "succeeded":
        raise AdapterError(
            f"{adapter.name}: {result.get('status')}: {result.get('detail')}"
        )
    return result


def _norm(path: str) -> str:
    return path.rstrip("/")


def _prowl_state(agent: dict) -> State:
    """The session's state, with a finished turn read from the screen.

    Prowl's status stays `working` while a background task such as the
    session's own monitor runs, even after the turn ends; `raw_state` still
    reads the screen, so an idle screen under a working status is idle.
    """
    status = agent.get("status")
    if status == "working" and agent.get("raw_state") == "idle":
        return State.IDLE
    return _PROWL_STATES.get(status, State.UNKNOWN)


def _prowl_detail(agent: dict) -> str:
    """The screen reason, marked as background work when an idle screen sits under a working status."""
    detail = agent.get("screen_reason") or agent.get("detection_reason") or ""
    if agent.get("status") == "working" and agent.get("raw_state") == "idle":
        detail += f" {BACKGROUND_MARKER}"
    return detail


class Prowl:
    name = "prowl"

    def sessions(self) -> list[Session]:
        result = _run(
            PROWL,
            {"schemaVersion": 1, "operation": "agents", "arguments": {}},
            ADAPTER_TIMEOUT_SECONDS,
        )
        found = []
        for agent in result["response"]["data"].get("agents", []):
            pane = agent.get("pane") or {}
            found.append(
                Session(
                    backend=self.name,
                    handle=pane.get("id") or agent.get("id"),
                    cwd=_norm(
                        pane.get("cwd")
                        or (agent.get("project") or {}).get("path")
                        or ""
                    ),
                    state=_prowl_state(agent),
                    changed_at=agent.get("last_changed_at"),
                    detail=_prowl_detail(agent),
                )
            )
        return found

    def read(self, session: Session, lines: int = PANE_LINES) -> str:
        request = {
            "schemaVersion": 1,
            "operation": "read",
            "arguments": {"pane": session.handle, "last": lines},
        }
        result = _run(PROWL, request, ADAPTER_TIMEOUT_SECONDS)
        return result["response"]["data"].get("text") or ""


class Herdr:
    name = "herdr"

    def sessions(self) -> list[Session]:
        result = _run(
            HERDR,
            {"schemaVersion": 1, "operation": "inventory", "arguments": {}},
            ADAPTER_TIMEOUT_SECONDS,
        )
        found = []
        for agent in result["response"].get("result", {}).get("agents", []):
            found.append(
                Session(
                    backend=self.name,
                    handle=agent.get("name"),
                    cwd=_norm(agent.get("cwd") or ""),
                    state=_HERDR_STATES.get(agent.get("agent_status"), State.UNKNOWN),
                    changed_at=None,
                    detail=agent.get("pane_id") or "",
                )
            )
        return found

    def read(self, session: Session, lines: int = PANE_LINES) -> str:
        request = {
            "schemaVersion": 1,
            "operation": "read",
            "arguments": {"agent": session.handle, "lines": lines},
        }
        result = _run(HERDR, request, ADAPTER_TIMEOUT_SECONDS)
        return result["response"].get("output") or ""


BACKENDS: dict[str, Backend] = {"prowl": Prowl(), "herdr": Herdr()}


def background_work(session: Session, text: str | None) -> bool:
    """Whether the session's turn ended with work still running.

    Prowl reports this natively; herdr needs the pane text.
    """
    if session.backend == Prowl.name:
        return BACKGROUND_MARKER in session.detail
    return bool(text and _BACKGROUND.search(text))


def context_percent(text: str) -> int | None:
    """The last context figure a status line shows, or None when the pane shows none."""
    matches = _CONTEXT.findall(text)
    return int(matches[-1]) if matches else None


def under(sessions: list[Session], prefix: str, exclude: list[str]) -> list[Session]:
    """Every session whose working directory lies under prefix, minus the excluded paths."""
    root = _norm(prefix) + "/"
    return [
        s
        for s in sessions
        if (s.cwd + "/").startswith(root)
        and not any(s.cwd == _norm(x) for x in exclude)
    ]


def find(
    sessions: list[Session], *, cwd: str | None = None, handle: str | None = None
) -> Session | None:
    for session in sessions:
        if cwd is not None and session.cwd == _norm(cwd):
            return session
        if handle is not None and session.handle == handle:
            return session
    return None
