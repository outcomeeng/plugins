"""The skip-report channel between a gate step's pytest child and its summary.

One channel, one home: the option the orchestrator names in the step's argv,
the configuration name it is stored under, the two fields of each recorded
line, the naming of the file those lines are written to, the status a recorded
row carries in the summary, and the line the run prints for it. Splitting these
across the modules at either end leaves the channel with no module that states
it as its subject, so a reader of either end sees half a contract.

Both ends of the channel are here: the names the orchestrator reads when it
puts the destination in a step's argv and prints each recorded row, and the
pytest plugin that writes the records into it.

The plugin is registered through the repository's pytest configuration. The
orchestrator names the destination in the step's own argv, so it reaches the
recorder through pytest's configuration and is constructor-injected into the
object that records; nothing reads process state. One record is written per
declared skip, and none when the option is absent or when a skip carries no
switch's own declared reason. The recorder owns no predicate: the gate's linked
tests decide what the recorded entries mean.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Final

from outcomeeng.validation.agent_disable import declared_switch

if TYPE_CHECKING:
    import pytest

SKIP_REPORT_OPTION: Final = "--oe-skip-report"
"""The pytest option naming the file a step's declared skips are recorded in."""
SKIP_REPORT_DEST: Final = "oe_skip_report"
"""The pytest configuration name that option is stored under."""
SKIP_REPORT_TEST_FIELD: Final = "test"
"""The recorded field naming the row a switch declared optional."""
SKIP_REPORT_SWITCH_FIELD: Final = "switch"
"""The recorded field naming the switch that declared the skip."""
SKIP_REPORT_FILE_PREFIX: Final = "outcomeeng-validation-skips-"
"""The prefix of the per-step file the recorded lines are written to."""
SKIP_REPORT_FILE_SUFFIX: Final = ".jsonl"
"""The suffix of that file, naming the one-record-per-line shape it carries."""
STEP_SKIP_STATUS: Final = "SKIP"
"""The status a recorded row carries, distinct from its step's own status."""
SKIP_LINE_FORM: Final = "{status}  {test}  {switch}"
"""The line a run prints per recorded row, after its step's status line."""


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
