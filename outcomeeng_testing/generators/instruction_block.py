"""Hypothesis domains for instruction-block render and reconcile properties."""

from __future__ import annotations

from types import ModuleType

from hypothesis import strategies as st
from hypothesis.strategies import SearchStrategy


def versions() -> SearchStrategy[tuple[int, int, int]]:
    """Generate bounded dotted-numeric version triples."""
    part = st.integers(min_value=0, max_value=999)
    return st.tuples(part, part, part)


def region_bodies() -> SearchStrategy[str]:
    """Generate non-empty shared-region bodies that round-trip through fences."""
    return st.text(
        alphabet=st.characters(
            whitelist_categories=("L", "N"), whitelist_characters=" -_`"
        ),
        min_size=1,
    ).filter(lambda body: body.strip() != "")


def free_instruction_content() -> SearchStrategy[str]:
    """Generate multiline instruction content without fence-forming characters."""
    return st.text(
        alphabet=st.characters(
            whitelist_categories=("L", "N"), whitelist_characters=" -_`\n"
        ),
        max_size=200,
    )


def to_version(parts: tuple[int, int, int]) -> str:
    """Render a generated version triple in the production dotted form."""
    return ".".join(str(part) for part in parts)


def shared_document(module: ModuleType, name: str, body: str) -> str:
    """Build one complete shared-region document around a generated body."""
    return (
        f"{module.shared_open_marker(name)}\n\n{body}\n\n"
        f"{module.shared_close_marker(name)}\n"
    )
