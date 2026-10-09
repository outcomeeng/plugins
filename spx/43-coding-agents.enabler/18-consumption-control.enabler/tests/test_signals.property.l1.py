"""Generated budget and pace signals preserve occurrence identities."""

from outcomeeng_testing.harnesses.consumption_control import (
    SignalObservation,
    signal_property,
)


def test_configured_budget_pace_and_identity() -> None:
    def check(observed: SignalObservation) -> None:
        assert observed.actual_kinds == observed.expected_kinds
        assert observed.identities == observed.repeated_identities
        assert observed.configured_alert == observed.actual_alert
        assert (
            observed.actual_pace is None
            or observed.actual_pace == observed.expected_pace
        )
        assert observed.conversion is None

    signal_property(check)
