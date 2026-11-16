"""Evidence harness for JSON-first eval reports.

Exposes the report fixture, the embedded-payload reader, and JSON file readers;
every verdict lives in the linked tests.
"""

from __future__ import annotations

import json
from html.parser import HTMLParser
from pathlib import Path
from typing import cast

from outcomeeng_evals.report import (
    EMBEDDED_RESULTS_SCRIPT_ID,
    EMBEDDED_RESULTS_SCRIPT_TYPE,
)
from outcomeeng_testing.evals.factories import ReportFixture, load_report_fixture

_FIXTURE_PATH = Path(__file__).parents[1] / "fixtures/evals/report_suite.json"


class ReportHarnessError(RuntimeError):
    """A report artifact the harness read had an unusable shape."""


class _EmbeddedResultsParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._inside_results = False
        self.payload_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        self._inside_results = (
            tag == "script"
            and attributes.get("id") == EMBEDDED_RESULTS_SCRIPT_ID
            and attributes.get("type") == EMBEDDED_RESULTS_SCRIPT_TYPE
        )

    def handle_endtag(self, tag: str) -> None:
        if tag == "script":
            self._inside_results = False

    def handle_data(self, data: str) -> None:
        if self._inside_results:
            self.payload_parts.append(data)


def read_json_object(path: Path) -> dict[str, object]:
    """Read one JSON object from a report file."""

    with path.open(encoding="utf-8") as report_file:
        payload: object = json.load(report_file)
    if not isinstance(payload, dict):
        raise ReportHarnessError(f"{path} does not hold a JSON object")
    return cast(dict[str, object], payload)


def embedded_payload(path: Path) -> dict[str, object]:
    """Read the JSON payload embedded in a rendered HTML report."""

    parser = _EmbeddedResultsParser()
    with path.open(encoding="utf-8") as html_file:
        parser.feed(html_file.read())
    payload: object = json.loads("".join(parser.payload_parts))
    if not isinstance(payload, dict):
        raise ReportHarnessError(f"{path} embeds no JSON object")
    return cast(dict[str, object], payload)


def report_fixture() -> ReportFixture:
    """Load the captured report fixture."""

    return load_report_fixture(_FIXTURE_PATH)
