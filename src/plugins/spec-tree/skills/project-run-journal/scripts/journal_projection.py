"""Consumer-side run-journal projection — stdlib only, pure.

Shared by the agentic verification surfaces (auditing, reviewing) that drive
the ``spx journal`` channel. Build channel event inputs from a run's results;
compute the rollup over an event prefix; render the human-readable surface
from an event prefix. These functions touch no journal backend, filesystem,
or network, so they are verified at ``l1`` without a real journal and without
mocking — the consuming skill drives the channel and passes event data to and
from them.

Portability: standard library only. No third-party imports, no ``spx`` import.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

# Source-owned vocabulary. Consumers and tests import these rather than
# hand-writing the event-type strings or status values.
EVENT_SOURCE = "spec-tree/verification"

SCOPE_ENTERED = "verification.scope.entered"
FINDING_REPORTED = "verification.finding.reported"
RUN_COMPLETED = "verification.run.completed"

# The channel append-input string fields the producer must supply with
# non-empty values (the channel itself assigns ``specversion``, ``streamid``,
# ``seq``, and ``runid``). Named here so the contract has one source.
EVENT_INPUT_STRING_FIELDS: tuple[str, ...] = ("id", "source", "type", "time")


class Severity(StrEnum):
    """Per-finding severity contributed to the rollup."""

    REJECT = "reject"
    WARNING = "warning"
    INFO = "info"
    UNKNOWN = "unknown"


class Outcome(StrEnum):
    """The run's rolled-up overall."""

    APPROVED = "approved"
    REJECTED = "rejected"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class Finding:
    """One finding in a verification run's results.

    ``line`` is ``None`` for a whole-file finding.
    """

    file: str
    line: int | None
    rule: str
    severity: Severity
    message: str


@dataclass(frozen=True)
class RunResult:
    """The generic, type-agnostic results of one verification run.

    Auditing and reviewing each adapt their own result shape into this; the
    projection knows nothing of either's verdict schema.
    """

    target: str
    scope_hash: str
    branch: str
    findings: tuple[Finding, ...] = ()


def build_events(run: RunResult, *, now: str, attempt: int = 1) -> list[dict]:
    """Build the ordered channel event-input sequence for a run.

    Yields a ``scope.entered`` event, one ``finding.reported`` event per
    finding (in order), and a terminal ``run.completed`` event carrying the
    rolled-up overall. Each returned dict is a valid channel append input:
    non-empty ``id``/``source``/``type``/``time`` strings and an integer
    ``attempt``, plus a ``data`` object. The channel assigns the remaining
    CloudEvents attributes.
    """
    events: list[dict] = []

    def event(event_type: str, data: dict) -> dict:
        return {
            "id": f"{event_type}.{len(events) + 1}",
            "source": EVENT_SOURCE,
            "type": event_type,
            "time": now,
            "attempt": attempt,
            "data": data,
        }

    events.append(
        event(
            SCOPE_ENTERED,
            {"target": run.target, "scope_hash": run.scope_hash, "branch": run.branch},
        )
    )
    for finding in run.findings:
        events.append(
            event(
                FINDING_REPORTED,
                {
                    "file": finding.file,
                    "line": finding.line,
                    "rule": finding.rule,
                    "severity": str(finding.severity),
                    "message": finding.message,
                },
            )
        )
    events.append(event(RUN_COMPLETED, {"overall": str(compute_overall(events))}))
    return events


def compute_overall(events: list[dict]) -> Outcome:
    """Roll an event prefix up to the run's overall.

    Any rejecting finding maps the run to ``REJECTED``; otherwise any unknown
    finding maps it to ``UNKNOWN``; otherwise ``APPROVED``. A pure fold over
    the ``finding.reported`` events' severities — independent of how many
    other event kinds the prefix carries.
    """
    severities = [
        event.get("data", {}).get("severity")
        for event in events
        if event.get("type") == FINDING_REPORTED
    ]
    if any(severity == Severity.REJECT.value for severity in severities):
        return Outcome.REJECTED
    if any(severity == Severity.UNKNOWN.value for severity in severities):
        return Outcome.UNKNOWN
    return Outcome.APPROVED


def render_surface(events: list[dict]) -> str:
    """Render the human-readable verdict surface from an event prefix.

    A pure projection of the event history into Markdown — the same input
    produces the same surface on every backend.
    """
    lines: list[str] = []
    for event in events:
        data = event.get("data", {})
        event_type = event.get("type")
        if event_type == SCOPE_ENTERED:
            lines.append(f"# Verification run: {data.get('target', '')}")
        elif event_type == FINDING_REPORTED:
            location = data.get("file", "")
            line_no = data.get("line")
            if line_no is not None:
                location = f"{location}:{line_no}"
            lines.append(
                f"- [{data.get('severity', '')}] {location} — {data.get('message', '')}"
            )
        elif event_type == RUN_COMPLETED:
            lines.append(f"\n**Overall: {data.get('overall', '')}**")
    return "\n".join(lines)
