"""CLI entry point for marketplace verification recipes.

Usage::

    python3 -m outcomeeng.validation check
    python3 -m outcomeeng.validation validation
    python3 -m outcomeeng.validation test -- -k gate

Constructs the production `ProcessSpawner` adapter, binds the output sink
to stdout, and runs the selected recipe. Returns the orchestrator's exit
code; signal delivery propagates as `128 + signum` per the runner.
"""

from __future__ import annotations

import argparse
import sys

from outcomeeng.validation import ProductionSpawner, run_check, run_recipe
from outcomeeng.validation._steps import (
    CHECK_RECIPES,
    RECIPE_CHECK,
    RECIPE_TEST,
    RECIPE_VALIDATION,
    VALIDATION_RECIPE,
    test_recipe,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python3 -m outcomeeng.validation")
    parser.add_argument(
        "recipe",
        nargs="?",
        choices=(RECIPE_CHECK, RECIPE_VALIDATION, RECIPE_TEST),
        default=RECIPE_CHECK,
    )
    parser.add_argument("recipe_args", nargs=argparse.REMAINDER)
    return parser


def _recipe_args(args: list[str]) -> tuple[str, ...]:
    if args and args[0] == "--":
        return tuple(args[1:])
    return tuple(args)


def main(argv: list[str] | None = None) -> int:
    parsed = _parser().parse_args(argv)
    spawner = ProductionSpawner()
    if parsed.recipe == RECIPE_VALIDATION:
        return run_recipe(spawner=spawner, sink=sys.stdout, recipe=VALIDATION_RECIPE)
    if parsed.recipe == RECIPE_TEST:
        return run_recipe(
            spawner=spawner,
            sink=sys.stdout,
            recipe=test_recipe(_recipe_args(parsed.recipe_args)),
        )
    return run_check(spawner=spawner, sink=sys.stdout, recipes=CHECK_RECIPES)


if __name__ == "__main__":
    raise SystemExit(main())
