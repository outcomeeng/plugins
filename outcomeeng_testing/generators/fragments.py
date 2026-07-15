"""Hypothesis strategies for include-fragment body content.

Powers the verbatim-preservation property tests: once an include resolves, the
fragment file's body must reappear unchanged. The body is the varying domain,
so the evidence searches the space of document content instead of naming one
example. Two strategies, one per contract boundary in
``outcomeeng.distribution.build``:

- ``fragment_bodies()`` — arbitrary text, delimiter sequences included.
  ``expand_include`` reads the referenced file verbatim, so its preservation
  holds for every body, including one that contains the custom directive or
  variable delimiters.
- ``inert_fragment_bodies()`` — text free of the custom directive delimiter
  (``BLOCK_DELIMITER_START``) and variable delimiter (``VARIABLE_DELIMITER_START``).
  ``render_text`` recursively expands directives found in an included body and
  runs a Jinja pass when the variable delimiter appears, so its verbatim
  inlining holds only for a body that carries neither token.
"""

from __future__ import annotations

from hypothesis import strategies as st
from hypothesis.strategies import SearchStrategy

from outcomeeng.distribution.build import (
    BLOCK_DELIMITER_END,
    BLOCK_DELIMITER_START,
    VARIABLE_DELIMITER_END,
    VARIABLE_DELIMITER_START,
)

# Characters that exercise verbatim preservation: prose, markdown structure,
# whitespace a naive normalizer would collapse, and non-ASCII that must survive
# the UTF-8 round trip through the fragment file.
_BODY_ALPHABET = (
    "abcdefghijklmnopqrstuvwxyz"
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "0123456789"
    " \t\n"
    "#-*`_>|.:/'\"()[]"
    "{}%!"
    "é—…✓→"
)

_MAX_LINE_LENGTH = 80
_MAX_LINES = 12

# Delimiter sequences whose presence is the interesting edge for expand_include:
# the reader must reproduce them, not interpret them. Built from source-owned
# delimiter constants so the tokens track the production contract.
_DELIMITER_TOKENS = [
    BLOCK_DELIMITER_START,
    BLOCK_DELIMITER_END,
    VARIABLE_DELIMITER_START,
    VARIABLE_DELIMITER_END,
    "{%",
    "%}",
    "{{",
    "}}",
]


def _lines() -> SearchStrategy[list[str]]:
    return st.lists(
        st.text(alphabet=_BODY_ALPHABET, max_size=_MAX_LINE_LENGTH),
        max_size=_MAX_LINES,
    )


def fragment_bodies() -> SearchStrategy[str]:
    """Arbitrary document bodies, delimiter sequences allowed.

    The domain spans prose, markdown structure, significant whitespace,
    non-ASCII, and the custom delimiter tokens themselves. Use for the
    unconditional verbatim contract of ``expand_include``.
    """
    return st.lists(
        st.one_of(
            st.text(alphabet=_BODY_ALPHABET, max_size=_MAX_LINE_LENGTH),
            st.sampled_from(_DELIMITER_TOKENS),
        ),
        max_size=_MAX_LINES,
    ).map("\n".join)


def inert_fragment_bodies() -> SearchStrategy[str]:
    """Document bodies free of the custom directive and variable delimiters.

    ``render_text`` inlines such a body verbatim because no token triggers a
    further directive expansion or Jinja pass.
    """
    return (
        _lines()
        .map("\n".join)
        .filter(
            lambda body: (
                BLOCK_DELIMITER_START not in body
                and VARIABLE_DELIMITER_START not in body
            )
        )
    )


def include_chain_indices() -> SearchStrategy[list[int]]:
    """Generate distinct suffixes for variable-length recursive include chains."""
    return st.lists(st.integers(min_value=0), min_size=1, unique=True)
