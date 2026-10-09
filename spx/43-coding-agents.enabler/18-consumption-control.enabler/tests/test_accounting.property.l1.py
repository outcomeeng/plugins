"""Generated native usage reconciliation against captured external pricing."""

from outcomeeng_testing.harnesses.consumption_control import (
    AccountingObservation,
    accounting_property,
)


def test_streaming_usage_and_native_children() -> None:
    def check(observed: AccountingObservation) -> None:
        assert observed.reconciled == observed.expected
        assert observed.cost == observed.oracle_cost
        assert observed.identity_stable
        assert observed.native_parent == observed.expected_parent
        assert observed.child

    accounting_property(check)
