"""Compliance evidence for the spx version-floor gate step.

The gate step fails when the version the `spx` CLI on the path reports is below the
marketplace's declared minimum (`REQUIRED_SPX_VERSION`), so a floor above what the
pinned build reports fails the gate rather than shipping.

The floor, the version reader, and the gate step are imported from the checker
module, which owns them. The violating floors derive from the version the real
`spx` CLI reports, so the evidence copies no version value and exercises the real
tool rather than an invented workflow shape.
"""

from __future__ import annotations

from pathlib import Path

from outcomeeng.validation import spx_version


def _floor_relative_to_reported(step: int) -> str:
    reported = spx_version.read_reported_version()
    assert reported is not None, "the spx CLI on the path reports no version"
    parts = spx_version.parse_version(reported)
    return ".".join(str(part) for part in (*parts[:-1], parts[-1] + step))


def test_reported_version_meets_the_declared_floor() -> None:
    reported = spx_version.read_reported_version()

    assert reported is not None
    assert spx_version.is_satisfied(reported, spx_version.REQUIRED_SPX_VERSION)
    assert spx_version.main() == 0


def test_floor_equal_to_the_reported_version_passes() -> None:
    assert spx_version.main(floor=_floor_relative_to_reported(0)) == 0


def test_floor_above_the_reported_version_fails() -> None:
    assert spx_version.main(floor=_floor_relative_to_reported(1)) == 1


def test_cli_that_is_absent_fails(tmp_path: Path) -> None:
    absent = tmp_path / "spx"

    assert spx_version.read_reported_version(str(absent)) is None
    assert spx_version.main(executable=str(absent)) == 1
