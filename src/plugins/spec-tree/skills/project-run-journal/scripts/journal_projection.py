"""Consumer-side run-journal projection — stdlib only, pure.

Shared by the agentic verification surfaces (audit, review) that drive
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
from typing import Any, Mapping

# Source-owned vocabulary. Consumers and tests import these rather than
# hand-writing the event-type strings or status values.
EVENT_SOURCE = "/spx/journal"

SCOPE_ENTERED = "verification.scope.entered"
FINDING_REPORTED = "verification.finding.reported"
RUN_COMPLETED = "com.outcomeeng.spx.journal.run.completed"

RUN_STATE_BRANCH_NAME = "branchName"
RUN_STATE_BRANCH_SLUG = "branchSlug"
RUN_STATE_TARGET_KIND = "targetKind"
RUN_STATE_PULL_REQUEST_NUMBER = "pullRequestNumber"
RUN_STATE_HEAD_SHA = "headSha"
RUN_STATE_BASE_REF = "baseRef"
RUN_STATE_BASE_SHA = "baseSha"
RUN_STATE_CONFIG_DIGEST = "configDigest"
RUN_STATE_PARTICIPANTS = "participants"
RUN_STATE_SCOPE = "scope"
RUN_STATE_STARTED_AT = "startedAt"
RUN_STATE_COMPLETED_AT = "completedAt"
RUN_STATE_OUTPUT_PATHS = "outputPaths"
RUN_STATE_STATUS = "status"
RUN_STATE_SCOPE_HASH = "scopeHash"

RUN_STATE_FIELDS: tuple[str, ...] = (
    RUN_STATE_BRANCH_NAME,
    RUN_STATE_BRANCH_SLUG,
    RUN_STATE_TARGET_KIND,
    RUN_STATE_HEAD_SHA,
    RUN_STATE_BASE_REF,
    RUN_STATE_CONFIG_DIGEST,
    RUN_STATE_PARTICIPANTS,
    RUN_STATE_SCOPE,
    RUN_STATE_STARTED_AT,
    RUN_STATE_COMPLETED_AT,
    RUN_STATE_OUTPUT_PATHS,
    RUN_STATE_STATUS,
)

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


class JournalTargetKind(StrEnum):
    """The target kinds accepted by the core journal run state."""

    BRANCH = "branch"
    PULL_REQUEST = "pull-request"


class JournalRunStatus(StrEnum):
    """The terminal statuses accepted by the core journal run state."""

    APPROVED = "approved"
    REJECTED = "rejected"
    FAILED = "failed"
    INTERRUPTED = "interrupted"


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

    Audit and review each adapt their own result shape into this; the
    projection knows nothing of either's verdict schema.
    """

    target: str
    scope_hash: str
    branch_name: str
    branch_slug: str
    head_sha: str
    base_ref: str
    config_digest: str
    participants: tuple[str, ...]
    scope: Mapping[str, Any]
    started_at: str
    completed_at: str
    output_paths: tuple[str, ...]
    findings: tuple[Finding, ...] = ()
    target_kind: JournalTargetKind = JournalTargetKind.BRANCH
    base_sha: str | None = None
    pull_request_number: int | None = None


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
            {
                "target": run.target,
                RUN_STATE_SCOPE_HASH: run.scope_hash,
                RUN_STATE_BRANCH_NAME: run.branch_name,
                RUN_STATE_BRANCH_SLUG: run.branch_slug,
                RUN_STATE_HEAD_SHA: run.head_sha,
                RUN_STATE_BASE_REF: run.base_ref,
            },
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
    events.append(
        event(
            RUN_COMPLETED,
            journal_run_state_record(
                run, status=terminal_status(compute_overall(events))
            ),
        )
    )
    return events


def journal_run_state_record(
    run: RunResult, *, status: JournalRunStatus
) -> dict[str, object]:
    """Serialize a run result into the core journal run-state record."""
    _require_run_state(run)
    return {
        RUN_STATE_BRANCH_NAME: run.branch_name,
        RUN_STATE_BRANCH_SLUG: run.branch_slug,
        RUN_STATE_TARGET_KIND: str(run.target_kind),
        **(
            {}
            if run.pull_request_number is None
            else {RUN_STATE_PULL_REQUEST_NUMBER: run.pull_request_number}
        ),
        RUN_STATE_HEAD_SHA: run.head_sha,
        RUN_STATE_BASE_REF: run.base_ref,
        **({} if run.base_sha is None else {RUN_STATE_BASE_SHA: run.base_sha}),
        RUN_STATE_CONFIG_DIGEST: run.config_digest,
        RUN_STATE_PARTICIPANTS: list(run.participants),
        RUN_STATE_SCOPE: dict(run.scope),
        RUN_STATE_STARTED_AT: run.started_at,
        RUN_STATE_COMPLETED_AT: run.completed_at,
        RUN_STATE_OUTPUT_PATHS: list(run.output_paths),
        RUN_STATE_STATUS: str(status),
    }


def terminal_status(outcome: Outcome) -> JournalRunStatus:
    """Map the verdict rollup to the core journal terminal-status vocabulary."""
    if outcome == Outcome.APPROVED:
        return JournalRunStatus.APPROVED
    if outcome == Outcome.REJECTED:
        return JournalRunStatus.REJECTED
    return JournalRunStatus.FAILED


def _require_run_state(run: RunResult) -> None:
    string_fields = {
        "target": run.target,
        RUN_STATE_SCOPE_HASH: run.scope_hash,
        RUN_STATE_BRANCH_NAME: run.branch_name,
        RUN_STATE_BRANCH_SLUG: run.branch_slug,
        RUN_STATE_HEAD_SHA: run.head_sha,
        RUN_STATE_BASE_REF: run.base_ref,
        RUN_STATE_CONFIG_DIGEST: run.config_digest,
        RUN_STATE_STARTED_AT: run.started_at,
        RUN_STATE_COMPLETED_AT: run.completed_at,
    }
    for field, value in string_fields.items():
        if value == "":
            raise ValueError(f"{field} must be a non-empty string")
    if run.base_sha == "":
        raise ValueError(f"{RUN_STATE_BASE_SHA} must be non-empty when present")
    if not run.participants:
        raise ValueError(f"{RUN_STATE_PARTICIPANTS} must contain at least one entry")
    if not all(run.participants):
        raise ValueError(
            f"{RUN_STATE_PARTICIPANTS} must contain only non-empty strings"
        )
    if not all(run.output_paths):
        raise ValueError(
            f"{RUN_STATE_OUTPUT_PATHS} must contain only non-empty strings"
        )


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
            overall = str(compute_overall(events))
            status = data.get(RUN_STATE_STATUS, "")
            lines.append(f"\n**Overall: {overall} (status: {status})**")
    return "\n".join(lines)
