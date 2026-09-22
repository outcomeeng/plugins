"""Record rows a declared agent switch skipped, for the gate's run summary.

A pytest plugin registered through the repository's pytest configuration. The
orchestrator names the destination in the step's own argv as a plugin option,
so the destination reaches the recorder through pytest's configuration and is
constructor-injected into the object that records; nothing reads process state.
One record is written per declared skip, and none when the option is absent or
when a skip carries no switch's own declared reason. The recorder owns no
predicate: the gate's linked tests decide what the recorded entries mean.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from outcomeeng.validation.agent_disable import declared_switch
from outcomeeng.validation.skip_report import (
    SKIP_REPORT_DEST,
    SKIP_REPORT_OPTION,
    SKIP_REPORT_SWITCH_FIELD,
    SKIP_REPORT_TEST_FIELD,
)


class DeclaredSkipRecorder:
    """Append one record per declared skip to the destination it was given."""

    def __init__(self, destination: Path) -> None:
        self._destination = destination

    def pytest_runtest_logreport(self, report: pytest.TestReport) -> None:
        """Record this row when a switch's own declared reason skipped it."""
        if not report.skipped:
            return
        switch = declared_switch(report.longreprtext)
        if switch is None:
            return
        record = {
            SKIP_REPORT_TEST_FIELD: report.nodeid,
            SKIP_REPORT_SWITCH_FIELD: switch,
        }
        with self._destination.open("a", encoding="utf-8") as handle:
            handle.write(f"{json.dumps(record, sort_keys=True)}\n")


def pytest_addoption(parser: pytest.Parser) -> None:
    """Declare the option the orchestrator names in the step's argv."""
    parser.addoption(
        SKIP_REPORT_OPTION,
        dest=SKIP_REPORT_DEST,
        default=None,
        help="File to record rows a declared agent switch skipped.",
    )


def pytest_configure(config: pytest.Config) -> None:
    """Register the recorder only when the run names a destination."""
    destination = config.getoption(SKIP_REPORT_DEST, default=None)
    if destination is None:
        return
    config.pluginmanager.register(DeclaredSkipRecorder(Path(str(destination))))
