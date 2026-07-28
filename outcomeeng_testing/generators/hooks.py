"""Generated domains for agent-hook evidence."""

from __future__ import annotations

from hypothesis import strategies as st


def session_ids() -> st.SearchStrategy[str]:
    """Generate UUID-form session identities."""
    return st.uuids().map(str)


__all__ = ["session_ids"]
