"""Complete native configuration domains remain forbidden as authored literals."""

from outcomeeng.distribution.profiles import (
    MODEL_IDENTIFIERS,
    NATIVE_CONFIGURATION_FIELDS,
)
from outcomeeng.validation.profile_configuration import find_profile_literals
from outcomeeng_testing.generators.profile_binding import (
    AUTHORED_BINDINGS,
    BARE_NAME_BINDINGS,
    PLACEHOLDER_BINDINGS,
    READ_BINDINGS,
)


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


def test_only_literal_and_template_token_bindings_are_assignments() -> None:
    for field in NATIVE_CONFIGURATION_FIELDS:
        for binding in AUTHORED_BINDINGS:
            assert find_profile_literals(f"{field} = {binding}") == [(1, field)]
        for binding in READ_BINDINGS:
            assert find_profile_literals(f"{field} = {binding}") == []
            assert find_profile_literals(f"{field}: {binding}") == []


def test_every_other_binding_is_an_assignment_in_colon_and_equals_form() -> None:
    for field in NATIVE_CONFIGURATION_FIELDS:
        for binding in AUTHORED_BINDINGS:
            assert find_profile_literals(f"{field}: {binding}") == [(1, field)]
            assert find_profile_literals(f"{field} = {binding}") == [(1, field)]


def test_unquoted_values_are_assignments_in_yaml_form() -> None:
    for field in NATIVE_CONFIGURATION_FIELDS:
        for binding in BARE_NAME_BINDINGS:
            assert find_profile_literals(f"{field}: {binding}") == [(1, field)]


def test_interpolation_placeholders_in_message_text_are_no_assignment() -> None:
    for field in NATIVE_CONFIGURATION_FIELDS:
        for binding in PLACEHOLDER_BINDINGS:
            assert find_profile_literals(f"{field}: {binding}") == []
