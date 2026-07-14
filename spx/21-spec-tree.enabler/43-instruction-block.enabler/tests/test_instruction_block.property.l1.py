"""Property evidence for the instruction-block render model.

Generated domains, run configuration, and replay diagnostics are owned by test infrastructure.
"""

from outcomeeng_testing.harnesses import instruction_block as harness


def test_render_output_version_equals_installed() -> None:
    harness.assert_render_output_version_equals_installed()


def test_managed_surface_ends_with_single_newline() -> None:
    harness.assert_managed_surface_ends_with_single_newline()


def test_is_stale_matches_numeric_version_order() -> None:
    harness.assert_is_stale_matches_numeric_version_order()


def test_reconcile_makes_shared_region_identical() -> None:
    harness.assert_reconcile_makes_shared_region_identical()


def test_reconcile_identical_region_is_idempotent() -> None:
    harness.assert_reconcile_identical_region_is_idempotent()


def test_bootstrap_wraps_at_most_one_shared_region() -> None:
    harness.assert_bootstrap_wraps_at_most_one_shared_region()


def test_biggest_span_ratio_determines_wrap_decision() -> None:
    harness.assert_biggest_span_ratio_determines_wrap_decision()
