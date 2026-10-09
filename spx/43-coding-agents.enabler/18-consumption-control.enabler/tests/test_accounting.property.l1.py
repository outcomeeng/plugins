"""Generated native usage reconciliation against captured external pricing."""

from decimal import Decimal

from outcomeeng_testing.harnesses.consumption_control import (
    AccountingObservation,
    UnknownPricingObservation,
    unknown_pricing_property,
    accounting_property,
)


def test_streaming_usage_and_native_children() -> None:
    def check(observed: AccountingObservation) -> None:
        assert all(value is not None for value in observed.normalized)
        assert observed.reconciled is not None
        assert observed.components is not None
        assert tuple(observed.reconciled[observed.fields.TOKENS]) == (
            max(row[0] for row in observed.snapshots),
            max(row[1] for row in observed.snapshots),
            max(row[2] + row[3] for row in observed.snapshots),
            max(row[4] for row in observed.snapshots),
        )
        assert sum(observed.components.values(), Decimal()) == sum(
            (
                Decimal(max(row[index] for row in observed.snapshots)) * rate
                for index, rate in enumerate(observed.rates)
            ),
            Decimal(),
        ) / Decimal(1_000_000)
        assert all(
            value is not None
            and value[observed.fields.IDENTITY]
            == observed.reconciled[observed.fields.IDENTITY]
            for value in observed.normalized
        )
        assert observed.reconciled[observed.fields.PARENT] == observed.expected_parent
        assert observed.reconciled[observed.fields.CHILD]

    accounting_property(check)


def test_unsupported_models_preserve_measured_usage_and_named_gaps() -> None:
    def check(observed: UnknownPricingObservation) -> None:
        assert observed.components is None
        assert any(observed.model in gap for gap in observed.normalization_gaps)
        assert any(observed.model in gap for gap in observed.measured_gaps)
        assert observed.unpriced_requests == observed.expected_requests
        assert observed.measured_usage == observed.generated_usage

    unknown_pricing_property(check)
