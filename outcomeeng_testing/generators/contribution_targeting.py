"""Generator-owned input domains for contribution-targeting property evidence."""

from __future__ import annotations

from hypothesis import strategies as st
from hypothesis.strategies import SearchStrategy

PERMISSION_MAX_LENGTH = 32


def unrecognized_permissions(recognized: frozenset[str]) -> SearchStrategy[str]:
    """Non-empty `viewerPermission` values outside the sets the resolver names.

    `gh` reports the permission as an open string, so the values that fall
    outside both named buckets are a domain rather than a list: a permission
    GitHub adds later arrives here without the resolver changing. The recognized
    set is supplied by the caller so this module never reads it from the source
    under test.
    """
    return st.text(min_size=1, max_size=PERMISSION_MAX_LENGTH).filter(
        lambda value: value not in recognized
    )


def fork_states() -> SearchStrategy[bool]:
    """Both fork states a checkout can report."""
    return st.booleans()
