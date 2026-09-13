"""Variable plugin and authored-role names for namespace evidence."""

from __future__ import annotations

import string

from hypothesis import strategies as st


def agent_name_components() -> st.SearchStrategy[tuple[str, str]]:
    """Generate independent lowercase hyphenated plugin and role components."""
    names = st.lists(
        st.text(alphabet=string.ascii_lowercase + string.digits, min_size=1),
        min_size=1,
    ).map("-".join)
    return st.tuples(names, names)
