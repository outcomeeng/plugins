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


def override_rates() -> st.SearchStrategy[tuple[str, ...]]:
    """Vary every rate of one price-override entry over non-negative finite decimals."""
    rate = st.decimals(
        min_value=Decimal(0),
        max_value=Decimal(1_000),
        places=4,
        allow_nan=False,
        allow_infinity=False,
    ).map(str)
    return st.tuples(rate, rate, rate, rate, rate)


def invalid_rates() -> st.SearchStrategy[object]:
    """Vary rejected price-override rates: negative, non-finite, non-numeric, non-string."""
    return st.one_of(
        st.decimals(max_value=Decimal("-0.0001"), places=4, allow_nan=False).map(str),
        st.decimals(allow_nan=True, allow_infinity=True)
        .filter(lambda value: not value.is_finite())
        .map(str),
        st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=1, max_size=12),
        st.integers(min_value=0, max_value=1_000),
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


def alert_reads() -> st.SearchStrategy[tuple[list[tuple[str, int, int]], int]]:
    """Vary stored alert records over identities, recording offsets, and the read cutoff.

    Offsets draw from a narrow range so records share instants, and the cutoff
    ranges from before the earliest to after the latest possible offset so it
    lands on, between, and outside the recorded instants.
    """
    record = st.tuples(
        st.binary(min_size=4, max_size=4).map(bytes.hex),
        st.integers(min_value=0, max_value=12),
        st.integers(min_value=1, max_value=1_000),
    )
    return st.tuples(
        st.lists(record, max_size=12, unique_by=lambda value: value[0]),
        st.integers(min_value=-1, max_value=13),
    )


_NAMESPACE_SEGMENT_ALPHABET = (
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
)
_NAMESPACE_SEPARATOR = "."


def _segments() -> st.SearchStrategy[str]:
    """One non-empty segment of ASCII letters, digits, hyphens and underscores."""
    return st.text(alphabet=_NAMESPACE_SEGMENT_ALPHABET, min_size=1, max_size=14)


def valid_namespaces() -> st.SearchStrategy[str]:
    """Vary namespaces of one or more dot-separated non-empty segments, so hyphens and
    underscores fall at segment edges and in the interior."""
    return st.lists(_segments(), min_size=1, max_size=4).map(_NAMESPACE_SEPARATOR.join)


def distinct_namespace_pairs() -> st.SearchStrategy[tuple[str, str]]:
    """Vary two namespaces that name different job sets, including nested ones."""
    return st.tuples(valid_namespaces(), valid_namespaces()).filter(
        lambda pair: pair[0] != pair[1]
    )


def nonconforming_plist_paths(directory: str, label: str) -> st.SearchStrategy[str]:
    """Vary recorded launch-agent paths that break the plist-naming convention for
    ``label``: a relative path, a file under ``directory`` named for another label, or
    the label without its plist suffix."""
    relative = (
        st.lists(_segments(), min_size=1, max_size=3)
        .map("/".join)
        .map(lambda prefix: prefix + "/" + label + ".plist")
    )
    renamed = _segments().map(lambda segment: directory + "/" + segment + ".plist")
    unsuffixed = st.just(directory + "/" + label)
    return st.one_of(relative, renamed, unsuffixed)


def invalid_namespaces(maximum: int) -> st.SearchStrategy[str]:
    """Vary namespaces broken by construction: an empty value, an empty segment, a
    whitespace or path-separator character, another foreign ASCII character, or a
    length beyond ``maximum``."""
    foreign = st.characters(codec="ascii").filter(
        lambda character: (
            character not in _NAMESPACE_SEGMENT_ALPHABET + _NAMESPACE_SEPARATOR
        )
    )
    whitespace = st.sampled_from(" \t\n\r\v\f")
    separators = st.sampled_from("/\\")
    broken = st.one_of(foreign, whitespace, separators)

    def insert(parts: tuple[str, str, int]) -> str:
        namespace, character, position = parts
        offset = position % (len(namespace) + 1)
        return namespace[:offset] + character + namespace[offset:]

    corrupted = st.tuples(valid_namespaces(), broken, st.integers(min_value=0)).map(
        insert
    )
    edged = st.tuples(valid_namespaces(), st.booleans()).map(
        lambda parts: (
            _NAMESPACE_SEPARATOR + parts[0]
            if parts[1]
            else parts[0] + _NAMESPACE_SEPARATOR
        )
    )
    gapped = st.tuples(valid_namespaces(), valid_namespaces()).map(
        lambda parts: parts[0] + _NAMESPACE_SEPARATOR * 2 + parts[1]
    )
    overlong = st.integers(min_value=maximum + 1, max_value=maximum + 40).map(
        lambda length: "a" * length
    )
    return st.one_of(
        corrupted,
        edged,
        gapped,
        overlong,
        st.just(""),
        st.just(_NAMESPACE_SEPARATOR),
    )
