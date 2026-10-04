from pathlib import Path

from outcomeeng_testing.generators.position_direction import invalid_intervals
from outcomeeng_testing.harnesses.position_direction import (
    INVALID_INTERVALS,
    MONITOR_SCRIPT,
    ROSTER_SCRIPT,
    VALID_WATCH_FIXTURE,
    check_examples,
    copy_into,
    invocation,
    run_script,
    scratch_dir,
    state_fixture,
    state_fixture_defect,
    violating_watch_fixtures,
    watch_fixture,
    watch_fixture_defect,
)


def test_a_watch_file_that_violates_the_contract_is_rejected_naming_the_defect() -> (
    None
):
    names = violating_watch_fixtures()
    assert names, "no violating watch fixture exists"
    with scratch_dir() as directory:
        for script in (ROSTER_SCRIPT, MONITOR_SCRIPT):
            for name in names:
                state = Path(directory) / "state.json"
                completed = run_script(
                    script, invocation(script, watch_fixture(name), state)
                )
                defect = watch_fixture_defect(name)
                assert completed.returncode != 0, f"{script} accepted {name}"
                assert defect in completed.stderr, (
                    f"{script} on {name} did not name {defect!r}: {completed.stderr!r}"
                )
                assert not state.exists(), f"{script} wrote state for {name}"


def test_a_missing_watch_file_is_rejected_naming_its_path() -> None:
    with scratch_dir() as directory:
        missing = Path(directory) / "absent" / "watch.json"
        state = Path(directory) / "state.json"
        for script in (ROSTER_SCRIPT, MONITOR_SCRIPT):
            completed = run_script(script, invocation(script, missing, state))
            assert completed.returncode != 0
            assert str(missing) in completed.stderr


def test_a_malformed_state_file_is_rejected_naming_the_defect() -> None:
    with scratch_dir() as directory:
        state = copy_into(Path(directory), state_fixture("not-json"))
        completed = run_script(
            MONITOR_SCRIPT, invocation(MONITOR_SCRIPT, VALID_WATCH_FIXTURE, state)
        )
        assert completed.returncode != 0
        assert state_fixture_defect("not-json") in completed.stderr


def test_an_argument_list_that_departs_from_the_usage_is_rejected() -> None:
    with scratch_dir() as directory:
        state = Path(directory) / "state.json"
        valid = {
            ROSTER_SCRIPT: invocation(ROSTER_SCRIPT, VALID_WATCH_FIXTURE, state),
            MONITOR_SCRIPT: invocation(MONITOR_SCRIPT, VALID_WATCH_FIXTURE, state),
        }
        for script, arguments in valid.items():
            missing_one = arguments[:-1]
            one_extra = [*arguments, VALID_WATCH_FIXTURE]
            unknown_option = [*arguments, "--no-such-option"]
            for departing in (missing_one, one_extra, unknown_option):
                completed = run_script(script, departing)
                assert completed.returncode != 0, f"{script} accepted {departing}"
                assert completed.stderr.strip() != "", f"{script} named no defect"


def test_an_interval_that_is_not_a_positive_finite_number_is_rejected() -> None:
    with scratch_dir() as directory:
        state = Path(directory) / "state.json"

        def rejected(interval: str) -> None:
            completed = run_script(
                MONITOR_SCRIPT,
                [
                    *invocation(MONITOR_SCRIPT, VALID_WATCH_FIXTURE, state),
                    "--every",
                    interval,
                ],
            )
            assert completed.returncode != 0, f"accepted --every {interval}"
            assert "--every" in completed.stderr

        check_examples(invalid_intervals(), rejected, INVALID_INTERVALS)


def test_a_watch_file_that_keeps_the_contract_is_accepted() -> None:
    with scratch_dir() as directory:
        state = Path(directory) / "state.json"
        for script in (ROSTER_SCRIPT, MONITOR_SCRIPT):
            completed = run_script(
                script, invocation(script, VALID_WATCH_FIXTURE, state)
            )
            assert completed.returncode == 0, completed.stderr
