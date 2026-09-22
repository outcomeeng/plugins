"""The skip-report channel between a gate step's pytest child and its summary.

One channel, one home: the option the orchestrator names in the step's argv,
the configuration name it is stored under, the two fields of each recorded
line, the naming of the file those lines are written to, the status a recorded
row carries in the summary, and the line the run prints for it. Splitting these
across the modules at either end leaves the channel with no module that states
it as its subject, so a reader of either end sees half a contract.

Both ends of the channel read these names from here: the orchestrator that
names the destination in a step's argv and prints each recorded row, and the
pytest plugin that writes the records. The plugin itself still lives in the
test-infrastructure package, which is a placement its own node's note carries.
"""

from __future__ import annotations

from typing import Final

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
