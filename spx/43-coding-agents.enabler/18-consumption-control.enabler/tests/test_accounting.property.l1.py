"""Generated native usage reconciliation against captured external pricing."""

from outcomeeng_testing.harnesses.consumption_control import (
    AccountingObservation,
    UnknownPricingObservation,
    unknown_pricing_property,
    accounting_property,
)


def test_streaming_usage_and_native_children() -> None:
    def check(observed: AccountingObservation) -> None:
        assert observed.reconciled == observed.expected
        assert observed.cost == observed.oracle_cost
        assert observed.identities[0] == observed.identities[1]
        assert observed.native_parent == observed.expected_parent
        assert observed.child

    accounting_property(check)


def test_unsupported_models_preserve_measured_usage_and_named_gaps() -> None:
    def check(observed: UnknownPricingObservation) -> None:
        assert observed.components is None
        assert any(observed.model in gap for gap in observed.normalization_gaps)
        assert any(observed.model in gap for gap in observed.measured_gaps)
        assert observed.unpriced_requests == observed.expected_requests
        assert observed.measured_usage == observed.generated_usage

    unknown_pricing_property(check)
