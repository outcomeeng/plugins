"""Actionable ``dist/`` drift reporter for the build-orchestration gate.

The gate's ``dist-diff`` step and the lefthook pre-commit drift check both run
this module in place of a raw ``git diff --exit-code dist``. A raw diff dumps the
full unified hunks of every regenerated file — noise that buries the one fact the
reader needs: ``dist/`` is out of sync, and what to do about it.

This reporter instead lists the drifting ``dist/`` paths and prints remediation
matched to the working-tree state. When ``src/plugins/`` carries matching
uncommitted edits, the drift is the expected pre-commit state — the regenerated
``dist/`` just needs to be committed alongside ``src/``. When ``src/plugins/`` is
clean, ``dist/`` has genuinely drifted and a rebuild is the fix. Either way the
process exits non-zero so the gate still fails.
"""

from __future__ import annotations

import subprocess
from collections.abc import Sequence
from pathlib import Path
from typing import Final

from outcomeeng.distribution.orchestration import DIST_ROOT_NAME, SOURCE_PLUGINS_DIR

HEADER: Final = "dist/ differs from a fresh build."
DRIFTING_FILES_HEADING: Final = "Drifting generated files:"
EXPECTED_PRECOMMIT_NOTE: Final = "Expected pre-commit state"
DRIFT_REBUILD_NOTE: Final = "Run `just build-skills`"


def _git_stdout(args: Sequence[str], *, cwd: Path) -> str:
    """Return stdout of ``git args`` run in ``cwd``, raising on failure."""
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=True,
    ).stdout


def drifting_dist_entries(*, cwd: Path = Path(".")) -> list[str]:
    """Return ``git diff --name-status`` lines for drifting ``dist/`` paths."""
    raw = _git_stdout(["diff", "--name-status", "--", DIST_ROOT_NAME], cwd=cwd)
    return [line for line in raw.splitlines() if line.strip()]


def src_has_uncommitted_edits(*, cwd: Path = Path(".")) -> bool:
    """Return whether ``src/plugins/`` carries uncommitted working-tree edits."""
    raw = _git_stdout(
        ["status", "--porcelain", "--", SOURCE_PLUGINS_DIR.as_posix()], cwd=cwd
    )
    return bool(raw.strip())


def render_report(entries: Sequence[str], *, src_dirty: bool) -> str:
    """Render the actionable drift report from drifting entries and src state."""
    lines = [HEADER, "", DRIFTING_FILES_HEADING]
    lines += [f"  {entry}" for entry in entries]
    lines.append("")
    if src_dirty:
        lines.append("Detected: src/plugins/ has matching uncommitted edits.")
        lines.append(f"→ {EXPECTED_PRECOMMIT_NOTE}. Commit src/ and dist/ together;")
        lines.append(
            "  the lefthook pre-commit hook stages the regenerated dist/ for you."
        )
    else:
        lines.append("Detected: src/plugins/ is clean.")
        lines.append(f"→ dist/ drifted from src/. {DRIFT_REBUILD_NOTE}, then commit.")
    return "\n".join(lines)


def dist_drift_report(*, cwd: Path = Path(".")) -> str | None:
    """Return the actionable drift report, or ``None`` when ``dist/`` is in sync."""
    entries = drifting_dist_entries(cwd=cwd)
    if not entries:
        return None
    return render_report(entries, src_dirty=src_has_uncommitted_edits(cwd=cwd))


def main(*, cwd: Path = Path(".")) -> int:
    """Print the drift report and return 1 on drift, or return 0 when in sync."""
    report = dist_drift_report(cwd=cwd)
    if report is None:
        return 0
    print(report)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
