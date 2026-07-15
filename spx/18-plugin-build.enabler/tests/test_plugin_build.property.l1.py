"""Property evidence for build determinism and idempotence."""

from __future__ import annotations

from outcomeeng_testing.harnesses.plugin_build import (
    canonical_build_is_deterministic,
    canonical_build_is_idempotent,
    canonical_build_rejects_formatter_version_drift,
)


def test_same_source_produces_byte_identical_outputs() -> None:
    assert canonical_build_is_deterministic()


def test_running_build_twice_produces_no_second_pass_change() -> None:
    assert canonical_build_is_idempotent()


def test_formatter_version_drift_cannot_change_existing_output() -> None:
    assert canonical_build_rejects_formatter_version_drift()
