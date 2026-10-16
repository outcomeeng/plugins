"""Every valid request ends with exactly one printed line."""

import json

from outcomeeng_testing.harnesses.event_wait import (
    WorldObservation,
    run_composed_worlds,
)


def test_every_valid_request_ends_by_printing_exactly_one_line_and_exiting() -> None:
    def check(observed: WorldObservation) -> None:
        we = observed.contracts.wait_event
        lines = observed.stdout.splitlines()
        assert observed.stdout.endswith("\n"), observed.stdout
        assert len(lines) == 1, observed.stdout
        line = json.loads(lines[0])
        assert isinstance(line, dict), observed.stdout
        form = line[we.KIND_FIELD]
        assert form in (we.LINE_EVENT, we.LINE_UNREADABLE, we.LINE_TIMEOUT), line
        assert (observed.exit_code == 0) == (
            form in (we.LINE_EVENT, we.LINE_TIMEOUT)
        ), line

    run_composed_worlds(check)
