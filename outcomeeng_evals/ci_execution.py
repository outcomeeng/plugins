"""Python-owned execution for CI eval plans."""

from __future__ import annotations

import subprocess
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Final, Literal

from outcomeeng_evals.ci_plan import EvalPlanItem

UV_RUN_EVALS_ARGV_PREFIX: Final = ("uv", "run", "outcomeeng-evals", "run")
PLUGIN_DIR_FLAG: Final = "--plugin-dir"
CASE_ID_FLAG: Final = "--case-id"
DEFAULT_CI_WORKERS: Final = "1"
DEFAULT_CI_MAX_BUDGET_USD: Final = "0.50"
DEFAULT_CI_TIMEOUT_SECONDS: Final = "120"
EXIT_SUCCESS: Final = 0
EXIT_FAILURE: Final = 1
CiRunSettingName = Literal["workers", "max_budget_usd", "timeout_seconds"]


@dataclass(frozen=True)
class CiRunSettingOption:
    """Source-owned argv flag for one CI runtime setting."""

    flag: str
    setting: CiRunSettingName


@dataclass(frozen=True)
class CiRunSettings:
    """Cost and runtime settings for CI eval execution."""

    workers: str = DEFAULT_CI_WORKERS
    max_budget_usd: str = DEFAULT_CI_MAX_BUDGET_USD
    timeout_seconds: str = DEFAULT_CI_TIMEOUT_SECONDS


CI_RUN_SETTING_OPTIONS: Final = (
    CiRunSettingOption(flag="--workers", setting="workers"),
    CiRunSettingOption(flag="--max-budget-usd", setting="max_budget_usd"),
    CiRunSettingOption(flag="--timeout-seconds", setting="timeout_seconds"),
)


@dataclass(frozen=True)
class CiExecutionResult:
    """Aggregate result for a CI eval plan execution."""

    exit_code: int
    attempted: int
    failed: tuple[EvalPlanItem, ...]


CommandRunner = Callable[[Sequence[str]], int]


def command_for_plan_item(
    item: EvalPlanItem,
    *,
    settings: CiRunSettings,
) -> tuple[str, ...]:
    """Build the source-owned argv for one planned eval suite."""

    command: list[str] = [
        *UV_RUN_EVALS_ARGV_PREFIX,
        str(item.eval_toml),
        PLUGIN_DIR_FLAG,
        str(item.plugin_dir),
    ]
    for option in CI_RUN_SETTING_OPTIONS:
        command.extend((option.flag, _ci_run_setting_value(settings, option.setting)))
    for case_id in item.case_ids:
        command.extend((CASE_ID_FLAG, case_id))
    return tuple(command)


def execute_ci_plan(
    plan: Sequence[EvalPlanItem],
    *,
    settings: CiRunSettings,
    runner: CommandRunner | None = None,
) -> CiExecutionResult:
    """Run every selected eval suite and aggregate failures."""

    command_runner = runner or _run_subprocess
    failed: list[EvalPlanItem] = []
    for item in plan:
        return_code = command_runner(command_for_plan_item(item, settings=settings))
        if return_code != EXIT_SUCCESS:
            failed.append(item)
    return CiExecutionResult(
        exit_code=EXIT_FAILURE if failed else EXIT_SUCCESS,
        attempted=len(plan),
        failed=tuple(failed),
    )


def _run_subprocess(command: Sequence[str]) -> int:
    completed = subprocess.run(command, check=False)
    return completed.returncode


def _ci_run_setting_value(
    settings: CiRunSettings,
    setting: CiRunSettingName,
) -> str:
    match setting:
        case "workers":
            return settings.workers
        case "max_budget_usd":
            return settings.max_budget_usd
        case "timeout_seconds":
            return settings.timeout_seconds
