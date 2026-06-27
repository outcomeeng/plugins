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

import json
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Mapping

# Source-owned vocabulary. Consumers and tests import these rather than
# hand-writing the event-type strings or status values.
EVENT_SOURCE = "/spx/journal"

SCOPE_ENTERED = "verification.scope.entered"
SCOPE_ADVANCED = "verification.scope.advanced"
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

    ``line`` is ``None`` for a whole-file finding. ``concern`` and ``action``
    are optional review-kind fields: the review kind populates them so the
    finding event carries the full review finding (category and required
    change) for downstream surfaces and the cross-run fold; the audit kind
    leaves them ``None`` and the projection omits them, so audit events and
    surfaces are unchanged.
    """

    file: str
    line: int | None
    rule: str
    severity: Severity
    message: str
    concern: str | None = None
    action: str | None = None


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


@dataclass(frozen=True)
class RunMetadata:
    """The run identity a streaming verification run derives before it opens.

    The agentic kinds (audit, review) both derive this same identity and pass
    it to the scope-entered and run-completed builders. It lives here, in the
    shared projection, so each adapter parses its run-identity JSON through
    one helper rather than each re-declaring the dataclass and parser. The
    streaming emit reads the identity for the scope-entered event and the full
    run-state record for the terminal event; the findings stream as separate
    events, so the run identity carries none.
    """

    target: str
    scope_hash: str
    branch_name: str
    branch_slug: str
    head_sha: str
    base_ref: str
    base_sha: str
    config_digest: str
    participants: tuple[str, ...]
    scope: Mapping[str, Any]
    started_at: str
    completed_at: str
    output_paths: tuple[str, ...] = ()
    target_kind: object = None
    pull_request_number: int | None = None


def run_from_metadata(metadata: RunMetadata) -> RunResult:
    """Build the projection ``RunResult`` from a parsed run identity."""
    return RunResult(
        target=metadata.target,
        scope_hash=metadata.scope_hash,
        branch_name=metadata.branch_name,
        branch_slug=metadata.branch_slug,
        head_sha=metadata.head_sha,
        base_ref=metadata.base_ref,
        base_sha=metadata.base_sha,
        config_digest=metadata.config_digest,
        participants=metadata.participants,
        scope=metadata.scope,
        started_at=metadata.started_at,
        completed_at=metadata.completed_at,
        output_paths=metadata.output_paths,
        target_kind=(
            JournalTargetKind.BRANCH
            if metadata.target_kind is None
            else JournalTargetKind(metadata.target_kind)
        ),
        pull_request_number=metadata.pull_request_number,
    )


def run_metadata_from_json(text: str) -> RunMetadata:
    """Parse a run-identity JSON object into a :class:`RunMetadata`.

    The streaming adapters derive the run identity at the start of a run and
    pass it as JSON to the ``scope-entered`` and ``run-completed`` event
    subcommands; this is the one parser both kinds invoke.
    """
    data = _require_json_object(text, name="metadata")
    return RunMetadata(
        target=_require_metadata_string(data, "target"),
        scope_hash=_require_metadata_string(data, RUN_STATE_SCOPE_HASH),
        branch_name=_require_metadata_string(data, RUN_STATE_BRANCH_NAME),
        branch_slug=_require_metadata_string(data, RUN_STATE_BRANCH_SLUG),
        head_sha=_require_metadata_string(data, RUN_STATE_HEAD_SHA),
        base_ref=_require_metadata_string(data, RUN_STATE_BASE_REF),
        base_sha=_require_metadata_string(data, RUN_STATE_BASE_SHA),
        config_digest=_require_metadata_string(data, RUN_STATE_CONFIG_DIGEST),
        participants=_require_metadata_string_tuple(data, RUN_STATE_PARTICIPANTS),
        scope=_require_metadata_mapping(data, RUN_STATE_SCOPE),
        started_at=_require_metadata_string(data, RUN_STATE_STARTED_AT),
        completed_at=_require_metadata_string(data, RUN_STATE_COMPLETED_AT),
        output_paths=_optional_metadata_string_tuple(data, RUN_STATE_OUTPUT_PATHS),
        target_kind=_require_metadata_string(data, RUN_STATE_TARGET_KIND),
        pull_request_number=_optional_metadata_positive_int(
            data, RUN_STATE_PULL_REQUEST_NUMBER
        ),
    )


def _require_json_object(text: str, *, name: str) -> dict[str, Any]:
    value = json.loads(text)
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be a JSON object")
    return value


def _require_metadata_string(data: Mapping[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or value == "":
        raise ValueError(f"metadata {key!r} must be a non-empty string")
    return value


def _require_metadata_mapping(data: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    value = data.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"metadata {key!r} must be a JSON object")
    return value


def _require_metadata_string_tuple(
    data: Mapping[str, Any], key: str
) -> tuple[str, ...]:
    value = data.get(key)
    if not isinstance(value, list) or not all(
        isinstance(item, str) and item for item in value
    ):
        raise ValueError(f"metadata {key!r} must be a JSON array of non-empty strings")
    return tuple(value)


def _optional_metadata_string_tuple(
    data: Mapping[str, Any], key: str
) -> tuple[str, ...]:
    value = data.get(key, [])
    if not isinstance(value, list) or not all(
        isinstance(item, str) and item for item in value
    ):
        raise ValueError(f"metadata {key!r} must be a JSON array of non-empty strings")
    return tuple(value)


def _optional_metadata_positive_int(data: Mapping[str, Any], key: str) -> int | None:
    value = data.get(key)
    if value is None:
        return None
    if not isinstance(value, int) or value <= 0:
        raise ValueError(f"metadata {key!r} must be a positive integer when present")
    return value


def _event(event_type: str, data: dict, *, now: str, attempt: int) -> dict:
    """Assemble one channel append input.

    The ``id`` is the event type — a stable, type-based identifier. The
    channel assigns ``seq`` (the event's order in the run) and accepts a
    non-unique ``id``, so a streaming run appends many ``scope.advanced`` and
    ``finding.reported`` events that share one ``id`` each and are ordered by
    the channel's ``seq``. ``source``/``type``/``time`` are non-empty strings
    and ``attempt`` an integer; the channel assigns the remaining CloudEvents
    attributes.
    """
    return {
        "id": event_type,
        "source": EVENT_SOURCE,
        "type": event_type,
        "time": now,
        "attempt": attempt,
        "data": data,
    }


def scope_entered_event(run: RunResult, *, now: str, attempt: int = 1) -> dict:
    """Build the scope-entered event that opens a streaming run.

    Carries the run's identity — target, scope hash, and branch/head/base —
    known the moment the run begins, before any unit of scope is examined.
    The consuming skill appends this first, then streams ``scope.advanced``
    and ``finding.reported`` events as the run advances.
    """
    return _event(
        SCOPE_ENTERED,
        {
            "target": run.target,
            RUN_STATE_SCOPE_HASH: run.scope_hash,
            RUN_STATE_BRANCH_NAME: run.branch_name,
            RUN_STATE_BRANCH_SLUG: run.branch_slug,
            RUN_STATE_HEAD_SHA: run.head_sha,
            RUN_STATE_BASE_REF: run.base_ref,
        },
        now=now,
        attempt=attempt,
    )


def scope_advanced_event(unit: str, *, now: str, attempt: int = 1) -> dict:
    """Build a scope-advanced event naming the unit of scope just examined.

    The run appends one of these as it reaches each unit of its scope — a
    changed file for review, a partition for audit — so a reader resuming
    from a cursor watches the run advance through its scope in flight.
    """
    return _event(SCOPE_ADVANCED, {"unit": unit}, now=now, attempt=attempt)


def finding_reported_event(finding: Finding, *, now: str, attempt: int = 1) -> dict:
    """Build a finding-reported event for one raised finding.

    ``concern`` and ``action`` are carried only when the finding sets them
    (the review kind); the audit kind leaves them ``None`` and they are
    omitted, so the audit event shape is unchanged.
    """
    data: dict[str, object] = {
        "file": finding.file,
        "line": finding.line,
        "rule": finding.rule,
        "severity": str(finding.severity),
        "message": finding.message,
    }
    if finding.concern is not None:
        data["concern"] = finding.concern
    if finding.action is not None:
        data["action"] = finding.action
    return _event(FINDING_REPORTED, data, now=now, attempt=attempt)


def run_completed_event(
    run: RunResult, *, status: JournalRunStatus, now: str, attempt: int = 1
) -> dict:
    """Build the terminal run-completed event that seals a streaming run.

    Its data is the core journal run-state record carrying the run's
    identity, timestamps, output paths, and terminal status. The consuming
    skill computes ``status`` from the journal prefix it has streamed —
    ``terminal_status`` over ``compute_overall`` of the appended
    ``finding.reported`` events — and passes it here, so the terminal status
    reflects the findings the run raised.
    """
    return _event(
        RUN_COMPLETED,
        journal_run_state_record(run, status=status),
        now=now,
        attempt=attempt,
    )


def build_events(run: RunResult, *, now: str, attempt: int = 1) -> list[dict]:
    """Build the ordered channel event-input sequence for a run.

    Yields a ``scope.entered`` event, one ``finding.reported`` event per
    finding (in order), and a terminal ``run.completed`` event carrying the
    rolled-up overall. Each returned dict is a valid channel append input:
    non-empty ``id``/``source``/``type``/``time`` strings and an integer
    ``attempt``, plus a ``data`` object. The channel assigns the remaining
    CloudEvents attributes.

    This batch builder serves the audit kind, which adapts a finished wrapper
    verdict into one ``RunResult`` and emits its events together; the streaming
    kinds (review) append each event through the per-event builders above as
    the run advances.
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
        elif event_type == SCOPE_ADVANCED:
            lines.append(f"- examined {data.get('unit', '')}")
        elif event_type == FINDING_REPORTED:
            location = data.get("file", "")
            line_no = data.get("line")
            if line_no is not None:
                location = f"{location}:{line_no}"
            severity = data.get("severity", "")
            concern = data.get("concern")
            label = f"{severity} {concern}" if concern is not None else severity
            line = f"- [{label}] {location} — {data.get('message', '')}"
            action = data.get("action")
            if action is not None:
                line = f"{line} Required: {action}"
            lines.append(line)
        elif event_type == RUN_COMPLETED:
            overall = str(compute_overall(events))
            status = data.get(RUN_STATE_STATUS, "")
            lines.append(f"\n**Overall: {overall} (status: {status})**")
    return "\n".join(lines)
