"""One view of watched sessions across Prowl (local) and herdr (cloud).

Each backend is reached only through the typed operations of its sibling
coding-agents adapter, imported by its file location, so this module owns no
Prowl or herdr command grammar.
"""

from __future__ import annotations

import functools
import importlib.util
import re
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from types import ModuleType
from typing import Protocol, cast

# The plugin's skills directory, from which the sibling adapters load.
SKILLS_DIR = Path(__file__).resolve().parents[2]
PROWL_ADAPTER = ("operate-prowl", "prowl_environment")
HERDR_ADAPTER = ("operate-herdr", "herdr_environment")

# How many trailing pane lines a read returns.
READ_LINES = 15


class State(StrEnum):
    """One state set for every backend."""

    WORKING = "working"
    IDLE = "idle"
    BLOCKED = "blocked"
    DONE = "done"
    UNKNOWN = "unknown"


# The states in which a session's turn has ended.
ENDED = frozenset({State.IDLE, State.DONE})

# What a Prowl session's detail carries when its idle screen sits under a working status.
BACKGROUND_MARKER = "backgroundWork"

# Fields of one agent in Prowl's agent inventory the adapter passes through.
PROWL_AGENT_STATUS = "status"
PROWL_SCREEN_STATE = "raw_state"
PROWL_SCREEN_REASON = "screen_reason"
PROWL_DETECTION_REASON = "detection_reason"
PROWL_CHANGED_AT = "last_changed_at"
PROWL_PANE_CWD = "cwd"

_PROWL_STATES = {
    "working": State.WORKING,
    "idle": State.IDLE,
    "waiting": State.BLOCKED,
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
    backend: str  # a BACKENDS name
    handle: str  # pane id for prowl, agent name for herdr
    cwd: str
    state: State
    changed_at: str | None
    detail: str


class AdapterError(RuntimeError):
    pass


class Backend(Protocol):
    """The two reads the roster and the monitor take from a backend."""

    def sessions(self) -> list[Session]: ...

    def read(self, session: Session, lines: int = READ_LINES) -> str: ...


def sibling_adapter(skill: str, module_name: str) -> ModuleType:
    """Load a sibling adapter skill's script by the installed tree's layout."""
    cached = sys.modules.get(module_name)
    if cached is not None:
        return cached
    path = SKILLS_DIR / skill / "scripts" / f"{module_name}.py"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {module_name} from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        # A module that failed to execute never stays cached as if it loaded.
        del sys.modules[spec.name]
        raise
    return module


@functools.cache
def _prowl() -> ModuleType:
    return sibling_adapter(*PROWL_ADAPTER)


@functools.cache
def _herdr() -> ModuleType:
    return sibling_adapter(*HERDR_ADAPTER)


def _succeeded(adapter: ModuleType, name: str, request: object) -> dict[str, object]:
    """Run one adapter operation with its own runner; its result, or the failure raised."""
    result = cast(
        dict[str, object], adapter.execute(request, adapter.SubprocessRunner())
    )
    if result.get(adapter.STATUS_FIELD) != adapter.ExecutionStatus.SUCCEEDED:
        raise AdapterError(
            f"{name}: {result.get(adapter.STATUS_FIELD)}: {result.get(adapter.DETAIL_FIELD)}"
        )
    return result


def _object(value: object) -> Mapping[str, object]:
    return cast(Mapping[str, object], value) if isinstance(value, dict) else {}


def _text(value: object) -> str:
    return value if isinstance(value, str) else ""


def _norm(path: str) -> str:
    return path.rstrip("/")


def _prowl_screen_idle(agent: Mapping[str, object]) -> bool:
    """Prowl's status stays `working` while a background task such as the session's
    own monitor runs, even after the turn ends; `raw_state` still reads the screen."""
    return (
        agent.get(PROWL_AGENT_STATUS) == State.WORKING
        and agent.get(PROWL_SCREEN_STATE) == State.IDLE
    )


def _prowl_state(agent: Mapping[str, object]) -> State:
    """The session's state, with a finished turn read from the screen."""
    if _prowl_screen_idle(agent):
        return State.IDLE
    return _PROWL_STATES.get(_text(agent.get(PROWL_AGENT_STATUS)), State.UNKNOWN)


def _prowl_detail(agent: Mapping[str, object]) -> str:
    """The screen reason, marked as background work when an idle screen sits under a working status."""
    detail = _text(agent.get(PROWL_SCREEN_REASON)) or _text(
        agent.get(PROWL_DETECTION_REASON)
    )
    if _prowl_screen_idle(agent):
        detail += f" {BACKGROUND_MARKER}"
    return detail


class Prowl:
    name = "prowl"

    def sessions(self) -> list[Session]:
        adapter = _prowl()
        result = _succeeded(
            adapter, self.name, adapter.operation_request(adapter.Operation.AGENTS)
        )
        data = _object(
            _object(result.get(adapter.RESPONSE_FIELD)).get(adapter.DATA_FIELD)
        )
        agents = data.get(adapter.AGENTS_FIELD)
        found = []
        for item in agents if isinstance(agents, list) else []:
            agent = _object(item)
            pane = _object(agent.get(adapter.PANE_FIELD))
            project = _object(agent.get(adapter.PROJECT_FIELD))
            found.append(
                Session(
                    backend=self.name,
                    handle=_text(pane.get(adapter.ID_FIELD))
                    or _text(agent.get(adapter.ID_FIELD)),
                    cwd=_norm(
                        _text(pane.get(PROWL_PANE_CWD))
                        or _text(project.get(adapter.PATH_FIELD))
                    ),
                    state=_prowl_state(agent),
                    changed_at=_text(agent.get(PROWL_CHANGED_AT)) or None,
                    detail=_prowl_detail(agent),
                )
            )
        return found

    def read(self, session: Session, lines: int = READ_LINES) -> str:
        adapter = _prowl()
        request = adapter.operation_request(
            adapter.Operation.READ, pane=session.handle, last=lines
        )
        result = _succeeded(adapter, self.name, request)
        data = _object(
            _object(result.get(adapter.RESPONSE_FIELD)).get(adapter.DATA_FIELD)
        )
        return _text(data.get(adapter.TEXT_FIELD))


class Herdr:
    name = "herdr"

    def sessions(self) -> list[Session]:
        adapter = _herdr()
        result = _succeeded(
            adapter, self.name, adapter.operation_request(adapter.Operation.INVENTORY)
        )
        agents = result.get(adapter.AGENTS_RESULT_FIELD)
        found = []
        for item in agents if isinstance(agents, list) else []:
            agent = _object(item)
            status = _text(agent.get(adapter.AGENT_STATUS_FIELD))
            found.append(
                Session(
                    backend=self.name,
                    handle=_text(agent.get(adapter.NAME_FIELD)),
                    cwd=_norm(_text(agent.get(adapter.CWD_FIELD))),
                    state=State(status) if status in State else State.UNKNOWN,
                    changed_at=None,
                    detail=_text(agent.get(adapter.PANE_ID_FIELD)),
                )
            )
        return found

    def read(self, session: Session, lines: int = READ_LINES) -> str:
        adapter = _herdr()
        request = adapter.operation_request(
            adapter.Operation.READ, agent=session.handle, lines=lines
        )
        result = _succeeded(adapter, self.name, request)
        response = _object(result.get(adapter.RESPONSE_FIELD))
        return _text(response.get(adapter.OUTPUT_FIELD))


BACKENDS: Mapping[str, Backend] = {Prowl.name: Prowl(), Herdr.name: Herdr()}


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


def under(
    sessions: Sequence[Session], prefix: str, exclude: Sequence[str]
) -> list[Session]:
    """Every session whose working directory lies under prefix, minus the excluded paths."""
    root = _norm(prefix) + "/"
    return [
        s
        for s in sessions
        if (s.cwd + "/").startswith(root)
        and not any(s.cwd == _norm(x) for x in exclude)
    ]


def find(
    sessions: Sequence[Session], *, cwd: str | None = None, handle: str | None = None
) -> Session | None:
    for session in sessions:
        if cwd is not None and session.cwd == _norm(cwd):
            return session
        if handle is not None and session.handle == handle:
            return session
    return None
