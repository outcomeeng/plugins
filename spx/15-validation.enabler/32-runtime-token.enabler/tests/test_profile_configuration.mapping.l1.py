"""Complete native configuration domains remain forbidden as authored literals."""

from outcomeeng.distribution.profiles import NATIVE_CONFIGURATION_FIELDS
from outcomeeng.models import CLAUDE_MODEL_FAMILIES, MODEL_IDENTIFIERS
from outcomeeng.validation.profile_configuration import find_profile_literals
from outcomeeng_testing.generators.model_identifiers import unowned_model_identifiers


def test_every_owned_model_identifier_is_rejected() -> None:
    for model in MODEL_IDENTIFIERS:
        assert find_profile_literals(model) == [(1, model)]


def test_every_unowned_model_identifier_is_rejected() -> None:
    for identifier in unowned_model_identifiers():
        assert find_profile_literals(identifier) == [(1, identifier)]


def test_every_bare_model_family_name_is_rejected() -> None:
    for family in CLAUDE_MODEL_FAMILIES:
        assert find_profile_literals(family) == [(1, family)]


def test_every_native_field_assignment_is_rejected() -> None:
    for field in NATIVE_CONFIGURATION_FIELDS:
        for assignment in (
            f'{field}: "value"',
            f'{field} = "value"',
            f'{{"{field}": "value"}}',
        ):
            assert find_profile_literals(assignment) == [(1, field)]
