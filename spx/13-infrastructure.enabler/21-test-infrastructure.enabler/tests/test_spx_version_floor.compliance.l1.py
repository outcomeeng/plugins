"""Compliance evidence for the spx version-floor gate step.

Verifies the rule in
`spx/13-infrastructure.enabler/21-test-infrastructure.enabler/15-ci-gate.adr.md`:
a gate step fails when the `@outcomeeng/spx` version the CI workflow pins is
below the marketplace's declared minimum (`REQUIRED_SPX_VERSION`), so a skill or
test depending on an unpinned or unpublished spx capability fails the gate rather
than shipping.

The floor (`REQUIRED_SPX_VERSION`) and the pin parser are imported from the
checker module — the source of truth — so this evidence never restates a copied
floor value or pin regex.
"""

from __future__ import annotations

from pathlib import Path
from typing import Final

from outcomeeng.validation import spx_version

# A pin one patch below the floor — the canonical violating case the rule must
# detect. Built from the source-owned floor so it tracks the floor automatically.
_FLOOR_TUPLE: Final = spx_version.parse_version(spx_version.REQUIRED_SPX_VERSION)
_BELOW_FLOOR: Final = ".".join(
    str(part) for part in (*_FLOOR_TUPLE[:-1], _FLOOR_TUPLE[-1] - 1)
)


class TestVersionComparison:
    def test_pin_above_floor_is_satisfied(self) -> None:
        assert spx_version.is_satisfied("99.0.0", spx_version.REQUIRED_SPX_VERSION)

    def test_pin_equal_to_floor_is_satisfied(self) -> None:
        assert spx_version.is_satisfied(
            spx_version.REQUIRED_SPX_VERSION, spx_version.REQUIRED_SPX_VERSION
        )

    def test_pin_below_floor_is_not_satisfied(self) -> None:
        # The violating case the gate rule exists to catch.
        assert not spx_version.is_satisfied(
            _BELOW_FLOOR, spx_version.REQUIRED_SPX_VERSION
        )


class TestPinExtraction:
    def test_reads_pinned_version_from_workflow_line(self) -> None:
        text = '      SPX_VERSION: "1.2.3" # renovate: datasource=npm depName=x'
        assert spx_version.read_pinned_version(text) == "1.2.3"

    def test_absent_pin_returns_none(self) -> None:
        assert spx_version.read_pinned_version("no pin here\n") is None

    def test_below_floor_pin_is_detected_through_the_real_code_path(self) -> None:
        # Exercise the exact composition main() uses — extract then compare —
        # against a workflow that pins below the floor, proving the failure path.
        text = f'      SPX_VERSION: "{_BELOW_FLOOR}"'
        pinned = spx_version.read_pinned_version(text)
        assert pinned is not None
        assert not spx_version.is_satisfied(pinned, spx_version.REQUIRED_SPX_VERSION)


def _workflow_with_pin(pin: str) -> str:
    return f'      SPX_VERSION: "{pin}" # renovate: datasource=npm depName=x\n'


class TestGateStepExitCodes:
    def test_pin_at_floor_passes(self, tmp_path: Path) -> None:
        workflow = tmp_path / "check.yml"
        workflow.write_text(_workflow_with_pin(spx_version.REQUIRED_SPX_VERSION))
        assert spx_version.main(workflow) == 0

    def test_pin_below_floor_fails(self, tmp_path: Path) -> None:
        # The compliance rule: a sub-floor pin makes the gate step fail.
        workflow = tmp_path / "check.yml"
        workflow.write_text(_workflow_with_pin(_BELOW_FLOOR))
        assert spx_version.main(workflow) == 1

    def test_non_numeric_pin_fails_closed(self, tmp_path: Path) -> None:
        # A pin matching the line shape but not dotted-numeric fails with a
        # named cause, never an uncaught traceback.
        workflow = tmp_path / "check.yml"
        workflow.write_text(
            _workflow_with_pin(f"{spx_version.REQUIRED_SPX_VERSION}-rc1")
        )
        assert spx_version.main(workflow) == 1

    def test_absent_pin_fails(self, tmp_path: Path) -> None:
        workflow = tmp_path / "check.yml"
        workflow.write_text("no pin declared here\n")
        assert spx_version.main(workflow) == 1

    def test_missing_workflow_file_fails(self, tmp_path: Path) -> None:
        assert spx_version.main(tmp_path / "absent.yml") == 1


class TestLiveRepositoryState:
    def test_workflow_pins_at_or_above_the_floor(self) -> None:
        pinned = spx_version.read_pinned_version(
            spx_version.WORKFLOW_PATH.read_text(encoding="utf-8")
        )
        assert pinned is not None, "the CI workflow declares no SPX_VERSION pin"
        assert spx_version.is_satisfied(pinned, spx_version.REQUIRED_SPX_VERSION), (
            f"CI pins spx {pinned}, below the required floor "
            f"{spx_version.REQUIRED_SPX_VERSION}"
        )

    def test_gate_step_passes_on_the_live_repository(self) -> None:
        assert spx_version.main() == 0
