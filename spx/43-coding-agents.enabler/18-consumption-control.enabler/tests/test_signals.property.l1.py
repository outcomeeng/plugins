"""Generated budget and pace signals preserve occurrence identities."""

from outcomeeng_testing.harnesses.consumption_control import (
    SignalObservation,
    signal_property,
)


def test_configured_budget_pace_and_identity() -> None:
    def check(observed: SignalObservation) -> None:
        assert (observed.kinds.ROLLING_THRESHOLD in observed.actual_kinds) == (
            observed.amount >= observed.configured_alert
        )
        assert (observed.kinds.WEEKLY_BUDGET in observed.actual_kinds) == (
            observed.amount >= observed.budget
        )
        assert (observed.kinds.WEEKLY_PACE in observed.actual_kinds) == (
            observed.amount >= observed.expected_pace
        )
        assert all(
            record[observed.fields.CONFIGURATION] == observed.configuration
            for record in observed.records
        )
        assert all(
            (
                record[observed.fields.START_UTC],
                record[observed.fields.END_EXCLUSIVE_UTC],
            )
            == (
                observed.current_window
                if record[observed.fields.KIND] == observed.kinds.ROLLING_THRESHOLD
                else observed.weekly_window
            )
            for record in observed.records
        )
        assert observed.identities == observed.repeated_identities
        assert observed.configured_alert == observed.actual_alert
        assert (
            observed.actual_pace is None
            or observed.actual_pace == observed.expected_pace
        )
        assert observed.conversion is None

    signal_property(check)
