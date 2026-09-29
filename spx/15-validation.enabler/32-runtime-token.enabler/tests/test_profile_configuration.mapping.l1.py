"""Complete native configuration domains remain forbidden as authored literals."""

from outcomeeng.models import CLAUDE_MODEL_FAMILIES, MODEL_IDENTIFIERS
from outcomeeng.validation.profile_configuration import find_profile_literals
from outcomeeng_testing.generators.model_identifiers import unowned_model_identifiers
from outcomeeng_testing.generators.profile_configuration import (
    native_field_assignments,
    token_document,
)


def test_every_owned_model_identifier_is_rejected() -> None:
    document = token_document((model, (model,)) for model in sorted(MODEL_IDENTIFIERS))

    assert document.placed
    assert find_profile_literals(document.text) == [
        (placed.line, placed.token) for placed in document.placed
    ]


def test_every_unowned_model_identifier_is_rejected() -> None:
    document = token_document(
        (identifier, (identifier,)) for identifier in unowned_model_identifiers()
    )

    assert document.placed
    assert find_profile_literals(document.text) == [
        (placed.line, placed.token) for placed in document.placed
    ]


def test_every_bare_model_family_name_is_rejected() -> None:
    document = token_document(
        (family, (family,)) for family in sorted(CLAUDE_MODEL_FAMILIES)
    )

    assert document.placed
    assert find_profile_literals(document.text) == [
        (placed.line, placed.token) for placed in document.placed
    ]


def test_every_native_field_assignment_is_rejected() -> None:
    document = token_document(
        (assignment.text, assignment.tokens)
        for assignment in native_field_assignments()
    )

    assert document.placed
    assert sorted(find_profile_literals(document.text)) == sorted(
        (placed.line, placed.token) for placed in document.placed
    )
