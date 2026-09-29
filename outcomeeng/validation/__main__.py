"""CLI entry point for marketplace verification recipes.

Usage::

    python3 -m outcomeeng.validation check
    python3 -m outcomeeng.validation check-full
    python3 -m outcomeeng.validation validation
    python3 -m outcomeeng.validation test -- -k gate

Constructs the production `ProcessSpawner` adapter, binds the output sink
to stdout, and runs the selected recipe; a caller may inject both. Returns
the orchestrator's exit code; signal delivery propagates as `128 + signum`
per the runner.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Final, TextIO

from outcomeeng.validation import (
    ProcessSpawner,
    ProductionSpawner,
    run_check,
    run_recipe,
)
from outcomeeng.validation.selected_gate import RECIPE_CHECK_FULL, run_selected_check
from outcomeeng.validation._steps import (
    CHECK_RECIPES,
    RECIPE_CHECK,
    RECIPE_TEST,
    RECIPE_VALIDATION,
    VALIDATION_RECIPE,
    test_recipe,
)

# The token that ends the entry point's own arguments; every argument after it
# is forwarded to the selected recipe.
RECIPE_ARGS_SEPARATOR: Final = "--"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python3 -m outcomeeng.validation")
    parser.add_argument(
        "recipe",
        nargs="?",
        choices=(RECIPE_CHECK, RECIPE_CHECK_FULL, RECIPE_VALIDATION, RECIPE_TEST),
        default=RECIPE_CHECK,
    )
    parser.add_argument("recipe_args", nargs=argparse.REMAINDER)
    return parser


def _recipe_args(args: list[str]) -> tuple[str, ...]:
    if args and args[0] == RECIPE_ARGS_SEPARATOR:
        return tuple(args[1:])
    return tuple(args)


def main(
    argv: list[str] | None = None,
    *,
    spawner: ProcessSpawner | None = None,
    sink: TextIO | None = None,
) -> int:
    parsed = _parser().parse_args(argv)
    process_spawner = spawner if spawner is not None else ProductionSpawner()
    output = sink if sink is not None else sys.stdout
    if parsed.recipe == RECIPE_VALIDATION:
        return run_recipe(
            spawner=process_spawner, sink=output, recipe=VALIDATION_RECIPE
        )
    if parsed.recipe == RECIPE_TEST:
        return run_recipe(
            spawner=process_spawner,
            sink=output,
            recipe=test_recipe(_recipe_args(parsed.recipe_args)),
        )
    if parsed.recipe == RECIPE_CHECK_FULL:
        return run_check(spawner=process_spawner, sink=output, recipes=CHECK_RECIPES)
    return run_selected_check(spawner=process_spawner, sink=output, repo=Path.cwd())


if __name__ == "__main__":
    raise SystemExit(main())
