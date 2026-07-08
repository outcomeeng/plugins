"""Marketplace gate: every evidence link resolves to its target file.

Walks the project's spec tree, finds every ``[eval](path)`` and
``[test](path)`` reference in markdown files, and asserts each target
exists and matches its expected shape (``eval.toml`` for eval links,
pytest collectable for test links). Exit 0 when all links resolve,
exit 1 otherwise. Wired into ``just check-full``.
"""

from __future__ import annotations

import sys
from pathlib import Path

from outcomeeng_testing.evals.link_integrity import (
    BrokenEvalLink,
    BrokenTestLink,
    validate_eval_links,
    validate_test_links,
)


SPEC_TREE_ROOT = "spx"


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    root = Path(args[0]) if args else Path(SPEC_TREE_ROOT)
    if not root.is_dir():
        print(f"validate_eval_links: directory not found: {root}", file=sys.stderr)
        return 1
    broken_eval = validate_eval_links(root)
    broken_test = validate_test_links(root)
    if not broken_eval and not broken_test:
        return 0
    _report_eval(broken_eval)
    _report_test(broken_test)
    return 1


def _report_eval(broken: list[BrokenEvalLink]) -> None:
    for entry in broken:
        print(
            f"BROKEN [eval] link in {entry.source}: {entry.target} — {entry.reason}",
            file=sys.stderr,
        )


def _report_test(broken: list[BrokenTestLink]) -> None:
    for entry in broken:
        print(
            f"BROKEN [test] link in {entry.source}: {entry.target} — {entry.reason}",
            file=sys.stderr,
        )


if __name__ == "__main__":
    sys.exit(main())
