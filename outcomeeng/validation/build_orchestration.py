"""Validate build orchestration wiring for committed runtime trees."""

from __future__ import annotations

import sys
from pathlib import Path

from outcomeeng.distribution.orchestration import check_build_orchestration


def main(argv: list[str] | None = None) -> int:
    """Run build orchestration validation for a repository root."""

    args = argv if argv is not None else sys.argv[1:]
    root = Path(args[0]) if args else Path(".")

    errors = check_build_orchestration(root)
    for message in errors:
        print(f"error: build orchestration: {message}", file=sys.stderr)

    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
