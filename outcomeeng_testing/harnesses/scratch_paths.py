"""Resource lifecycle and observations for fixed-temporary-path evidence."""

from __future__ import annotations

from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory

from outcomeeng.distribution.contracts import SKILL_FILENAME
from outcomeeng.validation.scratch_paths import (
    ALLOW_MARKER,
    find_fixed_temporary_paths,
    format_violation,
    main,
    scan_file,
)
from outcomeeng_testing.generators.scratch_paths import (
    fixed_temporary_paths,
    portable_scratch_sources,
)


def violation_reports_file_line_reference_and_failure() -> bool:
    """Exercise file scanning and command diagnostics for a generated violation."""
    reference = fixed_temporary_paths()[0]
    content = "\n".join((*portable_scratch_sources()[:1], reference))
    with TemporaryDirectory() as temporary_directory:
        path = Path(temporary_directory) / SKILL_FILENAME
        path.write_text(content, encoding="utf-8")
        (violation,) = scan_file(path)
        output = StringIO()
        with redirect_stdout(output):
            exit_code = main([str(path)])
        return exit_code != 0 and output.getvalue().strip() == format_violation(
            violation
        )


def portable_content_reports_nothing_and_succeeds() -> bool:
    """Exercise file scanning and command output for every portable category."""
    with TemporaryDirectory() as temporary_directory:
        path = Path(temporary_directory) / SKILL_FILENAME
        path.write_text("\n".join(portable_scratch_sources()), encoding="utf-8")
        output = StringIO()
        with redirect_stdout(output):
            exit_code = main([str(path)])
        return exit_code == 0 and output.getvalue() == "" and scan_file(path) == []


def every_fixed_temporary_category_is_flagged() -> bool:
    """Return whether each generated prohibited category is rejected."""
    return all(
        find_fixed_temporary_paths(reference) for reference in fixed_temporary_paths()
    )


def every_portable_scratch_category_is_accepted() -> bool:
    """Return whether each generated allowed category is accepted."""
    return all(
        not find_fixed_temporary_paths(reference)
        for reference in portable_scratch_sources()
    )


def allow_marker_exempts_only_its_own_line() -> bool:
    """Exercise the marker's per-line scope against a two-line subject.

    A marked line and an unmarked line carry the same prohibited path, so a
    marker whose scope leaked to the file would drop the unmarked violation
    and a marker with no effect would keep the marked one.
    """
    violation = fixed_temporary_paths()[0]
    marked = f"{violation} {ALLOW_MARKER}"
    found = find_fixed_temporary_paths("\n".join((marked, violation)))
    return [lineno for lineno, _ in found] == [2]
