"""Generated domains for instruction-block property evidence."""

from __future__ import annotations

from hypothesis import strategies as st


def version_parts() -> st.SearchStrategy[tuple[int, int, int]]:
    """Generate dotted-version components across the supported synthetic domain."""
    part = st.integers(min_value=0, max_value=999)
    return st.tuples(part, part, part)


def shared_region_bodies() -> st.SearchStrategy[str]:
    """Generate non-empty bodies that cannot form shared-region fences."""
    return st.text(
        alphabet=st.characters(
            whitelist_categories=("L", "N"),
            whitelist_characters=" -_`",
        ),
        min_size=1,
    ).filter(lambda body: body.strip() != "")


def free_instruction_content() -> st.SearchStrategy[str]:
    """Generate multiline content that cannot form shared-region fences."""
    return st.text(
        alphabet=st.characters(
            whitelist_categories=("L", "N"),
            whitelist_characters=" -_`\n",
        ),
        max_size=200,
    )
