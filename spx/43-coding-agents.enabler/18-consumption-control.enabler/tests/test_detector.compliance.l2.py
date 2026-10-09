"""Persisted alert occurrences survive repeated finite evaluations."""

from outcomeeng_testing.harnesses.consumption_control import (
    detector_observation,
    workspace,
)


def test_repeated_signal_has_one_durable_record() -> None:
    with workspace() as work:
        observed = detector_observation(work)
        assert observed.first_count
        assert observed.first_count == observed.second_count == observed.durable_count
        assert observed.first_identities == observed.second_identities
        assert all(
            status == observed.expected_existing_status
            for status in observed.existing_statuses
        )
        assert observed.source_before == observed.source_after
