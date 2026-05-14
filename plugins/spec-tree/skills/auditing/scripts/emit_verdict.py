#!/usr/bin/env python3
"""Emit an audit verdict in markdown, markdown+JSON, or JSON-only form.

Reads a JSON verdict document from stdin (or ``--file``), validates it
against the canonical schema in ``verdict.py``, and writes one of three
surface forms to stdout (or ``--output``):

- ``markdown``       — human-readable table only. For local inspection.
- ``markdown+json``  — table followed by an HTML-comment-delimited JSON
                       block. For PR-comment delivery: humans read the
                       table, tooling parses the JSON.
- ``json-only``      — raw JSON, no markdown carrier. For skill-to-skill
                       internal calls.

Portability: stdlib only. Invoked from skill content as
``python3 "${CLAUDE_SKILL_DIR}/scripts/emit_verdict.py" ...`` — the skill
loader substitutes the path before the agent sees the command.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Bare ``import verdict`` resolves because this file is invoked as a script
# (Python prepends the script's directory to ``sys.path``). Tests exercise
# this script through ``subprocess`` calls, not via ``importlib`` loading;
# the audit_orchestrator.py loader pattern is only needed for modules that
# tests import directly.
import verdict
from verdict import (
    JSON_BLOCK_BEGIN,
    JSON_BLOCK_END,
    Finding,
    Row,
    Verdict,
    VerdictValidationError,
)

FORMAT_MARKDOWN = "markdown"
FORMAT_MARKDOWN_JSON = "markdown+json"
FORMAT_JSON_ONLY = "json-only"
FORMAT_CHOICES = (FORMAT_MARKDOWN, FORMAT_MARKDOWN_JSON, FORMAT_JSON_ONLY)

EXIT_OK = 0
EXIT_VALIDATION_ERROR = 1
EXIT_IO_ERROR = 2

# Cell escape: backslash first so it does not corrupt the subsequent escapes.
CELL_BACKSLASH = ("\\", r"\\")
CELL_PIPE = ("|", r"\|")
CELL_NEWLINE = ("\n", r"\n")


def main(argv: list[str] | None = None) -> int:
    """Entry point. Returns a process exit code."""
    args = _parse_args(argv)
    try:
        text = _read_input(args.file)
    except OSError as exc:
        print(f"emit_verdict: cannot read input: {exc}", file=sys.stderr)
        return EXIT_IO_ERROR
    try:
        parsed = verdict.parse_json(text)
    except VerdictValidationError as exc:
        print(f"emit_verdict: invalid verdict: {exc}", file=sys.stderr)
        return EXIT_VALIDATION_ERROR
    rendered = render(parsed, args.format)
    try:
        _write_output(args.output, rendered)
    except OSError as exc:
        print(f"emit_verdict: cannot write output: {exc}", file=sys.stderr)
        return EXIT_IO_ERROR
    return EXIT_OK


def render(v: Verdict, fmt: str) -> str:
    """Return the surface-form string for the verdict in the requested format.

    All three forms terminate with a trailing newline so the output composes
    cleanly with line-oriented tooling (`read_verdict.py` and external
    consumers that expect a newline-terminated JSON document; matches
    `read_verdict`'s `dump_json(...) + "\\n"` output convention).
    """
    if fmt == FORMAT_JSON_ONLY:
        return verdict.dump_json(v) + "\n"
    md = _render_markdown(v, depth=1)
    if fmt == FORMAT_MARKDOWN:
        return md
    if fmt == FORMAT_MARKDOWN_JSON:
        payload = verdict.dump_json(v)
        return (
            md.rstrip("\n")
            + "\n\n"
            + JSON_BLOCK_BEGIN
            + "\n"
            + payload
            + "\n"
            + JSON_BLOCK_END
            + "\n"
        )
    raise ValueError(f"unknown format {fmt!r}; expected one of {FORMAT_CHOICES}")


def _render_markdown(v: Verdict, *, depth: int) -> str:
    """Render one verdict (and its children) as nested markdown sections.

    ``depth`` controls the heading level (1 → ``#``, 2 → ``##``, …) so
    nested child verdicts produce a coherent outline.
    """
    parts: list[str] = []
    # Markdown caps headings at level 6 (`######`); deeper nesting
    # would render as plain text preceded by `#######` in many
    # renderers. Today's hierarchy is at most two levels deep
    # (orchestrator wrapper + dispatched-skill children), but the
    # clamp keeps the output valid if a future composition adds depth.
    # The same clamp applies to the children-section header below
    # (``"#" * min(depth + 1, 6)``) and the findings-section header
    # passed via ``depth=depth + 1`` — every heading written by this
    # module is clamped uniformly so the output stays well-formed at
    # every level.
    hash_prefix = "#" * min(depth, 6)
    parts.append(f"{hash_prefix} Audit verdict — {_escape_inline(v.skill)}")
    parts.append("")
    parts.append(f"- **Overall:** {v.overall.value}")
    parts.append(f"- **Target:** `{_escape_codespan(v.target)}`")
    if v.metadata:
        parts.append("- **Metadata:**")
        for key in sorted(v.metadata):
            parts.append(
                f"  - `{_escape_codespan(key)}`: {_escape_inline(v.metadata[key])}"
            )
    parts.append("")
    if v.rows:
        parts.append(_render_rows_table(v.rows))
        parts.append("")
        findings_section = _render_findings_section(v.rows, depth=depth + 1)
        if findings_section:
            parts.append(findings_section)
            parts.append("")
    if v.resolved:
        parts.append(
            _render_verdict_finding_section(
                "Resolved findings", v.resolved, depth=depth + 1
            )
        )
        parts.append("")
    if v.reopened:
        parts.append(
            _render_verdict_finding_section(
                "Reopened findings", v.reopened, depth=depth + 1
            )
        )
        parts.append("")
    if v.children:
        parts.append(f"{'#' * min(depth + 1, 6)} Child verdicts")
        parts.append("")
        for child in v.children:
            parts.append(_render_markdown(child, depth=depth + 2))
            parts.append("")
    return "\n".join(parts).rstrip("\n") + "\n"


def _render_rows_table(rows: tuple[Row, ...]) -> str:
    """Render the concern × status × finding-count table."""
    lines: list[str] = [
        "| Concern | Status | Findings |",
        "| ------- | ------ | -------- |",
    ]
    for row in rows:
        count = len(row.findings)
        finding_cell = "—" if count == 0 else str(count)
        lines.append(
            f"| {_escape_cell(row.name)} | {row.status.value} | {finding_cell} |"
        )
    return "\n".join(lines)


def _render_findings_section(rows: tuple[Row, ...], *, depth: int) -> str:
    """Render the per-row findings detail, omitting rows with no findings."""
    rendered: list[str] = []
    for row in rows:
        if not row.findings:
            continue
        rendered.append(
            f"{'#' * depth} {_escape_inline(row.name)} — {row.status.value}"
        )
        rendered.append("")
        for finding in row.findings:
            rendered.append(_render_finding_bullet(finding))
        rendered.append("")
    return "\n".join(rendered).rstrip("\n")


def _render_verdict_finding_section(
    heading: str, findings: tuple[Finding, ...], *, depth: int
) -> str:
    """Render one verdict-level finding list (resolved or reopened).

    Used for the ``resolved`` and ``reopened`` finding lists on a Verdict
    when a caller diffs the current audit against a prior verdict. Heading
    level is clamped to depth 6 to match the row-section convention. The
    same finding-bullet format used for row findings keeps the surface
    visually consistent across all finding lists in the verdict.
    """
    rendered: list[str] = [
        f"{'#' * min(depth, 6)} {_escape_inline(heading)}",
        "",
    ]
    for finding in findings:
        rendered.append(_render_finding_bullet(finding))
    return "\n".join(rendered).rstrip("\n")


def _render_finding_bullet(finding: Finding) -> str:
    # ``file`` and ``rule`` are rendered inside backtick code spans;
    # ``id`` and ``message`` are rendered in ordinary prose context.
    # The two contexts have different backtick-handling rules — see
    # ``_escape_codespan`` and ``_escape_inline`` for the per-context
    # behaviour. Conflating them (a single helper that strips backticks
    # everywhere) is the silent-fidelity-loss footgun this split avoids.
    location = (
        f"`{_escape_codespan(finding.file)}:{finding.line}`"
        if finding.line is not None
        else f"`{_escape_codespan(finding.file)}`"
    )
    return (
        f"- **{_escape_inline(finding.id)}** {location} — "
        f"`{_escape_codespan(finding.rule)}` "
        f"({finding.severity.value}): {_escape_inline(finding.message)}"
    )


def _escape_cell(text: str) -> str:
    """Escape a string for safe inclusion in a markdown table cell.

    Order: backslash first (otherwise it corrupts the subsequent escape
    sequences), then pipe, then newline. Same escaping policy as the
    historical orchestrator's inline cell escape.
    """
    out = text.replace(*CELL_BACKSLASH)
    out = out.replace(*CELL_PIPE)
    out = out.replace(*CELL_NEWLINE)
    return out


def _escape_inline(text: str) -> str:
    """Escape a string for inline markdown context (prose, bold, emphasis).

    Replaces newlines with spaces so a multi-line value still renders on
    one row. Backticks are preserved verbatim — in ordinary inline
    context (a finding message, a bold span) a backtick opens a code
    span that the renderer matches against the next backtick in the
    string. The string ends at the bullet line's end, so an unmatched
    backtick degrades to a literal character in every common renderer.
    The fidelity-loss footgun is in code-span context (``_escape_codespan``),
    not here.

    Backslashes and pipes are left alone — they have no special inline
    meaning outside table cells.
    """
    return text.replace("\n", " ")


def _escape_codespan(text: str) -> str:
    """Escape a string for inclusion inside a backtick code span.

    CommonMark does **not** process backslash escapes inside backtick
    code spans — a value containing a backtick rendered as
    `` `{value}` `` would prematurely close the span no matter how the
    backtick is "escaped". This helper substitutes ``'`` for ``` ` ```
    so the surrounding span stays well-formed; the substitution is a
    deliberate fidelity trade for span correctness.

    Values containing literal backticks (rare in audit targets) lose
    the backtick character on the way through. Newlines are still
    replaced with spaces so a multi-line value does not break the row
    layout.
    """
    return text.replace("\n", " ").replace("`", "'")


def _read_input(path: str | None) -> str:
    if path is None or path == "-":
        return sys.stdin.read()
    return Path(path).read_text(encoding="utf-8")


def _write_output(path: str | None, content: str) -> None:
    if path is None or path == "-":
        sys.stdout.write(content)
        return
    Path(path).write_text(content, encoding="utf-8")


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="emit_verdict",
        description=(
            "Emit an audit verdict in markdown, markdown+JSON, or JSON-only "
            "form. Reads JSON from stdin (or --file) and writes the surface "
            "form to stdout (or --output)."
        ),
    )
    parser.add_argument(
        "--format",
        choices=FORMAT_CHOICES,
        default=FORMAT_MARKDOWN_JSON,
        help="Output surface form. Default: markdown+json (PR-comment delivery).",
    )
    parser.add_argument(
        "--file",
        default=None,
        help="Input file path. Use '-' or omit to read from stdin.",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output file path. Use '-' or omit to write to stdout.",
    )
    return parser.parse_args(argv)


if __name__ == "__main__":
    sys.exit(main())
