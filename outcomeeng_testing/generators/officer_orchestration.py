"""Generated input domains for the officer-ledger derivation evidence."""

from __future__ import annotations

import json
from typing import Protocol

from hypothesis import strategies as st

# A leading tilde cannot open any JSON production, so every body built from this
# prefix is a non-JSON document by construction rather than by filtering.
NON_JSON_PREFIX = "~"


class LedgerVocabulary(Protocol):
    """The source-owned names these domains are constructed against."""

    LEDGER_FIELD: str
    DERIVE_OPERATION: str
    READ_CAUSES: frozenset[str]
    SCALAR_EVENT_COLLECTIONS: tuple[tuple[str, str], ...]


def store_message_ids() -> st.SearchStrategy[int]:
    """Integer identities the mail store assigns to a delivered record."""
    return st.integers(min_value=1, max_value=1_000_000)


def run_tokens() -> st.SearchStrategy[str]:
    """Non-empty run tokens a sealed verification-journal run carries."""
    return st.from_regex(r"[a-z0-9][a-z0-9-]{0,23}", fullmatch=True)


def change_identifiers() -> st.SearchStrategy[str]:
    """Change identities of the shape the declared Change store issues."""
    return st.from_regex(r"[a-z]{1,8}/[a-z]{1,8}#[0-9]{1,4}", fullmatch=True)


def leading_record_counts() -> st.SearchStrategy[int]:
    """How many conforming records precede an offending one in a document."""
    return st.integers(min_value=0, max_value=3)


def pass_labels() -> st.SearchStrategy[str]:
    """Labels an officer round carries as its `pass` event value."""
    return st.from_regex(r"(round|pass)-[0-9]{1,3}", fullmatch=True)


def currencies() -> st.SearchStrategy[str]:
    """Currency codes a spend event denominates its amount in."""
    return st.from_regex(r"[A-Z]{3}", fullmatch=True)


def spend_amounts() -> st.SearchStrategy[str]:
    """Decimal spend amounts, carried as strings so no float rounding enters."""
    return st.decimals(
        min_value=-1_000_000,
        max_value=1_000_000,
        places=2,
        allow_nan=False,
        allow_infinity=False,
    ).map(str)


def durations() -> st.SearchStrategy[str]:
    """Non-negative wall-time durations, carried as decimal strings."""
    return st.decimals(
        min_value=0,
        max_value=1_000_000,
        places=2,
        allow_nan=False,
        allow_infinity=False,
    ).map(str)


def spend_series() -> st.SearchStrategy[dict[str, list[str]]]:
    """Amounts grouped by the currency that denominates each of them."""
    return st.dictionaries(
        keys=currencies(),
        values=st.lists(spend_amounts(), min_size=1, max_size=6),
        min_size=1,
        max_size=4,
    )


def duration_series() -> st.SearchStrategy[list[str]]:
    """Durations spread across the events of one derivation."""
    return st.lists(durations(), min_size=1, max_size=8)


def non_ledger_bodies(module: LedgerVocabulary) -> st.SearchStrategy[str]:
    """Mail-record bodies that are not a JSON document carrying a ledger object."""
    scalars = st.one_of(
        st.integers(),
        st.booleans(),
        st.none(),
        st.text(max_size=24),
    ).map(json.dumps)
    arrays = st.lists(st.integers(), max_size=4).map(json.dumps)
    foreign_keys = st.from_regex(r"[a-z]{1,10}", fullmatch=True).filter(
        lambda key: key != module.LEDGER_FIELD
    )
    objects = st.dictionaries(
        keys=foreign_keys,
        values=st.integers(),
        max_size=4,
    ).map(json.dumps)
    # Event fields carried at the top level rather than under a ledger object:
    # the body that would contribute were the ledger gate absent.
    unwrapped_events = st.dictionaries(
        keys=st.sampled_from(
            [event_field for event_field, _ in module.SCALAR_EVENT_COLLECTIONS]
        ),
        values=pass_labels(),
        min_size=1,
    ).map(json.dumps)
    unparseable = st.text(max_size=32).map(lambda text: NON_JSON_PREFIX + text)
    return st.one_of(unparseable, scalars, arrays, objects, unwrapped_events)


def read_details() -> st.SearchStrategy[dict[str, str]]:
    """Payload a read carries beside its cause."""
    return st.dictionaries(
        keys=st.from_regex(r"[a-z]{1,10}", fullmatch=True),
        values=st.text(max_size=24),
        max_size=3,
    )


def foreign_read_causes(module: LedgerVocabulary) -> st.SearchStrategy[object]:
    """Read causes outside the derivation's declared cause set."""
    return st.one_of(
        st.text(max_size=16),
        st.integers(),
        st.booleans(),
        st.none(),
    ).filter(lambda cause: cause not in module.READ_CAUSES)


def foreign_argument_vectors(module: LedgerVocabulary) -> st.SearchStrategy[list[str]]:
    """Argument vectors other than the entry point's declared derive vector."""
    declared = [module.DERIVE_OPERATION]
    return st.lists(
        st.from_regex(r"[a-z][a-z-]{0,11}", fullmatch=True),
        max_size=3,
    ).filter(lambda vector: vector != declared)


def mail_carriers() -> st.SearchStrategy[list[tuple[int, str]]]:
    """Distinct mail identities, each carrying one pass label."""
    return st.lists(
        st.tuples(store_message_ids(), pass_labels()),
        min_size=1,
        max_size=4,
        unique_by=lambda carrier: carrier[0],
    )


def journal_carriers() -> st.SearchStrategy[list[tuple[str, str]]]:
    """Distinct run tokens, each carrying one pass label."""
    return st.lists(
        st.tuples(run_tokens(), pass_labels()),
        min_size=1,
        max_size=4,
        unique_by=lambda carrier: carrier[0],
    )


def repeated_run_series() -> st.SearchStrategy[list[tuple[str, str]]]:
    """Run tokens drawn with repetition from a pool, each with one pass label."""
    return st.lists(run_tokens(), min_size=1, max_size=3, unique=True).flatmap(
        lambda pool: st.lists(
            st.tuples(st.sampled_from(pool), pass_labels()),
            min_size=1,
            max_size=6,
        )
    )
