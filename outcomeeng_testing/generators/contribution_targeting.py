"""Generator-owned input domains for contribution-targeting property evidence."""

from __future__ import annotations

from hypothesis import strategies as st
from hypothesis.strategies import SearchStrategy

PERMISSION_MAX_LENGTH = 32


def unrecognized_permissions(recognized: frozenset[str]) -> SearchStrategy[str]:
    """Non-empty `viewerPermission` values outside the sets the resolver names.

    `gh` reports the permission as an open string, so the values that fall
    outside both named buckets are a domain rather than a list. Every permission
    the platform documents today is named in one bucket or the other, so this
    domain is the remainder: a value whose access level the resolver has no
    statement about, which blocks rather than defaulting to either bucket. The
    recognized set is supplied by the caller so this module never reads it from
    the source under test.
    """
    return st.text(min_size=1, max_size=PERMISSION_MAX_LENGTH).filter(
        lambda value: value not in recognized
    )


def fork_states() -> SearchStrategy[bool]:
    """Both fork states a checkout can report."""
    return st.booleans()
