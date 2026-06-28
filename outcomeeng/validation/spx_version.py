"""Enforce that the CI-pinned ``@outcomeeng/spx`` version meets the floor the
shipped skills depend on.

The shipped ``spec-tree`` skills (``/handoff``, ``/pickup``) and their co-located
tests invoke the ``spx`` CLI and assume the behavior of a specific version. A
skill or test that assumes a capability absent from the pinned spx ships a
runtime contract the consumer's installed CLI cannot honor, and surfaces only as
an opaque test failure against the pinned CLI or as a consumer-side regression.

``REQUIRED_SPX_VERSION`` is the single source of truth for that floor — the
lowest published spx version whose capabilities the skills and tests depend on.
This step reads the version the CI workflow pins (``SPX_VERSION`` in
``.github/workflows/check.yml``) and fails when the pin falls below the floor, so
the gap is named in the same ``just check`` a contributor runs before merge
("skills require spx >= X, CI pins Y") rather than left to a downstream test.

The floor rises only when a skill begins to depend on a newer capability. Because
the pin can only reach a version published to the registry, a floor set to an
unpublished version cannot be matched by any installable pin — the floor enforces
publish-before-depend by construction.

Usage::

    uv run python -m outcomeeng.validation.spx_version

Exit codes:
    0 - The pinned spx version meets or exceeds the declared floor
    1 - The pinned version is below the floor, no pin could be read, or the
        pinned value is not a dotted-numeric version
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Final

# The lowest published @outcomeeng/spx version whose capabilities the shipped
# skills and their tests depend on. Raise this when a skill starts to rely on a
# newer spx capability; the CI pin must then advance to a published version at or
# above it. spx 0.6.7 introduced `spx -C <path> session handoff`, which the
# /issue skill uses for cross-repository follow-up capture. spx 0.6.3 exposes
# worktree occupancy statuses as `running` and `free`, which the diagnose and
# pickup skills and the agent-environment tests consume. spx 0.6.1 introduced
# `spx session show --json`, the producer-owned session-frontmatter parser that
# /pickup claim verification consumes. spx 0.6.0 introduced the `spx journal`
# channel (open/append/seal/read/render over a type-agnostic append-only run
# journal), the run-journal contract the agentic verification skills bind for
# their durable run state (0.5.6 introduced `spx hook run session-start`, the
# host-lifecycle hook runner the spec-tree plugin's SessionStart hook delegates
# to for session identity, project-dir exports, and worktree occupancy; 0.5.4
# introduced the explicit work-branch git_ref the /handoff and /pickup skills
# depend on).
REQUIRED_SPX_VERSION: Final = "0.6.7"

_REPO_ROOT: Final = Path(__file__).resolve().parents[2]
WORKFLOW_PATH: Final = _REPO_ROOT / ".github" / "workflows" / "check.yml"

# The pinned-version line the CI workflow declares (and Renovate advances).
_PIN_PATTERN: Final[re.Pattern[str]] = re.compile(r'SPX_VERSION:\s*"([^"]+)"')


def parse_version(version: str) -> tuple[int, ...]:
    """Parse a dotted-numeric version into a comparable tuple of ints.

    Raises ``ValueError`` on a non-dotted-numeric value so a malformed pin or
    floor is a loud failure rather than a silent mis-comparison.
    """
    return tuple(int(part) for part in version.split("."))


def read_pinned_version(workflow_text: str) -> str | None:
    """Return the ``SPX_VERSION`` value the workflow pins, or None when absent."""
    match = _PIN_PATTERN.search(workflow_text)
    return match.group(1) if match else None


def is_satisfied(pinned: str, floor: str) -> bool:
    """Return whether ``pinned`` is at or above ``floor`` by dotted-numeric order."""
    return parse_version(pinned) >= parse_version(floor)


def main(workflow_path: Path = WORKFLOW_PATH) -> int:
    """Read the workflow pin and fail when it is below ``REQUIRED_SPX_VERSION``."""
    if not workflow_path.is_file():
        print(f"error: CI workflow not found at {workflow_path}", file=sys.stderr)
        return 1

    pinned = read_pinned_version(workflow_path.read_text(encoding="utf-8"))
    if pinned is None:
        print(
            f"error: no SPX_VERSION pin found in {workflow_path}",
            file=sys.stderr,
        )
        return 1

    try:
        satisfied = is_satisfied(pinned, REQUIRED_SPX_VERSION)
    except ValueError:
        # A pin that matches the line shape but is not dotted-numeric (e.g. a
        # prerelease tag) cannot be ordered against the floor — fail closed with
        # a named cause rather than an uncaught traceback.
        print(
            f"error: SPX_VERSION pin {pinned!r} in {workflow_path} is not a "
            "dotted-numeric version and cannot be compared to the floor "
            f"{REQUIRED_SPX_VERSION}.",
            file=sys.stderr,
        )
        return 1

    if not satisfied:
        print(
            "error: shipped skills require @outcomeeng/spx >= "
            f"{REQUIRED_SPX_VERSION}, but the CI workflow pins {pinned}. "
            "Publish an spx release at or above the floor and advance "
            "SPX_VERSION in .github/workflows/check.yml to it.",
            file=sys.stderr,
        )
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
