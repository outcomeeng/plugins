"""Resource lifecycle and observations for fixed-temporary-path evidence.

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
from outcomeeng.validation.scratch_paths import (
    ALLOW_MARKER,
    Violation,
    find_fixed_temporary_paths,
    main,
    scan_file,
)
from outcomeeng_testing.generators.scratch_paths import (
    fixed_temporary_paths,
    portable_scratch_sources,
)


@dataclass(frozen=True)
class ScanObservation:
    """What one command run over one file produced."""

    path: Path
    exit_code: int
    stdout: str
    violations: tuple[Violation, ...]


def _observe(content: str) -> ScanObservation:
    """Run the real command over ``content`` and capture what it produced."""
    with TemporaryDirectory() as temporary_directory:
        path = Path(temporary_directory) / SKILL_FILENAME
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


def observe_violation_scan() -> ScanObservation:
    """Observe the command over a file whose last line names a fixed path."""
    return _observe(
        "\n".join((portable_scratch_sources()[0], fixed_temporary_paths()[0]))
    )


def observe_portable_scan() -> ScanObservation:
    """Observe the command over a file carrying every portable category."""
    return _observe("\n".join(portable_scratch_sources()))


def observe_allow_marker_lines() -> tuple[int, ...]:
    """Return the reported line numbers for a marked line above an identical bare one.

    Both lines carry the same prohibited path, so a marker whose scope leaked to
    the file reports nothing and a marker with no effect reports both.
    """
    violation = fixed_temporary_paths()[0]
    subject = "\n".join((f"{violation} {ALLOW_MARKER}", violation))
    return tuple(lineno for lineno, _ in find_fixed_temporary_paths(subject))
