"""Variable native usage and spending domains for consumption evidence."""

from __future__ import annotations

from hypothesis import strategies as st
from decimal import Decimal


def usage_snapshots() -> st.SearchStrategy[tuple[tuple[int, ...], tuple[int, ...]]]:
    counts = st.tuples(
        st.integers(min_value=0, max_value=1_000_000_000),
        st.integers(min_value=0, max_value=1_000_000_000),
        st.integers(min_value=0, max_value=1_000_000_000),
        st.integers(min_value=1, max_value=1_000_000_000),
    )
    return st.tuples(counts, counts)


def duration_snapshots() -> st.SearchStrategy[tuple[tuple[int, ...], tuple[int, ...]]]:
    """Cumulative native snapshots vary both cache-duration counters independently."""
    base = st.tuples(
        st.integers(min_value=0, max_value=1_000_000),
        st.integers(min_value=0, max_value=1_000_000),
        st.integers(min_value=1, max_value=1_000_000),
        st.integers(min_value=1, max_value=1_000_000),
        st.integers(min_value=1, max_value=1_000_000),
    )
    increment = st.tuples(
        *(st.integers(min_value=0, max_value=1_000_000) for _ in range(5))
    )
    return st.tuples(base, increment).map(
        lambda values: (
            values[0],
            tuple(a + b for a, b in zip(*values, strict=True)),
        )
    )


def spending_cases() -> st.SearchStrategy[tuple[int, int, int]]:
    return st.tuples(
        st.integers(min_value=1, max_value=100_000),
        st.integers(min_value=1, max_value=100_000),
        st.integers(min_value=1, max_value=604_799),
    )


def invalid_amounts() -> st.SearchStrategy[str]:
    return st.decimals(max_value=Decimal(0), allow_nan=True, allow_infinity=True).map(
        str
    )


def growing_contexts() -> st.SearchStrategy[list[int]]:
    return st.lists(
        st.integers(min_value=1, max_value=10_000), min_size=2, max_size=32
    ).map(sorted)


def unsupported_models() -> st.SearchStrategy[str]:
    """Vary an explicitly unsupported namespace outside every released price key."""
    return st.text(
        alphabet="abcdefghijklmnopqrstuvwxyz0123456789", min_size=1, max_size=30
    ).map(lambda suffix: "unsupported-model-" + suffix)
