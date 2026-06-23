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

import importlib.util
import subprocess
import sys
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
HEADER: Final = "spx/ guide files differ from a fresh render."
REMEDIATION: Final = (
    "Run `just guide-check` and commit the regenerated spx/CLAUDE.md and spx/AGENTS.md."
)


def _run(args: Sequence[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(args), cwd=_REPO_ROOT, capture_output=True, text=True, check=True
    )


def guide_paths() -> tuple[str, ...]:
    """Derive the spx-relative guide paths from the generator's own enumeration.

    ``RUNTIME_GUIDE_FILENAMES`` in the shipped generator is the authoritative set of
    runtime guide filenames; deriving from it rather than a parallel constant means a
    new runtime's guide is covered by the drift check without editing this module.
    """
    spec = importlib.util.spec_from_file_location("update_spx", _GENERATOR)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load update_spx from {_GENERATOR}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    filenames: dict[str, str] = module.RUNTIME_GUIDE_FILENAMES
    return tuple(f"spx/{name}" for name in filenames.values())


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
    paths = guide_paths()
    _run(["git", "add", "--intent-to-add", *paths])
    result = _run(["git", "diff", "--name-only", "--", *paths])
    return [line for line in result.stdout.splitlines() if line.strip()]


def render_report(drift: Sequence[str]) -> str:
    """Render the actionable drift report from the drifting guide paths."""
    return "\n".join([HEADER, "", *(f"  {path}" for path in drift), "", REMEDIATION])


def main(argv: Sequence[str] | None = None) -> int:
    try:
        regenerate_guides()
        drift = drifting_guides()
    except subprocess.CalledProcessError as exc:
        # Surface the failed command's own diagnostic — captured output is otherwise
        # swallowed by the default traceback, leaving the reporter unactionable.
        sys.stderr.write(exc.stderr or "")
        print(f"{HEADER}\n  the spx-guide gate failed; see the error above.")
        return 1
    if not drift:
        return 0
    print(render_report(drift))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
