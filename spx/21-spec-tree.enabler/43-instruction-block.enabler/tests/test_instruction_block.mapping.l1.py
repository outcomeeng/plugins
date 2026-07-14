"""Mapping evidence for the instruction-block render model.

Finite source and topology domains enter through harness-owned assertion entrypoints.
"""

from outcomeeng_testing.harnesses import instruction_block as harness


def test_extension_maps_to_language() -> None:
    harness.assert_extension_maps_to_language()


def test_detected_language_set_is_the_mapped_extensions() -> None:
    harness.assert_detected_language_set_is_mapped_extensions()


def test_language_block_appears_iff_enabled() -> None:
    harness.assert_language_block_appears_iff_enabled()


def test_check_maps_router_state_to_report() -> None:
    harness.assert_check_maps_router_state_to_report()


def test_check_maps_shared_region_state_to_report() -> None:
    harness.assert_check_maps_shared_region_state_to_report()


def test_topology_maps_to_bootstrap_outcome() -> None:
    harness.assert_topology_maps_to_bootstrap_outcome()
