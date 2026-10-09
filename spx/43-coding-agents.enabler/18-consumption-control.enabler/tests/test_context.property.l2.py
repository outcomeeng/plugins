"""Growing native contexts retain marginal usage and cost trends."""

from math import isclose
from outcomeeng_testing.harnesses.consumption_control import (
    ContextObservation,
    context_property,
)


def test_growing_context_and_marginal_cost() -> None:
    def check(observed: ContextObservation) -> None:
        assert observed.requests == observed.expected_requests
        assert isclose(
            observed.early_context,
            observed.unit_context
            * sum(
                observed.factors[
                    : min(
                        observed.sample_limit,
                        max(1, len(observed.factors) // observed.sample_divisor),
                    )
                ]
            )
            / min(
                observed.sample_limit,
                max(1, len(observed.factors) // observed.sample_divisor),
            ),
        )
        assert isclose(
            observed.late_context,
            observed.unit_context
            * sum(
                observed.factors[
                    -min(
                        observed.sample_limit,
                        max(1, len(observed.factors) // observed.sample_divisor),
                    ) :
                ]
            )
            / min(
                observed.sample_limit,
                max(1, len(observed.factors) // observed.sample_divisor),
            ),
        )
        assert isclose(
            observed.early_cost,
            observed.unit_cost
            * sum(
                observed.factors[
                    : min(
                        observed.sample_limit,
                        max(1, len(observed.factors) // observed.sample_divisor),
                    )
                ]
            )
            / min(
                observed.sample_limit,
                max(1, len(observed.factors) // observed.sample_divisor),
            ),
        )
        assert isclose(
            observed.late_cost,
            observed.unit_cost
            * sum(
                observed.factors[
                    -min(
                        observed.sample_limit,
                        max(1, len(observed.factors) // observed.sample_divisor),
                    ) :
                ]
            )
            / min(
                observed.sample_limit,
                max(1, len(observed.factors) // observed.sample_divisor),
            ),
        )
        assert isclose(
            observed.growth,
            sum(
                observed.factors[
                    -min(
                        observed.sample_limit,
                        max(1, len(observed.factors) // observed.sample_divisor),
                    ) :
                ]
            )
            / sum(
                observed.factors[
                    : min(
                        observed.sample_limit,
                        max(1, len(observed.factors) // observed.sample_divisor),
                    )
                ]
            ),
        )
        assert isclose(
            observed.cost_growth,
            sum(
                observed.factors[
                    -min(
                        observed.sample_limit,
                        max(1, len(observed.factors) // observed.sample_divisor),
                    ) :
                ]
            )
            / sum(
                observed.factors[
                    : min(
                        observed.sample_limit,
                        max(1, len(observed.factors) // observed.sample_divisor),
                    )
                ]
            ),
        )
        assert isclose(
            observed.measurement[observed.fields.API_EQUIVALENT_USD],
            observed.unit_cost * sum(observed.factors),
        )
        assert all(
            group[observed.fields.REQUESTS] == len(observed.factors)
            and isclose(
                group[observed.fields.API_EQUIVALENT_USD],
                observed.unit_cost * sum(observed.factors),
            )
            for category in (observed.fields.SESSIONS, observed.fields.MODELS)
            for group in observed.measurement[category].values()
        )
        assert all(
            isclose(
                observed.measurement[observed.fields.COST_COMPONENTS][key],
                observed.unit_components[key] * sum(observed.factors),
            )
            for key in observed.token_keys
        )
        assert all(
            isclose(
                group[observed.fields.COST_COMPONENTS][key],
                observed.unit_components[key] * sum(observed.factors),
            )
            for category in (observed.fields.SESSIONS, observed.fields.MODELS)
            for group in observed.measurement[category].values()
            for key in observed.token_keys
        )

    context_property(check)
