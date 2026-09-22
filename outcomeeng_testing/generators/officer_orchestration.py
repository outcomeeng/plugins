"""Generated input domains for the officer-ledger derivation evidence."""

from __future__ import annotations

import decimal
import functools
import json
import sys
from dataclasses import dataclass
from typing import Protocol

from hypothesis import strategies as st

# A leading tilde cannot open any JSON production, so every body built from this
# prefix is a non-JSON document by construction rather than by filtering.
NON_JSON_PREFIX = "~"
DIGITS = "0123456789"
# How far the nesting probe descends before it reports that this interpreter's
# scanner guards no depth it can reach. A document past this width says more
# about the machine's memory than about the scanner, so the probe stops here.
NESTING_PROBE_CEILING = 1 << 20
# How far past the probed refusal depth a generated document may nest. Every
# width in the band refuses, and the band keeps the domain from collapsing onto
# the single depth the probe returned.
NESTING_OVERSHOOT = 64
# Bytes UTF-8 assigns to no position: `0xC0` and `0xC1` encode only overlong
# forms, and `0xF5` through `0xFF` lie past the last code point UTF-8 reaches.
# One of them anywhere in a stream refuses the decode wherever it falls, so a
# document carrying one is undecodable by construction rather than by position.
UNDECODABLE_BYTES = (0xC0, 0xC1, *range(0xF5, 0x100))
# The widest ASCII run placed either side of the undecodable byte, so the
# refusal is reached from a document whose every other byte decodes.
MAX_DECODABLE_RUN = 16
# The significant-digit limit the default decimal context rounds a total to.
# The generated decimal widths straddle it so the domain reaches the precision
# where an exact accumulation and a default-context one disagree.
DEFAULT_DECIMAL_PRECISION = decimal.DefaultContext.prec
MAX_INTEGER_DIGITS = 12
MAX_FRACTION_DIGITS = DEFAULT_DECIMAL_PRECISION + 8


@dataclass(frozen=True, slots=True)
class EventPayload:
    """The values one generated ledger event carries.

    This module builds the payload, so it owns the payload's shape: every
    consumer reaches each value through these attributes rather than
    re-typing a key. The names are this domain's own — the document field each
    value lands under is the derivation's to name, and a consumer reads that
    name from the derivation module.
    """

    label: str
    currency: str
    amount: str
    duration: str


class LedgerVocabulary(Protocol):
    """The source-owned names these domains are constructed against."""

    LEDGER_FIELD: str
    SCHEMA_VERSION: int
    SCHEMA_VERSION_FIELD: str
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


def _decimal_literals(signs: st.SearchStrategy[str]) -> st.SearchStrategy[str]:
    """Plain decimal literals whose fractional precision varies per value.

    The domain straddles the precision at which a decimal context starts
    rounding a running total. The narrow branch ranges from an absent fraction
    through widths an IEEE-754 double carries exactly and widths no double
    represents at all. The wide branch carries a coefficient longer than
    `DEFAULT_DECIMAL_PRECISION`, so a total accumulated in the default context
    loses digits the literal carried while an exact accumulation keeps them —
    the precision at which the two accumulations disagree, and the reason the
    domain reaches it rather than stopping below it. Literals are composed as
    text rather than through a float or a fixed-`places` decimal, so the
    generated value is exactly the digits the derivation receives.
    """
    # A leading non-zero digit makes the coefficient as long as the fraction,
    # so the width past the default precision is significant digits rather than
    # leading zeros no context would round away.
    wide_fractions = st.from_regex(
        rf"[1-9][0-9]{{{DEFAULT_DECIMAL_PRECISION},{MAX_FRACTION_DIGITS - 1}}}",
        fullmatch=True,
    )
    return st.builds(
        lambda sign, integer, fraction: (
            f"{sign}{integer}.{fraction}" if fraction else f"{sign}{integer}"
        ),
        sign=signs,
        integer=st.from_regex(
            rf"0|[1-9][0-9]{{0,{MAX_INTEGER_DIGITS - 1}}}", fullmatch=True
        ),
        fraction=st.one_of(
            st.text(alphabet=DIGITS, min_size=0, max_size=MAX_FRACTION_DIGITS),
            wide_fractions,
        ),
    )


def spend_amounts() -> st.SearchStrategy[str]:
    """Signed decimal spend amounts of varying fractional precision."""
    return _decimal_literals(st.sampled_from(("", "-")))


def durations() -> st.SearchStrategy[str]:
    """Non-negative wall-time durations of varying fractional precision."""
    return _decimal_literals(st.just(""))


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


def _oversized_integer_literals() -> st.SearchStrategy[str]:
    """Integer literals wider than the interpreter converts from a digit string.

    The JSON scanner reads an integer literal by converting its digit string,
    so a literal past `sys.get_int_max_str_digits()` refuses the whole document
    — a refusal no leading character announces and no syntax error names. The
    width is read from the running interpreter rather than copied here, and a
    limit of zero means the interpreter converts any width, so the domain then
    holds no member at all.
    """
    limit = sys.get_int_max_str_digits()
    if not limit:
        return st.nothing()
    return st.integers(min_value=limit + 1, max_value=limit + 64).map(
        lambda width: "1" * width
    )


@functools.cache
def _nesting_refusal_depth() -> int | None:
    """The shallowest probed nesting depth the running scanner refuses.

    No interpreter publishes the depth at which its JSON scanner's recursion
    guard trips — the figure moves with the feature release and with the stack
    the caller descends from — so the depth is read from the running scanner by
    doubling a nesting run until it refuses, exactly as the oversized-integer
    domain reads its width from `sys.get_int_max_str_digits()`. A deeper stack
    trips the guard sooner, so a depth this probe reaches from its own shallow
    stack still refuses from the deeper one a test runner descends from.

    A `None` result means the probe reached `NESTING_PROBE_CEILING` without a
    refusal, and the domain then holds no member at all.
    """
    depth = 1
    while depth <= NESTING_PROBE_CEILING:
        try:
            json.loads("[" * depth)
        except RecursionError:
            return depth
        except ValueError:
            # The run is unterminated, so every depth below the guard refuses
            # for want of a value rather than for want of stack. That refusal
            # is the ordinary syntax one, not the guard this probe looks for.
            pass
        depth *= 2
    return None


def _deeply_nested_documents() -> st.SearchStrategy[str]:
    """Documents nested past the running scanner's recursion guard.

    The run is left unterminated: the scanner descends through every opening
    bracket before it reads anything else, so the guard is what refuses and the
    document stays half the width a balanced one would need.
    """
    depth = _nesting_refusal_depth()
    if depth is None:
        return st.nothing()
    return st.integers(min_value=depth, max_value=depth + NESTING_OVERSHOOT).map(
        lambda width: "[" * width
    )


def _undecodable_byte_documents() -> st.SearchStrategy[bytes]:
    """Byte sequences no codec decodes, surrounded by bytes that do.

    A source arrives at the entry point as a stream of bytes a codec turns into
    text, so a byte the codec assigns to nothing refuses the document before a
    JSON production is ever read. The undecodable byte is placed between two
    decodable runs, so the refusal is reached from a document the codec would
    otherwise have carried whole.
    """
    ascii_runs = st.binary(max_size=MAX_DECODABLE_RUN).map(
        lambda raw: bytes(byte & 0x7F for byte in raw)
    )
    return st.builds(
        lambda prefix, byte, suffix: prefix + bytes([byte]) + suffix,
        prefix=ascii_runs,
        byte=st.sampled_from(UNDECODABLE_BYTES),
        suffix=ascii_runs,
    )


def parser_refused_documents(
    module: LedgerVocabulary,
) -> st.SearchStrategy[str | bytes]:
    """Source documents the JSON parser refuses to read at all.

    One shape per class the refusal contract names. Text no JSON production
    can open. An integer literal past the interpreter's conversion limit,
    carried both alone and inside an otherwise well-formed envelope, so the
    domain reaches a refusal the document's opening character does not
    announce. Nesting past the scanner's own recursion guard, whose depth the
    running interpreter supplies. And bytes no codec decodes, which refuse the
    document before any JSON production is read — the class the document's
    text cannot express, because text is already decoded, so it reaches the
    entry point as the bytes a stream still has to decode.
    """
    oversized = _oversized_integer_literals()
    return st.one_of(
        st.text(max_size=32).map(lambda text: NON_JSON_PREFIX + text),
        oversized,
        oversized.map(
            lambda literal: f'{{"{module.SCHEMA_VERSION_FIELD}": {literal}}}'
        ),
        _deeply_nested_documents(),
        _undecodable_byte_documents(),
    )


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
    # A body the parser refuses part-way through rather than at its first
    # character: the ledger key is present, and the literal under it is wider
    # than the interpreter converts, so the body never becomes a ledger object.
    unreadable_ledger = _oversized_integer_literals().map(
        lambda literal: f'{{"{module.LEDGER_FIELD}": {literal}}}'
    )
    # A body whose ledger key is present and whose value the parser reads
    # whole, but which is not an object: a string, an array, null, a number,
    # or a boolean. The refusal branch above never reaches this shape, because
    # the parser rejects its literal before any value is typed, so only these
    # bodies carry a readable non-object ledger into the derivation.
    readable_non_object_ledger = st.one_of(
        st.text(max_size=24),
        st.lists(st.integers(), max_size=4),
        st.none(),
        st.integers(),
        st.floats(allow_nan=False, allow_infinity=False),
        st.booleans(),
    ).map(lambda value: json.dumps({module.LEDGER_FIELD: value}))
    return st.one_of(
        unparseable,
        unreadable_ledger,
        readable_non_object_ledger,
        scalars,
        arrays,
        objects,
        unwrapped_events,
    )


def read_details() -> st.SearchStrategy[dict[str, str]]:
    """Payload a read carries beside its cause."""
    return st.dictionaries(
        keys=st.from_regex(r"[a-z]{1,10}", fullmatch=True),
        values=st.text(max_size=24),
        max_size=3,
    )


def foreign_read_causes(module: LedgerVocabulary) -> st.SearchStrategy[object]:
    """Read causes outside the derivation's declared cause set.

    A source document's `cause` is whatever JSON carries under that key, so the
    domain spans both halves of the JSON value space. The scalar branch is
    filtered against the declared set, which each of its members can be
    compared with. The container branch — a JSON array and a JSON object — lies
    outside a set of strings by construction and carries no such filter,
    because comparing an unhashable value against a set is the very operation a
    gate performs on it: filtering here would refuse the domain instead of
    reaching the refusal the document owes. A container's members are drawn so
    that a declared cause can sit among them, which is what a gate reading
    inside a container rather than reading the value it received would find.
    """
    declared = st.sampled_from(sorted(module.READ_CAUSES))
    members = st.one_of(declared, st.text(max_size=16), st.integers())
    scalars = st.one_of(
        st.text(max_size=16),
        st.integers(),
        st.booleans(),
        st.none(),
    ).filter(lambda cause: cause not in module.READ_CAUSES)
    containers = st.one_of(
        st.lists(members, max_size=3),
        st.dictionaries(
            keys=st.from_regex(r"[a-z]{1,10}", fullmatch=True),
            values=members,
            max_size=3,
        ),
    )
    return st.one_of(scalars, containers)


def foreign_argument_vectors(module: LedgerVocabulary) -> st.SearchStrategy[list[str]]:
    """Argument vectors other than the entry point's declared derive vector."""
    declared = [module.DERIVE_OPERATION]
    return st.lists(
        st.from_regex(r"[a-z][a-z-]{0,11}", fullmatch=True),
        max_size=3,
    ).filter(lambda vector: vector != declared)


def foreign_schema_versions(module: LedgerVocabulary) -> st.SearchStrategy[object]:
    """Schema versions other than the integer the entry point declares.

    Each branch is constructed rather than filtered out of a wider domain, so
    it names the way its members differ. A boolean and a float can carry the
    declared version's value without being that integer — the distinction a
    gate comparing values alone does not draw — while the remaining branches
    differ in value, in type, or in both.
    """
    declared = module.SCHEMA_VERSION
    return st.one_of(
        st.booleans(),
        st.just(float(declared)),
        st.floats(allow_nan=False, allow_infinity=False),
        st.integers().filter(lambda version: version != declared),
        st.text(max_size=8),
        st.none(),
    )


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


def event_payloads() -> st.SearchStrategy[EventPayload]:
    """The label, currency, amount, and duration one generated event carries."""
    return st.builds(
        EventPayload,
        label=pass_labels(),
        currency=currencies(),
        amount=spend_amounts(),
        duration=durations(),
    )


def repeated_mail_series() -> st.SearchStrategy[list[tuple[int, EventPayload]]]:
    """Store ids drawn with repetition from a pool, each with one payload."""
    return st.lists(store_message_ids(), min_size=1, max_size=3, unique=True).flatmap(
        lambda pool: st.lists(
            st.tuples(st.sampled_from(pool), event_payloads()),
            min_size=1,
            max_size=6,
        )
    )


def repeated_run_series() -> st.SearchStrategy[list[tuple[str, EventPayload]]]:
    """Run tokens drawn with repetition from a pool, each with one payload."""
    return st.lists(run_tokens(), min_size=1, max_size=3, unique=True).flatmap(
        lambda pool: st.lists(
            st.tuples(st.sampled_from(pool), event_payloads()),
            min_size=1,
            max_size=6,
        )
    )


def repeat_counts() -> st.SearchStrategy[int]:
    """How often one record repeats a value inside a single collection."""
    return st.integers(min_value=2, max_value=4)


def finding_entries() -> st.SearchStrategy[dict[str, str]]:
    """The finding-provenance payload one record lists in its collection."""
    return st.dictionaries(
        keys=st.from_regex(r"[a-z]{1,10}", fullmatch=True),
        values=st.text(max_size=24),
        max_size=3,
    )


def declared_read_causes(module: LedgerVocabulary) -> st.SearchStrategy[str]:
    """Causes drawn from the derivation's own declared cause set."""
    return st.sampled_from(sorted(module.READ_CAUSES))
