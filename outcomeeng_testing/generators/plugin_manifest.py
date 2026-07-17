"""Generated domains for plugin-manifest property evidence."""

from __future__ import annotations

from hypothesis import strategies as st
from hypothesis.strategies import SearchStrategy


def semantic_versions() -> SearchStrategy[str]:
    """Return generated semantic-version strings."""
    return st.tuples(
        st.integers(min_value=0),
        st.integers(min_value=0),
        st.integers(min_value=0),
    ).map(lambda parts: ".".join(str(part) for part in parts))


def distinct_version_pairs() -> SearchStrategy[tuple[str, str]]:
    """Return generated unequal semantic-version pairs."""
    return st.tuples(semantic_versions(), semantic_versions()).filter(
        lambda versions: versions[0] != versions[1]
    )
