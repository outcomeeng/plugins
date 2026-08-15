import pytest

from outcomeeng.validation.grant_locality import (
    SKILL_DIR_VARIABLES,
    find_escaping_grants,
    frontmatter,
)
from outcomeeng_testing.generators.grant_locality import (
    body_mentions,
    escaping_grant_declarations,
    local_grant_declarations,
    skill_files_whose_body_mentions_an_escaping_grant,
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


@pytest.mark.parametrize("content", skill_files_whose_body_mentions_an_escaping_grant())
def test_escaping_grant_outside_the_frontmatter_is_not_a_violation(
    content: str,
) -> None:
    """Every body spelling of a prohibited grant passes, column zero included.

    The scan runs through `frontmatter` on a whole file, because that boundary
    is what the rule names: the column-zero spelling is byte-identical to a
    declaration line, so a check that only skipped indented lines would pass
    every other case here and still fail the standard that documents the rule.
    """
    found = find_escaping_grants(frontmatter(content))
    assert not found, f"body mention flagged as a grant: {content!r} -> {found!r}"


@pytest.mark.parametrize("mention", body_mentions())
def test_no_body_spelling_is_reachable_without_the_frontmatter_boundary(
    mention: str,
) -> None:
    """Each body spelling is carried by a file whose frontmatter excludes it.

    This keeps the category list and the files that exercise it from drifting
    apart: a spelling added to `body_mentions` with no file carrying it would
    leave the rule above asserting nothing about it.
    """
    carriers = [
        content
        for content in skill_files_whose_body_mentions_an_escaping_grant()
        if mention in frontmatter(content) or mention in content
    ]
    assert carriers, f"no skill file carries the body spelling {mention!r}"
    assert all(mention not in frontmatter(content) for content in carriers), (
        f"body spelling {mention!r} landed inside frontmatter"
    )


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
