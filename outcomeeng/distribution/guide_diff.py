"""Actionable spx-guide drift reporter for the validation gate.

The gate's ``guide-diff`` step and the ``just guide-check`` recipe run this module
to enforce the render-model ADR's gate: regenerate ``spx/CLAUDE.md`` and
``spx/AGENTS.md`` from the canonical template via the shipped update-spx generator,
then fail when either drifts from its committed content. It is the guide analogue of
``dist-diff``.

A guide absent from the index — a first run, or a worktree where the guides were
never committed — registers as drift via ``--intent-to-add``, because a plain
``git diff`` reports only tracked changes and would otherwise pass silently while
leaving the freshly written guides uncommitted.
"""

from __future__ import annotations

import subprocess
from collections.abc import Sequence
from pathlib import Path
from typing import Final

_REPO_ROOT: Final = Path(__file__).resolve().parents[2]
_GENERATOR: Final = (
    _REPO_ROOT / "src/plugins/spec-tree/skills/update-spx/scripts/update_spx.py"
)
_TEMPLATE: Final = (
    _REPO_ROOT / "src/plugins/spec-tree/skills/understand/templates/spx-claude.md"
)
_GUIDE_PATHS: Final = ("spx/CLAUDE.md", "spx/AGENTS.md")

HEADER: Final = "spx/ guide files differ from a fresh render."
REMEDIATION: Final = (
    "Run `just guide-check` and commit the regenerated spx/CLAUDE.md and spx/AGENTS.md."
)


def _run(args: Sequence[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(args), cwd=_REPO_ROOT, capture_output=True, text=True, check=True
    )


def regenerate_guides() -> None:
    """Render both guide files in place via the shipped update-spx generator."""
    _run(
        [
            "python3",
            str(_GENERATOR),
            "--template",
            str(_TEMPLATE),
            "--spx-dir",
            "spx",
            "--write",
        ]
    )


def drifting_guides() -> list[str]:
    """Return the guide paths that drift from their committed content.

    ``--intent-to-add`` makes an absent-from-index guide register as drift; a plain
    ``git diff`` reports only tracked changes and would pass silently on a first run.
    """
    _run(["git", "add", "--intent-to-add", *_GUIDE_PATHS])
    result = _run(["git", "diff", "--name-only", "--", *_GUIDE_PATHS])
    return [line for line in result.stdout.splitlines() if line.strip()]


def render_report(drift: Sequence[str]) -> str:
    """Render the actionable drift report from the drifting guide paths."""
    return "\n".join([HEADER, "", *(f"  {path}" for path in drift), "", REMEDIATION])


def main(argv: Sequence[str] | None = None) -> int:
    regenerate_guides()
    drift = drifting_guides()
    if not drift:
        return 0
    print(render_report(drift))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
