"""Open invalid configuration domains are rejected with field diagnostics."""

from decimal import Decimal

from outcomeeng_testing.harnesses.consumption_control import (
    PriceOverrideObservation,
    configuration_property,
    invalid_namespace_property,
    invalid_price_override_property,
    invalid_routed_namespace_property,
    NamespaceRoute,
    price_override_property,
    valid_namespace_property,
    valid_routed_namespace_property,
)


def test_nonpositive_and_nonfinite_money_is_rejected() -> None:
    def check(diagnostics: list[tuple[str, str]]) -> None:
        assert diagnostics
        assert all(field in message for field, message in diagnostics)

    configuration_property(check)


def test_price_override_replaces_only_the_models_it_lists() -> None:
    def check(observed: PriceOverrideObservation) -> None:
        assert observed.resolved == tuple(Decimal(rate) for rate in observed.written)
        assert observed.resolved_others == observed.bundled_others
        assert observed.effective_file == observed.written_file

    price_override_property(check)


def test_invalid_price_override_names_its_rejected_field() -> None:
    def check(diagnostic: tuple[str, str]) -> None:
        location, message = diagnostic
        assert location in message

    invalid_price_override_property(check)


def test_invalid_namespace_names_its_rejected_field() -> None:
    def check(diagnostic: tuple[str, str]) -> None:
        field, message = diagnostic
        assert field in message

    invalid_namespace_property(check)


def test_valid_namespace_is_accepted_and_saved_unchanged() -> None:
    def check(namespace: str, resolved: str, saved: str) -> None:
        assert resolved == namespace
        assert saved == namespace

    valid_namespace_property(check)


def test_invalid_namespace_is_rejected_on_the_saved_and_option_routes() -> None:
    def check(
        route: NamespaceRoute, namespace: str, diagnostic: tuple[str, str]
    ) -> None:
        field, message = diagnostic
        assert message, (route, namespace)
        assert field in message

    invalid_routed_namespace_property(check)


def test_valid_namespace_is_accepted_on_the_saved_and_option_routes() -> None:
    def check(route: NamespaceRoute, namespace: str, resolved: str) -> None:
        assert resolved == namespace, route

    valid_routed_namespace_property(check)
