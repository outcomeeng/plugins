"""One run of the control-positions entry point records each action the configuration selects."""

from outcomeeng_testing.generators.control_positions import (
    ALPHA,
    BETA,
    CEILING_MAXIMUM_PERCENT,
    COMPACTION_CONTEXT_PERCENT,
    LOW_CONTEXT_PERCENT,
    PACE_TOKENS,
    PAUSE_MULTIPLE,
    WEEKLY_CEILING_PERCENT,
    PositionSpec,
    share,
    tokens_above,
    tokens_under,
)
from outcomeeng_testing.harnesses.control_positions import (
    ConfigSpec,
    PassStep,
    load_control_positions,
    run_passes,
    with_config,
)

CONTEXT_PERCENT = COMPACTION_CONTEXT_PERCENT


def slice_world() -> tuple[ConfigSpec, tuple[PositionSpec, ...]]:
    compacted = PositionSpec(1, ALPHA)
    paced = PositionSpec(2, ALPHA)
    skipped = PositionSpec(3, ALPHA)
    herdr = PositionSpec(4, ALPHA, in_prowl=False)
    stopped_one = PositionSpec(5, BETA)
    stopped_two = PositionSpec(6, BETA)
    positions = (compacted, paced, skipped, herdr, stopped_one, stopped_two)
    return ConfigSpec(positions, skip=(skipped.worktree,)), positions


def test_pass_records_compaction_pause_resume_and_stop_for_the_configured_world() -> (
    None
):
    module = load_control_positions()
    config, positions = slice_world()
    compacted, paced, skipped, herdr, stopped_one, stopped_two = positions
    measured_share = share(PACE_TOKENS, 2)
    heavy = tokens_above(measured_share, PAUSE_MULTIPLE)
    light = tokens_under(measured_share)
    contexts = {
        compacted.worktree: CONTEXT_PERCENT,
        paced.worktree: LOW_CONTEXT_PERCENT,
        skipped.worktree: 90,
        herdr.worktree: 90,
    }
    first = PassStep(
        contexts=contexts,
        weekly={ALPHA: 0, BETA: WEEKLY_CEILING_PERCENT + 1},
        tokens={paced.worktree: heavy, compacted.worktree: light},
    )
    second = PassStep(
        contexts=contexts,
        tokens={paced.worktree: heavy, compacted.worktree: light},
    )
    third = PassStep(tokens={paced.worktree: light, compacted.worktree: light})

    passes = run_passes(module, config, [first, second, third], via_main=True)

    action = module.Action
    field = module.RecordField

    def recorded(index: int) -> set[tuple[str, str]]:
        return {
            (record[field.ACTION], record[field.POSITION])
            for record in passes[index].new_records
        }

    assert {pass_.exit_code for pass_ in passes} == {0}
    assert (action.COMPACT, compacted.worktree) in recorded(0)
    assert {
        (action.STOP, stopped_one.worktree),
        (action.STOP, stopped_two.worktree),
    } <= recorded(0)
    assert (action.PAUSE, paced.worktree) in recorded(1)
    assert (action.RESUME, paced.worktree) in recorded(2)
    assert not [
        call
        for pass_ in passes
        for call in pass_.calls
        if call.pane in {skipped.pane, herdr.pane}
    ]
    assert {record[field.POSITION] for record in passes[-1].records}.isdisjoint(
        {skipped.worktree, herdr.worktree}
    )


def test_pass_without_the_stop_authorization_stops_nothing_and_reports_why() -> None:
    module = load_control_positions()
    config, _ = slice_world()
    unauthorized = with_config(config, stop_authorized=False)
    step = PassStep(weekly={ALPHA: 0, BETA: WEEKLY_CEILING_PERCENT + 1})

    (observed,) = run_passes(module, unauthorized, [step])

    assert not [call for call in observed.calls if call.operation == "send"]
    assert module.Action.STOP not in {
        record[module.RecordField.ACTION] for record in observed.records
    }
    assert module.ReportKind.STOP_UNAUTHORIZED in {
        report.kind for report in observed.reports
    }


def test_pass_with_a_ceiling_above_the_maximum_is_rejected_before_any_action() -> None:
    module = load_control_positions()
    config, _ = slice_world()
    rejected = with_config(config, weekly_ceiling_percent=CEILING_MAXIMUM_PERCENT + 1)
    step = PassStep(weekly={BETA: 100}, contexts={})

    (observed,) = run_passes(module, rejected, [step])

    assert isinstance(observed.error, module.ConfigurationError)
    assert observed.error.field == module.ConfigField.WEEKLY_CEILING_PERCENT
    assert not observed.calls
    assert not observed.records
