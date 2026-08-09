import pytest

from outcomeeng.validation.grant_locality import (
    SKILL_DIR_VARIABLES,
    find_escaping_grants,
)
from outcomeeng_testing.generators.grant_locality import (
    body_mentions,
    escaping_grant_declarations,
    local_grant_declarations,
)


@pytest.mark.parametrize("declaration", escaping_grant_declarations())
def test_escaping_grant_category_is_flagged(declaration: str) -> None:
    assert find_escaping_grants(declaration), (
        f"escaping grant passed unflagged: {declaration!r}"
    )


@pytest.mark.parametrize("declaration", local_grant_declarations())
def test_local_grant_category_is_accepted(declaration: str) -> None:
    found = find_escaping_grants(declaration)
    assert not found, f"local grant flagged: {declaration!r} -> {found!r}"


@pytest.mark.parametrize("mention", body_mentions())
def test_escaping_grant_outside_a_field_declaration_is_not_a_violation(
    mention: str,
) -> None:
    found = find_escaping_grants(mention)
    assert not found, f"body mention flagged as a grant: {mention!r} -> {found!r}"


def test_every_target_spelling_of_the_variable_is_covered() -> None:
    """Each spelling the validator names appears in a flagged declaration.

    The build renders one authored token into each generated tree, so a rule
    reading a single spelling passes every skill in the other. The spellings are
    imported from the validator; what this checks is that the flagged set
    exercises all of them, not that the validator's list has some fixed content.
    """
    flagged = "\n".join(escaping_grant_declarations())
    uncovered = [
        variable
        for variable in SKILL_DIR_VARIABLES
        if not find_escaping_grants(
            "\n".join(
                line for line in flagged.splitlines() if f"${{{variable}}}" in line
            )
        )
    ]
    assert not uncovered, f"no flagged declaration exercises {uncovered!r}"
