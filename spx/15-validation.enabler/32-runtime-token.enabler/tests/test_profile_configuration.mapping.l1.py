"""Complete native configuration domains remain forbidden as authored literals."""

from outcomeeng.distribution.profiles import (
    MODEL_IDENTIFIERS,
    NATIVE_CONFIGURATION_FIELDS,
)
from outcomeeng.validation.profile_configuration import find_profile_literals


def test_every_owned_model_identifier_is_rejected() -> None:
    for model in MODEL_IDENTIFIERS:
        assert find_profile_literals(model) == [(1, model)]


def test_every_native_field_assignment_is_rejected() -> None:
    for field in NATIVE_CONFIGURATION_FIELDS:
        for assignment in (
            f'{field}: "value"',
            f'{field} = "value"',
            f'{{"{field}": "value"}}',
        ):
            assert find_profile_literals(assignment) == [(1, field)]
