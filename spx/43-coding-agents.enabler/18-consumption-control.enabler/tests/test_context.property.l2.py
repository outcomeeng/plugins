"""Growing native contexts retain marginal usage and cost trends."""

from math import isclose
from outcomeeng_testing.harnesses.consumption_control import (
    ContextObservation,
    context_property,
)


def test_growing_context_and_marginal_cost() -> None:
    def check(observed: ContextObservation) -> None:
        assert observed.requests == observed.expected_requests
        assert observed.late_context >= observed.early_context
        assert observed.late_cost >= observed.early_cost
        assert isclose(observed.growth, observed.cost_growth)

    context_property(check)
