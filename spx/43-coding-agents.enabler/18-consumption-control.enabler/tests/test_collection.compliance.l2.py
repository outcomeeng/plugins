"""Captured native records resume through real transactional SQLite state."""

from outcomeeng_testing.harnesses.consumption_control import (
    collection_observation,
    collection_bounds_observation,
    workspace,
)


def test_originals_partial_rows_duplicates_and_native_children() -> None:
    with workspace() as work:
        observed = collection_observation(work)
        assert observed.before == observed.after
        assert observed.first_requests == observed.expected_excluded
        assert observed.after_requests == observed.expected_requests
        assert observed.resumed_usage == observed.expected_usage
        assert observed.partial_gaps
        assert observed.start_boundary_requests == observed.expected_requests
        assert observed.excluded_boundary_requests == observed.expected_excluded
        assert observed.child_requests == observed.expected_children
        assert observed.bytes_read <= observed.byte_bound


def test_exhaustion_is_visible_and_durable_offsets_resume() -> None:
    observed = collection_bounds_observation()
    assert observed.bytes_read == observed.byte_limit
    assert any(
        gap.startswith(observed.prefixes.COLLECTION_BOUND) for gap in observed.gaps
    )
    assert not any(observed.complete)
    assert observed.first_offset_total == observed.persisted_offset_total
    assert observed.resumed_offset_total > observed.persisted_offset_total
    assert observed.clock_gaps
    assert not observed.clock_bytes
    assert observed.resumed_clock_requests == observed.expected_clock_requests
    assert observed.discovery_cursor
    assert any(
        gap.startswith(observed.prefixes.DISCOVERY_INCOMPLETE)
        for gap in observed.discovery_gaps
    )
    assert any(
        gap.startswith(observed.prefixes.DISCOVERY_CAPACITY)
        for gap in observed.capacity_gaps
    )
