"""Bounded transcript behavior evidence and portable local report artifacts."""

from __future__ import annotations


import csv
import hashlib
import html
import io
import json
import os
import tempfile
from collections import Counter
from decimal import Decimal
from enum import StrEnum
from pathlib import Path

from usage_accounting import AccountingField
from usage_accounting import (
    EXCERPT_CHARS,
    TOKEN_KEYS,
    Evidence,
    Json,
    encoded,
    timestamp,
)

MAX_SCREEN_ROWS = 20_000
MAX_EXAMPLES = 20
MAX_RANKED = 50
MAX_REPORTS = 96
REPORT_DIRECTORY = "reports"
ALERT_DIRECTORY = "alerts"
RETENTION_NAME = "retention-status.json"
REPORT_NAME = "report.html"
MEASUREMENT_NAME = "measurements.json"
CSV_NAME = "sessions.csv"
EVIDENCE_NAME = "evidence.html"
STYLE = """:root{color-scheme:light;--paper:#f5f0e5;--ink:#20302c;--accent:#99421f;--line:#c9c4b7}
*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font:17px Baskerville,Georgia,serif}
main{max-width:1200px;margin:auto;padding:36px 28px}header{border-top:8px solid var(--ink);padding-top:18px}
h1{font-size:clamp(34px,6vw,68px);line-height:1.05;margin:12px 0 20px;font-weight:500;letter-spacing:-1px}
h2{font-size:25px;margin:24px 0 12px}p{line-height:1.5}a{color:var(--accent)}a:focus-visible,summary:focus-visible{outline:3px solid var(--accent);outline-offset:4px}
.window,.number,table,pre{font:13px Menlo,Consolas,monospace}.window{overflow-wrap:anywhere}
.metrics{display:flex;flex-wrap:wrap;border-block:1px solid var(--line);margin:24px 0}.metric{flex:1 1 180px;padding:18px 14px;border-right:1px solid var(--line)}
.metric:first-child{flex-basis:260px;background:var(--ink);color:var(--paper)}.metric strong{display:block;font:30px Menlo,Consolas,monospace;margin-top:8px}
details{border-top:1px solid var(--line);padding:16px 0}summary{cursor:pointer;font-size:23px}summary:hover{color:var(--accent)}
.scroll{overflow-x:auto}table{border-collapse:collapse;width:100%;margin:16px 0}th,td{text-align:left;vertical-align:top;border-bottom:1px solid var(--line);padding:10px 8px}th{white-space:nowrap}
td:first-child{max-width:260px;overflow-wrap:anywhere}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#e7e2d7;padding:16px}
.badge{display:inline-block;padding:4px 8px;border:1px solid var(--accent);color:var(--accent);font:12px Menlo,Consolas,monospace}
.bar{height:7px;background:var(--ink);margin-top:7px}.evidence{scroll-margin-top:20px;border-top:2px solid var(--ink);padding-top:12px;margin-top:28px}
@media(max-width:600px){main{padding:20px 14px}.metric{border-right:0}table{font-size:11px}}
@media(prefers-reduced-motion:no-preference){details[open]>div{animation:appear .15s ease-out}@keyframes appear{from{opacity:0;transform:translateY(3px)}to{opacity:1;transform:none}}}
"""


class ReportSection(StrEnum):
    CONSUMPTION = "Consumption breakdown"
    CONTEXT = "Context growth"
    CACHE = "Cache analysis"
    USEFUL_WORK = "Waste and useful work"


UNKNOWN_OUTPUT = "Delivered output and usefulness remain unknown until independent store, merge or pinned verification evidence establishes them."


class ReportField(StrEnum):
    """Wire fields consumed by the module's public evidence contract."""

    MEASUREMENT = "measurement"
    MODEL_INVOCATIONS = "model_invocations"
    REFERENCES = "references"
    REPORT_GAPS = "report_gaps"


class NumberFormat(StrEnum):
    """Public numeric presentation policy for frozen report measurements."""

    SUMMARY_COST = ",.2f"
    COST = ".4f"
    REQUEST_COST = ".5f"
    COUNT = ","
    CONTEXT = ",.0f"
    SHARE = ".1%"
    GROWTH = ".2f"


NUMBER_PREFIXES = {
    NumberFormat.SUMMARY_COST: "$",
    NumberFormat.COST: "$",
    NumberFormat.REQUEST_COST: "$",
}
NUMBER_SUFFIXES = {NumberFormat.GROWTH: "×"}
UNKNOWN_NUMBER = "unknown"


def display_number(value: int | float | Decimal | None, style: NumberFormat) -> str:
    if value is None:
        return UNKNOWN_NUMBER
    return (
        NUMBER_PREFIXES.get(style, "")
        + format(value, style)
        + NUMBER_SUFFIXES.get(style, "")
    )


def atomic_write(path: Path, content: str | bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            dir=path.parent, prefix=".usage-", delete=False
        ) as stream:
            temporary = Path(stream.name)
            stream.write(content.encode() if isinstance(content, str) else content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def json_write(path: Path, value: object) -> None:
    atomic_write(path, json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def behavior(evidence: Evidence, measurement: Json) -> Json:
    rows = evidence.db.execute(
        "SELECT * FROM behavior WHERE stamp>=? AND stamp<? ORDER BY stamp,identity LIMIT ?",
        (
            measurement[AccountingField.START_UTC],
            measurement[AccountingField.END_EXCLUSIVE_UTC],
            MAX_SCREEN_ROWS + 1,
        ),
    ).fetchall()
    bounded = len(rows) > MAX_SCREEN_ROWS
    tools: Counter[str] = Counter()
    skills: Counter[str] = Counter()
    paths: Counter[str] = Counter()
    commands: Counter[str] = Counter()
    repeats: Counter[tuple[str, str]] = Counter()
    first_repeat: dict[tuple[str, str], Json] = {}
    examples: list[Json] = []
    characters = errors = launches = 0
    results = user_turns = 0
    for row in rows[:MAX_SCREEN_ROWS]:
        if row[AccountingField.KIND] == "user_turn":
            user_turns += 1
            continue
        item = json.loads(row["payload"])
        item["reference"] = (
            "e"
            + hashlib.sha256(row[AccountingField.IDENTITY].encode()).hexdigest()[:24]
        )
        if row[AccountingField.KIND] == "tool_use":
            name = row["tool"]
            tools[name] += 1
            launches += name.lower() in ("agent", "task")
            arguments = item.get("arguments")
            if isinstance(arguments, dict):
                if name.lower() == "skill":
                    skills[str(arguments.get("skill") or "unknown")] += 1
                for argument_key in ("file_path", "path", "pattern"):
                    if arguments.get(argument_key):
                        paths[str(arguments[argument_key])] += 1
                command = arguments.get("command") or arguments.get("cmd")
                if isinstance(command, str):
                    commands[command[:EXCERPT_CHARS]] += 1
            repeat_key = (row["session"], row["signature"])
            repeats[repeat_key] += 1
            first_repeat.setdefault(repeat_key, item)
        else:
            results += 1
            characters += row["characters"]
            errors += row["error"]
            examples.append(item)
            examples.sort(key=lambda value: value["characters"], reverse=True)
            del examples[MAX_EXAMPLES:]
    repeated = []
    for repeat_key, count in repeats.most_common(MAX_EXAMPLES):
        if count > 1:
            item = dict(first_repeat[repeat_key])
            item.update(
                {
                    "count": count,
                    "classification": "Repeated arguments; necessity remains unknown.",
                }
            )
            repeated.append(item)
    references = {item["reference"]: item for item in examples + repeated}
    return {
        "tool_calls": sum(tools.values()),
        "user_text_turns": user_turns,
        "tools": dict(tools.most_common(MAX_RANKED)),
        "skills": dict(skills.most_common(MAX_RANKED)),
        "mcp_tools": {
            key: count for key, count in tools.items() if key.startswith("mcp__")
        },
        "agent_launches": launches,
        "native_child_requests": measurement[AccountingField.CHILD_REQUESTS],
        "read_or_search_operands": dict(paths.most_common(MAX_RANKED)),
        "shell_commands": dict(commands.most_common(MAX_RANKED)),
        "tool_results": results,
        "tool_result_characters": characters,
        "explicit_tool_errors": errors,
        "large_results": examples,
        "repeated_calls": repeated,
        ReportField.REFERENCES: references,
        AccountingField.GAPS: (
            ["Behavior query bound reached; counts are partial."] if bounded else []
        )
        + [
            "Character counts measure serialized tool-result content; they are not token or request-cost attribution.",
            "Repeated arguments can be required after a subject changes; repetition alone establishes no waste.",
            "Native child paths establish relationships; launch counts and session counts measure different events.",
            "Unrecorded skill/plugin calls, shell file reads, retries and abandoned work remain unknown.",
        ],
    }


def escape(value: object) -> str:
    return html.escape(str(value))


def table(headers: tuple[str, ...], rows: list[list[object]]) -> str:
    return (
        '<div class="scroll"><table><thead><tr>'
        + "".join(f"<th>{escape(v)}</th>" for v in headers)
        + "</tr></thead><tbody>"
        + "".join(
            "<tr>" + "".join(f"<td>{escape(v)}</td>" for v in row) + "</tr>"
            for row in rows
        )
        + "</tbody></table></div>"
    )


def page(title: str, content: str) -> str:
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>'
        + escape(title)
        + "</title><style>"
        + STYLE
        + "</style></head><body><main>"
        + content
        + "</main></body></html>"
    )


def detail(title: str, content: str, opened: bool = False) -> str:
    return (
        "<details"
        + (" open" if opened else "")
        + "><summary>"
        + escape(title)
        + "</summary><div>"
        + content
        + "</div></details>"
    )


def csv_sessions(measurement: Json) -> str:
    output = io.StringIO(newline="")
    keys = (
        "session",
        "first_utc",
        "last_utc",
        "model",
        "parent",
        "child",
        "requests",
        *TOKEN_KEYS,
        "api_equivalent_usd",
        "share_measured_cost",
        "early_context_mean",
        "late_context_mean",
        "context_growth_ratio",
    )
    writer = csv.writer(output)
    writer.writerow(keys)
    for session, group in measurement[AccountingField.SESSIONS].items():
        writer.writerow(
            [session if key == "session" else group.get(key) for key in keys]
        )
    return output.getvalue()


def render(measurement: Json, screening: Json, previous: Json | None) -> str:
    total = measurement[AccountingField.API_EQUIVALENT_USD]
    components = sorted(
        measurement["cost_components"].items(), key=lambda item: item[1], reverse=True
    )
    ranked = sorted(
        measurement[AccountingField.SESSIONS].items(),
        key=lambda item: item[1][AccountingField.API_EQUIVALENT_USD],
        reverse=True,
    )
    dashboard = (
        '<header><span class="badge">LOCAL USAGE EVIDENCE</span><h1>Consumption control</h1><p class="window">'
        + escape(measurement[AccountingField.START_UTC])
        + " → "
        + escape(measurement[AccountingField.END_EXCLUSIVE_UTC])
        + ' · UTC · end exclusive</p><p><a href="measurements.json">Read JSON</a> · <a href="sessions.csv">Read CSV</a> · <a href="evidence.html">Inspect transcripts</a></p></header>'
    )
    dashboard += (
        '<div class="metrics">'
        + "".join(
            '<div class="metric">'
            + escape(label)
            + "<strong>"
            + escape(value)
            + "</strong></div>"
            for label, value in (
                (
                    "API-equivalent estimate",
                    display_number(total, NumberFormat.SUMMARY_COST),
                ),
                (
                    "LLM requests",
                    display_number(
                        measurement[AccountingField.REQUESTS], NumberFormat.COUNT
                    ),
                ),
                (
                    "Native child requests",
                    display_number(
                        measurement[AccountingField.CHILD_REQUESTS], NumberFormat.COUNT
                    ),
                ),
                ("Coverage gaps", len(measurement[AccountingField.GAPS])),
            )
        )
        + "</div>"
    )
    conclusion = (
        "<ul>"
        + "".join(
            f"<li>{escape(key.replace('_', ' ').capitalize())}: ${amount:,.2f}, {amount / total:.1%} of measured cost.</li>"
            for key, amount in components[:3]
            if total
        )
        + "</ul>"
    )
    conclusion += "<p>These values explain measured API-equivalent consumption. The subscription allowance has no established conversion from these amounts.</p>"
    if previous:
        conclusion += f"<p>Previous interval: ${previous[AccountingField.API_EQUIVALENT_USD]:,.2f} across {previous[AccountingField.REQUESTS]:,} requests; compare coverage before interpreting the change.</p>"
    dashboard += detail("Executive conclusion", conclusion, True)
    dashboard += detail(
        ReportSection.CONSUMPTION,
        table(
            (
                "Session",
                "Start UTC",
                "Observed span (s)",
                "Model",
                "Requests",
                "Input",
                "Cache read",
                "Cache write",
                "Output",
                "Estimate",
                "Share",
            ),
            [
                [
                    session,
                    g["first_utc"],
                    g["duration_seconds"],
                    g[AccountingField.MODEL],
                    g[AccountingField.REQUESTS],
                    *[g[k] for k in TOKEN_KEYS],
                    display_number(
                        g[AccountingField.API_EQUIVALENT_USD], NumberFormat.COST
                    ),
                    display_number(
                        g[AccountingField.SHARE_MEASURED_COST], NumberFormat.SHARE
                    ),
                ]
                for session, g in ranked[:MAX_RANKED]
            ],
        )
        + table(
            ("Model", "Requests", "API-equivalent estimate", "Share"),
            [
                [
                    name,
                    value[AccountingField.REQUESTS],
                    display_number(
                        value[AccountingField.API_EQUIVALENT_USD], NumberFormat.COST
                    ),
                    display_number(
                        value[AccountingField.SHARE_MEASURED_COST], NumberFormat.SHARE
                    ),
                ]
                for name, value in sorted(
                    measurement[AccountingField.MODELS].items(),
                    key=lambda pair: pair[1][AccountingField.API_EQUIVALENT_USD],
                    reverse=True,
                )[:MAX_RANKED]
            ],
        )
        + table(
            ("Workspace", "Requests", "API-equivalent estimate"),
            [
                [
                    name,
                    value[AccountingField.REQUESTS],
                    display_number(
                        value[AccountingField.API_EQUIVALENT_USD], NumberFormat.COST
                    ),
                ]
                for name, value in sorted(
                    measurement[AccountingField.WORKSPACES].items(),
                    key=lambda pair: pair[1][AccountingField.API_EQUIVALENT_USD],
                    reverse=True,
                )[:MAX_RANKED]
            ],
        ),
        True,
    )
    dashboard += detail(
        "Top causes",
        table(
            ("Measured component", "Estimate", "Contribution"),
            [
                [
                    key,
                    display_number(amount, NumberFormat.COST),
                    display_number(
                        amount / total if total else None, NumberFormat.SHARE
                    ),
                ]
                for key, amount in components
            ],
        )
        + "<p>Component shares establish accounting contribution. Exact attribution to a tool, skill, or plugin remains unknown.</p>",
    )
    dashboard += detail(
        ReportSection.CONTEXT,
        table(
            (
                "Session",
                "Early input",
                "Late input",
                "Growth",
                "Early request cost",
                "Late request cost",
            ),
            [
                [
                    session,
                    display_number(
                        g[AccountingField.EARLY_CONTEXT_MEAN], NumberFormat.CONTEXT
                    ),
                    display_number(
                        g[AccountingField.LATE_CONTEXT_MEAN], NumberFormat.CONTEXT
                    ),
                    display_number(
                        g[AccountingField.CONTEXT_GROWTH_RATIO], NumberFormat.GROWTH
                    ),
                    display_number(
                        g[AccountingField.EARLY_COST_MEAN], NumberFormat.REQUEST_COST
                    ),
                    display_number(
                        g[AccountingField.LATE_COST_MEAN], NumberFormat.REQUEST_COST
                    ),
                ]
                for session, g in ranked[:MAX_RANKED]
            ],
        )
        + "<p>Samples use up to ten requests from each end, capped at one quarter of session requests. Input includes uncached input, cache reads and cache writes. Unpriced requests weaken cost comparisons.</p>",
    )
    dashboard += detail(
        ReportSection.CACHE,
        table(
            ("Usage field", "Tokens", "Estimated component"),
            [
                [
                    key,
                    measurement[key],
                    display_number(
                        measurement[AccountingField.COST_COMPONENTS][key],
                        NumberFormat.COST,
                    ),
                ]
                for key in TOKEN_KEYS
            ],
        )
        + f"<p>Cache-read share of measured input: {escape(display_number(measurement[AccountingField.CACHE_READ_SHARE], NumberFormat.SHARE))}. Cache-write duration assumptions: {measurement['pricing_assumption_requests']:,} requests.</p>",
    )
    links = (
        "<ul>"
        + "".join(
            '<li><a href="evidence.html#'
            + escape(item["reference"])
            + '">Inspect '
            + escape(item.get("tool") or "tool result")
            + "</a>: "
            + escape(item.get("count") or item["characters"])
            + (" repeats" if "count" in item else " characters")
            + "</li>"
            for item in screening["large_results"][:5] + screening["repeated_calls"][:5]
        )
        + "</ul>"
    )
    dashboard += detail(
        "Agent and tool activity",
        f"<p>{screening['user_text_turns']:,} recorded user text turns; {screening['tool_calls']:,} tool calls; {screening['agent_launches']:,} launch calls; {screening['explicit_tool_errors']:,} explicit tool errors.</p>"
        + links
        + table(
            ("Tool", "Calls"),
            [[key, value] for key, value in screening["tools"].items()],
        )
        + "<pre>"
        + escape(
            json.dumps(
                {
                    key: screening[key]
                    for key in (
                        "skills",
                        "mcp_tools",
                        "read_or_search_operands",
                        "shell_commands",
                    )
                },
                indent=2,
            )
        )
        + "</pre>",
    )
    dashboard += detail(
        ReportSection.USEFUL_WORK,
        "<p>Measured work includes processing context, creating cache entries and producing output. Repeated calls are inspection candidates; their necessity is unverified. "
        + UNKNOWN_OUTPUT
        + "</p>",
    )
    dashboard += detail(
        "Highest-leverage checks",
        "<ol><li>Inspect the highest-cost sessions and their early-versus-late context before changing session boundaries.</li><li>Inspect repeated calls and their transcript subjects before removing required checks.</li><li>Compare cache creation and model shares across equally covered windows before changing execution choices.</li></ol><p>Expected subscription savings remain unknown. Preserve required gates and resource ceilings.</p>",
    )
    dashboard += detail(
        "Missing evidence",
        "<pre>"
        + escape(
            json.dumps(
                measurement[AccountingField.GAPS] + screening[AccountingField.GAPS],
                indent=2,
            )
        )
        + '</pre><p>Local transcript coverage does not establish account-wide completeness, subscription-quota conversion, or exact retained-context content. Pricing source: <a href="'
        + escape(measurement["pricing"]["source"])
        + '">Read pricing</a>.</p>',
        bool(measurement[AccountingField.GAPS]),
    )
    return page("Consumption control", dashboard)


def write_report(
    root: Path, measurement: Json, screening: Json, previous: Json | None = None
) -> Path:
    identity = hashlib.sha256(
        encoded(
            {
                ReportField.MEASUREMENT: measurement,
                "screening": screening,
                "previous": previous,
            }
        ).encode()
    ).hexdigest()
    directory = root / REPORT_DIRECTORY / identity
    envelope = {
        "schema_version": 1,
        ReportField.MEASUREMENT: measurement,
        "previous": previous,
        "behavior": screening,
        "artifact_identity": identity,
        ReportField.MODEL_INVOCATIONS: 0,
    }
    json_write(directory / MEASUREMENT_NAME, envelope)
    atomic_write(directory / CSV_NAME, csv_sessions(measurement))
    evidence_body = '<header><h1>Transcript evidence</h1><p><a href="report.html">Read report</a></p></header>'
    for reference, item in screening[ReportField.REFERENCES].items():
        source = Path(item["source"])
        evidence_body += (
            '<section class="evidence" id="'
            + escape(reference)
            + '"><h2>'
            + escape(item.get("tool") or "Tool result")
            + '</h2><p class="window">'
            + escape(item["stamp"])
            + " · "
            + escape(item["session"])
            + '</p><p><a href="'
            + escape(source.as_uri())
            + '">Open source</a> · UUID: '
            + escape(item[AccountingField.UUID])
            + "</p><pre>"
            + escape(item[AccountingField.EXCERPT])
            + "</pre><p>Excerpt truncated: "
            + escape(item["truncated"])
            + "</p></section>"
        )
    atomic_write(directory / EVIDENCE_NAME, page("Transcript evidence", evidence_body))
    atomic_write(directory / REPORT_NAME, render(measurement, screening, previous))
    json_write(
        root / "latest-report.json",
        {
            "artifact_identity": identity,
            "path": str(directory / REPORT_NAME),
            AccountingField.START_UTC: measurement[AccountingField.START_UTC],
            AccountingField.END_EXCLUSIVE_UTC: measurement[
                AccountingField.END_EXCLUSIVE_UTC
            ],
        },
    )
    json_write(
        root / RETENTION_NAME,
        {ReportField.REPORT_GAPS: retain_reports(root, directory)},
    )
    return directory / REPORT_NAME


def retain_reports(root: Path, current: Path) -> list[str]:
    reports = root / REPORT_DIRECTORY
    gaps: list[str] = []
    candidates: list[tuple[float, Path]] = []
    with os.scandir(reports) as entries:
        for index, entry in enumerate(entries):
            if index >= MAX_REPORTS * 4:
                gaps.append(
                    "report retention scan bound reached; additional directories remain uninspected"
                )
                break
            if entry.is_symlink() or not entry.is_dir(follow_symlinks=False):
                continue
            path = Path(entry.path)
            if len(entry.name) != 64 or any(
                character not in "0123456789abcdef" for character in entry.name
            ):
                continue
            candidates.append((entry.stat(follow_symlinks=False).st_mtime, path))
    candidates.sort(reverse=True)
    for _, path in candidates[MAX_REPORTS:]:
        if path == current:
            continue
        marker = path / MEASUREMENT_NAME
        try:
            if marker.is_symlink() or marker.stat().st_size > 16 * 1024 * 1024:
                continue
            value = json.loads(marker.read_text())
            if value.get("artifact_identity") != path.name:
                continue
            expected = (MEASUREMENT_NAME, CSV_NAME, EVIDENCE_NAME, REPORT_NAME)
            names: set[str] = set()
            with os.scandir(path) as children:
                for child in children:
                    names.add(child.name)
                    if len(names) > len(expected):
                        break
            if names != set(expected):
                gaps.append(f"report retention preserved unrecognized contents: {path}")
                continue
            if any((path / name).is_symlink() for name in expected):
                continue
            for name in expected:
                (path / name).unlink()
            path.rmdir()
        except (OSError, ValueError, AttributeError) as error:
            gaps.append(f"report retention failed: {path}: {error}")
    return gaps


def retain_alerts(root: Path, cutoff: str) -> list[str]:
    directory = root / ALERT_DIRECTORY
    if not directory.exists():
        return []
    if directory.is_symlink():
        raise ValueError(f"Managed alert directory is symlinked: {directory}")
    gaps: list[str] = []
    with os.scandir(directory) as entries:
        for index, entry in enumerate(entries):
            if index >= 4096:
                gaps.append(
                    "alert retention scan bound reached; additional entries remain uninspected"
                )
                break
            if (
                entry.is_symlink()
                or not entry.is_file(follow_symlinks=False)
                or len(entry.name) != 69
                or not entry.name.endswith(".json")
            ):
                continue
            identity = entry.name[:-5]
            if any(c not in "0123456789abcdef" for c in identity):
                continue
            path = Path(entry.path)
            try:
                if entry.stat(follow_symlinks=False).st_size > 16 * 1024 * 1024:
                    gaps.append(f"alert retention preserved oversized record: {path}")
                    continue
                value = json.loads(path.read_text())
                alert = value.get("signal") if isinstance(value, dict) else None
                if (
                    not isinstance(alert, dict)
                    or alert.get(AccountingField.IDENTITY) != identity
                ):
                    gaps.append(
                        f"alert retention preserved unrecognized record: {path}"
                    )
                    continue
                if timestamp(
                    str(alert.get(AccountingField.END_EXCLUSIVE_UTC))
                ) < timestamp(cutoff):
                    path.unlink()
            except (OSError, ValueError, AttributeError) as error:
                gaps.append(f"alert retention failed: {path}: {error}")
    return gaps
