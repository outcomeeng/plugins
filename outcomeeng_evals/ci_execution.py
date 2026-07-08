"""Python-owned execution for CI eval plans."""

from __future__ import annotations

import subprocess
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Final

from outcomeeng_evals.ci_plan import EvalPlanItem

UV_RUN_EVALS_ARGV_PREFIX: Final = ("uv", "run", "outcomeeng-evals", "run")
DEFAULT_CI_WORKERS: Final = "1"
DEFAULT_CI_MAX_BUDGET_USD: Final = "0.50"
DEFAULT_CI_TIMEOUT_SECONDS: Final = "120"
EXIT_SUCCESS: Final = 0
EXIT_FAILURE: Final = 1


@dataclass(frozen=True)
class CiRunSettings:
    """Cost and runtime settings for CI eval execution."""

    workers: str = DEFAULT_CI_WORKERS
    max_budget_usd: str = DEFAULT_CI_MAX_BUDGET_USD
    timeout_seconds: str = DEFAULT_CI_TIMEOUT_SECONDS


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
        "--plugin-dir",
        str(item.plugin_dir),
        "--workers",
        settings.workers,
        "--max-budget-usd",
        settings.max_budget_usd,
        "--timeout-seconds",
        settings.timeout_seconds,
    ]
    for case_id in item.case_ids:
        command.extend(("--case-id", case_id))
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
