from datetime import timedelta
from itertools import product

from hypothesis import strategies as st

from outcomeeng_testing.generators.position_direction import (
    MailHistory,
    Watched,
    background_texts,
    deadlines,
    digit_free_texts,
    distinct_pairs,
    every_percent,
    handles,
    mail_histories,
    remind_minutes,
    stall_minutes,
    status_line,
    subjects,
    thresholds,
    ticking,
    watched,
)
from outcomeeng_testing.harnesses.position_direction import (
    ABSENCES,
    BACKGROUND_EDGES,
    BROKEN_CHANNELS,
    BROKEN_SOURCES,
    CONTEXT_STEPS,
    DEADLINE_EXITS,
    EXIT_SLACK_SECONDS,
    MAIL_EDGES,
    REMIND_EDGES,
    STALL_EDGES,
    STATE_EDGES,
    Rig,
    check_examples,
    load_scripts,
    run_loop_to_deadline,
    scratch_dir,
    watch_with,
)

scripts = load_scripts()
Signal = scripts.monitor.Signal
State = scripts.environment.State
ENDED = scripts.environment.ENDED
backends = sorted(scripts.environment.BACKENDS)


def named(events: list, signal: Signal) -> list:
    return [event for event in events if event.signal == signal]


def test_mail_is_withheld_on_a_fresh_state_then_signalled_once_per_new_record() -> None:
    def check(history: MailHistory) -> None:
        rig = Rig(watch_with(mail={"channel": history.channel, "agent": history.agent}))
        for record in history.existing:
            rig.inbox.deliver(*record)
        assert named(rig.poll(), Signal.MAIL) == []

        for record in history.arrived:
            rig.inbox.deliver(*record)
        events = named(rig.poll(), Signal.MAIL)
        assert [event.subject for event in events] == [
            str(record_id) for record_id, _, _ in history.arrived
        ]
        for event, (_, sender, subject) in zip(events, history.arrived, strict=True):
            assert sender in event.detail
            assert subject in event.detail
        assert named(rig.poll(), Signal.MAIL) == []

    check_examples(mail_histories(), check, MAIL_EDGES)


def test_blocked_and_went_idle_signal_on_their_edges_over_every_state_pair() -> None:
    def check(subject: Watched) -> None:
        for backend in backends:
            for previous, current in product(State, State):
                rig = Rig.watching(subject.position, backend, subject.cwd)
                rig.place(previous, subject.handle)
                first = rig.poll()
                rig.place(current, subject.handle)
                events = rig.poll()
                where = f"{backend} {previous} -> {current}"

                assert bool(named(first, Signal.BLOCKED)) == (
                    previous == State.BLOCKED
                ), where
                assert bool(named(events, Signal.BLOCKED)) == (
                    current == State.BLOCKED and previous != State.BLOCKED
                ), where
                assert bool(named(events, Signal.WENT_IDLE)) == (
                    previous == State.WORKING and current in ENDED
                ), where
                assert named(first, Signal.WENT_IDLE) == [], where
                assert named(events, Signal.WAITING_ON_BACKGROUND) == [], where

    check_examples(watched(), check, STATE_EDGES)


def test_blocked_repeats_once_after_the_remind_interval() -> None:
    def check(case: tuple[Watched, int, bool]) -> None:
        subject, minutes, configured = case
        entry = {"blocked_remind_minutes": minutes} if configured else {}
        remind = (
            minutes if configured else scripts.monitor.DEFAULT_BLOCKED_REMIND_MINUTES
        )
        for backend in backends:
            rig = Rig.watching(subject.position, backend, subject.cwd, **entry)
            rig.place(State.BLOCKED, subject.handle)
            assert len(named(rig.poll(), Signal.BLOCKED)) == 1
            assert named(rig.poll(timedelta(minutes=remind - 2)), Signal.BLOCKED) == []
            assert len(named(rig.poll(timedelta(minutes=3)), Signal.BLOCKED)) == 1
            assert named(rig.poll(), Signal.BLOCKED) == []

    check_examples(
        st.tuples(watched(), remind_minutes(), st.booleans()), check, REMIND_EDGES
    )


def test_a_turn_that_ends_with_background_work_signals_waiting_and_idles_when_it_ends() -> (
    None
):
    def check(case: tuple[Watched, str, bool]) -> None:
        subject, background, report = case
        for backend in backends:
            rig = Rig.watching(
                subject.position, backend, subject.cwd, report_background=report
            )
            rig.place(State.WORKING, subject.handle)
            rig.poll()
            if backend == scripts.environment.Prowl.name:
                marker = f"{subject.position} {scripts.environment.BACKGROUND_MARKER}"
                rig.place(State.IDLE, subject.handle, detail=marker)
            else:
                rig.place(State.IDLE, subject.handle, text=background)
            events = rig.poll()
            assert bool(named(events, Signal.WAITING_ON_BACKGROUND)) == report
            assert named(events, Signal.WENT_IDLE) == []

            rig.place(State.IDLE, subject.handle, text="")
            assert len(named(rig.poll(), Signal.WENT_IDLE)) == 1
            assert named(rig.poll(), Signal.WENT_IDLE) == []

    check_examples(
        st.tuples(watched(), background_texts(), st.booleans()),
        check,
        BACKGROUND_EDGES,
    )


def test_a_working_pane_unchanged_for_the_stall_interval_signals_stalled_once() -> None:
    def check(case: tuple[Watched, int, str, str]) -> None:
        subject, stall, first, second = case
        window = timedelta(minutes=stall + 1)
        for backend in backends:
            rig = Rig.watching(
                subject.position, backend, subject.cwd, stall_minutes=stall
            )
            rig.place(State.WORKING, subject.handle, text=ticking(first, 1))
            assert named(rig.poll(), Signal.STALLED) == []
            rig.place(State.WORKING, subject.handle, text=ticking(first, 2))
            short = timedelta(minutes=stall - 1)
            assert named(rig.poll(short), Signal.STALLED) == []
            rig.place(State.WORKING, subject.handle, text=ticking(first, 3))
            assert len(named(rig.poll(timedelta(minutes=2)), Signal.STALLED)) == 1
            rig.place(State.WORKING, subject.handle, text=ticking(first, 4))
            assert named(rig.poll(), Signal.STALLED) == []

            rig.place(State.WORKING, subject.handle, text=ticking(second, 5))
            assert named(rig.poll(window), Signal.STALLED) == []
            rig.place(State.WORKING, subject.handle, text=ticking(second, 6))
            assert len(named(rig.poll(window), Signal.STALLED)) == 1

    strategy = st.tuples(
        watched(), stall_minutes(), digit_free_texts(), digit_free_texts()
    ).filter(lambda case: case[2] != case[3])
    check_examples(strategy, check, STALL_EDGES)


def test_each_compaction_tier_signals_once_per_five_percent_step() -> None:
    tiers = scripts.monitor.TIERS
    step = scripts.monitor.TIER_STEP_PERCENT
    tier_signals = {signal for _, _, signal in tiers}

    def due(percent: int, state: State) -> list:
        for threshold, ended_only, signal in tiers:
            if percent >= threshold and (not ended_only or state in ENDED):
                return [signal]
        return []

    def check(case: tuple[Watched, int]) -> None:
        subject, enabled = case
        for backend in backends:
            for state in State:
                for percent in every_percent():
                    rig = Rig.watching(
                        subject.position, backend, subject.cwd, context_percent=enabled
                    )
                    rig.place(state, subject.handle, text=status_line(percent))
                    shown = [e.signal for e in rig.poll() if e.signal in tier_signals]
                    where = f"{backend} {state} {percent}%"
                    assert shown == due(percent, state), where

                    bucket_start = percent // step * step
                    siblings = [
                        other
                        for other in range(bucket_start, bucket_start + step)
                        if other != percent
                        and other <= 100
                        and due(other, state) == due(percent, state)
                    ]
                    if siblings:
                        rig.place(state, subject.handle, text=status_line(siblings[0]))
                        again = [e for e in rig.poll() if e.signal in tier_signals]
                        assert again == [], where

                    following = bucket_start + step
                    if following <= 100:
                        rig.place(state, subject.handle, text=status_line(following))
                        shown = [
                            e.signal for e in rig.poll() if e.signal in tier_signals
                        ]
                        assert shown == due(following, state), where

    check_examples(st.tuples(watched(), thresholds()), check, CONTEXT_STEPS)


def test_absent_signals_once_for_each_loss_of_a_watched_session() -> None:
    def check(subject: Watched) -> None:
        for backend in backends:
            rig = Rig.watching(subject.position, backend, subject.cwd)
            first = named(rig.poll(), Signal.ABSENT)
            assert [event.subject for event in first] == [subject.position]
            assert named(rig.poll(), Signal.ABSENT) == []

            rig.place(State.WORKING, subject.handle)
            assert named(rig.poll(), Signal.ABSENT) == []
            rig.vacate()
            lost = named(rig.poll(), Signal.ABSENT)
            assert [event.subject for event in lost] == [subject.position]
            assert named(rig.poll(), Signal.ABSENT) == []

    check_examples(watched(), check, ABSENCES)


def test_a_failing_source_signals_watch_broken_while_the_other_sources_are_polled() -> (
    None
):
    def check(case: tuple[tuple[Watched, Watched], str, str, str, int]) -> None:
        (
            (failing_side, healthy_side),
            mail_failure,
            inventory_failure,
            read_failure,
            enabled,
        ) = case
        failing, healthy = backends
        watch = watch_with(
            mail={"channel": failing_side.cwd, "agent": failing_side.position},
            sessions=[
                {
                    "position": failing_side.position,
                    "backend": failing,
                    "cwd": failing_side.cwd,
                },
                {
                    "position": healthy_side.position,
                    "backend": healthy,
                    "cwd": healthy_side.cwd,
                    "context_percent": enabled,
                },
            ],
        )
        rig = Rig(watch)
        rig.inbox.failure = mail_failure
        rig.backends[failing].inventory = inventory_failure
        blocked = rig.session(
            healthy, healthy_side.handle, healthy_side.cwd, State.BLOCKED
        )
        rig.backends[healthy].inventory = [blocked]
        rig.backends[healthy].read_failures[healthy_side.handle] = read_failure

        first = rig.poll()
        second = rig.poll()
        broken = named(first + second, Signal.WATCH_BROKEN)
        for failure in (mail_failure, inventory_failure, read_failure):
            assert any(failure in event.detail for event in broken), failure
        assert [e.subject for e in named(first, Signal.BLOCKED)] == [
            healthy_side.position
        ]

    strategy = st.tuples(
        distinct_pairs(), subjects(), subjects(), subjects(), thresholds()
    )
    check_examples(strategy, check, BROKEN_SOURCES)


def test_an_unreadable_mail_channel_signals_watch_broken_and_polling_goes_on() -> None:
    def check(case: tuple[tuple[Watched, Watched], str]) -> None:
        (mailing, blocked_side), channel_name = case
        with scratch_dir() as directory:
            channel = f"{directory}/{channel_name}"
            watch = watch_with(
                mail={"channel": channel, "agent": mailing.position},
                sessions=[
                    {
                        "position": blocked_side.position,
                        "backend": backends[0],
                        "cwd": blocked_side.cwd,
                    }
                ],
            )
            rig = Rig(watch)
            rig.read_mail_through_the_adapter()
            blocked = rig.session(
                backends[0], blocked_side.handle, blocked_side.cwd, State.BLOCKED
            )
            rig.backends[backends[0]].inventory = [blocked]

            first = rig.poll()
            second = rig.poll()
            broken = named(first + second, Signal.WATCH_BROKEN)
            assert broken != []
            assert {event.subject for event in broken} == {"mail"}
            assert all(channel in event.detail for event in broken)
            assert [e.subject for e in named(first, Signal.BLOCKED)] == [
                blocked_side.position
            ]

    check_examples(st.tuples(distinct_pairs(), handles()), check, BROKEN_CHANNELS)


def test_the_loop_exits_on_its_own_at_the_deadline_it_is_given() -> None:
    def check(deadline: float) -> None:
        run = run_loop_to_deadline(deadline)
        assert run.exited, run
        assert run.returncode == 0, run
        assert run.elapsed_seconds >= run.deadline_seconds, run
        latest = run.deadline_seconds + run.interval_seconds + EXIT_SLACK_SECONDS
        assert run.elapsed_seconds <= latest, run

    check_examples(deadlines(), check, DEADLINE_EXITS)
