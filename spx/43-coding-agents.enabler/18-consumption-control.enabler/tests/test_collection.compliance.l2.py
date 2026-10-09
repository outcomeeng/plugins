"""Captured native records resume through real transactional SQLite state."""

from outcomeeng_testing.harnesses.consumption_control import (
    collection_observation,
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
