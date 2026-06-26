"""Classify the current changeset for /merge transport selection.

Reports whether the changeset is coordination-note-only — every changed path a
`PLAN.md` or `ISSUES.md` — over the full changed-file set (committed branch
scope plus uncommitted working-tree changes), with counts computed over the
whole set so a large changeset is never misclassified from a truncated sample.

Base-ref resolution and committed branch-scope derivation route through the
canonical `changeset_scope` module — never re-implemented here — per the
`scope-changeset` skill's contract.
Working-tree status is /merge's own concern: `changeset_scope` owns committed
diff scope against the remote-tracking base only, not the uncommitted index.

Portability: stdlib only — no third-party packages, no `uv`, no `outcomeeng_*`
imports. This script ships into consumer plugin trees where only the standard
library is available.

Tested inputs and error cases: `test_classify_changeset.scenario.l1.py`
exercises coordination-note-only, mixed, empty, and duplicate path sets;
positive and negative `PLAN.md` / `ISSUES.md` basename recognition; importlib
loading of the co-located `changeset_scope.py`; end-to-end changed-path
delegation through `detect_base_ref` and `branch_scope`; and git porcelain
records for paths containing spaces before this script is bundled.
"""

from __future__ import annotations

import importlib.util
import pathlib
import re
import subprocess
import sys
from types import ModuleType

COORDINATION_NOTE_BASENAMES = ("PLAN.md", "ISSUES.md")
_COORDINATION_NOTE = re.compile(
    r"(^|/)("
    + "|".join(re.escape(name) for name in COORDINATION_NOTE_BASENAMES)
    + r")$"
)
_CHANGESET_SCOPE_RELPATH = ("scope-changeset", "scripts", "changeset_scope.py")
_PREVIEW_LIMIT = 40


def _load_changeset_scope() -> ModuleType:
    """Load the sibling `changeset_scope` module via the co-location convention.

    The module lives at `plugins/spec-tree/skills/scope-changeset/scripts/
    changeset_scope.py`, resolved relative to this script so no path is
    hard-coded in agent prose. Cached in `sys.modules` so repeated loads in one
    process reuse the same module object.
    """
    cached = sys.modules.get("changeset_scope")
    if cached is not None:
        return cached
    skills_dir = pathlib.Path(__file__).resolve().parent.parent.parent
    path = skills_dir.joinpath(*_CHANGESET_SCOPE_RELPATH)
    spec = importlib.util.spec_from_file_location("changeset_scope", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load changeset_scope from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["changeset_scope"] = module
    spec.loader.exec_module(module)
    return module


def _working_tree_paths(repo: pathlib.Path) -> list[str]:
    """Return paths with uncommitted changes, NUL-parsed and unquoted.

    `git status --porcelain -z` emits unquoted, NUL-separated records — the same
    path spelling `git diff --name-only` (and therefore `changeset_scope`)
    produces, so working-tree and committed paths de-duplicate. Without `-z`,
    git C-quotes any path containing a space or non-ASCII character (`"a b.md"`
    with literal quotes), which both breaks the coordination-note match and
    defeats de-duplication against the committed scope.

    Each record is `XY <path>`; a rename or copy record (`R`/`C` in the status)
    is followed by a separate NUL field carrying the source path, which is
    consumed and discarded so only the destination path is counted once.
    """
    result = subprocess.run(
        ["git", "status", "--porcelain", "-z"],  # noqa: S607 — git via PATH, portable helper
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )
    fields = result.stdout.split("\x00")
    paths: list[str] = []
    index = 0
    while index < len(fields):
        record = fields[index]
        index += 1
        if not record:
            continue
        status, path = record[:2], record[3:]
        if path:
            paths.append(path)
        if "R" in status or "C" in status:
            index += 1  # discard the rename/copy source path in the next field
    return paths


def is_coordination_note(path: str) -> bool:
    """True when `path`'s basename is a coordination note (`PLAN.md`/`ISSUES.md`)."""
    return _COORDINATION_NOTE.search(path) is not None


def classify(paths: list[str]) -> tuple[int, int]:
    """Return `(total, non_coordination_note_count)` over the unique path set.

    The changeset is coordination-note-only exactly when `total > 0` and the
    non-coordination-note count is `0`.
    """
    unique = sorted(set(paths))
    total = len(unique)
    noncoord = sum(1 for path in unique if not is_coordination_note(path))
    return total, noncoord


def changed_paths(repo: pathlib.Path) -> list[str]:
    """Full changed-file set: committed branch scope plus working-tree changes."""
    changeset_scope = _load_changeset_scope()
    base = changeset_scope.detect_base_ref(repo)
    committed = changeset_scope.branch_scope(base, repo=repo)
    working = _working_tree_paths(repo)
    return [*committed, *working]


def main() -> int:
    repo = pathlib.Path.cwd()
    paths = changed_paths(repo)
    total, noncoord = classify(paths)
    print(
        f"total changed files: {total}; non-coordination-note files: {noncoord} "
        "— coordination-note-only iff total>0 and non-coordination-note=0"
    )
    for path in sorted(set(paths))[:_PREVIEW_LIMIT]:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
