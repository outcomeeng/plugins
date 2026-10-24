"""CLI entry point for marketplace verification recipes.

Usage::

    python3 -m outcomeeng.validation check
    python3 -m outcomeeng.validation check-full
    python3 -m outcomeeng.validation validation
    python3 -m outcomeeng.validation test -- -k gate
    python3 -m outcomeeng.validation test-on-demand

Constructs the production `ProcessSpawner` adapter, binds the output sink
to stdout, and runs the selected recipe. Returns the orchestrator's exit
code; signal delivery propagates as `128 + signum` per the runner.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import TextIO

from outcomeeng.validation import ProcessSpawner, ProductionSpawner, run_recipe
from outcomeeng.validation.selected_gate import (
    RECIPE_CHECK_FULL,
    run_full_check,
    run_selected_check,
)
from outcomeeng.validation._steps import (
    RECIPE_CHECK,
    RECIPE_TEST,
    RECIPE_TEST_ON_DEMAND,
    RECIPE_VALIDATION,
    VALIDATION_RECIPE,
    discover_on_demand_tests,
    on_demand_recipe,
    test_recipe,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python3 -m outcomeeng.validation")
    parser.add_argument(
        "recipe",
        nargs="?",
        choices=(
            RECIPE_CHECK,
            RECIPE_CHECK_FULL,
            RECIPE_VALIDATION,
            RECIPE_TEST,
            RECIPE_TEST_ON_DEMAND,
        ),
        default=RECIPE_CHECK,
    )
    parser.add_argument("recipe_args", nargs=argparse.REMAINDER)
    return parser


def _recipe_args(args: list[str]) -> tuple[str, ...]:
    if args and args[0] == "--":
        return tuple(args[1:])
    return tuple(args)


def main(
    argv: list[str] | None = None,
    *,
    spawner: ProcessSpawner | None = None,
    sink: TextIO | None = None,
    repo: Path | None = None,
) -> int:
    """Run the recipe ``argv`` selects.

    The spawner, output sink, and repository root default to the production
    adapter, stdout, and the current directory; a caller injects each to run
    the same dispatch against recorded spawns and another repository.
    """

    parsed = _parser().parse_args(argv)
    bound_spawner = spawner if spawner is not None else ProductionSpawner()
    bound_sink = sink if sink is not None else sys.stdout
    bound_repo = repo if repo is not None else Path.cwd()
    if parsed.recipe == RECIPE_VALIDATION:
        return run_recipe(
            spawner=bound_spawner, sink=bound_sink, recipe=VALIDATION_RECIPE
        )
    if parsed.recipe == RECIPE_TEST:
        return run_recipe(
            spawner=bound_spawner,
            sink=bound_sink,
            recipe=test_recipe(_recipe_args(parsed.recipe_args)),
        )
    if parsed.recipe == RECIPE_TEST_ON_DEMAND:
        return run_recipe(
            spawner=bound_spawner,
            sink=bound_sink,
            recipe=on_demand_recipe(discover_on_demand_tests(bound_repo)),
        )
    if parsed.recipe == RECIPE_CHECK_FULL:
        return run_full_check(spawner=bound_spawner, sink=bound_sink, repo=bound_repo)
    return run_selected_check(spawner=bound_spawner, sink=bound_sink, repo=bound_repo)


if __name__ == "__main__":
    raise SystemExit(main())
