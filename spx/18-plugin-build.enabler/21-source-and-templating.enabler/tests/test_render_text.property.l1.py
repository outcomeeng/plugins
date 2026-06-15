"""Properties of render_text's include handling: verbatim inlining and
unbounded recursive resolution.

For a body free of further directives and the variable delimiter, render_text
replaces the include directive with the file's content unchanged and leaves the
surrounding template untouched. Generating the body and the surrounding prose
searches the space of directive-free content — significant whitespace, markdown
structure, non-ASCII — that the single-line and multi-line examples never
covered.

When an included body itself contains an include directive, render_text
re-processes the inlined body, so an include chain resolves to its innermost
fragment regardless of depth. Generating the chain depth searches that recursion
beyond the one- and two-level scenario examples, falsifying an implementation
that handles a fixed number of passes but breaks deeper.

Scope note: the verbatim guarantee is conditional at render level. A body that
itself contains an include/require_skill directive is recursively expanded, and
a body containing the variable delimiter triggers a Jinja pass — so the verbatim
domain is deliberately the directive-free, variable-delimiter-free body. The
unconditional verbatim read lives at expand_include
(test_expand_include.property.l1.py).
"""

from __future__ import annotations

import pytest
from hypothesis import given
from hypothesis import strategies as st

from outcomeeng.distribution.build import (
    IMPLEMENTED,
    SHARED_FRAGMENT_FILENAME,
    IncludeDirective,
    format_directive,
    render_text,
)
from outcomeeng_testing.generators.fragments import inert_fragment_bodies
from outcomeeng_testing.harnesses.src_tree import src_tree

# Arbitrary kebab-case labels for the shared topic; the body and the
# surrounding content are the varying domain under test.
SCOPE = "samplescope"
TOPIC = "sampletopic"
_DIRECTIVE_TEXT = format_directive(
    IncludeDirective(path=f"{SCOPE}/{TOPIC}/{SHARED_FRAGMENT_FILENAME}")
)

# Chain-resolution domain: topics chain-topic-0 .. chain-topic-(N-1), each
# including the next, the last carrying the directive-free sentinel body.
CHAIN_TOPIC_PREFIX = "chain-topic"
SENTINEL_BODY = "innermost chain body\nsecond line\n"


def _chain_topic_path(index: int) -> str:
    return f"{SCOPE}/{CHAIN_TOPIC_PREFIX}-{index}/{SHARED_FRAGMENT_FILENAME}"


@pytest.fixture(autouse=True)
def _require_module_implemented() -> None:
    if not IMPLEMENTED:
        pytest.fail(
            "outcomeeng.distribution.build is a stub; implement it before "
            "running this test, or filter via `spx test passing` "
            "(node is listed in spx/EXCLUDE)"
        )


class TestInlinesBodyVerbatim:
    """render_text replaces the directive with the file's body unchanged."""

    @given(
        prefix=inert_fragment_bodies(),
        body=inert_fragment_bodies(),
        suffix=inert_fragment_bodies(),
    )
    def test_body_inlined_verbatim_between_surrounding_content(
        self, prefix: str, body: str, suffix: str
    ) -> None:
        with src_tree() as builder:
            builder.add_shared_topic(SCOPE, TOPIC, body)
            # Newline-separate the parts: each value is individually delimiter-free,
            # but directly abutting them could form a delimiter that straddles a
            # junction (e.g. a prefix ending in "{" beside a body starting "{!"),
            # which render_text would then expand or Jinja-process. The newline
            # isolates verbatim inlining from junction delimiter formation.
            template = f"{prefix}\n{_DIRECTIVE_TEXT}\n{suffix}"

            result = render_text(template, shared_root=builder.shared_root)

            assert result == f"{prefix}\n{body}\n{suffix}"


class TestRecursiveIncludeDepthResolves:
    """render_text resolves an include chain to its innermost body at any depth."""

    @given(depth=st.integers(min_value=1, max_value=8))
    def test_chain_of_n_includes_resolves_to_innermost_body(self, depth: int) -> None:
        with src_tree() as builder:
            for index in range(depth):
                if index == depth - 1:
                    body = SENTINEL_BODY
                else:
                    body = format_directive(
                        IncludeDirective(path=_chain_topic_path(index + 1))
                    )
                builder.add_shared_topic(SCOPE, f"{CHAIN_TOPIC_PREFIX}-{index}", body)

            template = format_directive(IncludeDirective(path=_chain_topic_path(0)))

            result = render_text(template, shared_root=builder.shared_root)

            # Every level of the chain re-processes its inlined body until the
            # directive-free sentinel surfaces, regardless of how deep the chain.
            assert result == SENTINEL_BODY
