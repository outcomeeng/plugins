"""Resource lifecycle and observations for grant-locality evidence.

Every function here produces an observation and returns it. The predicate that
decides pass or fail belongs to the linked test, so a failure names the actual
value rather than collapsing to a bare ``False``.
"""

from __future__ import annotations

from contextlib import redirect_stdout
from dataclasses import dataclass
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory

from outcomeeng.distribution.contracts import SKILL_FILENAME
from outcomeeng.validation.grant_locality import (
    Violation,
    main,
    scan_file,
)
from outcomeeng_testing.generators.grant_locality import (
    escaping_grant_declarations,
    local_grant_declarations,
)


@dataclass(frozen=True)
class ScanObservation:
    """What one command run over one skill file produced."""

    path: Path
    exit_code: int
    stdout: str
    violations: tuple[Violation, ...]


def _observe(content: str, *, filename: str = SKILL_FILENAME) -> ScanObservation:
    """Run the real command over ``content`` and capture what it produced."""
    with TemporaryDirectory() as temporary_directory:
        path = Path(temporary_directory) / filename
        path.write_text(content, encoding="utf-8")
        violations = tuple(scan_file(path))
        output = StringIO()
        with redirect_stdout(output):
            exit_code = main([str(path)])
        return ScanObservation(
            path=path,
            exit_code=exit_code,
            stdout=output.getvalue(),
            violations=violations,
        )


def observe_escaping_scan() -> ScanObservation:
    """Observe the command over a skill whose last line escapes the directory."""
    return _observe(
        "\n".join((local_grant_declarations()[0], escaping_grant_declarations()[0]))
    )


def observe_local_scan() -> ScanObservation:
    """Observe the command over a skill carrying every local grant category."""
    return _observe("\n".join(local_grant_declarations()))


def observe_content(content: str) -> ScanObservation:
    """Observe the command over caller-supplied skill content."""
    return _observe(content)
