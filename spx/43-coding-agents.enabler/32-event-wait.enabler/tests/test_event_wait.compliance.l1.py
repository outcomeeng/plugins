"""The wait rejects a request without a positive timeout before reading any source,
keeps no state, changes nothing, and never outlives its timeout."""

import json

from outcomeeng_testing.harnesses.event_wait import (
    DefectObservation,
    WorldObservation,
    real_quiet_run,
    run_composed_worlds,
    run_timeout_defects,
)


def test_request_without_a_positive_timeout_prints_the_invalid_line_before_any_read() -> (
    None
):
    def check(observed: DefectObservation) -> None:
        we = observed.contracts.wait_event
        run = observed.execution
        lines = run.stdout.splitlines()
        assert len(lines) == 1, run.stdout
        assert json.loads(lines[0])[we.KIND_FIELD] == we.LINE_INVALID
        assert run.exit_code != 0
        assert run.calls == ()
        assert run.clock.current == 0
        assert run.clock.sleeps == []

    run_timeout_defects(check)


def test_a_run_crosses_only_read_commands_and_leaves_no_file_or_state_change() -> None:
    def check(observed: WorldObservation) -> None:
        am = observed.contracts.agent_mail
        hm = observed.contracts.herdr
        reads = (
            tuple(am.PUBLIC_GIT_COMMON_DIR_COMMAND),
            am.PUBLIC_AM_COMMAND_PREFIXES[am.Operation.WAIT],
            hm.PUBLIC_HERDR_COMMAND_PREFIXES[hm.Operation.INVENTORY],
        )
        for call in observed.calls:
            assert any(call.argv[: len(read)] == read for read in reads), call.argv
        assert observed.workspace_after == []
        assert observed.state_after == observed.state_before

    run_composed_worlds(check)


def test_a_run_ends_within_its_timeout_and_bounds_every_command() -> None:
    def check(observed: WorldObservation) -> None:
        am = observed.contracts.agent_mail
        timeout = observed.case.timeout_seconds
        assert observed.clock.current <= timeout
        for call in observed.calls:
            if call.argv == tuple(am.PUBLIC_GIT_COMMON_DIR_COMMAND):
                continue
            assert call.bound is not None, call.argv
            assert call.started + call.bound <= timeout, call.argv

    run_composed_worlds(check)


def test_a_real_run_prints_one_line_at_its_timeout_and_leaves_no_process_or_file() -> (
    None
):
    observed = real_quiet_run()
    we = observed.contracts.wait_event
    lines = observed.stdout.splitlines()
    assert len(lines) == 1, observed.stdout
    line = json.loads(lines[0])
    assert line[we.KIND_FIELD] == we.LINE_TIMEOUT
    assert observed.return_code == 0
    assert observed.elapsed_seconds <= observed.timeout_seconds + observed.grace_seconds
    assert not observed.survivors
    assert observed.workspace_after == []
