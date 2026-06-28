"""Audit consumer's run-journal adapter — stdlib only.

Bridges the audit verdict toolchain to the shared run-journal projection.
``/audit``'s dispatched skills emit verdicts conforming to ``verdict.py``'s
schema; the run journal records a verification run as ``spx journal`` events
and derives the verdict from the sealed event prefix through the shared,
type-agnostic projection in ``journal_projection.py``. This adapter maps one
audit wrapper verdict onto that projection's generic ``RunResult`` so the
audit run records and renders through the one shared projection rather than
re-implementing event construction, the rollup, or the render.

Per-event CLI subcommands drive the stateless local emit:

- ``metadata`` validates run identity fields and prints the JSON object passed
  to event subcommands.
- ``scope-entered`` prints the opening scope-entered event from metadata.
- ``scope-advanced`` prints a progress event naming one completed partition.
- ``findings-reported`` reads one verdict JSON on stdin and prints one
  finding-reported event per projected finding.
- ``run-completed`` reads the streamed event prefix on stdin and prints the
  terminal run-completed event from metadata and that prefix.
- ``render`` reads a sealed event prefix (``spx journal read`` JSON) on stdin
  and prints the run's rolled-up overall and the human-readable surface.

The rollup the run reports is ``journal_projection.compute_overall`` over the
event prefix — the shared projection owns it. This adapter's only contract is
that translation: a wrapper verdict's outcome under the toolchain's rollup is
preserved once routed through the journal.

Portability: standard library only. ``verdict.py`` (sibling) and
``journal_projection.py`` (the project-run-journal skill) are loaded relative
to this file's location, so the adapter resolves them whether it runs as
``python3 journal_emit.py`` or is loaded through ``importlib`` by a test. The
verdict types are imported under ``TYPE_CHECKING`` only — the runtime modules
come from the file-relative loader, so the static types annotate the wrapper
the adapter reads without a runtime import dependency.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import pathlib
import sys
from dataclasses import dataclass, replace
from types import ModuleType
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import verdict as verdict_schema

_HERE = pathlib.Path(__file__).resolve().parent


def _load_sibling_module(name: str, path: pathlib.Path) -> ModuleType:
    """Load a plugin script as a module by path, cached under ``sys.modules``.

    The marketplace ships every plugin script under ``scripts/`` as a bare
    module rather than an importable package. The cache check keeps one module
    identity per name so a test that also loads ``journal_projection`` through
    its own harness shares this module object rather than a divergent copy.
    """
    cached = sys.modules.get(name)
    if cached is not None:
        return cached
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


verdict = _load_sibling_module("verdict", _HERE / "verdict.py")
jp = _load_sibling_module(
    "journal_projection",
    _HERE.parents[1] / "project-run-journal" / "scripts" / "journal_projection.py",
)

# Journal-side severity strings, read from the shared projection's vocabulary
# so the adapter owns no severity literal of its own. A failing contributor
# without a representative finding and every unknown contributor are surfaced
# through a synthesized finding carrying these severities — the verdict
# toolchain has no unknown finding severity, and an orchestrator gate row
# carries no findings at all.
_REJECT: str = str(jp.Severity.REJECT)
_UNKNOWN: str = str(jp.Severity.UNKNOWN)

_FAILING_STATUSES = frozenset({str(verdict.Status.FAIL), str(verdict.Status.REJECTED)})
_UNKNOWN_STATUS = str(verdict.Status.UNKNOWN)


@dataclass(frozen=True)
class _ProjectedFinding:
    """One run finding in the projection's vocabulary, before channel events.

    Holds the journal-side severity string so the audit-specific mapping stays
    here and the channel-event construction stays a thin call into the shared
    projection.
    """

    file: str
    line: int | None
    rule: str
    severity: str
    message: str


@dataclass(frozen=True)
class MetadataValues:
    """Raw run metadata values before shared projection validation."""

    target: str
    scope_hash: str
    branch_name: str
    branch_slug: str
    head_sha: str
    base_ref: str
    base_sha: str
    config_digest: str
    participants: tuple[str, ...]
    scope: dict[str, Any]
    started_at: str
    completed_at: str
    output_paths: tuple[str, ...]
    target_kind: object
    pull_request_number: int | None = None


def _map_finding(finding: verdict_schema.Finding) -> _ProjectedFinding:
    # The verdict and journal severities share member names (REJECT/WARNING/
    # INFO), so the journal severity is the projection member of the same name
    # — no hand-written severity table.
    return _ProjectedFinding(
        file=finding.file,
        line=finding.line,
        rule=finding.rule,
        severity=str(getattr(jp.Severity, finding.severity.name)),
        message=finding.message,
    )


def _marker(name: str, severity: str, message: str) -> _ProjectedFinding:
    return _ProjectedFinding(
        file=name, line=None, rule=name, severity=severity, message=message
    )


def _project_row(row: verdict_schema.Row) -> list[_ProjectedFinding]:
    findings = [_map_finding(finding) for finding in row.findings]
    status = str(row.status)
    if status in _FAILING_STATUSES and not any(
        finding.severity == _REJECT for finding in findings
    ):
        findings.append(_marker(row.name, _REJECT, "row failed"))
    elif status == _UNKNOWN_STATUS:
        findings.append(_marker(row.name, _UNKNOWN, "row outcome unknown"))
    return findings


def _project_verdict(node: verdict_schema.Verdict) -> list[_ProjectedFinding]:
    findings: list[_ProjectedFinding] = []
    for row in node.rows:
        findings.extend(_project_row(row))
    for child in node.children:
        findings.extend(_project_child(child))
    return findings


def _project_child(child: verdict_schema.Verdict) -> list[_ProjectedFinding]:
    findings = _project_verdict(child)
    status = str(child.overall)
    if status in _FAILING_STATUSES and not any(
        finding.severity == _REJECT for finding in findings
    ):
        findings.append(_marker(child.skill, _REJECT, "child rejected"))
    elif status == _UNKNOWN_STATUS:
        findings.append(_marker(child.skill, _UNKNOWN, "child outcome unknown"))
    return findings


def metadata_from_values(values: MetadataValues) -> object:
    """Build validated run metadata for streaming audit events."""
    payload: dict[str, object] = {
        "target": values.target,
        jp.RUN_STATE_SCOPE_HASH: values.scope_hash,
        jp.RUN_STATE_BRANCH_NAME: values.branch_name,
        jp.RUN_STATE_BRANCH_SLUG: values.branch_slug,
        jp.RUN_STATE_TARGET_KIND: str(jp.JournalTargetKind(values.target_kind)),
        jp.RUN_STATE_HEAD_SHA: values.head_sha,
        jp.RUN_STATE_BASE_REF: values.base_ref,
        jp.RUN_STATE_BASE_SHA: values.base_sha,
        jp.RUN_STATE_CONFIG_DIGEST: values.config_digest,
        jp.RUN_STATE_PARTICIPANTS: list(values.participants),
        jp.RUN_STATE_SCOPE: values.scope,
        jp.RUN_STATE_STARTED_AT: values.started_at,
        jp.RUN_STATE_COMPLETED_AT: values.completed_at,
        jp.RUN_STATE_OUTPUT_PATHS: list(values.output_paths),
    }
    if values.pull_request_number is not None:
        payload[jp.RUN_STATE_PULL_REQUEST_NUMBER] = values.pull_request_number
    return jp.run_metadata_from_json(json.dumps(payload))


def scope_entered_event(
    metadata: object, *, now: str, attempt: int = 1
) -> dict[str, object]:
    """Build the scope-entered event from the audit run metadata."""
    return jp.scope_entered_event(
        jp.run_from_metadata(metadata), now=now, attempt=attempt
    )


def scope_advanced_event(unit: str, *, now: str, attempt: int = 1) -> dict[str, object]:
    """Build a scope-advanced event for one completed audit partition."""
    return jp.scope_advanced_event(unit, now=now, attempt=attempt)


def finding_events_for_verdict(
    node: verdict_schema.Verdict, *, now: str, attempt: int = 1
) -> list[dict[str, object]]:
    """Build finding-reported events for one streamed audit verdict."""
    return [
        jp.finding_reported_event(
            jp.Finding(
                file=finding.file,
                line=finding.line,
                rule=finding.rule,
                severity=jp.Severity(finding.severity),
                message=finding.message,
            ),
            now=now,
            attempt=attempt,
        )
        for finding in _project_verdict(node)
    ]


def finding_events_for_child(
    child: verdict_schema.Verdict, *, now: str, attempt: int = 1
) -> list[dict[str, object]]:
    """Build finding events for a streamed child verdict contribution."""
    return [
        jp.finding_reported_event(
            jp.Finding(
                file=finding.file,
                line=finding.line,
                rule=finding.rule,
                severity=jp.Severity(finding.severity),
                message=finding.message,
            ),
            now=now,
            attempt=attempt,
        )
        for finding in _project_child(child)
    ]


def run_completed_event(
    metadata: object,
    prefix: list[dict[str, object]],
    *,
    completed_at: str,
    now: str,
    attempt: int = 1,
) -> dict[str, object]:
    """Build the terminal run-completed event from the streamed prefix."""
    run = replace(jp.run_from_metadata(metadata), completed_at=completed_at)
    return jp.run_completed_event(
        run,
        status=jp.terminal_status(jp.compute_overall(prefix)),
        now=now,
        attempt=attempt,
    )


def render_events(events: list[dict[str, object]]) -> dict[str, str]:
    """Roll up and render a sealed event prefix into the run's verdict."""
    return {
        "overall": str(jp.compute_overall(events)),
        "surface": str(jp.render_surface(events)),
    }


def _emit_event(event: dict[str, object]) -> int:
    sys.stdout.write(json.dumps(event) + "\n")
    return 0


def _emit_metadata(args: argparse.Namespace) -> int:
    try:
        participants = _json_string_tuple(args.participants_json, name="participants")
        scope = _json_object(args.scope_json, name="scope")
        output_paths = _json_string_tuple(args.output_paths_json, name="output paths")
        metadata = metadata_from_values(
            MetadataValues(
                target=args.target,
                scope_hash=args.scope_hash,
                branch_name=args.branch_name,
                branch_slug=args.branch_slug,
                head_sha=args.head_sha,
                base_ref=args.base_ref,
                base_sha=args.base_sha,
                config_digest=args.config_digest,
                participants=participants,
                scope=scope,
                started_at=args.started_at,
                completed_at=args.completed_at,
                output_paths=output_paths,
                target_kind=args.target_kind,
                pull_request_number=args.pull_request_number,
            )
        )
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        sys.stderr.write(f"{exc}\n")
        return 1
    payload = {
        "target": metadata.target,
        jp.RUN_STATE_SCOPE_HASH: metadata.scope_hash,
        jp.RUN_STATE_BRANCH_NAME: metadata.branch_name,
        jp.RUN_STATE_BRANCH_SLUG: metadata.branch_slug,
        jp.RUN_STATE_HEAD_SHA: metadata.head_sha,
        jp.RUN_STATE_BASE_REF: metadata.base_ref,
        jp.RUN_STATE_BASE_SHA: metadata.base_sha,
        jp.RUN_STATE_CONFIG_DIGEST: metadata.config_digest,
        jp.RUN_STATE_PARTICIPANTS: list(metadata.participants),
        jp.RUN_STATE_SCOPE: dict(metadata.scope),
        jp.RUN_STATE_STARTED_AT: metadata.started_at,
        jp.RUN_STATE_COMPLETED_AT: metadata.completed_at,
        jp.RUN_STATE_OUTPUT_PATHS: list(metadata.output_paths),
        jp.RUN_STATE_TARGET_KIND: str(metadata.target_kind),
    }
    if metadata.pull_request_number is not None:
        payload[jp.RUN_STATE_PULL_REQUEST_NUMBER] = metadata.pull_request_number
    json.dump(payload, sys.stdout)
    return 0


def _scope_entered(args: argparse.Namespace) -> int:
    try:
        metadata = jp.run_metadata_from_json(args.metadata)
    except ValueError as exc:
        sys.stderr.write(f"{exc}\n")
        return 1
    return _emit_event(
        scope_entered_event(metadata, now=args.now, attempt=args.attempt)
    )


def _scope_advanced(args: argparse.Namespace) -> int:
    return _emit_event(
        scope_advanced_event(args.unit, now=args.now, attempt=args.attempt)
    )


def _findings_reported(args: argparse.Namespace) -> int:
    try:
        node = verdict.parse_json(sys.stdin.read())
    except ValueError as exc:
        sys.stderr.write(f"{exc}\n")
        return 1
    for event in finding_events_for_child(node, now=args.now, attempt=args.attempt):
        _emit_event(event)
    return 0


def _run_completed(args: argparse.Namespace) -> int:
    try:
        metadata = jp.run_metadata_from_json(args.metadata)
        prefix = json.load(sys.stdin)
    except (ValueError, json.JSONDecodeError) as exc:
        sys.stderr.write(f"{exc}\n")
        return 1
    if not isinstance(prefix, list):
        sys.stderr.write("event prefix must be a JSON array\n")
        return 1
    return _emit_event(
        run_completed_event(
            metadata,
            prefix,
            completed_at=args.completed_at,
            now=args.now,
            attempt=args.attempt,
        )
    )


def _render() -> int:
    json.dump(render_events(json.load(sys.stdin)), sys.stdout)
    return 0


def _json_object(text: str, *, name: str) -> dict[str, Any]:
    value = json.loads(text)
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be a JSON object")
    return value


def _json_string_tuple(text: str, *, name: str) -> tuple[str, ...]:
    value = json.loads(text)
    if not isinstance(value, list) or not all(
        isinstance(item, str) and item for item in value
    ):
        raise ValueError(f"{name} must be a JSON array of non-empty strings")
    return tuple(value)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    def _add_event_args(sub: argparse.ArgumentParser) -> None:
        sub.add_argument("--now", required=True, help="UTC timestamp for the event")
        sub.add_argument(
            "--attempt", type=int, default=1, help="run attempt number (default 1)"
        )

    metadata = subparsers.add_parser(
        "metadata",
        help="validate run identity fields and print metadata JSON",
    )
    metadata.add_argument("--target", required=True)
    metadata.add_argument("--scope-hash", required=True)
    metadata.add_argument("--branch-name", required=True)
    metadata.add_argument("--branch-slug", required=True)
    metadata.add_argument("--head-sha", required=True)
    metadata.add_argument("--base-ref", required=True)
    metadata.add_argument("--base-sha", required=True)
    metadata.add_argument("--config-digest", required=True)
    metadata.add_argument("--participants-json", required=True)
    metadata.add_argument("--scope-json", required=True)
    metadata.add_argument("--started-at", required=True)
    metadata.add_argument("--completed-at", required=True)
    metadata.add_argument("--output-paths-json", required=True)
    metadata.add_argument("--target-kind", default=str(jp.JournalTargetKind.BRANCH))
    metadata.add_argument("--pull-request-number", type=int, default=None)

    scope_entered = subparsers.add_parser(
        "scope-entered",
        help="print the scope-entered event opening a streaming audit run",
    )
    _add_event_args(scope_entered)
    scope_entered.add_argument("--metadata", required=True)

    scope_advanced = subparsers.add_parser(
        "scope-advanced",
        help="print a scope-advanced event naming one completed audit partition",
    )
    _add_event_args(scope_advanced)
    scope_advanced.add_argument("--unit", required=True)

    findings_reported = subparsers.add_parser(
        "findings-reported",
        help="read one verdict JSON and print finding-reported events",
    )
    _add_event_args(findings_reported)

    run_completed = subparsers.add_parser(
        "run-completed",
        help="print the terminal run-completed event from streamed prefix JSON",
    )
    _add_event_args(run_completed)
    run_completed.add_argument("--metadata", required=True)
    run_completed.add_argument("--completed-at", required=True)

    subparsers.add_parser(
        "render",
        help="roll up and render a sealed event prefix (stdin) to a verdict (stdout)",
    )

    args = parser.parse_args(argv)
    handlers = {
        "metadata": _emit_metadata,
        "scope-entered": _scope_entered,
        "scope-advanced": _scope_advanced,
        "findings-reported": _findings_reported,
        "run-completed": _run_completed,
    }
    handler = handlers.get(args.command)
    if handler is not None:
        return handler(args)
    return _render()


if __name__ == "__main__":
    raise SystemExit(main())
