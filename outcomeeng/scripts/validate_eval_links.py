"""Marketplace gate: every ``[eval](path)`` link resolves to an existing eval.toml.

Walks the project's spec tree, finds every ``[eval](path)`` reference in
markdown files, and asserts each target is an existing ``eval.toml``.
Exit 0 when all links resolve, exit 1 otherwise. Wired into ``just check``.
"""

from __future__ import annotations

import sys
from pathlib import Path

from outcomeeng_testing.evals.link_integrity import (
    BrokenEvalLink,
    validate_eval_links,
)


SPEC_TREE_ROOT = "spx"


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    root = Path(args[0]) if args else Path(SPEC_TREE_ROOT)
    if not root.is_dir():
        print(f"validate_eval_links: directory not found: {root}", file=sys.stderr)
        return 1
    broken = validate_eval_links(root)
    if not broken:
        return 0
    _report(broken)
    return 1


def _report(broken: list[BrokenEvalLink]) -> None:
    for entry in broken:
        print(
            f"BROKEN [eval] link in {entry.source}: {entry.target} — {entry.reason}",
            file=sys.stderr,
        )


if __name__ == "__main__":
    sys.exit(main())
