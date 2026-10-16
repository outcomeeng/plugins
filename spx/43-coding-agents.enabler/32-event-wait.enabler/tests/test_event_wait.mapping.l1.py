"""Each source's capability result maps to one source-owned line form."""

import json
from typing import Any

from outcomeeng_testing.generators.event_wait import PaneReading, SpendReading
from outcomeeng_testing.harnesses.event_wait import (
    DefectObservation,
    WorldObservation,
    line_form_runs,
    run_non_object_documents,
    run_single_source_worlds,
    run_unknown_source_kinds,
)


def only_line(stdout: str) -> dict[str, Any]:
    lines = stdout.splitlines()
    assert len(lines) == 1, stdout
    line = json.loads(lines[0])
    assert isinstance(line, dict), stdout
    return line


def test_mail_wait_result_maps_to_an_event_a_timeout_or_an_unreadable_source() -> None:
    def check(observed: WorldObservation) -> None:
        we = observed.contracts.wait_event
        am = observed.contracts.agent_mail
        line = only_line(observed.stdout)
        oracle = observed.mail_oracle
        assert oracle is not None
        succeeded = oracle[am.STATUS_FIELD] == am.ExecutionStatus.SUCCEEDED
        outcome = oracle[am.DATA_FIELD][am.OUTCOME_FIELD] if succeeded else None
        if outcome == am.WaitOutcome.RECEIVED:
            record = oracle[am.DATA_FIELD][am.RECORD_FIELD]
            assert observed.exit_code == 0
            assert line[we.KIND_FIELD] == we.LINE_EVENT
            assert line[we.SOURCE_FIELD] == we.SOURCE_MAIL
            assert line[we.RECORD_FIELD] == {
                we.RECORD_ID_FIELD: record[am.RECORD_ID_FIELD],
                we.RECORD_SENDER_FIELD: record[am.SENDER_FIELD],
                we.RECORD_KIND_FIELD: str(record[am.KIND_FIELD]),
                we.RECORD_SUBJECT_FIELD: record[am.RECORD_SUBJECT_FIELD],
            }
        elif outcome == am.WaitOutcome.TIMEOUT:
            assert observed.exit_code == 0
            assert line[we.KIND_FIELD] == we.LINE_TIMEOUT
            assert line[we.TIMEOUT_FIELD] == observed.case.timeout_seconds
        else:
            [entry] = line[we.SOURCES_FIELD]
            assert observed.exit_code != 0
            assert line[we.KIND_FIELD] == we.LINE_UNREADABLE
            assert entry[we.SOURCE_FIELD] == we.SOURCE_MAIL
            assert entry[we.MAIL_AGENT_FIELD] == observed.case.agent
            assert entry[we.DETAIL_FIELD]

    run_single_source_worlds("mail", check)


def test_pane_source_maps_the_first_changed_session_or_an_unreadable_source() -> None:
    def check(observed: WorldObservation) -> None:
        c = observed.contracts
        we, hm = c.wait_event, c.herdr
        line = only_line(observed.stdout)
        reading = observed.case.pane
        oracle = observed.pane_oracle
        requested = observed.pane_requested
        if reading is PaneReading.FOREIGN_ENVIRONMENT:
            [entry] = line[we.SOURCES_FIELD]
            assert oracle is None
            assert observed.exit_code != 0
            assert line[we.KIND_FIELD] == we.LINE_UNREADABLE
            assert entry[we.SOURCE_FIELD] == we.SOURCE_PANE
            assert entry[we.PANE_ENVIRONMENT_FIELD] == c.foreign_environment
            assert c.foreign_environment in entry[we.DETAIL_FIELD]
            assert observed.calls == ()
            return
        assert oracle is not None
        if oracle[hm.STATUS_FIELD] != hm.ExecutionStatus.SUCCEEDED:
            [entry] = line[we.SOURCES_FIELD]
            assert observed.exit_code != 0
            assert line[we.KIND_FIELD] == we.LINE_UNREADABLE
            assert entry[we.SOURCE_FIELD] == we.SOURCE_PANE
            assert entry[we.DETAIL_FIELD]
            return
        agents = oracle[hm.AGENTS_FIELD]
        first_name = requested[0][0]
        named = [agent for agent in agents if agent.get(hm.NAME_FIELD) == first_name]
        if reading is PaneReading.ABSENT_SESSION:
            assert named == []
        if reading is PaneReading.AMBIGUOUS:
            assert len(named) > 1
        if reading is PaneReading.INCOMPLETE:
            assert named[0][hm.MISSING_FIELDS_FIELD]
        if reading is not PaneReading.INVENTORY:
            [entry] = line[we.SOURCES_FIELD]
            assert observed.exit_code != 0
            assert line[we.KIND_FIELD] == we.LINE_UNREADABLE
            assert entry[we.SOURCE_FIELD] == we.SOURCE_PANE
            assert entry[we.PANE_SESSION_FIELD] == first_name
            return
        projected = {
            agent[hm.NAME_FIELD]: str(agent[hm.AGENT_STATUS_FIELD]) for agent in agents
        }
        changed = [
            (name, handled) for name, handled in requested if projected[name] != handled
        ]
        assert observed.exit_code == 0
        if changed:
            name, handled = changed[0]
            assert line[we.KIND_FIELD] == we.LINE_EVENT
            assert line[we.SOURCE_FIELD] == we.SOURCE_PANE
            assert line[we.PANE_ENVIRONMENT_FIELD] == we.ENVIRONMENT_HERDR
            assert line[we.PANE_SESSION_FIELD] == name
            assert line[we.PANE_STATE_FIELD] == projected[name]
            assert line[we.PREVIOUS_STATE_FIELD] == handled
        else:
            assert line[we.KIND_FIELD] == we.LINE_TIMEOUT

    run_single_source_worlds("pane", check)


def test_spend_source_maps_the_first_recorded_alert_or_an_unreadable_state_root() -> (
    None
):
    def check(observed: WorldObservation) -> None:
        c = observed.contracts
        we, accounting = c.wait_event, c.accounting
        line = only_line(observed.stdout)
        oracle = observed.spend_oracle
        cutoff = observed.spend_cutoff
        assert oracle is not None
        assert cutoff is not None
        if observed.case.spend is SpendReading.RECORDED:
            later = sorted(
                (record for record in observed.spend_stored if record[1] > cutoff),
                key=lambda record: (record[1], record[0]),
            )
            assert observed.exit_code == 0
            if later:
                identity, _, stamp, signal = later[0]
                assert line[we.KIND_FIELD] == we.LINE_EVENT
                assert line[we.SOURCE_FIELD] == we.SOURCE_SPEND
                assert line[we.IDENTITY_FIELD] == identity
                assert line[we.RECORDED_UTC_FIELD] == stamp
                assert line[we.SIGNAL_FIELD] == signal
            else:
                assert line[we.KIND_FIELD] == we.LINE_TIMEOUT
            return
        [source] = observed.request[we.SOURCES_FIELD]
        [entry] = line[we.SOURCES_FIELD]
        assert oracle["status"] == accounting.AlertReadStatus.UNREADABLE
        assert observed.exit_code != 0
        assert line[we.KIND_FIELD] == we.LINE_UNREADABLE
        assert entry[we.SOURCE_FIELD] == we.SOURCE_SPEND
        assert entry[we.SPEND_ROOT_FIELD] == source[we.SPEND_ROOT_FIELD]
        assert entry[we.DETAIL_FIELD]

    run_single_source_worlds("spend", check)


def test_clock_source_maps_its_arrival_before_the_timeout_to_a_clock_event() -> None:
    def check(observed: WorldObservation) -> None:
        we = observed.contracts.wait_event
        line = only_line(observed.stdout)
        offset = observed.case.clock_offset
        assert offset is not None
        [source] = observed.request[we.SOURCES_FIELD]
        assert observed.exit_code == 0
        assert offset < observed.case.timeout_seconds
        assert line[we.KIND_FIELD] == we.LINE_EVENT
        assert line[we.SOURCE_FIELD] == we.SOURCE_CLOCK
        assert line[we.CLOCK_AT_FIELD] == source[we.CLOCK_AT_FIELD]
        assert observed.clock.current == offset

    run_single_source_worlds("clock", check)


def test_an_unknown_source_kind_maps_to_the_invalid_request_line() -> None:
    def check(observed: DefectObservation, kind: str) -> None:
        we = observed.contracts.wait_event
        run = observed.execution
        line = only_line(run.stdout)
        assert line[we.KIND_FIELD] == we.LINE_INVALID
        assert run.exit_code != 0
        assert run.calls == ()

    run_unknown_source_kinds(check)


def test_a_document_that_is_not_one_json_object_maps_to_the_invalid_request_line() -> (
    None
):
    def check(observed: DefectObservation, text: str) -> None:
        we = observed.contracts.wait_event
        run = observed.execution
        line = only_line(run.stdout)
        assert line[we.KIND_FIELD] == we.LINE_INVALID
        assert run.exit_code != 0
        assert run.calls == ()

    run_non_object_documents(check)


def test_each_line_form_is_one_json_object_on_one_line_with_its_own_kind_and_exit() -> (
    None
):
    observed = line_form_runs()
    we = observed.contracts.wait_event
    zero_exit = (we.LINE_EVENT, we.LINE_TIMEOUT)

    assert len(observed.executions) == 4
    for form, run in observed.executions.items():
        assert only_line(run.stdout)[we.KIND_FIELD] == form
        assert (run.exit_code == 0) == (form in zero_exit), form
