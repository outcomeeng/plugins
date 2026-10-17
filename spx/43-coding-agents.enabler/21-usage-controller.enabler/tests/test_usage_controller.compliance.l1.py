"""The usage controller's ALWAYS and NEVER rules hold against violating passes."""

import json
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
    PASS_BOUND_MINUTES,
    PAUSE_MULTIPLE,
    SECONDS_PER_MINUTE,
    WEEKLY_CEILING_PERCENT,
    AgentKind,
    PositionSpec,
    alpha_positions,
    ceiling_accepted_values,
    ceiling_rejected_values,
    just_before_pass_bound,
    non_finite_values,
    share,
    sibling_api_changes,
    token_reserve_shortfalls,
    tokens_above,
    tokens_at_most,
    tokens_under,
)
from outcomeeng_testing.harnesses.control_positions import (
    BASE_TIME,
    INVALID_VALUE,
    NUMERIC_CONFIG_FIELDS,
    SCALAR_CONFIG_FIELDS,
    STANDARD_ERROR_PATH_KEY,
    STANDARD_OUT_PATH_KEY,
    ChangedApiTokens,
    ConfigSpec,
    PassObservation,
    PassStep,
    changed_sibling_api,
    installed_job,
    load_control_positions,
    pass_window,
    token_measurement_limit_seconds,
    real_parser_world,
    run_passes,
    schedule_observation,
    sibling_registry,
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


def test_pass_ends_within_five_minutes_when_a_command_starts_just_before_the_bound() -> (
    None
):
    module = load_control_positions()
    positions = alpha_positions(4)
    config = ConfigSpec(positions)
    step = PassStep(contexts={item.worktree: LOW_CONTEXT_PERCENT for item in positions})
    command_timeout = module.SubprocessRunner().timeout_seconds

    for start in just_before_pass_bound(command_timeout):
        (observed,) = run_passes(
            module, config, [step], leading_seconds=(start,), hangs=True
        )
        assert observed.elapsed_seconds <= PASS_BOUND_MINUTES * SECONDS_PER_MINUTE


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
        assert not ceiling <= CEILING_MAXIMUM_PERCENT
        config = ConfigSpec(positions, weekly_ceiling_percent=ceiling)
        (rejected,) = run_passes(module, config, [step])
        assert isinstance(rejected.error, module.ConfigurationError)
        assert rejected.error.field == module.ConfigField.WEEKLY_CEILING_PERCENT
        assert not rejected.calls
        assert not rejected.records


def test_non_finite_numbers_are_rejected_naming_every_numeric_field() -> None:
    module = load_control_positions()
    positions = alpha_positions(1)
    (position,) = positions
    step = PassStep(contexts={position.worktree: COMPACTION_CONTEXT_PERCENT})

    for value in non_finite_values():
        cases = [
            (
                module.ConfigField[name],
                ConfigSpec(positions, overrides={module.ConfigField[name]: value}),
            )
            for name in NUMERIC_CONFIG_FIELDS
        ]
        cases.append(
            (
                module.ConfigField.PACE_TOKENS,
                ConfigSpec(positions, pace={position.subscription: value}),
            )
        )
        for field, config in cases:
            (rejected,) = run_passes(module, config, [step])
            assert isinstance(rejected.error, module.ConfigurationError)
            assert rejected.error.field == field
            assert str(field) in str(rejected.error)
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


def test_consumption_control_parser_measures_the_worktree_after_collecting_its_transcripts() -> (
    None
):
    module = load_control_positions(built=True)
    measured, other, absent = alpha_positions(3)

    with real_parser_world(module) as world:
        # No consumption-control job has collected: the source collects itself.
        world.add_transcript_row(measured.worktree)
        world.add_transcript_row(other.worktree)
        world.add_transcript_row(other.worktree)

        first = world.tokens.tokens(measured.worktree, *world.window)
        second = world.tokens.tokens(other.worktree, *world.window)
        assert first == world.tokens_per_row
        assert second == 2 * world.tokens_per_row
        assert world.tokens.tokens(absent.worktree, *world.window) is None
        assert world.tokens.tokens(measured.worktree, *world.after_rows_window) is None

        # A transcript written after an earlier measurement is read by the next.
        world.add_transcript_row(measured.worktree)
        refreshed = world.tokens.tokens(measured.worktree, *world.window)
        assert refreshed == 2 * world.tokens_per_row


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


def test_installed_job_delivers_each_pass_output_to_files_in_the_data_root() -> None:
    # Clauses: the launchd clause (the installed job starts one finite pass) and the
    # ceiling clause (the controller "tells the operator to switch accounts" and
    # "reports why" it stopped nothing). The scheduled pass is the only unattended
    # pass, and launchd discards the standard streams of a job that names no file for
    # them, so the notices a pass prints reach the operator only through a file. The
    # contract: the installed plist names a standard output path and a standard error
    # path, each a file inside the data root the installed pass writes to; the two
    # paths may be equal or distinct. Rejects the mutation that installs the job with
    # no output paths (launchd discards the notices), and the one that points them
    # outside the data root (/dev/null or a directory the operator never reads).
    module = load_control_positions()

    job = installed_job(module)

    for key in (STANDARD_OUT_PATH_KEY, STANDARD_ERROR_PATH_KEY):
        assert key in job.plist, (
            f"installed plist lacks {key}: keys {sorted(job.plist)}"
        )
        path = Path(job.plist[key])
        assert path.is_absolute(), (key, path)
        assert path.parent.is_relative_to(job.data_root), (key, path, job.data_root)


def test_interactive_pass_prints_one_json_line_with_the_reports_on_standard_output() -> (
    None
):
    # Clauses: the launchd clause (the skill runs one pass on request) and the ceiling
    # clause ("reports why" nothing was stopped). Rejects the mutation that moves the
    # redirect of the scheduled job into the pass itself, so the interactive run prints
    # nothing, or prints more than the one JSON line, on standard output.
    module = load_control_positions()
    positions = alpha_positions(2)
    config = ConfigSpec(positions, stop_authorized=False)
    at_ceiling = PassStep(weekly={ALPHA: WEEKLY_CEILING_PERCENT})

    (observed,) = run_passes(module, config, [at_ceiling], via_main=True)

    lines = observed.stdout.splitlines()
    assert len(lines) == 1, observed.stdout
    document = json.loads(lines[0])
    assert module.ReportKind.STOP_UNAUTHORIZED in {
        report["kind"] for report in document["reports"]
    }, document


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


def test_token_measurement_is_skipped_when_its_longest_span_does_not_fit_the_bound() -> (
    None
):
    module = load_control_positions()
    positions = alpha_positions(2)
    config = ConfigSpec(positions)
    step = PassStep(contexts={item.worktree: LOW_CONTEXT_PERCENT for item in positions})
    bound = PASS_BOUND_MINUTES * SECONDS_PER_MINUTE
    reserve = token_measurement_limit_seconds()

    for left in token_reserve_shortfalls(reserve):
        # The inventory command takes no time; the first read leaves `left` seconds.
        (short,) = run_passes(
            module, config, [step], leading_seconds=(0.0, bound - left)
        )
        assert not short.token_queries
        assert not set(short.unfinished) & {item.worktree for item in positions}
        assert {
            report.subject
            for report in short.reports
            if report.kind == module.ReportKind.UNMEASURED_PACE
        } == {item.worktree for item in positions}

    (fits,) = run_passes(module, config, [step], leading_seconds=(0.0, bound - reserve))
    assert positions[0].worktree in {query[0] for query in fits.token_queries}


def test_pass_ends_within_five_minutes_when_a_token_measurement_takes_its_longest_span() -> (
    None
):
    module = load_control_positions()
    positions = alpha_positions(2)
    config = ConfigSpec(positions)
    step = PassStep(contexts={item.worktree: LOW_CONTEXT_PERCENT for item in positions})
    bound = PASS_BOUND_MINUTES * SECONDS_PER_MINUTE
    reserve = token_measurement_limit_seconds()

    for left in (*token_reserve_shortfalls(reserve), reserve):
        (observed,) = run_passes(
            module,
            config,
            [step],
            leading_seconds=(0.0, bound - left),
            token_seconds=reserve,
        )
        assert observed.elapsed_seconds <= bound


def test_changed_sibling_api_leaves_pace_unmeasured_and_keeps_context_compaction() -> (
    None
):
    module = load_control_positions(built=True)
    (position,) = alpha_positions(1)
    config = ConfigSpec((position,))
    step = PassStep(contexts={position.worktree: COMPACTION_CONTEXT_PERCENT})

    with real_parser_world(module) as world:
        world.add_transcript_row(position.worktree)
        assert (
            module.ConsumptionTokens().tokens(position.worktree, *world.window)
            == world.tokens_per_row
        )

        for change in sibling_api_changes():
            with changed_sibling_api(world.accounting, change, position.worktree):
                assert (
                    module.ConsumptionTokens().tokens(position.worktree, *world.window)
                    is None
                ), change
                (observed,) = run_passes(
                    module, config, [step], token_source=module.ConsumptionTokens()
                )

            assert observed.error is None, change
            assert {
                report.subject
                for report in observed.reports
                if report.kind == module.ReportKind.UNMEASURED_PACE
            } == {position.worktree}, change
            assert [
                (call.pane, call.argument)
                for call in observed.calls
                if call.operation == "send"
            ] == [(position.pane, COMPACT_TEXT)], change


# Resume rests on a measurement. Evidence for the clause "resumes by the prompt
# `continue` at the first pass where its spend is back under its share" and the
# record clause that a record names a true reason. Each position starts paused by
# two consecutive heavy passes; the pass under test follows.


def test_paused_position_stays_paused_when_the_token_measurement_is_skipped() -> None:
    # Clause: resume only when spend is back under the share. Rejects the mutation
    # that treats a skipped token measurement (no ratio) as a spend under the share.
    module = load_control_positions()
    (position,) = alpha_positions(1)
    config = ConfigSpec((position,))
    position_share = share(PACE_TOKENS, 1)
    heavy = PassStep(
        tokens={position.worktree: tokens_above(position_share, PAUSE_MULTIPLE)}
    )
    light = PassStep(tokens={position.worktree: tokens_under(position_share)})
    bound = PASS_BOUND_MINUTES * SECONDS_PER_MINUTE
    reserve = token_measurement_limit_seconds()

    for left in token_reserve_shortfalls(reserve):
        skipped = PassStep(leading_seconds=(0.0, bound - left))

        first, second, during, after = run_passes(
            module, config, [heavy, heavy, skipped, light]
        )

        assert [
            (call.pane, (call.argument or "").lower())
            for call in second.calls
            if call.operation == "key"
        ] == [(position.pane, ESCAPE_KEY)], left
        assert not during.token_queries, left
        assert (position.pane, CONTINUE_TEXT) not in {
            (call.pane, call.argument) for call in during.calls
        }, left
        assert module.Action.RESUME not in {
            record[module.RecordField.ACTION] for record in during.new_records
        }, left
        assert position.worktree in {
            report.subject
            for report in during.reports
            if report.kind == module.ReportKind.UNMEASURED_PACE
        }, left
        assert (position.pane, CONTINUE_TEXT) in {
            (call.pane, call.argument) for call in after.calls
        }, left
        assert module.Action.RESUME in {
            record[module.RecordField.ACTION] for record in after.new_records
        }, left


def test_paused_position_stays_paused_when_the_token_source_is_unusable() -> None:
    # Clause: resume only when spend is back under the share. Rejects the mutation
    # that treats a sibling accounting interface that no longer answers (no ratio)
    # as a spend under the share.
    module = load_control_positions(built=True)
    (position,) = alpha_positions(1)
    config = ConfigSpec((position,))
    position_share = share(PACE_TOKENS, 1)
    heavy = PassStep(
        tokens={position.worktree: tokens_above(position_share, PAUSE_MULTIPLE)}
    )
    light = PassStep(tokens={position.worktree: tokens_under(position_share)})

    with real_parser_world(module) as world:
        world.add_transcript_row(position.worktree)
        for change in sibling_api_changes():
            unusable = PassStep(
                token_source=ChangedApiTokens(
                    module, world.accounting, change, position.worktree
                )
            )

            first, second, during, after = run_passes(
                module, config, [heavy, heavy, unusable, light]
            )

            assert [
                (call.pane, (call.argument or "").lower())
                for call in second.calls
                if call.operation == "key"
            ] == [(position.pane, ESCAPE_KEY)], change
            assert (position.pane, CONTINUE_TEXT) not in {
                (call.pane, call.argument) for call in during.calls
            }, change
            assert module.Action.RESUME not in {
                record[module.RecordField.ACTION] for record in during.new_records
            }, change
            assert position.worktree in {
                report.subject
                for report in during.reports
                if report.kind == module.ReportKind.UNMEASURED_PACE
            }, change
            assert (position.pane, CONTINUE_TEXT) in {
                (call.pane, call.argument) for call in after.calls
            }, change
            assert module.Action.RESUME in {
                record[module.RecordField.ACTION] for record in after.new_records
            }, change


def test_paused_position_stays_paused_when_its_subscription_has_no_configured_pace() -> (
    None
):
    # Clause: resume only when spend is back under the share, and the share is the
    # subscription's pace divided among its positions. Rejects the mutation that
    # resumes a paused position whose share is undefined (no configured pace).
    module = load_control_positions()
    (position,) = alpha_positions(1)
    config = ConfigSpec((position,))
    position_share = share(PACE_TOKENS, 1)
    heavy = PassStep(
        tokens={position.worktree: tokens_above(position_share, PAUSE_MULTIPLE)}
    )
    light = PassStep(
        config=config, tokens={position.worktree: tokens_under(position_share)}
    )
    unpaced = PassStep(
        config=with_config(config, unpaced=(position.subscription,)),
        tokens={position.worktree: tokens_under(position_share)},
    )

    first, second, during, after = run_passes(
        module, config, [heavy, heavy, unpaced, light]
    )

    assert [
        (call.pane, (call.argument or "").lower())
        for call in second.calls
        if call.operation == "key"
    ] == [(position.pane, ESCAPE_KEY)]
    assert (position.pane, CONTINUE_TEXT) not in {
        (call.pane, call.argument) for call in during.calls
    }
    assert module.Action.RESUME not in {
        record[module.RecordField.ACTION] for record in during.new_records
    }
    assert position.worktree in {
        report.subject
        for report in during.reports
        if report.kind == module.ReportKind.UNMEASURED_PACE
    }
    assert (position.pane, CONTINUE_TEXT) in {
        (call.pane, call.argument) for call in after.calls
    }
    assert module.Action.RESUME in {
        record[module.RecordField.ACTION] for record in after.new_records
    }


def test_resume_without_a_session_in_the_window_states_its_true_basis() -> None:
    # Clauses: a paused position resumes at the first pass where its spend is back
    # under its share (a paused position makes no requests, so the parser finds no
    # session for it), and a record names a true reason. Rejects the mutation that
    # records an unmeasured resume with the measured-spend reason.
    module = load_control_positions(built=True)
    (position,) = alpha_positions(1)
    other = PositionSpec(2, ALPHA)
    config = ConfigSpec((position,))
    position_share = share(PACE_TOKENS, 1)
    under = tokens_under(position_share)
    heavy = PassStep(
        tokens={position.worktree: tokens_above(position_share, PAUSE_MULTIPLE)}
    )
    light = PassStep(tokens={position.worktree: under})

    def resumes(observation: PassObservation) -> list[dict[str, object]]:
        return [
            record
            for record in observation.new_records
            if record[module.RecordField.ACTION] == module.Action.RESUME
        ]

    *_, measured_pass = run_passes(module, config, [heavy, heavy, light])
    (measured,) = resumes(measured_pass)

    with real_parser_world(module) as world:
        world.add_transcript_row(other.worktree)
        no_session = PassStep(token_source=module.ConsumptionTokens())
        steps = [heavy, heavy, no_session]
        measuring_pass = len(steps) - 1
        start_time = world.start_time_for(measuring_pass)
        window = pass_window(start_time, measuring_pass)
        assert world.tokens.tokens(other.worktree, *window) == world.tokens_per_row
        assert world.tokens.tokens(position.worktree, *window) is None

        _, second, unmeasured_pass = run_passes(
            module, config, steps, start_time=start_time
        )

    (unmeasured,) = resumes(unmeasured_pass)
    field = module.RecordField
    assert (position.pane, CONTINUE_TEXT) in {
        (call.pane, call.argument) for call in unmeasured_pass.calls
    }
    assert [
        (call.pane, (call.argument or "").lower())
        for call in second.calls
        if call.operation == "key"
    ] == [(position.pane, ESCAPE_KEY)]
    assert str(under) in measured[field.MEASUREMENT]
    assert unmeasured[field.REASON] not in (None, "")
    assert unmeasured[field.REASON] != measured[field.REASON]
    assert not any(char.isdigit() for char in unmeasured[field.MEASUREMENT])


def test_measured_spend_under_the_share_resumes_the_paused_position() -> None:
    # Clause: resumes by `continue` at the first pass where its spend is back under
    # its share. Rejects the mutation that never resumes (or resumes only after a
    # second pass) once a measured spend is under the share, and pins the measured
    # record naming the measured spend.
    module = load_control_positions()
    (position,) = alpha_positions(1)
    config = ConfigSpec((position,))
    position_share = share(PACE_TOKENS, 1)
    under = tokens_under(position_share)
    heavy = PassStep(
        tokens={position.worktree: tokens_above(position_share, PAUSE_MULTIPLE)}
    )
    light = PassStep(tokens={position.worktree: under})

    first, second, resumed = run_passes(module, config, [heavy, heavy, light])

    field = module.RecordField
    records = [
        record
        for record in resumed.new_records
        if record[field.ACTION] == module.Action.RESUME
    ]
    assert (position.pane, CONTINUE_TEXT) in {
        (call.pane, call.argument) for call in resumed.calls
    }
    assert [record[field.POSITION] for record in records] == [position.worktree]
    assert str(under) in records[0][field.MEASUREMENT]
    assert records[0][field.REASON] not in (None, "")
    assert not [
        unmeasured
        for unmeasured in resumed.reports
        if unmeasured.kind == module.ReportKind.UNMEASURED_PACE
    ]


# Pause streaks, paused state, and failed actions. Each case names the spec clause it
# observes and the mutation of the controller it rejects. The sequences start from
# one position (or the stated number) whose share is its subscription's pace divided
# among the measured positions.


def sends_of(observation: PassObservation) -> list[tuple[str | None, str | None]]:
    return [
        (call.pane, call.argument)
        for call in observation.calls
        if call.operation == "send"
    ]


def keys_of(observation: PassObservation) -> list[tuple[str | None, str]]:
    return [
        (call.pane, (call.argument or "").lower())
        for call in observation.calls
        if call.operation == "key"
    ]


def test_paused_position_stays_paused_when_the_accounting_history_is_incomplete() -> (
    None
):
    # Clauses: resumes by `continue` only at the first pass where its spend is back
    # under its share, and a position the parser measures no session for keeps its
    # pace unmeasured. A window without a session shows an idle position only when
    # the collection saw every source. Rejects the mutation that reads the absence
    # of a session as no session without requiring a complete history: it would send
    # `continue` and write a RESUME record while the transcript root is absent.
    module = load_control_positions(built=True)
    (position,) = alpha_positions(1)
    config = ConfigSpec((position,))
    position_share = share(PACE_TOKENS, 1)
    heavy = PassStep(
        tokens={position.worktree: tokens_above(position_share, PAUSE_MULTIPLE)}
    )
    light = PassStep(tokens={position.worktree: tokens_under(position_share)})

    with real_parser_world(module, transcript_root=False) as world:
        collected = world.collection()
        reading = world.tokens.reading(position.worktree, *world.window)
        incomplete = PassStep(token_source=module.ConsumptionTokens())

        _, second, during, after = run_passes(
            module, config, [heavy, heavy, incomplete, light]
        )

    assert collected[world.accounting.AccountingField.HISTORY_COMPLETE] is False
    assert reading.state == module.TokenState.UNMEASURED
    assert keys_of(second) == [(position.pane, ESCAPE_KEY)]
    assert (position.pane, CONTINUE_TEXT) not in sends_of(during)
    assert module.Action.RESUME not in {
        record[module.RecordField.ACTION] for record in during.new_records
    }
    assert position.worktree in {
        report.subject
        for report in during.reports
        if report.kind == module.ReportKind.UNMEASURED_PACE
    }
    assert (position.pane, CONTINUE_TEXT) in sends_of(after)
    assert module.Action.RESUME in {
        record[module.RecordField.ACTION] for record in after.new_records
    }


def test_pause_streak_counts_only_passes_that_measured_the_position() -> None:
    # Clause: a position that exceeds the pause multiple on two consecutive passes
    # is paused. A pass that did not measure the position (not hosted in Prowl, on
    # the skip list, or left unfinished at the bound) is not one of the consecutive
    # passes. Rejects the mutation that carries a streak across an unmeasured pass:
    # heavy, unmeasured, heavy would then pause on the third pass.
    module = load_control_positions()
    (position,) = alpha_positions(1)
    config = ConfigSpec((position,))
    position_share = share(PACE_TOKENS, 1)
    tokens = {position.worktree: tokens_above(position_share, PAUSE_MULTIPLE)}
    bound = PASS_BOUND_MINUTES * SECONDS_PER_MINUTE
    heavy = PassStep(tokens=tokens)
    heavy_again = PassStep(config=config, tokens=tokens)
    unmeasured_passes = {
        "not hosted in Prowl": PassStep(
            config=ConfigSpec((PositionSpec(position.ordinal, ALPHA, in_prowl=False),)),
            tokens=tokens,
        ),
        "on the skip list": PassStep(
            config=with_config(config, skip=(position.worktree,)), tokens=tokens
        ),
        "unfinished at the bound": PassStep(leading_seconds=(bound,), tokens=tokens),
    }

    for name, between in unmeasured_passes.items():
        first, skipped, third = run_passes(
            module, config, [heavy, between, heavy_again]
        )
        assert not skipped.token_queries, name
        assert not keys_of(first) + keys_of(skipped) + keys_of(third), name
        assert module.Action.PAUSE not in {
            record[module.RecordField.ACTION] for record in third.records
        }, name

        *_, paused = run_passes(
            module, config, [heavy, between, heavy_again, heavy_again]
        )
        assert keys_of(paused) == [(position.pane, ESCAPE_KEY)], name

    unfinished = run_passes(
        module, config, [unmeasured_passes["unfinished at the bound"]]
    )
    assert unfinished[0].unfinished == (position.worktree,)


def test_pause_is_remembered_when_the_pass_raises_after_the_pause_key() -> None:
    # Clauses: a position paused by the Escape key resumes at the first pass where
    # its spend is back under its share, and every pause is a durable record. A pass
    # whose record write raises after the key was sent has paused the position.
    # Rejects the mutation that saves the paused state only after a pass ends
    # without raising: the next pass would not hold the position paused and would
    # send it no `continue`.
    module = load_control_positions()
    (position,) = alpha_positions(1)
    config = ConfigSpec((position,))
    position_share = share(PACE_TOKENS, 1)
    tokens = {position.worktree: tokens_above(position_share, PAUSE_MULTIPLE)}
    heavy = PassStep(tokens=tokens)
    failing = PassStep(tokens=tokens, records_blocked=True)
    light = PassStep(tokens={position.worktree: tokens_under(position_share)})

    _, raised, after = run_passes(module, config, [heavy, failing, light])

    assert isinstance(raised.error, OSError)
    assert keys_of(raised) == [(position.pane, ESCAPE_KEY)]
    assert not raised.new_records
    assert (position.pane, CONTINUE_TEXT) in sends_of(after)
    assert module.Action.RESUME in {
        record[module.RecordField.ACTION] for record in after.new_records
    }


def test_switch_account_report_names_the_positions_whose_exit_send_failed() -> None:
    # Clause: at the weekly ceiling the controller sends `/exit` to every position of
    # the subscription and tells the operator to switch accounts; no record or
    # report recommends or claims an action the controller did not take. Rejects the
    # mutation that reports the positions as stopped, or leaves out the worktrees
    # that were not, when one or every `/exit` send fails.
    module = load_control_positions()
    positions = alpha_positions(3)
    config = ConfigSpec(positions)
    ceiling = PassStep(weekly={ALPHA: WEEKLY_CEILING_PERCENT})

    def switch_messages(observation: PassObservation) -> list[str]:
        return [
            report.message
            for report in observation.reports
            if report.kind == module.ReportKind.SWITCH_ACCOUNT
        ]

    def stopped_positions(observation: PassObservation) -> set[object]:
        return {
            record[module.RecordField.POSITION]
            for record in observation.new_records
            if record[module.RecordField.ACTION] == module.Action.STOP
        }

    (all_stopped,) = run_passes(module, config, [ceiling])
    (baseline,) = switch_messages(all_stopped)
    assert stopped_positions(all_stopped) == {item.worktree for item in positions}

    refused_one = PassStep(
        weekly=ceiling.weekly, refused=frozenset({("send", positions[1].pane)})
    )
    (one_failed,) = run_passes(module, config, [refused_one])
    (message,) = switch_messages(one_failed)
    assert message != baseline
    assert positions[1].worktree in message
    assert stopped_positions(one_failed) == {
        positions[0].worktree,
        positions[2].worktree,
    }
    assert module.ReportKind.ACTION_FAILED in {
        report.kind for report in one_failed.reports
    }

    refused_all = PassStep(
        weekly=ceiling.weekly,
        refused=frozenset({("send", item.pane) for item in positions}),
    )
    (every_failed,) = run_passes(module, config, [refused_all])
    (message,) = switch_messages(every_failed)
    assert message != baseline
    assert all(item.worktree in message for item in positions)
    assert not stopped_positions(every_failed)
    assert {(item.pane, STOP_TEXT) for item in positions} <= set(sends_of(every_failed))


def test_failed_exit_send_leaves_the_paused_position_paused() -> None:
    # Clauses: a paused position resumes at the first pass where its spend is back
    # under its share, and a stop is a position that received `/exit`. Rejects the
    # mutation that forgets the paused state of a position whose `/exit` send failed:
    # the later pass under the share would send it no `continue`.
    module = load_control_positions()
    (position,) = alpha_positions(1)
    config = ConfigSpec((position,))
    position_share = share(PACE_TOKENS, 1)
    tokens = {position.worktree: tokens_above(position_share, PAUSE_MULTIPLE)}
    heavy = PassStep(tokens=tokens)
    refused_exit = PassStep(
        tokens=tokens,
        weekly={ALPHA: WEEKLY_CEILING_PERCENT},
        refused=frozenset({("send", position.pane)}),
    )
    light = PassStep(tokens={position.worktree: tokens_under(position_share)})

    _, _, failed_stop, after = run_passes(
        module, config, [heavy, heavy, refused_exit, light]
    )

    assert (position.pane, STOP_TEXT) in sends_of(failed_stop)
    assert module.Action.STOP not in {
        record[module.RecordField.ACTION] for record in failed_stop.new_records
    }
    assert (position.pane, CONTINUE_TEXT) in sends_of(after)
    assert module.Action.RESUME in {
        record[module.RecordField.ACTION] for record in after.new_records
    }


def test_failed_continue_send_keeps_the_position_paused_and_writes_no_record() -> None:
    # Clauses: a paused position resumes by the prompt `continue`, and a record names
    # an action the controller took. Rejects the mutation that resumes the position
    # (forgets the pause or writes a RESUME record) when the `continue` send fails.
    module = load_control_positions()
    (position,) = alpha_positions(1)
    config = ConfigSpec((position,))
    position_share = share(PACE_TOKENS, 1)
    heavy = PassStep(
        tokens={position.worktree: tokens_above(position_share, PAUSE_MULTIPLE)}
    )
    light = PassStep(tokens={position.worktree: tokens_under(position_share)})
    refused_light = PassStep(
        tokens=light.tokens, refused=frozenset({("send", position.pane)})
    )

    _, _, failed, retried = run_passes(
        module, config, [heavy, heavy, refused_light, light]
    )

    assert (position.pane, CONTINUE_TEXT) in sends_of(failed)
    assert (position.worktree, module.ReportKind.ACTION_FAILED) in {
        (report.subject, report.kind) for report in failed.reports
    }
    assert not failed.new_records
    assert (position.pane, CONTINUE_TEXT) in sends_of(retried)
    assert module.Action.RESUME in {
        record[module.RecordField.ACTION] for record in retried.new_records
    }


def test_failed_pause_key_leaves_the_position_not_paused_and_writes_no_record() -> None:
    # Clauses: a position over the pause multiple on two consecutive passes is paused
    # by the Escape key, and a record names an action the controller took. Rejects
    # the mutation that marks the position paused, or writes a PAUSE record or the
    # pause notice, when the key send fails: the later pass under the share would
    # send `continue` to a position that was never paused.
    module = load_control_positions()
    (position,) = alpha_positions(1)
    config = ConfigSpec((position,))
    position_share = share(PACE_TOKENS, 1)
    tokens = {position.worktree: tokens_above(position_share, PAUSE_MULTIPLE)}
    heavy = PassStep(tokens=tokens)
    refused_key = PassStep(tokens=tokens, refused=frozenset({("key", position.pane)}))
    light = PassStep(tokens={position.worktree: tokens_under(position_share)})

    _, failed, under = run_passes(module, config, [heavy, refused_key, light])

    assert keys_of(failed) == [(position.pane, ESCAPE_KEY)]
    assert (position.worktree, module.ReportKind.ACTION_FAILED) in {
        (report.subject, report.kind) for report in failed.reports
    }
    assert module.ReportKind.PAUSE_NOTICE not in {
        report.kind for report in failed.reports
    }
    assert module.Action.PAUSE not in {
        record[module.RecordField.ACTION] for record in failed.new_records
    }
    assert (position.pane, CONTINUE_TEXT) not in sends_of(under)
    assert module.Action.RESUME not in {
        record[module.RecordField.ACTION] for record in under.new_records
    }

    *_, third = run_passes(module, config, [heavy, refused_key, heavy])
    assert keys_of(third) == [(position.pane, ESCAPE_KEY)]
    assert module.Action.PAUSE in {
        record[module.RecordField.ACTION] for record in third.new_records
    }


def test_inventory_at_the_pass_bound_marks_only_unskipped_positions_unfinished() -> (
    None
):
    # Clause: a pass that reaches the five-minute bound records its unfinished
    # positions and leaves them to the next pass, and a pane on the skip list
    # receives no action. Rejects the mutation that marks every configured position
    # unfinished (the skip-listed one included) or none when the inventory call
    # meets the bound.
    module = load_control_positions()
    positions = alpha_positions(3)
    skipped = positions[2]
    config = ConfigSpec(positions, skip=(skipped.worktree,))
    bound = PASS_BOUND_MINUTES * SECONDS_PER_MINUTE
    contexts = {item.worktree: COMPACTION_CONTEXT_PERCENT for item in positions}

    stalled, next_pass = run_passes(
        module,
        config,
        [PassStep(stall_seconds=bound), PassStep(contexts=contexts)],
    )

    assert not stalled.calls
    assert not stalled.token_queries
    assert set(stalled.unfinished) == {positions[0].worktree, positions[1].worktree}
    assert next_pass.unfinished == ()
    assert {pane for pane, _ in sends_of(next_pass)} == {
        positions[0].pane,
        positions[1].pane,
    }


def test_paused_state_holds_while_the_position_is_absent_or_skip_listed() -> None:
    # Clause: a paused position resumes at the first pass where its spend is back
    # under its share; a pane the Prowl inventory does not list, or the skip list
    # names, receives no action. Rejects the mutation that forgets the paused state
    # of a configured position not acted on in a pass, and the mutation that sends
    # `continue` to an absent or skip-listed position under its share.
    module = load_control_positions()
    (position,) = alpha_positions(1)
    config = ConfigSpec((position,))
    position_share = share(PACE_TOKENS, 1)
    heavy = PassStep(
        tokens={position.worktree: tokens_above(position_share, PAUSE_MULTIPLE)}
    )
    under = {position.worktree: tokens_under(position_share)}
    away = {
        "absent from Prowl": PassStep(
            config=ConfigSpec((PositionSpec(position.ordinal, ALPHA, in_prowl=False),)),
            tokens=under,
        ),
        "newly skip-listed": PassStep(
            config=with_config(config, skip=(position.worktree,)), tokens=under
        ),
    }
    returned = PassStep(config=config, tokens=under)

    for name, step in away.items():
        _, second, during, after = run_passes(
            module, config, [heavy, heavy, step, returned]
        )

        assert keys_of(second) == [(position.pane, ESCAPE_KEY)], name
        assert not [call for call in during.calls if call.pane == position.pane], name
        assert not during.new_records, name
        assert (position.pane, CONTINUE_TEXT) in sends_of(after), name
        assert module.Action.RESUME in {
            record[module.RecordField.ACTION] for record in after.new_records
        }, name


def test_paused_state_persists_across_a_controller_restart() -> None:
    # Clause: a paused position resumes at the first pass where its spend is back
    # under its share, so the pause outlives the pass that made it. Each pass runs
    # with fresh collaborators over the same data root, as a restarted scheduled
    # pass does. Rejects the mutation that drops the paused state between passes: a
    # paused position above its share at context use over the compaction threshold
    # would be compacted, and the pass under the share would send no `continue`.
    module = load_control_positions()
    (position,) = alpha_positions(1)
    config = ConfigSpec((position,))
    position_share = share(PACE_TOKENS, 1)
    tokens = {position.worktree: tokens_above(position_share, PAUSE_MULTIPLE)}
    heavy = PassStep(tokens=tokens)
    heavy_and_full = PassStep(
        tokens=tokens, contexts={position.worktree: COMPACTION_CONTEXT_PERCENT}
    )
    light = PassStep(tokens={position.worktree: tokens_under(position_share)})

    _, paused, restarted, resumed = run_passes(
        module, config, [heavy, heavy, heavy_and_full, light]
    )

    assert module.Action.PAUSE in {
        record[module.RecordField.ACTION] for record in paused.new_records
    }
    assert paused.record_files
    assert not restarted.new_records
    assert restarted.record_files == paused.record_files
    assert not keys_of(restarted)
    assert not sends_of(restarted)
    assert (position.pane, CONTINUE_TEXT) in sends_of(resumed)
    assert module.Action.RESUME in {
        record[module.RecordField.ACTION] for record in resumed.new_records
    }


def test_paused_entry_of_a_removed_worktree_is_cleared_without_action() -> None:
    # Clauses: a paused position resumes at the first pass where its spend is back
    # under its share, and a record names an action the controller took. A worktree
    # the configuration no longer lists is not held paused by the controller.
    # Rejects the mutation that keeps the paused entry of a removed worktree: when
    # the worktree returns under its share it would be sent `continue`, with a RESUME
    # record for a pause the operator's configuration had ended.
    module = load_control_positions()
    watched, other = alpha_positions(2)
    config = ConfigSpec((watched, other))
    position_share = share(PACE_TOKENS, 2)
    heavy = PassStep(
        tokens={watched.worktree: tokens_above(position_share, PAUSE_MULTIPLE)}
    )
    removed = PassStep(config=ConfigSpec((other,)))
    returned = PassStep(
        config=config, tokens={watched.worktree: tokens_under(position_share)}
    )

    _, paused, during, after = run_passes(
        module, config, [heavy, heavy, removed, returned]
    )

    assert keys_of(paused) == [(watched.pane, ESCAPE_KEY)]
    assert not [call for call in during.calls if call.pane == watched.pane]
    assert not during.new_records
    assert not [
        call
        for call in after.calls
        if call.pane == watched.pane and call.operation in {"key", "send"}
    ]
    assert module.Action.RESUME not in {
        record[module.RecordField.ACTION] for record in after.records
    }


# Sibling modules and the process. Clause: every collaborator is replaceable and a
# pass acts only through its data root and the Prowl operations (the clause that the
# controller reads token counts through the consumption-control parser and acts on
# panes through the Prowl operation surface by a `__file__`-relative import; the node
# declares no clause about a pass leaving the process untouched, so this is the
# closest). The controller loads a sibling skill's script to measure and to act; that
# load must leave the module registry of the process as the pass found it.


def test_a_pass_leaves_the_sibling_module_registry_as_it_found_it() -> None:
    # Clause: the controller reads tokens only through the consumption-control parser
    # and acts on panes only through the Prowl adapter, each loaded from a sibling
    # skill by a `__file__`-relative path. Rejects the mutation that leaves the loaded
    # sibling registered in `sys.modules` under its bare name (added name), for the
    # controller loaded from the authored tree and from the built tree, on the token
    # step, the data-root lookup, and the Prowl adapter load, through `run_pass` and
    # through `main`.
    positions = alpha_positions(2)
    config = ConfigSpec(positions)

    for built in (False, True):
        module = load_control_positions(built=built)
        for via_main in (False, True):
            step = PassStep(
                contexts={
                    item.worktree: COMPACTION_CONTEXT_PERCENT for item in positions
                },
                token_source=module.ConsumptionTokens(),
            )

            with sibling_registry(module) as registry:
                lookup = module.default_collaborators()
                (observed,) = run_passes(module, config, [step], via_main=via_main)

            leaked = {
                name
                for name in registry.names
                if registry.after[name] is not registry.before[name]
            }
            assert leaked == set(), (built, via_main)
            assert isinstance(lookup.data_root, Path)
            assert observed.error is None, (built, via_main)
            assert {
                report.subject
                for report in observed.reports
                if report.kind == module.ReportKind.UNMEASURED_PACE
            } == {item.worktree for item in positions}, (built, via_main)
            assert {
                call.pane for call in observed.calls if call.operation == "send"
            } == {item.pane for item in positions}, (built, via_main)


def test_a_pass_neither_replaces_nor_removes_a_module_registered_under_a_sibling_name() -> (
    None
):
    # Clause: as above. Rejects the mutation that discards the registration of a
    # sibling name before importing the sibling, replacing a module another part of
    # the process registered under that name (replaced module object), for the
    # controller loaded from the authored tree and from the built tree.
    positions = alpha_positions(2)
    config = ConfigSpec(positions)

    for built in (False, True):
        module = load_control_positions(built=built)
        step = PassStep(
            contexts={item.worktree: COMPACTION_CONTEXT_PERCENT for item in positions},
            token_source=module.ConsumptionTokens(),
        )

        with sibling_registry(module, foreign=True) as registry:
            module.default_collaborators()
            (observed,) = run_passes(module, config, [step])

        loaded = {module.TOKEN_ACCOUNTING[1], module.PROWL_ADAPTER[1]}
        replaced = {
            name for name in loaded if registry.after[name] is not registry.before[name]
        }
        leaked = {
            name
            for name in registry.names
            if registry.after[name] is not registry.before[name]
        }
        assert replaced == set(), built
        assert leaked == set(), built
        assert observed.error is None, built
        assert {call.pane for call in observed.calls if call.operation == "send"} == {
            item.pane for item in positions
        }, built
