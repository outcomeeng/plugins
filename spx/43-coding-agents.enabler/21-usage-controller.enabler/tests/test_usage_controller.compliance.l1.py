"""The usage controller's ALWAYS and NEVER rules hold against violating passes."""

from pathlib import Path

from outcomeeng_testing.generators.control_positions import (
    ALPHA,
    BETA,
    CEILING_MAXIMUM_PERCENT,
    COMPACTION_CONTEXT_PERCENT,
    COMPACTION_MULTIPLE,
    LOW_CONTEXT_PERCENT,
    PACE_TOKENS,
    PASS_INTERVAL_MINUTES,
    PAUSE_MULTIPLE,
    WEEKLY_CEILING_PERCENT,
    AgentKind,
    PositionSpec,
    alpha_positions,
    ceiling_accepted_values,
    ceiling_rejected_values,
    share,
    tokens_above,
    tokens_at_most,
    tokens_under,
)
from outcomeeng_testing.harnesses.control_positions import (
    BASE_TIME,
    INVALID_VALUE,
    SCALAR_CONFIG_FIELDS,
    ConfigSpec,
    PassObservation,
    PassStep,
    load_control_positions,
    run_passes,
    schedule_observation,
    with_config,
)

LABEL = "engineering.outcome.usage-control.positions"
STOP_TEXT = "/exit"
COMPACT_TEXT = "/compact"
CONTINUE_TEXT = "continue"
ESCAPE_KEY = "escape"
THIRTY_MINUTES_SECONDS = PASS_INTERVAL_MINUTES * 60


def test_skip_listed_pane_is_neither_measured_nor_acted_on() -> None:
    module = load_control_positions()
    positions = alpha_positions(3)
    skipped = positions[2]
    for key in (skipped.worktree, skipped.title):
        config = ConfigSpec(positions, skip=(key,))
        step = PassStep(
            contexts={item.worktree: COMPACTION_CONTEXT_PERCENT for item in positions},
            weekly={ALPHA: WEEKLY_CEILING_PERCENT},
            tokens={item.worktree: tokens_above(PACE_TOKENS, 2) for item in positions},
        )

        (observed,) = run_passes(module, config, [step])

        assert not [call for call in observed.calls if call.pane == skipped.pane]
        assert skipped.worktree not in {query[0] for query in observed.token_queries}
        assert {call.pane for call in observed.calls if call.operation == "send"} == {
            item.pane for item in positions[:2]
        }


def test_pass_stops_at_the_time_bound_and_records_unfinished_positions() -> None:
    module = load_control_positions()
    positions = alpha_positions(4)
    config = ConfigSpec(positions)
    step = PassStep(contexts={item.worktree: LOW_CONTEXT_PERCENT for item in positions})

    (unbounded,) = run_passes(module, config, [step])
    (bounded,) = run_passes(
        module, config, [step], seconds_per_command=module.PASS_BOUND_SECONDS / 2
    )

    measured = {call.pane for call in bounded.calls if call.operation == "read"}
    configured = {item.worktree for item in positions}
    unfinished_panes = {
        item.pane for item in positions if item.worktree in bounded.unfinished
    }
    assert unbounded.unfinished == ()
    assert bounded.unfinished
    assert set(bounded.unfinished) <= configured
    assert not measured & unfinished_panes
    assert measured | unfinished_panes == {item.pane for item in positions}


def test_pass_measures_each_position_once_and_runs_no_polling_loop() -> None:
    module = load_control_positions()
    positions = alpha_positions(3)
    config = ConfigSpec(positions)
    step = PassStep(
        contexts={item.worktree: COMPACTION_CONTEXT_PERCENT for item in positions},
        busy=frozenset(item.worktree for item in positions),
    )

    (observed,) = run_passes(module, config, [step])

    reads = [call.pane for call in observed.calls if call.operation == "read"]
    assert sorted(reads) == sorted(item.pane for item in positions)
    assert not [call for call in observed.calls if call.operation == "send"]


def test_context_threshold_compacts_at_the_first_idle_pass() -> None:
    module = load_control_positions()
    (position,) = alpha_positions(1)
    config = ConfigSpec((position,))
    below = COMPACTION_CONTEXT_PERCENT - 1
    above = COMPACTION_CONTEXT_PERCENT + 20

    for context, expected_sends in (
        (below, 0),
        (COMPACTION_CONTEXT_PERCENT, 1),
        (above, 1),
    ):
        step = PassStep(contexts={position.worktree: context})
        (observed,) = run_passes(module, config, [step])
        sends = [call for call in observed.calls if call.operation == "send"]
        assert len(sends) == expected_sends
        assert all(
            call.pane == position.pane and call.argument == COMPACT_TEXT
            for call in sends
        )

    busy = PassStep(
        contexts={position.worktree: above}, busy=frozenset({position.worktree})
    )
    idle = PassStep(contexts={position.worktree: above})
    first, second = run_passes(module, config, [busy, idle])
    assert not [call for call in first.calls if call.operation == "send"]
    assert [call.argument for call in second.calls if call.operation == "send"] == [
        COMPACT_TEXT
    ]


def test_spend_multiples_compact_pause_and_resume_against_the_share() -> None:
    module = load_control_positions()
    positions = alpha_positions(2)
    watched, other = positions
    config = ConfigSpec(positions)
    position_share = share(PACE_TOKENS, len(positions))
    above_compaction = tokens_above(position_share, COMPACTION_MULTIPLE)
    at_compaction = tokens_at_most(position_share, COMPACTION_MULTIPLE)
    above_pause = tokens_above(position_share, PAUSE_MULTIPLE)
    under = tokens_under(position_share)

    def sends(pass_observation: PassObservation) -> list[tuple[str | None, str | None]]:
        return [
            (call.pane, call.argument)
            for call in pass_observation.calls
            if call.operation == "send"
        ]

    (compacted,) = run_passes(
        module, config, [PassStep(tokens={watched.worktree: above_compaction})]
    )
    (kept,) = run_passes(
        module, config, [PassStep(tokens={watched.worktree: at_compaction})]
    )
    assert sends(compacted) == [(watched.pane, COMPACT_TEXT)]
    assert not sends(kept)

    heavy = PassStep(tokens={watched.worktree: above_pause})
    light = PassStep(tokens={watched.worktree: under})
    first, second, third, resumed = run_passes(
        module, config, [heavy, heavy, heavy, light]
    )
    keys = [
        [
            (call.pane, (call.argument or "").lower())
            for call in step.calls
            if call.operation == "key"
        ]
        for step in (first, second, third, resumed)
    ]
    assert keys == [[], [(watched.pane, ESCAPE_KEY)], [], []]
    assert (watched.pane, CONTINUE_TEXT) in sends(resumed)
    assert (watched.pane, CONTINUE_TEXT) not in sends(second) + sends(third)
    assert not [
        call
        for step in (first, second, third, resumed)
        for call in step.calls
        if call.pane == other.pane and call.operation in {"key", "send"}
    ]

    broken = run_passes(module, config, [heavy, light, heavy])
    assert not [
        call for step in broken for call in step.calls if call.operation == "key"
    ]

    skipped_config = with_config(config, skip=(other.worktree,))
    (solo,) = run_passes(
        module, skipped_config, [PassStep(tokens={watched.worktree: above_compaction})]
    )
    assert not sends(solo)


def test_weekly_ceiling_stops_every_unskipped_position_of_the_subscription() -> None:
    module = load_control_positions()
    alpha = alpha_positions(3)
    skipped = alpha[2]
    beta = PositionSpec(4, BETA)
    positions = (*alpha, beta)
    config = ConfigSpec(positions, skip=(skipped.worktree,))
    at_ceiling = PassStep(weekly={ALPHA: WEEKLY_CEILING_PERCENT, BETA: 0})
    below_ceiling = PassStep(weekly={ALPHA: WEEKLY_CEILING_PERCENT - 1, BETA: 0})

    (stopped,) = run_passes(module, config, [at_ceiling])
    (kept,) = run_passes(module, config, [below_ceiling])
    (unauthorized,) = run_passes(
        module, with_config(config, stop_authorized=False), [at_ceiling]
    )

    stops = [call for call in stopped.calls if call.operation == "send"]
    assert {call.pane for call in stops} == {alpha[0].pane, alpha[1].pane}
    assert {call.argument for call in stops} == {STOP_TEXT}
    assert not [
        call for call in stopped.calls if call.operation in {"tab-close", "pane-close"}
    ]
    assert {report.kind for report in stopped.reports} >= {
        module.ReportKind.SWITCH_ACCOUNT
    }
    assert not [call for call in kept.calls if call.operation == "send"]
    assert not [call for call in unauthorized.calls if call.operation == "send"]
    assert module.ReportKind.STOP_UNAUTHORIZED in {
        report.kind for report in unauthorized.reports
    }


def test_ceiling_above_the_maximum_is_rejected_before_any_action() -> None:
    module = load_control_positions()
    positions = alpha_positions(2)
    step = PassStep(weekly={ALPHA: 100}, contexts={positions[0].worktree: 90})

    for ceiling in ceiling_accepted_values():
        config = ConfigSpec(positions, weekly_ceiling_percent=ceiling)
        (accepted,) = run_passes(module, config, [step])
        assert accepted.error is None

    for ceiling in ceiling_rejected_values():
        assert ceiling > CEILING_MAXIMUM_PERCENT
        config = ConfigSpec(positions, weekly_ceiling_percent=ceiling)
        (rejected,) = run_passes(module, config, [step])
        assert isinstance(rejected.error, module.ConfigurationError)
        assert rejected.error.field == module.ConfigField.WEEKLY_CEILING_PERCENT
        assert not rejected.calls
        assert not rejected.records


def test_every_action_is_a_durable_record_and_no_record_recommends_an_unmade_action() -> (
    None
):
    module = load_control_positions()
    positions = alpha_positions(2)
    watched = positions[0]
    config = ConfigSpec(positions, key_authorized=False)
    heavy = PassStep(
        contexts={watched.worktree: COMPACTION_CONTEXT_PERCENT},
        tokens={watched.worktree: tokens_above(PACE_TOKENS / 2, PAUSE_MULTIPLE)},
    )
    ceiling = PassStep(weekly={ALPHA: WEEKLY_CEILING_PERCENT})

    first, second, third = run_passes(module, config, [heavy, heavy, ceiling])

    performed = {
        (call.pane, call.argument)
        for step in (first, second, third)
        for call in step.calls
        if call.operation in {"send", "key"}
    }
    actions = module.Action
    by_action = {
        (record[module.RecordField.ACTION], record[module.RecordField.POSITION])
        for record in third.records
    }
    assert (actions.COMPACT, watched.worktree) in by_action
    assert {action for action, _ in by_action} <= {actions.COMPACT, actions.STOP}
    assert {position for action, position in by_action if action == actions.STOP} == {
        item.worktree for item in positions
    }
    assert (watched.pane, COMPACT_TEXT) in performed
    assert len(third.record_files) >= len(third.records) > 0
    for record in third.records:
        for name in (
            module.RecordField.POSITION,
            module.RecordField.MEASUREMENT,
            module.RecordField.THRESHOLD,
            module.RecordField.REASON,
        ):
            assert record[name] not in (None, "")
        assert isinstance(record[module.RecordField.REASON], str)


def test_configuration_location_and_invalid_fields() -> None:
    module = load_control_positions()
    home = Path("/home/operator")
    explicit = Path("/xdg/config")

    assert module.config_path({"XDG_CONFIG_HOME": str(explicit)}, home) == (
        explicit / "outcome-engineering" / "control-positions.toml"
    )
    assert module.config_path({}, home) == (
        home / ".config" / "outcome-engineering" / "control-positions.toml"
    )

    positions = alpha_positions(1)
    step = PassStep(contexts={positions[0].worktree: COMPACTION_CONTEXT_PERCENT})
    for name in SCALAR_CONFIG_FIELDS:
        field = module.ConfigField[name]
        config = ConfigSpec(positions, overrides={field: INVALID_VALUE})
        (rejected,) = run_passes(module, config, [step])
        assert isinstance(rejected.error, module.ConfigurationError)
        assert rejected.error.field == field
        assert str(field) in str(rejected.error)
        assert not rejected.calls


def test_changed_file_takes_effect_at_the_next_pass_and_key_authorization_gates_pause() -> (
    None
):
    module = load_control_positions()
    positions = alpha_positions(1)
    (position,) = positions
    context = COMPACTION_CONTEXT_PERCENT + 1
    config = ConfigSpec(positions)
    raised = with_config(config, compaction_context_percent=context + 20)
    steps = [PassStep(contexts={position.worktree: context})] * 2
    first, second = run_passes(
        module, config, [steps[0], PassStep(steps[1].contexts, config=raised)]
    )
    assert [call.argument for call in first.calls if call.operation == "send"] == [
        COMPACT_TEXT
    ]
    assert not [call for call in second.calls if call.operation == "send"]

    heavy = PassStep(
        tokens={position.worktree: tokens_above(PACE_TOKENS, PAUSE_MULTIPLE)}
    )
    unauthorized = with_config(config, key_authorized=False)
    observed = run_passes(module, unauthorized, [heavy, heavy, heavy])
    assert not [
        call for step in observed for call in step.calls if call.operation == "key"
    ]
    assert module.ReportKind.KEY_UNAUTHORIZED in {
        report.kind for step in observed for report in step.reports
    }
    assert module.Action.PAUSE not in {
        record[module.RecordField.ACTION] for record in observed[-1].records
    }


def test_tokens_come_only_from_the_token_source_by_worktree_and_unmeasured_pace_keeps_context_rules() -> (
    None
):
    module = load_control_positions()
    measured, unmeasured, codex = (
        PositionSpec(1, ALPHA),
        PositionSpec(2, ALPHA),
        PositionSpec(3, BETA, AgentKind.CODEX),
    )
    positions = (measured, unmeasured, codex)
    config = ConfigSpec(positions)
    step = PassStep(
        contexts={
            measured.worktree: LOW_CONTEXT_PERCENT,
            unmeasured.worktree: COMPACTION_CONTEXT_PERCENT,
            codex.worktree: COMPACTION_CONTEXT_PERCENT,
        },
        weekly={ALPHA: 0, BETA: WEEKLY_CEILING_PERCENT},
        tokens={measured.worktree: 0},
    )

    (observed,) = run_passes(module, config, [step])

    window = (BASE_TIME.timestamp() - THIRTY_MINUTES_SECONDS, BASE_TIME.timestamp())
    queried = {query[0] for query in observed.token_queries}
    assert queried == {item.worktree for item in positions}
    assert all(
        (query[1].timestamp(), query[2].timestamp()) == window
        for query in observed.token_queries
    )
    unmeasured_reports = [
        report
        for report in observed.reports
        if report.kind == module.ReportKind.UNMEASURED_PACE
    ]
    assert {report.subject for report in unmeasured_reports} == {
        unmeasured.worktree,
        codex.worktree,
    }
    sends = {
        (call.pane, call.argument)
        for call in observed.calls
        if call.operation == "send"
    }
    assert (unmeasured.pane, COMPACT_TEXT) in sends
    assert (codex.pane, COMPACT_TEXT) in sends
    assert (codex.pane, STOP_TEXT) in sends


def test_scheduling_manages_one_finite_launchd_job_on_macos_only() -> None:
    module = load_control_positions()

    for operation in module.ScheduleOperation:
        observed = schedule_observation(module, operation, "darwin")
        assert observed.status != module.ScheduleStatus.UNSUPPORTED
        if operation == module.ScheduleOperation.INSTALL:
            assert observed.plist is not None
            assert observed.plist["Label"] == LABEL
            assert observed.plist["StartInterval"] == THIRTY_MINUTES_SECONDS
            assert not observed.plist.get("KeepAlive")
        else:
            assert any(LABEL in part for argv in observed.calls for part in argv)

    for platform in ("linux", "win32"):
        for operation in module.ScheduleOperation:
            observed = schedule_observation(module, operation, platform)
            assert observed.status == module.ScheduleStatus.UNSUPPORTED
            assert not observed.calls
            assert not observed.launch_agent_files


def test_position_in_a_herdr_pane_receives_no_measurement_and_no_action() -> None:
    module = load_control_positions()
    listed = PositionSpec(1, ALPHA)
    herdr = PositionSpec(2, ALPHA, in_prowl=False)
    config = ConfigSpec((listed, herdr))
    step = PassStep(
        contexts={herdr.worktree: 90, listed.worktree: LOW_CONTEXT_PERCENT},
        weekly={ALPHA: WEEKLY_CEILING_PERCENT},
        tokens={herdr.worktree: tokens_above(PACE_TOKENS, PAUSE_MULTIPLE)},
    )

    (observed,) = run_passes(module, config, [step])

    assert not [call for call in observed.calls if call.pane == herdr.pane]
    assert herdr.worktree not in {query[0] for query in observed.token_queries}
    assert herdr.worktree not in {
        record[module.RecordField.POSITION] for record in observed.records
    }
    assert [
        (call.pane, call.argument)
        for call in observed.calls
        if call.operation == "send"
    ] == [(listed.pane, STOP_TEXT)]
