from outcomeeng_testing.generators.position_direction import loop_counts
from outcomeeng_testing.harnesses.position_direction import (
    LOOP_RACES,
    check_examples,
    load_scripts,
    race_loops,
    take_over_killed_holder,
    take_over_stale_lock,
)

duplicate_signal = str(load_scripts().monitor.Signal.WATCH_DUPLICATE)


def test_loops_started_together_on_one_state_file_leave_one_running() -> None:
    def check(started: int) -> None:
        race = race_loops(started)
        assert len(race.running_pids) == 1, race
        assert len(race.exited_outputs) == started - 1, race
        for output in race.exited_outputs:
            assert duplicate_signal in output, race
        assert race.lock_holder == str(race.running_pids[0]), race

    check_examples(loop_counts(), check, LOOP_RACES)


def test_a_loop_takes_over_a_lock_whose_process_is_gone() -> None:
    takeover = take_over_stale_lock()
    assert not takeover.exited, takeover
    assert takeover.left_behind != takeover.lock_holder, takeover
    assert takeover.lock_holder == str(takeover.pid), takeover
    assert duplicate_signal not in takeover.output, takeover


def test_a_loop_takes_over_the_lock_of_a_holder_that_was_killed() -> None:
    takeover = take_over_killed_holder()
    assert not takeover.exited, takeover
    assert takeover.left_behind != takeover.lock_holder, takeover
    assert takeover.lock_holder == str(takeover.pid), takeover
    assert duplicate_signal not in takeover.output, takeover
