"""CLI entry point for the marketplace quality gate.

Usage::

    uv run python -m outcomeeng.validation

Constructs the production `ProcessSpawner` adapter, binds the output sink
to stdout, and runs the declared step list. Returns the orchestrator's
exit code; signal delivery propagates as `128 + signum` per the runner.
"""

from __future__ import annotations

import sys

from outcomeeng.validation import STEPS, ProductionSpawner, run


def main() -> int:
    return run(spawner=ProductionSpawner(), sink=sys.stdout, steps=STEPS)


if __name__ == "__main__":
    raise SystemExit(main())
