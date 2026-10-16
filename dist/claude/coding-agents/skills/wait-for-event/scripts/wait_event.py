#!/usr/bin/env python3
"""One bounded wait over mail, herdr agent session states, spend alerts, and a clock instant.

A request is one JSON object on standard input. The run prints exactly one JSON
line and exits: an event line, an unreadable-source line, a timeout line, or an
invalid-request line. It keeps no cursor, state file, or lock, sends nothing,
marks nothing read, starts no background process, and never outlives its timeout.
"""

from __future__ import annotations

import argparse
import datetime as dt
import importlib
import json
import math
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any, Callable, Mapping, TextIO

SKILLS_ROOT = Path(__file__).resolve().parents[2]
ADAPTER_MAIL = ("operate-agent-mail", "agent_mail")
ADAPTER_HERDR = ("operate-herdr", "herdr_environment")
ADAPTER_SPEND = ("control-token-spend", "usage_accounting")

SCHEMA_VERSION = 1
POLL_INTERVAL_SECONDS = 1.0
MAIL_WAIT_MAXIMUM_SECONDS = 3_600

KIND_FIELD = "kind"
SOURCES_FIELD = "sources"
TIMEOUT_FIELD = "timeoutSeconds"
SCHEMA_VERSION_FIELD = "schemaVersion"
DETAIL_FIELD = "detail"

# Fields of a source in the request.
MAIL_AGENT_FIELD = "agent"
MAIL_ID_FIELD = "id"
PANE_ENVIRONMENT_FIELD = "environment"
PANE_SESSIONS_FIELD = "sessions"
PANE_SESSION_FIELD = "session"
PANE_STATE_FIELD = "state"
SPEND_AFTER_FIELD = "after"
SPEND_ROOT_FIELD = "root"
CLOCK_AT_FIELD = "at"

# Fields of an event line and of an unreadable-source entry.
SOURCE_FIELD = "source"
RECORD_FIELD = "record"
RECORD_ID_FIELD = "id"
RECORD_SENDER_FIELD = "sender"
RECORD_KIND_FIELD = "kind"
RECORD_SUBJECT_FIELD = "subject"
PREVIOUS_STATE_FIELD = "previousState"
IDENTITY_FIELD = "identity"
RECORDED_UTC_FIELD = "recordedUtc"
SIGNAL_FIELD = "signal"
STATUS_FIELD = "status"

SOURCE_MAIL = "mail"
SOURCE_PANE = "pane"
SOURCE_SPEND = "spend"
SOURCE_CLOCK = "clock"
SOURCE_KINDS = (SOURCE_MAIL, SOURCE_PANE, SOURCE_SPEND, SOURCE_CLOCK)

ENVIRONMENT_HERDR = "herdr"

LINE_EVENT = "event"
LINE_UNREADABLE = "unreadable-source"
LINE_TIMEOUT = "timeout"
LINE_INVALID = "invalid-request"

EXIT_OK = 0
EXIT_UNREADABLE = 1
EXIT_INVALID = 2


class WaitEventError(RuntimeError):
    """A source cannot be read; the message names why."""


class InvalidRequest(ValueError):
    """The request is malformed; the message names the field."""


class MonotonicClock:
    """Wall-clock implementation of the run's time sources."""

    def now(self) -> float:
        return time.monotonic()

    def sleep(self, seconds: float) -> None:
        time.sleep(seconds)

    def instant(self) -> dt.datetime:
        return dt.datetime.now(dt.timezone.utc)


@dataclass(frozen=True)
class MailSource:
    agent: str
    after_id: int


@dataclass(frozen=True)
class PaneSource:
    environment: str
    sessions: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class SpendSource:
    after: dt.datetime
    after_text: str
    root: str | None


@dataclass(frozen=True)
class ClockSource:
    at: dt.datetime
    at_text: str


Source = MailSource | PaneSource | SpendSource | ClockSource


@dataclass(frozen=True)
class Request:
    timeout_seconds: float
    sources: tuple[Source, ...]


def _instant(value: object, location: str) -> dt.datetime:
    if not isinstance(value, str) or not value:
        raise InvalidRequest(f"{location} must be an ISO 8601 instant ending in Z")
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise InvalidRequest(
            f"{location} must be an ISO 8601 instant ending in Z; received {value!r}"
        ) from error
    if parsed.tzinfo is None:
        raise InvalidRequest(f"{location} needs an explicit UTC offset; use Z")
    return parsed.astimezone(dt.timezone.utc)


def _text(value: object, location: str) -> str:
    if not isinstance(value, str) or not value:
        raise InvalidRequest(f"{location} must be a non-empty string")
    return value


def _source(raw: object, location: str) -> Source:
    if not isinstance(raw, dict):
        raise InvalidRequest(f"{location} must be a JSON object")
    kind = raw.get(KIND_FIELD)
    if kind not in SOURCE_KINDS:
        raise InvalidRequest(
            f"{location}.{KIND_FIELD} must be one of {', '.join(SOURCE_KINDS)}; "
            f"received {kind!r}"
        )
    if kind == SOURCE_MAIL:
        after_id = raw.get(MAIL_ID_FIELD)
        if isinstance(after_id, bool) or not isinstance(after_id, int) or after_id < 0:
            raise InvalidRequest(
                f"{location}.{MAIL_ID_FIELD} must be the whole-number id of the last record handled, "
                "0 for none"
            )
        return MailSource(
            _text(raw.get(MAIL_AGENT_FIELD), f"{location}.{MAIL_AGENT_FIELD}"), after_id
        )
    if kind == SOURCE_PANE:
        environment = raw.get(PANE_ENVIRONMENT_FIELD, ENVIRONMENT_HERDR)
        sessions = raw.get(PANE_SESSIONS_FIELD)
        if not isinstance(sessions, list) or not sessions:
            raise InvalidRequest(
                f"{location}.{PANE_SESSIONS_FIELD} must be a non-empty array"
            )
        pairs = []
        for index, item in enumerate(sessions):
            where = f"{location}.{PANE_SESSIONS_FIELD}[{index}]"
            if not isinstance(item, dict):
                raise InvalidRequest(f"{where} must be a JSON object")
            pairs.append(
                (
                    _text(
                        item.get(PANE_SESSION_FIELD), f"{where}.{PANE_SESSION_FIELD}"
                    ),
                    _text(item.get(PANE_STATE_FIELD), f"{where}.{PANE_STATE_FIELD}"),
                )
            )
        return PaneSource(
            _text(environment, f"{location}.{PANE_ENVIRONMENT_FIELD}"), tuple(pairs)
        )
    if kind == SOURCE_SPEND:
        root = raw.get(SPEND_ROOT_FIELD)
        if root is not None:
            root = _text(root, f"{location}.{SPEND_ROOT_FIELD}")
        return SpendSource(
            _instant(raw.get(SPEND_AFTER_FIELD), f"{location}.{SPEND_AFTER_FIELD}"),
            str(raw[SPEND_AFTER_FIELD]),
            root,
        )
    return ClockSource(
        _instant(raw.get(CLOCK_AT_FIELD), f"{location}.{CLOCK_AT_FIELD}"),
        str(raw[CLOCK_AT_FIELD]),
    )


def parse_request(document: object) -> Request:
    """Validate one decoded request; raise InvalidRequest before any source is read."""
    if not isinstance(document, dict):
        raise InvalidRequest("the request must be one JSON object")
    timeout = document.get(TIMEOUT_FIELD)
    if (
        isinstance(timeout, bool)
        or not isinstance(timeout, (int, float))
        or not math.isfinite(timeout)
        or timeout <= 0
    ):
        raise InvalidRequest(f"{TIMEOUT_FIELD} must be a positive number of seconds")
    sources = document.get(SOURCES_FIELD)
    if not isinstance(sources, list) or not sources:
        raise InvalidRequest(f"{SOURCES_FIELD} must be a non-empty array")
    parsed = tuple(
        _source(item, f"{SOURCES_FIELD}[{index}]") for index, item in enumerate(sources)
    )
    return Request(float(timeout), parsed)


def _adapter(adapter: tuple[str, str]) -> ModuleType:
    """Load one sibling skill's script by a `__file__`-relative import."""
    skill, module = adapter
    directory = SKILLS_ROOT / skill / "scripts"
    path = directory / f"{module}.py"
    if not path.is_file():
        raise WaitEventError(
            f"the adapter script {path} does not exist; install the sibling skill "
            f"coding-agents:{skill} in the same plugin"
        )
    cached = sys.modules.get(module)
    if cached is not None and Path(getattr(cached, "__file__", "")) == path:
        return cached
    sys.modules.pop(module, None)
    sys.path.insert(0, str(directory))
    try:
        return importlib.import_module(module)
    except ImportError as error:
        raise WaitEventError(
            f"the adapter {path} cannot be imported: {error}"
        ) from error
    finally:
        sys.path.remove(str(directory))


@dataclass(frozen=True)
class Unreadable:
    source: str
    detail: str
    extra: Mapping[str, Any]

    def line_entry(self) -> dict[str, Any]:
        return {SOURCE_FIELD: self.source, **self.extra, DETAIL_FIELD: self.detail}


@dataclass(frozen=True)
class Event:
    fields: Mapping[str, Any]


class _BoundedRunner:
    """Hands the herdr adapter's runner no more time than the run has left."""

    def __init__(self, inner: Any, remaining: Callable[[], float]) -> None:
        self._inner = inner
        self._remaining = remaining

    def run(
        self,
        argv: tuple[str, ...],
        stdin: str | None = None,
        *,
        timeout_seconds: int = 30,
    ) -> Any:
        bound = max(1, min(int(timeout_seconds), math.ceil(self._remaining())))
        return self._inner.run(argv, stdin, timeout_seconds=bound)


def _poll_mail(
    source: MailSource,
    seconds: int,
    runner: Any,
    clock: Any,
) -> Event | Unreadable | None:
    identity = {MAIL_AGENT_FIELD: source.agent}
    try:
        adapter = _adapter(ADAPTER_MAIL)
        result = adapter.execute(
            {
                "schemaVersion": adapter.SCHEMA_VERSION,
                "operation": "wait",
                "arguments": {
                    "agent": source.agent,
                    "afterId": source.after_id,
                    "timeoutSeconds": seconds,
                },
            },
            adapter.SubprocessRunner() if runner is None else runner,
            clock,
        )
    except (WaitEventError, OSError, subprocess.TimeoutExpired) as error:
        return Unreadable(SOURCE_MAIL, str(error), identity)
    if result.get("status") != "succeeded":
        return Unreadable(
            SOURCE_MAIL,
            f"mail is {result.get('status')}: {result.get('detail')}",
            {**identity, STATUS_FIELD: str(result.get(STATUS_FIELD))},
        )
    data = result["data"]
    outcome = data["outcome"]
    if outcome == "timeout":
        return None
    if outcome == "unreachable":
        return Unreadable(
            SOURCE_MAIL,
            f"the inbox listing does not reach back to id {source.after_id}",
            {**identity, STATUS_FIELD: "unreachable"},
        )
    record = data["record"]
    return Event(
        {
            SOURCE_FIELD: SOURCE_MAIL,
            RECORD_FIELD: {
                RECORD_ID_FIELD: record["id"],
                RECORD_SENDER_FIELD: record["sender"],
                RECORD_KIND_FIELD: str(record["kind"]),
                RECORD_SUBJECT_FIELD: record["subject"],
            },
        }
    )


def _poll_pane(
    source: PaneSource, runner: Any, remaining: Callable[[], float]
) -> Event | Unreadable | None:
    identity = {PANE_ENVIRONMENT_FIELD: source.environment}
    if source.environment != ENVIRONMENT_HERDR:
        return Unreadable(
            SOURCE_PANE,
            f"the {source.environment} environment projects no agent session state",
            identity,
        )
    try:
        adapter = _adapter(ADAPTER_HERDR)
        bounded = _BoundedRunner(
            adapter.SubprocessRunner() if runner is None else runner, remaining
        )
        result = adapter.execute(
            {
                "schemaVersion": adapter.SCHEMA_VERSION,
                "operation": "inventory",
                "arguments": {},
            },
            bounded,
        )
    except (WaitEventError, OSError, subprocess.TimeoutExpired) as error:
        return Unreadable(SOURCE_PANE, str(error), identity)
    if result.get("status") != "succeeded":
        return Unreadable(
            SOURCE_PANE,
            f"herdr is {result.get('status')}: {result.get('detail')}",
            {**identity, STATUS_FIELD: str(result.get(STATUS_FIELD))},
        )
    agents = result.get("agents")
    if not isinstance(agents, list):
        return Unreadable(
            SOURCE_PANE, "the herdr inventory carries no agents", identity
        )
    for selector, handled in source.sessions:
        matches = [
            agent
            for agent in agents
            if selector in (agent.get("name"), agent.get("pane_id"))
        ]
        if not matches:
            return Unreadable(
                SOURCE_PANE,
                f"no hosted agent session matches {selector!r}",
                {**identity, PANE_SESSION_FIELD: selector},
            )
        if len(matches) > 1:
            return Unreadable(
                SOURCE_PANE,
                f"{len(matches)} hosted agent sessions match {selector!r}",
                {**identity, PANE_SESSION_FIELD: selector},
            )
        agent = matches[0]
        if agent.get("missingFields") or "agent_status" not in agent:
            return Unreadable(
                SOURCE_PANE,
                f"the evidence for {selector!r} lacks "
                f"{', '.join(agent.get('missingFields', ['agent_status']))}",
                {**identity, PANE_SESSION_FIELD: selector},
            )
        state = str(agent["agent_status"])
        if state != handled:
            return Event(
                {
                    SOURCE_FIELD: SOURCE_PANE,
                    PANE_ENVIRONMENT_FIELD: source.environment,
                    PANE_SESSION_FIELD: selector,
                    PANE_STATE_FIELD: state,
                    PREVIOUS_STATE_FIELD: handled,
                }
            )
    return None


def _poll_spend(source: SpendSource) -> Event | Unreadable | None:
    try:
        adapter = _adapter(ADAPTER_SPEND)
        root = Path(source.root) if source.root is not None else adapter.DEFAULT_ROOT
        result = adapter.recorded_alerts(root, source.after)
    except (WaitEventError, OSError) as error:
        return Unreadable(SOURCE_SPEND, str(error), {})
    if str(result["status"]) != "read":
        return Unreadable(
            SOURCE_SPEND,
            str(result.get("reason", "the detector state cannot be read")),
            {SPEND_ROOT_FIELD: str(result.get("root", ""))},
        )
    records = result["records"]
    if not records:
        return None
    first = records[0]
    return Event(
        {
            SOURCE_FIELD: SOURCE_SPEND,
            IDENTITY_FIELD: first["identity"],
            RECORDED_UTC_FIELD: first["recorded_utc"],
            SIGNAL_FIELD: first["signal"],
        }
    )


def _poll_clock(
    source: ClockSource, now: dt.datetime, horizon: dt.datetime
) -> Event | None:
    if source.at >= horizon or now < source.at:
        return None
    return Event({SOURCE_FIELD: SOURCE_CLOCK, CLOCK_AT_FIELD: source.at_text})


def wait_event(
    request: Request,
    *,
    runner: Any = None,
    clock: Any = None,
) -> tuple[dict[str, Any], int]:
    """Read the sources until the first event, an unreadable source, or the timeout."""
    clock = MonotonicClock() if clock is None else clock
    deadline = clock.now() + request.timeout_seconds
    horizon = clock.instant() + dt.timedelta(seconds=request.timeout_seconds)

    def remaining() -> float:
        return deadline - clock.now()

    mail = [s for s in request.sources if isinstance(s, MailSource)]
    others = [s for s in request.sources if not isinstance(s, MailSource)]
    while True:
        unreadable: list[Unreadable] = []
        for source in others:
            if isinstance(source, PaneSource):
                outcome: Event | Unreadable | None = _poll_pane(
                    source, runner, remaining
                )
            elif isinstance(source, SpendSource):
                outcome = _poll_spend(source)
            else:
                assert isinstance(source, ClockSource)
                outcome = _poll_clock(source, clock.instant(), horizon)
            if isinstance(outcome, Event):
                return _event_line(outcome), EXIT_OK
            if isinstance(outcome, Unreadable):
                unreadable.append(outcome)
        waited = False
        for source in mail:
            # With other sources to read, wait one second so each pass reads them again.
            seconds = min(
                math.floor(remaining()),
                MAIL_WAIT_MAXIMUM_SECONDS if not others and len(mail) == 1 else 1,
            )
            if seconds < 1:
                continue
            waited = True
            outcome = _poll_mail(source, seconds, runner, clock)
            if isinstance(outcome, Event):
                return _event_line(outcome), EXIT_OK
            if isinstance(outcome, Unreadable):
                unreadable.append(outcome)
        if unreadable:
            return (
                {
                    KIND_FIELD: LINE_UNREADABLE,
                    SCHEMA_VERSION_FIELD: SCHEMA_VERSION,
                    SOURCES_FIELD: [item.line_entry() for item in unreadable],
                },
                EXIT_UNREADABLE,
            )
        left = remaining()
        if left <= 0:
            return (
                {
                    KIND_FIELD: LINE_TIMEOUT,
                    SCHEMA_VERSION_FIELD: SCHEMA_VERSION,
                    TIMEOUT_FIELD: _number(request.timeout_seconds),
                },
                EXIT_OK,
            )
        if not waited:
            clock.sleep(min(POLL_INTERVAL_SECONDS, left))


def _number(value: float) -> int | float:
    return int(value) if float(value).is_integer() else value


def _event_line(event: Event) -> dict[str, Any]:
    return {
        KIND_FIELD: LINE_EVENT,
        SCHEMA_VERSION_FIELD: SCHEMA_VERSION,
        **event.fields,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="wait_event")
    parser.add_argument("operation", nargs="?", choices=["run"])
    return parser


def main(
    argv: list[str] | None = None,
    *,
    stdin: TextIO | None = None,
    stdout: TextIO | None = None,
    runner: Any = None,
    clock: Any = None,
) -> int:
    _parser().parse_args(argv)
    stdin = sys.stdin if stdin is None else stdin
    stdout = sys.stdout if stdout is None else stdout
    try:
        try:
            document = json.load(stdin)
        except json.JSONDecodeError as error:
            raise InvalidRequest(
                f"the request is not valid JSON: {error.msg}"
            ) from error
        request = parse_request(document)
    except InvalidRequest as error:
        line: dict[str, Any] = {
            KIND_FIELD: LINE_INVALID,
            SCHEMA_VERSION_FIELD: SCHEMA_VERSION,
            DETAIL_FIELD: str(error),
        }
        code = EXIT_INVALID
    else:
        line, code = wait_event(request, runner=runner, clock=clock)
    stdout.write(json.dumps(line) + "\n")
    return code


if __name__ == "__main__":
    sys.exit(main())
