"""Variable domains outside the closed central profile selection."""

from hypothesis import strategies as st

from outcomeeng.distribution.profiles import AgentProfile


def unknown_profile_names() -> st.SearchStrategy[str]:
    """Generate arbitrary strings outside the independently enumerable domain."""
    return st.text().filter(lambda value: value not in frozenset(AgentProfile))
