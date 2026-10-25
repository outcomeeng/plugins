"""Enforce that the version the ``spx`` CLI on the path reports meets the floor
the shipped skills depend on.

The shipped ``spec-tree`` skills (``/diagnose``, the verification wrappers, the
``SessionStart`` hook) and their co-located tests invoke the ``spx`` CLI and assume
the behavior of a specific version. A skill or test that assumes a capability absent
from the build the gate runs ships a runtime contract the consumer's installed CLI
cannot honor, and surfaces only as an opaque test failure or a consumer-side
regression.

``REQUIRED_SPX_VERSION`` is the single source of truth for that floor — the lowest
version a build of spx reports whose capabilities the skills and tests depend on.
This step runs ``spx --version`` and fails when the reported version falls below the
floor, so the gap is named in the same ``just check-full`` CI runs before merge
("skills require spx >= X, the build reports Y") rather than left to a downstream
test. The floor names no release channel: any build reporting the version meets it.

Usage::

    uv run python -m outcomeeng.validation.spx_version

Exit codes:
    0 - The reported spx version meets or exceeds the declared floor
    1 - The reported version is below the floor, or the CLI reports no version
"""

from __future__ import annotations

import re
import subprocess
import sys
from collections.abc import Callable
from shutil import which
from typing import Final

# The lowest published @outcomeeng/spx version whose capabilities the shipped
# skills and their tests depend on. Raise this when a skill starts to rely on a
# newer spx capability; the CI pin must then advance to a published version at or
# above it. spx 0.8.0 is the first release whose `spx validation markdown`
# enforces the 4.0 link shapes (`spx-link-shape`): a link is node-local or
# tree-absolute, and a decision cited as text is rejected; this repository's
# `spx/` tree conforms and the gate's `markdown` step runs that rule. spx 0.7.2
# is the first release whose project-configuration
# methodology version accepts the `MAJOR.MINOR` form; the shipped `/diagnose`
# skill invokes the CLI in consumer repositories whose declaration can be
# `4.0`, so that parser behavior is part of the floor's contract. spx 0.7.0 is
# the release whose `spx diagnose --format json`
# `worktree-pool` record carries `mainCheckoutPath`; this product's merge
# overlay reads that reading in its canonical-checkout preflight and again
# after feature-worktree cleanup, so the record's shape is part of the floor's
# contract. The agent-mail capability no longer reads it: it derives the mail
# project key from the repository's own common Git directory and invokes no
# spx command.
# spx 0.6.21 is the first release whose `spx verification run start`
# reports the resolved changed-path set as `resolvedScope` and whose `render`
# projection carries `auditScopeUnits`; the implementation audit's stage-4
# enumeration and its stage-7 reconciler read those two fields, and below this
# floor `render` omits the scope units entirely, so the reconciler can never
# exit zero and `finish` is unreachable. spx 0.6.15 made the manifest-independent default `spx diagnose`
# provider set include `worktree-pool` and classify a missing, detached, or
# wrong-branch designated main checkout through that record, which this
# product's merge overlay uses before merge mutation and after feature-worktree
# cleanup. spx 0.6.13 introduced `spx verification run`,
# including run start, input replay, scope evidence, finding evidence, finish,
# status, and render commands used by implementation audits. spx 0.6.10
# introduced `spx journal
# list` and branch-scope render selectors used by the review-run inspection
# helper. spx 0.6.7 introduced
# `spx -C <path> session handoff`. spx 0.6.3 exposes worktree occupancy
# statuses as `running` and `free`, which the diagnose and Change Lifecycle
# skills and the agent-environment tests consume. spx 0.6.1 introduced
# `spx session show --json`. spx 0.6.0 introduced the `spx journal` channel
# (open/append/seal/read/render over a type-agnostic append-only run journal),
# the run-journal contract the agentic verification skills bind for their
# durable run state (0.5.6 introduced `spx hook run session-start`, the
# host-lifecycle hook runner the spec-tree plugin's SessionStart hook delegates
# to for session identity, project-dir exports, and worktree occupancy; 0.5.4
# introduced the explicit work-branch git_ref).
VERIFICATION_RUN_MINIMUM_SPX_VERSION: Final = "0.6.13"
SPX_PACKAGE_NAME: Final = "@outcomeeng/spx"
PNPM_EXECUTABLE: Final = "pnpm"
PNPM_COMMAND_PREFIX: Final = (PNPM_EXECUTABLE, "dlx")
BUNX_EXECUTABLE: Final = "bunx"
BUNX_COMMAND_PREFIX: Final = (BUNX_EXECUTABLE, "--bun")
NPX_EXECUTABLE: Final = "npx"
NPX_COMMAND_PREFIX: Final = (NPX_EXECUTABLE, "--yes")
MINIMUM_RELEASE_PACKAGE_RUNNERS: Final = (
    (PNPM_EXECUTABLE, PNPM_COMMAND_PREFIX),
    (BUNX_EXECUTABLE, BUNX_COMMAND_PREFIX),
    (NPX_EXECUTABLE, NPX_COMMAND_PREFIX),
)
VERIFICATION_RUN_REQUIRED_COMMANDS: Final = (
    "start",
    "input",
    "scope",
    "finding",
    "finish",
    "render",
)
REQUIRED_SPX_VERSION: Final = "0.8.0"

SPX_EXECUTABLE: Final = "spx"
SPX_VERSION_ARGUMENT: Final = "--version"
_REPORTED_VERSION_PATTERN: Final[re.Pattern[str]] = re.compile(r"\d+(?:\.\d+)+")


def parse_version(version: str) -> tuple[int, ...]:
    """Parse a dotted-numeric version into a comparable tuple of ints.

    Raises ``ValueError`` on a non-dotted-numeric value so a malformed pin or
    floor is a loud failure rather than a silent mis-comparison.
    """
    return tuple(int(part) for part in version.split("."))


def parse_reported_version(output: str) -> str | None:
    """Return the first dotted-numeric version in ``spx --version`` output."""
    match = _REPORTED_VERSION_PATTERN.search(output)
    return match.group(0) if match else None


def read_reported_version(executable: str = SPX_EXECUTABLE) -> str | None:
    """Return the version the ``spx`` CLI on the path reports, or None when it reports none."""
    try:
        completed = subprocess.run(
            [executable, SPX_VERSION_ARGUMENT],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return None
    if completed.returncode != 0:
        return None
    return parse_reported_version(completed.stdout)


def is_satisfied(pinned: str, floor: str) -> bool:
    """Return whether ``pinned`` is at or above ``floor`` by dotted-numeric order."""
    return parse_version(pinned) >= parse_version(floor)


def verification_run_floor_is_satisfied(
    required_version: str = REQUIRED_SPX_VERSION,
) -> bool:
    """Return whether the shipped floor includes verification-run support."""
    return is_satisfied(required_version, VERIFICATION_RUN_MINIMUM_SPX_VERSION)


def minimum_release_package_command(
    package_spec: str,
    executable_finder: Callable[[str], str | None] = which,
) -> tuple[str, ...]:
    """Return the first available exact-release package-runner command."""
    for executable, command_prefix in MINIMUM_RELEASE_PACKAGE_RUNNERS:
        if executable_finder(executable) is not None:
            return (*command_prefix, package_spec)
    raise RuntimeError(
        "exact minimum-release SPX execution requires pnpm, bunx, or npx when "
        "the PATH version differs"
    )


def main(floor: str = REQUIRED_SPX_VERSION, executable: str = SPX_EXECUTABLE) -> int:
    """Fail when the version the ``spx`` CLI reports is below ``floor``."""
    if not verification_run_floor_is_satisfied(floor):
        print(
            "error: shipped implementation audits require spx >= "
            f"{VERIFICATION_RUN_MINIMUM_SPX_VERSION} for spx verification run, "
            f"but the repository floor is {floor}.",
            file=sys.stderr,
        )
        return 1

    reported = read_reported_version(executable)
    if reported is None:
        print(
            f"error: `{executable} {SPX_VERSION_ARGUMENT}` reported no version.",
            file=sys.stderr,
        )
        return 1

    if not is_satisfied(reported, floor):
        print(
            f"error: shipped skills require spx >= {floor}, but the spx build "
            f"on the path reports {reported}. Advance the spx commit pin in "
            "the CI workflow to a commit whose build reports at least the floor.",
            file=sys.stderr,
        )
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
