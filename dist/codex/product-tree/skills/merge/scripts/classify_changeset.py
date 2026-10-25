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

Tested inputs and error cases: the co-located classifier scenario and mapping
evidence exercises importlib loading of `changeset_scope.py`, end-to-end
changed-path delegation through `detect_base_ref` and `branch_scope`, finite
coordination-note classification, git porcelain records for paths containing
spaces, unconfigured remote-default diagnostics, and the environment failures
(absent sibling module, git absent from PATH, a directory outside any git
working tree) that each exit 1 behind the error prefix before this script is
bundled.
"""

from __future__ import annotations

import importlib.util
import pathlib
import re
import runpy
import subprocess
import sys
from types import ModuleType
from typing import cast

_CONTRACT_FILENAME = "merge_contract.py"
_CHANGESET_SCOPE_RELPATH = ("scope-changeset", "scripts", "changeset_scope.py")
_PREVIEW_LIMIT = 40
BASE_REF_ERROR_PREFIX = "error: merge changeset classification failed"
_DIFF_FIX = "Fetch origin so the remote-tracking base ref exists, then rerun."
_GIT_ABSENT_FIX = "Install git or add it to PATH, then rerun."
_NOT_A_WORKING_TREE_FIX = "Run the classifier from inside a git working tree."
_coordination_note_pattern: re.Pattern[str] | None = None


class ChangesetClassificationError(RuntimeError):
    """The merge classifier cannot derive a transport-selection changeset."""


def _git_absent_error(
    command: list[str], repo: pathlib.Path
) -> ChangesetClassificationError:
    return ChangesetClassificationError(
        f"cannot run `{' '.join(command)}` in {repo}: git is not on PATH. "
        f"{_GIT_ABSENT_FIX}"
    )


def _git_failure_error(
    command: list[str],
    repo: pathlib.Path,
    exc: subprocess.CalledProcessError,
    fix: str,
) -> ChangesetClassificationError:
    detail = (exc.stderr or "").strip() or f"exit status {exc.returncode}"
    return ChangesetClassificationError(
        f"`{' '.join(command)}` failed in {repo}: {detail}. {fix}"
    )


def _load_coordination_note_pattern() -> re.Pattern[str]:
    """Compile the coordination-note matcher from the sibling `merge_contract.py`.

    The sibling path is checked before it is executed, so an incomplete install
    reports the missing path instead of raising a raw traceback.
    """
    global _coordination_note_pattern  # noqa: PLW0603  # one-time lazy cache
    if _coordination_note_pattern is not None:
        return _coordination_note_pattern
    path = pathlib.Path(__file__).resolve().with_name(_CONTRACT_FILENAME)
    if not path.is_file():
        raise ChangesetClassificationError(
            f"cannot load {_CONTRACT_FILENAME} from {path}: the file is absent. "
            "Reinstall the product-tree plugin so the merge skill's scripts "
            "directory is complete."
        )
    try:
        contract = runpy.run_path(str(path))
        basenames = cast(tuple[str, ...], contract["COORDINATION_NOTE_BASENAMES"])
    except (OSError, SyntaxError, KeyError) as exc:
        raise ChangesetClassificationError(
            f"cannot read COORDINATION_NOTE_BASENAMES from {path}: "
            f"{type(exc).__name__}: {exc}. Reinstall the product-tree plugin."
        ) from exc
    _coordination_note_pattern = re.compile(
        r"(^|/)(" + "|".join(re.escape(name) for name in basenames) + r")$"
    )
    return _coordination_note_pattern


def _load_changeset_scope() -> ModuleType:
    """Load the sibling `changeset_scope` module via the co-location convention.

    The module lives at `plugins/product-tree/skills/scope-changeset/scripts/
    changeset_scope.py`, resolved relative to this script so no path is
    hard-coded in agent prose. Cached in `sys.modules` so repeated loads in one
    process reuse the same module object.
    """
    cached = sys.modules.get("changeset_scope")
    if cached is not None:
        return cached
    skills_dir = pathlib.Path(__file__).resolve().parent.parent.parent
    path = skills_dir.joinpath(*_CHANGESET_SCOPE_RELPATH)
    spec = (
        importlib.util.spec_from_file_location("changeset_scope", path)
        if path.is_file()
        else None
    )
    if spec is None or spec.loader is None:
        siblings = (
            sorted(entry.name for entry in skills_dir.iterdir() if entry.is_dir())
            if skills_dir.is_dir()
            else []
        )
        raise ChangesetClassificationError(
            f"cannot load changeset_scope from {path}; skills directory "
            f"{skills_dir} holds: {', '.join(siblings) or '(nothing)'}. "
            "Reinstall the product-tree plugin so the scope-changeset skill "
            "sits beside the merge skill."
        )
    module = importlib.util.module_from_spec(spec)
    sys.modules["changeset_scope"] = module
    try:
        spec.loader.exec_module(module)
    except (OSError, SyntaxError, ImportError) as exc:
        del sys.modules["changeset_scope"]
        raise ChangesetClassificationError(
            f"cannot execute changeset_scope from {path}: "
            f"{type(exc).__name__}: {exc}. Reinstall the product-tree plugin so "
            "the scope-changeset skill sits beside the merge skill."
        ) from exc
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
    command = ["git", "status", "--porcelain", "-z"]
    try:
        result = subprocess.run(  # noqa: S603  # fixed argument list, no shell
            command,  # noqa: S607  # git via PATH, portable helper
            cwd=repo,
            capture_output=True,
            text=True,
            check=True,
        )
    except FileNotFoundError as exc:
        raise _git_absent_error(command, repo) from exc
    except subprocess.CalledProcessError as exc:
        raise _git_failure_error(command, repo, exc, _NOT_A_WORKING_TREE_FIX) from exc
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
    return _load_coordination_note_pattern().search(path) is not None


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
    # Working-tree status runs first: it is the earliest git invocation that
    # fails for a directory outside any working tree, so that failure reports
    # git's own diagnostic rather than a base-ref configuration error.
    working = _working_tree_paths(repo)
    try:
        base = changeset_scope.detect_base_ref(repo)
        committed = changeset_scope.branch_scope(base, repo=repo)
    except changeset_scope.BaseRefNotConfiguredError as exc:
        raise ChangesetClassificationError(str(exc)) from exc
    except FileNotFoundError as exc:
        raise _git_absent_error(["git"], repo) from exc
    except subprocess.CalledProcessError as exc:
        raise _git_failure_error(list(exc.cmd), repo, exc, _DIFF_FIX) from exc
    return [*committed, *working]


def main() -> int:
    repo = pathlib.Path.cwd()
    try:
        paths = changed_paths(repo)
    except ChangesetClassificationError as exc:
        print(f"{BASE_REF_ERROR_PREFIX}: {exc}", file=sys.stderr)
        return 1
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
