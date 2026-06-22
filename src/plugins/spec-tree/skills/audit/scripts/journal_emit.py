"""Audit consumer's run-journal adapter — stdlib only.

Bridges the audit verdict toolchain to the shared run-journal projection.
``/audit``'s dispatched skills emit verdicts conforming to ``verdict.py``'s
schema; the run journal records a verification run as ``spx journal`` events
and derives the verdict from the sealed event prefix through the shared,
type-agnostic projection in ``journal_projection.py``. This adapter maps one
audit wrapper verdict onto that projection's generic ``RunResult`` so the
audit run records and renders through the one shared projection rather than
re-implementing event construction, the rollup, or the render.

Two CLI subcommands drive the stateless local emit:

- ``build-events`` reads a wrapper verdict (``verdict.py`` JSON) on stdin and
  prints the ordered ``spx journal`` channel event inputs as a JSON array; the
  consuming skill appends each to the channel.
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
from dataclasses import dataclass
from types import ModuleType
from typing import TYPE_CHECKING, cast

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


def events_for_wrapper(
    wrapper: verdict_schema.Verdict, *, now: str, attempt: int = 1
) -> list[dict[str, object]]:
    """Map an audit wrapper verdict onto the ordered journal event inputs.

    The wrapper's orchestrator rows and per-language children become the run's
    findings — each real finding mapped onto the projection's severity
    vocabulary, every failing or unknown contributor without a representative
    finding contributing a synthesized one — so the event prefix rolls up to
    the toolchain's overall over the same wrapper.
    """
    projected = _project_verdict(wrapper)
    run = jp.RunResult(
        target=wrapper.target,
        scope_hash=wrapper.metadata.get("scope_hash", ""),
        branch=wrapper.metadata.get("branch", ""),
        findings=tuple(
            jp.Finding(
                file=finding.file,
                line=finding.line,
                rule=finding.rule,
                severity=jp.Severity(finding.severity),
                message=finding.message,
            )
            for finding in projected
        ),
    )
    # ``jp`` is the file-relative-loaded shared projection (Any to the type
    # checker); ``build_events`` returns the channel event-input list.
    return cast(
        "list[dict[str, object]]", jp.build_events(run, now=now, attempt=attempt)
    )


def render_events(events: list[dict[str, object]]) -> dict[str, str]:
    """Roll up and render a sealed event prefix into the run's verdict."""
    return {
        "overall": str(jp.compute_overall(events)),
        "surface": str(jp.render_surface(events)),
    }


def _build_events(now: str, attempt: int) -> int:
    # One event per line so the consuming skill appends each to the channel
    # with one `spx journal append` per line, no array splitting.
    wrapper = verdict.parse_json(sys.stdin.read())
    for event in events_for_wrapper(wrapper, now=now, attempt=attempt):
        sys.stdout.write(json.dumps(event) + "\n")
    return 0


def _render() -> int:
    json.dump(render_events(json.load(sys.stdin)), sys.stdout)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    build = subparsers.add_parser(
        "build-events",
        help="map a wrapper verdict (stdin) to spx journal event inputs (stdout)",
    )
    build.add_argument("--now", required=True, help="UTC timestamp for every event")
    build.add_argument(
        "--attempt", type=int, default=1, help="run attempt number (default 1)"
    )

    subparsers.add_parser(
        "render",
        help="roll up and render a sealed event prefix (stdin) to a verdict (stdout)",
    )

    args = parser.parse_args(argv)
    if args.command == "build-events":
        return _build_events(args.now, args.attempt)
    return _render()


if __name__ == "__main__":
    raise SystemExit(main())
