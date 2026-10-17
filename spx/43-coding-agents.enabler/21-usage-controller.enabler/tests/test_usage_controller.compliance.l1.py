"""The usage controller's ALWAYS and NEVER rules hold against violating passes."""

import ast
import json
import os
import plistlib
import sys
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

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
    JOB_LABEL,
    NUMERIC_CONFIG_FIELDS,
    SCALAR_CONFIG_FIELDS,
    STANDARD_ERROR_PATH_KEY,
    STANDARD_OUT_PATH_KEY,
    ChangedApiTokens,
    CommandResult,
    ConfigSpec,
    PassObservation,
    PassStep,
    changed_sibling_api,
    install_observation,
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

    with real_parser_world(module) as world:
        world.add_transcript_row(position.worktree)
        assert (
            module.ConsumptionTokens().tokens(position.worktree, *world.window)
            == world.tokens_per_row
        )

        for change in sibling_api_changes():
            # The change meets the pass at its token step, the one interface the
            # controller reads from the accounting; the pass publishes its records
            # through the sibling's file publishing, which the change leaves alone.
            step = PassStep(
                contexts={position.worktree: COMPACTION_CONTEXT_PERCENT},
                token_source=ChangedApiTokens(
                    module, world.accounting, change, position.worktree
                ),
            )
            with changed_sibling_api(world.accounting, change, position.worktree):
                assert (
                    module.ConsumptionTokens().tokens(position.worktree, *world.window)
                    is None
                ), change
            (observed,) = run_passes(module, config, [step])

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


def test_inventory_that_uses_the_pass_bound_marks_unskipped_positions_unfinished_by_either_key() -> (
    None
):
    # Clause: a pass that reaches the five-minute bound records its unfinished
    # positions and leaves them to the next pass, and a pane on the skip list
    # receives no action; the skip list names a pane by title or worktree path.
    # Here the Prowl inventory call itself uses the rest of the time, so the pass
    # has read every pane title when it meets the bound. Rejects the mutation that
    # excludes only the worktree-path key from the unfinished set (a position
    # skipped by pane title is marked unfinished and ordered first in the next
    # pass), and the one that marks every configured position unfinished.
    # Limit: a pass that meets the bound before the inventory call returns has read
    # no title, and a configured position carries none, so only the worktree-path
    # key applies there (see the test above); no title store exists to consult.
    module = load_control_positions()
    positions = alpha_positions(3)
    skipped = positions[2]
    bound = PASS_BOUND_MINUTES * SECONDS_PER_MINUTE
    contexts = {item.worktree: COMPACTION_CONTEXT_PERCENT for item in positions}

    for key in (skipped.worktree, skipped.title):
        config = ConfigSpec(positions, skip=(key,))

        used, next_pass = run_passes(
            module,
            config,
            [PassStep(leading_seconds=(bound,)), PassStep(contexts=contexts)],
        )

        assert not [call for call in used.calls if call.pane == skipped.pane]
        assert set(used.unfinished) == {positions[0].worktree, positions[1].worktree}, (
            key
        )
        assert next_pass.unfinished == ()
        assert skipped.pane not in {pane for pane, _ in sends_of(next_pass)}


def _seed_plist(document: dict[str, object] | bytes) -> object:
    def seed(root: Path, plist_path: Path) -> None:
        plist_path.parent.mkdir(parents=True)
        plist_path.write_bytes(
            document if isinstance(document, bytes) else plistlib.dumps(document)
        )

    return seed


def _entry_point_name(module: object) -> str:
    return Path(module.__file__).name  # type: ignore[attr-defined]


def test_install_refuses_a_symlink_at_the_job_path_and_runs_no_launchctl_command() -> (
    None
):
    # Clause: the launchd clause (the installed job starts one finite pass). The
    # install writes the user's launch-agents directory; a link there is not an
    # artifact this controller owns. Rejects the mutation that writes through the
    # link (the link target is overwritten) and the one that refuses but still
    # loads or unloads a job.
    module = load_control_positions()
    target_bytes = b"the operator's file"

    def seed(root: Path, plist_path: Path) -> None:
        plist_path.parent.mkdir(parents=True)
        (root / "elsewhere.txt").write_bytes(target_bytes)
        plist_path.symlink_to(root / "elsewhere.txt")

    observed = install_observation(module, seed)

    assert observed.status == module.ScheduleStatus.FAILED
    assert str(observed.plist_path) in observed.detail
    assert "inspect" in observed.detail.lower()
    assert observed.files["elsewhere.txt"] == target_bytes
    assert observed.links == (observed.plist_key,)
    assert not observed.calls


def test_install_refuses_a_file_it_does_not_own_and_leaves_it_unchanged() -> None:
    # Clause: the launchd clause. A regular file at the job path is this
    # controller's only when it is a plist labelled with the job label whose
    # program arguments name the controller's entry point. Rejects the mutation that
    # replaces any file at the path, the one that checks the label only, and the one
    # that checks the entry point only.
    module = load_control_positions()
    entry = _entry_point_name(module)
    foreign_documents: list[dict[str, object] | bytes] = [
        b"not a property list",
        {"Label": "com.example.other", "ProgramArguments": ["/bin/true", entry]},
        {"Label": JOB_LABEL, "ProgramArguments": ["/bin/true", "other_script.py"]},
        {"ProgramArguments": ["/bin/true", entry]},
        {"Label": JOB_LABEL},
    ]

    for document in foreign_documents:
        original = document if isinstance(document, bytes) else plistlib.dumps(document)

        observed = install_observation(module, _seed_plist(document))  # type: ignore[arg-type]

        assert observed.status == module.ScheduleStatus.FAILED, document
        assert str(observed.plist_path) in observed.detail
        assert "inspect" in observed.detail.lower()
        assert observed.files[observed.plist_key] == original
        assert not observed.calls
        assert observed.launch_agent_entries == (observed.plist_path.name,)


def test_install_replaces_a_plist_an_earlier_install_wrote_and_loads_the_job() -> None:
    # Clause: the launchd clause. A plist an earlier install wrote, whatever
    # interpreter, location, or version wrote it, is the controller's own and is
    # replaced. Rejects the mutation that refuses every existing file (a second
    # install, or an upgrade, never completes).
    module = load_control_positions()
    earlier = {
        "Label": JOB_LABEL,
        "ProgramArguments": [
            "/old/python",
            f"/old/plugin/{_entry_point_name(module)}",
            "pass",
        ],
        "StartInterval": 60,
    }

    observed = install_observation(module, _seed_plist(earlier))

    assert observed.status == module.ScheduleStatus.SUCCEEDED, observed.detail
    document = plistlib.loads(observed.files[observed.plist_key])
    assert document["Label"] == JOB_LABEL
    assert document["ProgramArguments"] != earlier["ProgramArguments"]
    assert document["StartInterval"] == THIRTY_MINUTES_SECONDS
    assert [argv[1] for argv in observed.calls] == ["print", "bootout", "bootstrap"]


def test_failed_install_write_leaves_no_temporary_file_and_loads_nothing() -> None:
    # Clause: the launchd clause. The job file is written to a unique temporary file
    # beside it and renamed over it, so a write that fails publishes nothing and
    # leaves no stray file in the user's launch-agents directory. Rejects the
    # mutation that leaves the temporary file behind when the rename fails, and the
    # one that goes on to load the job after a failed write.
    module = load_control_positions()
    earlier = {
        "Label": JOB_LABEL,
        "ProgramArguments": [
            "/old/python",
            f"/old/plugin/{_entry_point_name(module)}",
            "pass",
        ],
    }

    observed = install_observation(module, _seed_plist(earlier), replace_fails=True)

    assert observed.status == module.ScheduleStatus.FAILED
    assert str(observed.plist_path) in observed.detail
    assert observed.launch_agent_entries == (observed.plist_path.name,)
    assert observed.files[observed.plist_key] == plistlib.dumps(earlier)
    assert not observed.calls


def test_install_checks_the_job_before_unloading_it_and_runs_launchctl_by_absolute_path() -> (
    None
):
    # Clause: the launchd clause. The install asks launchd whether the job is loaded,
    # unloads it only when it is, tolerates a "could not find service" answer as not
    # loaded, stops on any other failed answer with the command's text, and then
    # loads the new job; every command runs the absolute launchctl path. Rejects the
    # mutation that unloads without asking, the one that ignores a failed status
    # answer, and the one that finds launchctl on the search path.
    module = load_control_positions()
    not_loaded = CommandResult(113, "", "Could not find service in domain")
    broken = CommandResult(5, "", "Bootstrap failed: input/output error")

    loaded = install_observation(module)
    absent = install_observation(module, answers={"print": not_loaded})
    failing = install_observation(module, answers={"print": broken})

    assert [argv[1] for argv in loaded.calls] == ["print", "bootout", "bootstrap"]
    assert [argv[1] for argv in absent.calls] == ["print", "bootstrap"]
    assert absent.status == module.ScheduleStatus.SUCCEEDED
    assert [argv[1] for argv in failing.calls] == ["print"]
    assert failing.status == module.ScheduleStatus.FAILED
    assert broken.stderr in failing.detail
    for observed in (loaded, absent, failing):
        assert all(os.path.isabs(argv[0]) for argv in observed.calls)
        assert {argv[0] for argv in observed.calls} == {module.LAUNCHCTL}


def test_status_stop_and_restart_run_launchctl_by_absolute_path() -> None:
    # Clause: the launchd clause. Rejects the mutation that finds launchctl on the
    # search path for any scheduling operation.
    module = load_control_positions()

    for operation in module.ScheduleOperation:
        observed = schedule_observation(module, operation, "darwin")

        assert observed.calls
        assert all(os.path.isabs(argv[0]) for argv in observed.calls), operation
        assert {argv[0] for argv in observed.calls} == {module.LAUNCHCTL}


# Guards of the sibling consumption-control scripts that the position controller's own
# operations take as well. Each case compares one operation of the controller with the
# sibling function that does the same and the guard that function takes.

SIBLING_FILE_BYTES = 64 * 1024
RECORDS_DIRECTORY = "positions"
RECORD_SUFFIX = ".json"
CONFIGURATION_FILE = "control-positions.toml"
STATE_FILE = "control-positions-state.json"
VALID_POSITION = '[[positions]]\nworktree = "/work/a"\nsubscription = "alpha"\n'


def _settings_error(module: Any, text: str) -> Exception | None:
    with TemporaryDirectory(prefix="control-positions-evidence-") as temporary:
        path = Path(temporary) / CONFIGURATION_FILE
        path.write_text(text, encoding="utf-8")
        try:
            module.load_settings(path)
        except module.ConfigurationError as error:
            return error
    return None


@contextmanager
def _recorded_fsync() -> Iterator[list[int]]:
    calls: list[int] = []
    original = os.fsync

    def recording(descriptor: int) -> None:
        calls.append(descriptor)
        original(descriptor)

    os.fsync = recording
    try:
        yield calls
    finally:
        os.fsync = original


def _raised(call: Callable[[], object]) -> Exception | None:
    try:
        call()
    except (ValueError, OSError) as error:
        return error
    return None


def test_configuration_rejects_a_worktree_listed_twice_naming_the_field() -> None:
    # Clause: the configuration clause (an invalid file fails naming its field). A
    # pass keys panes, the paused set, streaks and the unfinished list by worktree, so
    # a worktree listed twice, under one subscription or under two, is invalid. Rejects
    # the mutation that accepts a duplicate entry.
    module = load_control_positions()
    for second in ("alpha", "beta"):
        duplicate = f'[[positions]]\nworktree = "/work/a"\nsubscription = "{second}"\n'

        error = _settings_error(module, VALID_POSITION + duplicate)

        assert isinstance(error, module.ConfigurationError), second
        assert error.field == module.ConfigField.WORKTREE
        assert "/work/a" in str(error)
    distinct = '[[positions]]\nworktree = "/work/b"\nsubscription = "alpha"\n'
    assert _settings_error(module, VALID_POSITION + distinct) is None


def test_configuration_rejects_an_empty_skip_entry_naming_the_field() -> None:
    # Clause: the configuration clause. An empty skip entry names no pane title or
    # worktree path. Rejects the mutation that accepts it.
    module = load_control_positions()

    error = _settings_error(module, 'skip = ["pane", ""]\n' + VALID_POSITION)

    assert isinstance(error, module.ConfigurationError)
    assert error.field == module.ConfigField.SKIP
    assert _settings_error(module, 'skip = ["pane"]\n' + VALID_POSITION) is None


def test_configuration_refuses_a_symlinked_or_oversized_file() -> None:
    # Clause: the configuration clause. The sibling controller refuses a symlinked
    # configuration file and one over 64 KiB; the position controller's file takes the
    # same guards. Rejects the mutation that follows a link or parses any size.
    module = load_control_positions()
    with TemporaryDirectory(prefix="control-positions-evidence-") as temporary:
        root = Path(temporary)
        real = root / "real.toml"
        real.write_text(VALID_POSITION, encoding="utf-8")
        linked = root / CONFIGURATION_FILE
        linked.symlink_to(real)
        oversized = root / "oversized.toml"
        oversized.write_text(
            VALID_POSITION + "# " + "x" * SIBLING_FILE_BYTES + "\n", encoding="utf-8"
        )

        assert len(module.load_settings(real).positions) == 1
        for refused in (linked, oversized):
            error = _raised(lambda: module.load_settings(refused))
            assert isinstance(error, module.ConfigurationError), refused.name
            assert str(refused) in str(error)


def test_records_are_numbered_after_the_highest_and_published_durably() -> None:
    # Clause: the durable-record clause. A record is published as the sibling
    # publishes a file: through a unique temporary file, an fsync, and a rename, never
    # replacing a record. Numbering follows the highest number on disk, so a gap in
    # the numbers neither hides a record nor sends the next one back to number one.
    # Rejects the mutation that skips the fsync, and the one that probes from one.
    module = load_control_positions()
    with TemporaryDirectory(prefix="control-positions-evidence-") as temporary:
        root = Path(temporary)
        directory = root / RECORDS_DIRECTORY
        directory.mkdir()
        for number in (1, 5):
            (directory / f"{number:08d}{RECORD_SUFFIX}").write_text(
                json.dumps({"n": number}), encoding="utf-8"
            )
        before = (directory / f"00000001{RECORD_SUFFIX}").read_bytes()

        with _recorded_fsync() as synced:
            written = module.append_record(root, {"n": 6})

        assert written.name == f"00000006{RECORD_SUFFIX}"
        assert synced
        assert (directory / f"00000001{RECORD_SUFFIX}").read_bytes() == before
        assert sorted(item.name for item in directory.iterdir()) == [
            f"{number:08d}{RECORD_SUFFIX}" for number in (1, 5, 6)
        ]
        assert [record["n"] for record in module.read_records(root)] == [1, 5, 6]


def test_a_symlinked_record_is_refused_on_read_and_never_written_through() -> None:
    # Clause: the durable-record clause. The sibling refuses a symlinked state file;
    # a record that is a link is refused on read, and a link planted at the next
    # number is never written through. Rejects the mutation that follows a link.
    module = load_control_positions()
    with TemporaryDirectory(prefix="control-positions-evidence-") as temporary:
        root = Path(temporary)
        directory = root / RECORDS_DIRECTORY
        directory.mkdir()
        victim = root / "victim.json"
        victim.write_text(json.dumps({"victim": True}), encoding="utf-8")
        (directory / f"00000001{RECORD_SUFFIX}").symlink_to(victim)

        error = _raised(lambda: module.read_records(root))
        assert error is not None
        assert f"00000001{RECORD_SUFFIX}" in str(error)

        (directory / f"00000002{RECORD_SUFFIX}").symlink_to(root / "absent.json")
        _raised(lambda: module.append_record(root, {"n": 3}))
        assert json.loads(victim.read_text(encoding="utf-8")) == {"victim": True}
        assert not (root / "absent.json").exists()


def test_state_is_published_durably_and_never_through_a_link() -> None:
    # Clause: the cross-pass state of the pause and resume clause. The state file is
    # published as the sibling publishes a file (unique temporary file, fsync, rename)
    # and a symlinked state file is refused as the sibling refuses it. Rejects the
    # mutation that writes a fixed temporary name a link can redirect, the one that
    # skips the fsync, and the one that replaces a linked state file.
    module = load_control_positions()
    state = module.PassState(streaks={"/work/a": 2}, paused={"/work/a"})
    with TemporaryDirectory(prefix="control-positions-evidence-") as temporary:
        root = Path(temporary)
        victim = root / "victim.txt"
        victim.write_text("untouched", encoding="utf-8")
        (root / "control-positions-state.tmp").symlink_to(victim)

        with _recorded_fsync() as synced:
            module.save_state(root, state)

        assert synced
        assert victim.read_text(encoding="utf-8") == "untouched"
        assert module.load_state(root).paused == {"/work/a"}

    with TemporaryDirectory(prefix="control-positions-evidence-") as temporary:
        root = Path(temporary)
        victim = root / "victim.json"
        victim.write_text("{}", encoding="utf-8")
        (root / STATE_FILE).symlink_to(victim)

        error = _raised(lambda: module.save_state(root, state))

        assert error is not None
        assert (root / STATE_FILE).is_symlink()
        assert victim.read_text(encoding="utf-8") == "{}"


def test_state_that_is_linked_or_malformed_is_refused_not_read_as_empty() -> None:
    # Clause: the pause and resume clause. Empty state would forget a paused position
    # for good, so a symlinked or malformed state file stops the pass with a message
    # naming the file, as the sibling refuses a symlinked state. An absent file is a
    # first pass and reads as empty. Rejects the mutation that reads either as empty.
    module = load_control_positions()
    with TemporaryDirectory(prefix="control-positions-evidence-") as temporary:
        root = Path(temporary)
        assert module.load_state(root).paused == set()
        (root / STATE_FILE).write_text("{not json", encoding="utf-8")

        malformed = _raised(lambda: module.load_state(root))

        assert malformed is not None
        assert str(root / STATE_FILE) in str(malformed)

    with TemporaryDirectory(prefix="control-positions-evidence-") as temporary:
        root = Path(temporary)
        real = root / "real.json"
        real.write_text(json.dumps({"paused": ["/work/a"]}), encoding="utf-8")
        (root / STATE_FILE).symlink_to(real)

        linked = _raised(lambda: module.load_state(root))

        assert linked is not None
        assert str(root / STATE_FILE) in str(linked)


def test_default_runner_bounds_captured_output_and_kills_a_hung_command() -> None:
    # Clause: the time-bound clause. The sibling runner kills a command at its
    # deadline and bounds the bytes it captures to 64 KiB; the position controller's
    # default runner does both. Rejects the mutation that captures without bound.
    module = load_control_positions()
    runner = module.SubprocessRunner()

    flooded = runner.run((sys.executable, "-c", "print('x' * 1_000_000)"))
    started = time.monotonic()
    hung = runner.run(
        (sys.executable, "-c", "import time; time.sleep(60)"), timeout_seconds=1
    )
    waited = time.monotonic() - started

    flooded_code = flooded.returncode
    flooded_bytes = len(flooded.stdout) + len(flooded.stderr)
    hung_code = hung.returncode
    assert flooded_code == module.UNREADABLE_EXIT_CODE
    assert flooded_bytes <= SIBLING_FILE_BYTES
    assert hung_code == module.UNREADABLE_EXIT_CODE
    assert waited < 30


def test_controller_scripts_reach_sibling_operations_without_restating_them() -> None:
    # Clause: the last ALWAYS clause (the controller reaches the sibling scripts by a
    # file-relative import). The atomic write and the bounded subprocess run belong to
    # the sibling consumption-control scripts, so the position controller's modules
    # import neither the temporary-file nor the subprocess machinery and call neither
    # the rename nor the fsync themselves. Rejects the mutation that restates them.
    module = load_control_positions()
    scripts = Path(module.__file__).parent
    forbidden_modules = {"tempfile", "subprocess", "selectors"}
    forbidden_calls = {("os", "replace"), ("os", "fsync")}
    for name in ("positions_store", "positions_schedule", "control_positions"):
        tree = ast.parse((scripts / f"{name}.py").read_text(encoding="utf-8"))
        imported = {
            alias.name.split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        } | {
            (node.module or "").split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
        }
        called = {
            (node.func.value.id, node.func.attr)
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
        }
        assert not imported & forbidden_modules, name
        assert not called & forbidden_calls, name
