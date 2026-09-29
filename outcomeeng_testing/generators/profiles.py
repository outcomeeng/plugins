"""Variable domains outside the closed central profile selection."""

from hypothesis import strategies as st

from outcomeeng.models import AgentProfile


def unknown_profile_names() -> st.SearchStrategy[str]:
    """Generate arbitrary strings outside the independently enumerable domain."""
    return st.text().filter(lambda value: value not in frozenset(AgentProfile))


def profile_name_case_variants() -> tuple[str, ...]:
    """Return each central profile name in upper and title case.

    A case variant is the nearest selection outside the case-sensitive profile
    domain, so it is the selection a case-folding fallback would accept.
    """
    variants = {
        variant
        for profile in AgentProfile
        for variant in (profile.upper(), profile.title())
    }
    return tuple(sorted(variants.difference(AgentProfile)))
