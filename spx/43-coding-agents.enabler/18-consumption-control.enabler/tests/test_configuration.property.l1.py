"""Open invalid monetary domains are rejected with field diagnostics."""

from outcomeeng_testing.harnesses.consumption_control import configuration_property


def test_nonpositive_and_nonfinite_money_is_rejected() -> None:
    def check(diagnostics: list[tuple[str, str]]) -> None:
        assert diagnostics
        assert all(field in message for field, message in diagnostics)

    configuration_property(check)
