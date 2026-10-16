"""Variable source compositions, readings, and request defects for the event wait."""

from __future__ import annotations

import json
import math
from collections.abc import Collection
from dataclasses import dataclass
from enum import StrEnum

from hypothesis import strategies as st

from outcomeeng_testing.generators.agent_mail import agent_names
from outcomeeng_testing.generators.consumption_control import alert_reads

TIMEOUT_CEILING_SECONDS = 20
CLOCK_OFFSET_CEILING_SECONDS = 25
SESSION_CEILING = 5


class MailReading(StrEnum):
    """What the agent-mail store answers a mail source's wait."""

    RECORD = "record"
    QUIET = "quiet"
    UNREACHABLE = "unreachable"
    UNAVAILABLE = "unavailable"
    HUNG = "hung"


class PaneReading(StrEnum):
    """What herdr answers a pane source's inventory read."""

    INVENTORY = "inventory"
    ABSENT_SESSION = "absent-session"
    AMBIGUOUS = "ambiguous"
    INCOMPLETE = "incomplete"
    UNAVAILABLE = "unavailable"
    HUNG = "hung"
    FOREIGN_ENVIRONMENT = "foreign-environment"


class SpendReading(StrEnum):
    """What the consumption-control detector state root holds."""

    RECORDED = "recorded"
    ABSENT_STATE = "absent-state"
    CORRUPT_STATE = "corrupt-state"


@dataclass(frozen=True)
class WorldCase:
    """One composition of sources, each with the reading it yields.

    A source the case does not name is `None`. `session_pairs` pairs the state
    herdr reports for each hosted session with the state the caller last handled.
    `alert_records` and `alert_cutoff` are the detector's stored alerts and the
    instant the spend source passes, as offsets from the detector's base.
    `clock_offset` is the clock source's instant in seconds after the run starts.
    """

    timeout_seconds: int
    agent: str
    mail: MailReading | None
    pane: PaneReading | None
    session_pairs: tuple[tuple[str, str], ...]
    spend: SpendReading | None
    alert_records: tuple[tuple[str, int, int], ...]
    alert_cutoff: int
    clock_offset: int | None


def session_pairs(
    states: Collection[str],
) -> st.SearchStrategy[tuple[tuple[str, str], ...]]:
    """Hosted sessions as (state herdr reports, state the caller last handled)."""
    ordered = tuple(states)
    pair = st.tuples(st.sampled_from(ordered), st.sampled_from(ordered))
    return st.lists(pair, min_size=1, max_size=SESSION_CEILING).map(tuple)


def _reading(
    sources: Collection[str],
    mandatory: Collection[str],
    source: str,
    readings: st.SearchStrategy[object],
) -> st.SearchStrategy[object]:
    if source not in sources:
        return st.none()
    if source in mandatory:
        return readings
    return st.none() | readings


def world_cases(
    *,
    sources: Collection[str],
    mandatory: Collection[str],
    mail: str,
    pane: str,
    spend: str,
    clock: str,
    states: Collection[str],
) -> st.SearchStrategy[WorldCase]:
    """Compositions over the named sources, each with a reading.

    `sources` names the source kinds the composition may carry. A kind in
    `mandatory` always carries its reading; every other kind carries its reading
    or none, and a composition carries at least one source.
    """

    def build(
        timeout_seconds: int,
        agent: str,
        mail_reading: MailReading | None,
        pane_reading: PaneReading | None,
        pairs: tuple[tuple[str, str], ...],
        spend_reading: SpendReading | None,
        alerts: tuple[list[tuple[str, int, int]], int],
        clock_offset: int | None,
    ) -> WorldCase:
        records, cutoff = alerts
        return WorldCase(
            timeout_seconds,
            agent,
            mail_reading,
            pane_reading,
            pairs,
            spend_reading,
            tuple(records),
            cutoff,
            clock_offset,
        )

    def carries_a_source(case: WorldCase) -> bool:
        return any(
            reading is not None
            for reading in (case.mail, case.pane, case.spend, case.clock_offset)
        )

    return st.builds(
        build,
        timeout_seconds=st.integers(min_value=1, max_value=TIMEOUT_CEILING_SECONDS),
        agent=agent_names(),
        mail_reading=_reading(
            sources, mandatory, mail, st.sampled_from(tuple(MailReading))
        ),
        pane_reading=_reading(
            sources, mandatory, pane, st.sampled_from(tuple(PaneReading))
        ),
        pairs=session_pairs(states),
        spend_reading=_reading(
            sources, mandatory, spend, st.sampled_from(tuple(SpendReading))
        ),
        alerts=alert_reads(),
        clock_offset=_reading(
            sources,
            mandatory,
            clock,
            st.integers(min_value=0, max_value=CLOCK_OFFSET_CEILING_SECONDS),
        ),
    ).filter(carries_a_source)


@dataclass(frozen=True)
class TimeoutDefect:
    """A request's timeout that is absent, not a number, or not a positive finite one."""

    present: bool
    value: object


def timeout_defects() -> st.SearchStrategy[TimeoutDefect]:
    absent = st.just(TimeoutDefect(False, None))
    not_positive = st.one_of(
        st.integers(max_value=0),
        st.floats(max_value=0.0, allow_nan=False),
    )
    not_finite = st.floats(allow_nan=True, allow_infinity=True).filter(
        lambda value: not math.isfinite(value)
    )
    not_numbers = st.one_of(
        st.text(max_size=12),
        st.booleans(),
        st.none(),
        st.lists(st.integers(), max_size=3),
    )
    return absent | st.one_of(not_positive, not_finite, not_numbers).map(
        lambda value: TimeoutDefect(True, value)
    )


def unknown_source_kinds(known: Collection[str]) -> st.SearchStrategy[str]:
    return st.from_regex(r"[a-z]{1,12}", fullmatch=True).filter(
        lambda kind: kind not in known
    )


def _is_json_object(text: str) -> bool:
    try:
        return isinstance(json.loads(text), dict)
    except ValueError:
        return False


def non_object_documents() -> st.SearchStrategy[str]:
    """Standard-input texts that are not one JSON object: other JSON values and non-JSON text."""
    other_values = st.one_of(
        st.lists(st.integers(), max_size=3),
        st.integers(),
        st.text(max_size=12),
        st.booleans(),
        st.none(),
    ).map(json.dumps)
    return other_values | st.text(max_size=40).filter(
        lambda text: not _is_json_object(text)
    )
