"""Record rows a declared agent switch skipped, for the gate's run summary.

A pytest plugin registered through the repository's pytest configuration. It
writes one record per declared skip to the file the orchestrator names in the
environment, and writes nothing when that variable is absent or when a skip
names no switch. It owns no predicate: the gate's linked tests decide what the
recorded entries mean.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from outcomeeng.validation.agent_disable import (
    SKIP_REPORT_ENV,
    SKIP_REPORT_SWITCH_FIELD,
    SKIP_REPORT_TEST_FIELD,
    declared_switch,
)


def pytest_runtest_logreport(report: pytest.TestReport) -> None:
    """Append one record for a row a declared switch skipped."""
    destination = os.environ.get(SKIP_REPORT_ENV)
    if destination is None or not report.skipped:
        return
    switch = declared_switch(report.longreprtext)
    if switch is None:
        return
    record = {
        SKIP_REPORT_TEST_FIELD: report.nodeid,
        SKIP_REPORT_SWITCH_FIELD: switch,
    }
    with Path(destination).open("a", encoding="utf-8") as handle:
        handle.write(f"{json.dumps(record, sort_keys=True)}\n")
