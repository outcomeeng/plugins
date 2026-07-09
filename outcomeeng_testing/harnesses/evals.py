"""Harnesses for eval CI execution evidence."""

from __future__ import annotations

from collections.abc import Callable, Sequence

from hypothesis import given, seed, settings

from outcomeeng_evals.ci_execution import (
    CASE_ID_FLAG,
    CI_RUN_SETTING_OPTIONS,
    PLUGIN_DIR_FLAG,
    UV_RUN_EVALS_ARGV_PREFIX,
    CiRunSettings,
    command_for_plan_item,
)
from outcomeeng_evals.ci_plan import EvalPlanItem
from outcomeeng_testing.generators.evals import ci_run_settings, eval_plan_items

CI_COMMAND_PROPERTY_SEED = 20260708
CI_COMMAND_PROPERTY_EXAMPLES = 60
CI_EXECUTION_MAPPING_TEST_PATH = (
    "just test "
    "spx/13-infrastructure.enabler/25-eval-harness.enabler/"
    "21-ci-execution.enabler/tests/test_ci_execution.mapping.l1.py::"
)


def ci_command_property(
    *,
    replay_test_name: str,
) -> Callable[
    [Callable[[EvalPlanItem, CiRunSettings], None]],
    Callable[[], None],
]:
    """Run CI command mapping evidence with reproducible failure diagnostics."""

    replay_path = f"{CI_EXECUTION_MAPPING_TEST_PATH}{replay_test_name}"

    def decorator(
        test_func: Callable[[EvalPlanItem, CiRunSettings], None],
    ) -> Callable[[], None]:
        configured = seed(CI_COMMAND_PROPERTY_SEED)(
            settings(max_examples=CI_COMMAND_PROPERTY_EXAMPLES, deadline=None)(
                given(item=eval_plan_items(), runtime_settings=ci_run_settings())(
                    test_func
                )
            )
        )

        def wrapper() -> None:
            try:
                configured()
            except AssertionError as error:
                error.add_note(f"Hypothesis seed: {CI_COMMAND_PROPERTY_SEED}")
                error.add_note(f"Replay path: {replay_path}")
                raise

        return wrapper

    return decorator


def assert_plan_items_map_to_run_commands_with_settings_and_case_selectors() -> None:
    """Assert generated plan items map to source-owned CI command argv shape."""

    @ci_command_property(
        replay_test_name="test_plan_items_map_to_run_commands_with_settings_and_case_selectors"
    )
    def assertion(item: EvalPlanItem, runtime_settings: CiRunSettings) -> None:
        command = command_for_plan_item(item, settings=runtime_settings)

        assert _consume_ci_command(command, item=item, settings=runtime_settings) == ()

    assertion()


def assert_multi_case_plan_item_preserves_case_selector_order() -> None:
    """Assert generated case selectors preserve item order in the command argv."""

    @ci_command_property(
        replay_test_name="test_multi_case_plan_item_preserves_case_selector_order"
    )
    def assertion(item: EvalPlanItem, runtime_settings: CiRunSettings) -> None:
        command = command_for_plan_item(item, settings=runtime_settings)

        assert _case_selector_values(command) == item.case_ids

    assertion()


def _consume_ci_command(
    command: Sequence[str],
    *,
    item: EvalPlanItem,
    settings: CiRunSettings,
) -> tuple[str, ...]:
    prefix_length = len(UV_RUN_EVALS_ARGV_PREFIX)
    assert tuple(command[:prefix_length]) == UV_RUN_EVALS_ARGV_PREFIX

    remaining = command[prefix_length:]
    assert remaining[0] == str(item.eval_toml)
    remaining = remaining[1:]

    remaining = _consume_flag_value(
        remaining,
        flag=PLUGIN_DIR_FLAG,
        value=str(item.plugin_dir),
    )
    for option in CI_RUN_SETTING_OPTIONS:
        remaining = _consume_flag_value(
            remaining,
            flag=option.flag,
            value=getattr(settings, option.setting),
        )

    for case_id in item.case_ids:
        remaining = _consume_flag_value(
            remaining,
            flag=CASE_ID_FLAG,
            value=case_id,
        )

    return tuple(remaining)


def _consume_flag_value(
    argv: Sequence[str],
    *,
    flag: str,
    value: str,
) -> Sequence[str]:
    assert len(argv) >= 2
    assert argv[0] == flag
    assert argv[1] == value
    return argv[2:]


def _case_selector_values(command: Sequence[str]) -> tuple[str, ...]:
    values: list[str] = []
    for index, token in enumerate(command):
        if token == CASE_ID_FLAG:
            values.append(command[index + 1])
    return tuple(values)
