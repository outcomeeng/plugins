"""Candidate texts and invalid offsets for the audit-change runner's ``read-candidate`` pieces.

A candidate is any UTF-8 text a Change record could hold, from empty to several
times the piece limit. The wire texts are the candidates read through the entry
point, where each piece costs one process, so they cover the characters whose
serialized form differs most from their text. The strategies vary the three properties that decide how
a piece fills: the candidate's length, the width of each character in UTF-8, and
how much each character grows when it is escaped in a serialized response. A
run of one short chunk repeated many times reaches lengths far past the
limit without a generated text of that size, and the chunk alphabets cover ASCII
text, characters JSON escapes, two- and three-byte characters, and characters
outside the Basic Multilingual Plane.

No strategy consults the runner: the lengths and alphabets come from the
contract, not from the runner's own piece arithmetic, so the pieces a linked
test observes are never the generator's own verdict. The two limits the runner
declares reach the strategies that place a text near the limits as arguments,
so a change to either limit moves the sweep with it.
"""

from __future__ import annotations

import string
from typing import Final, Literal

from hypothesis import strategies as st

_SURROGATE_CATEGORIES: Final[tuple[Literal["Cs"], ...]] = ("Cs",)
_ESCAPED_CHARACTERS: Final = '"\\\n\r\t\x00\x1f\x7f '
_MAX_CHUNK = 40
# Repetition counts that put a candidate from a few characters to several pieces long.
_MAX_REPEATS = 5000
# Offsets of up to this many characters have at most five digits. A candidate
# longer than this puts a six-digit ``next`` offset in the pieces near its end,
# where the ``null`` after the last piece is two bytes shorter than the number
# and so can make the full remainder fit when one more character does not.
_FIVE_DIGIT_OFFSET_LIMIT: Final = 100_000
# The remainder sweep starts this many bytes under the response byte limit, where
# a one-byte-per-character response comes within that margin of the limit.
_REMAINDER_SWEEP_MARGIN: Final = 500

# A wire text runs from one over this fraction of the piece character limit to
# this multiple of it.
_WIRE_SHORTEST_FRACTION: Final = 4
_WIRE_LONGEST_MULTIPLE: Final = 2

# Whole parts of a fractional offset stay small enough that adding one half is
# exact in a double, so the generated number has a fractional part.
_FRACTION_WHOLE_LIMIT: Final = 1_000_000
_MAX_COMPOUND_MEMBERS: Final = 3

_PLAIN_ALPHABET = st.sampled_from(string.ascii_letters + string.digits + " .,:#-\n")
_ESCAPED_ALPHABET = st.sampled_from(_ESCAPED_CHARACTERS)
_UNESCAPED_ASCII_ALPHABET = st.sampled_from(
    string.ascii_letters + string.digits + " .,:#-"
)
_WIDE_ALPHABET = st.characters(
    min_codepoint=0x80, blacklist_categories=_SURROGATE_CATEGORIES
)
_ANY_ALPHABET = st.characters(blacklist_categories=_SURROGATE_CATEGORIES)


def _chunks() -> st.SearchStrategy[str]:
    return st.one_of(
        st.text(_PLAIN_ALPHABET, min_size=1, max_size=_MAX_CHUNK),
        st.text(_ESCAPED_ALPHABET, min_size=1, max_size=_MAX_CHUNK),
        st.text(_WIDE_ALPHABET, min_size=1, max_size=_MAX_CHUNK),
        st.text(_ANY_ALPHABET, min_size=1, max_size=_MAX_CHUNK),
    )


def candidate_texts() -> st.SearchStrategy[str]:
    """Return non-empty and empty UTF-8 texts of widely varying length and width."""
    repeated = st.builds(
        lambda chunk, repeats: chunk * repeats,
        _chunks(),
        st.integers(min_value=0, max_value=_MAX_REPEATS),
    )
    mixed = st.lists(_chunks(), min_size=0, max_size=_MAX_CHUNK).map("".join)
    # The empty candidate is the one text the contract treats apart, so it is a
    # constant branch of the domain and appears in every run.
    return st.one_of(repeated, mixed, st.just(""))


def _remainder_sweep_start(byte_limit: int) -> int:
    return byte_limit - _REMAINDER_SWEEP_MARGIN


def long_candidate_texts(byte_limit: int) -> st.SearchStrategy[str]:
    """Return texts of one byte per character, past the five-digit offsets.

    Each text repeats a generated chunk of unescaped ASCII to a generated
    length, the width at which a character adds one byte to a response and the
    ``next`` value's digit count can outweigh it. The shortest text is one
    character past the five-digit offsets; the longest keeps every request that
    leaves a remainder of the sweep at a five-digit offset, so ``byte_limit``,
    the response byte limit the runner declares, sets where the sweep starts.
    """
    shortest = _FIVE_DIGIT_OFFSET_LIMIT + 1
    longest = _FIVE_DIGIT_OFFSET_LIMIT - 1 + _remainder_sweep_start(byte_limit)
    return st.builds(
        lambda chunk, length: (chunk * (length // len(chunk) + 1))[:length],
        st.text(_UNESCAPED_ASCII_ALPHABET, min_size=1, max_size=_MAX_CHUNK),
        st.integers(min_value=shortest, max_value=longest),
    )


def wire_candidate_texts(character_limit: int) -> st.SearchStrategy[str]:
    """Return texts of escaped or wide characters that need several pieces.

    Each text repeats a generated chunk of characters JSON escapes, of characters
    above ASCII, or of any characters except surrogates, to a generated length
    from a quarter of ``character_limit`` to twice it. These are the characters
    whose serialized form differs most from their text, so a response's bytes
    on the wire differ most from a count of its characters. ``character_limit``,
    the piece character limit the runner declares, sets the range.
    """
    chunks = st.one_of(
        st.text(_ESCAPED_ALPHABET, min_size=1, max_size=_MAX_CHUNK),
        st.text(_WIDE_ALPHABET, min_size=1, max_size=_MAX_CHUNK),
        st.text(_ANY_ALPHABET, min_size=1, max_size=_MAX_CHUNK),
    )
    return st.builds(
        lambda chunk, length: (chunk * (length // len(chunk) + 1))[:length],
        chunks,
        st.integers(
            min_value=character_limit // _WIRE_SHORTEST_FRACTION,
            max_value=character_limit * _WIRE_LONGEST_MULTIPLE,
        ),
    )


def invalid_offsets() -> st.SearchStrategy[object]:
    """Return JSON values that are not non-negative integers.

    An ``offset`` counts characters of the candidate from 0, so a valid one is a
    non-negative integer. Every strategy here builds a value outside that set by
    construction: a negative integer, a number with a fractional part, a string
    (including one of digits), a boolean, ``null``, an array, or an object.
    No strategy consults the runner.
    """
    negative_integers = st.integers(max_value=-1)
    fractional_numbers = st.integers(
        min_value=-_FRACTION_WHOLE_LIMIT, max_value=_FRACTION_WHOLE_LIMIT
    ).map(lambda whole: whole + 0.5)
    strings = st.one_of(st.text(), st.integers(min_value=0).map(str))
    arrays = st.lists(st.integers(), max_size=_MAX_COMPOUND_MEMBERS)
    objects = st.dictionaries(
        st.text(max_size=_MAX_CHUNK), st.integers(), max_size=_MAX_COMPOUND_MEMBERS
    )
    return st.one_of(
        negative_integers,
        fractional_numbers,
        strings,
        st.booleans(),
        st.none(),
        arrays,
        objects,
    )


def final_piece_remainders(byte_limit: int, character_limit: int) -> range:
    """Return the remainders, in characters, a request near the end of the long text leaves.

    The remainders run from where a one-byte-per-character response comes within
    the sweep margin of ``byte_limit`` up to ``character_limit``; one of them
    leaves a final piece one byte over the limit with its ``next`` as a number.
    """
    return range(_remainder_sweep_start(byte_limit), character_limit + 1)
