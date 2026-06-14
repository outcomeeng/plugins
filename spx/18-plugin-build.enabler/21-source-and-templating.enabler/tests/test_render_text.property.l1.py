"""Property: render_text inlines an included body verbatim into the output.

For a body free of further directives and the variable delimiter, render_text
replaces the include directive with the file's content unchanged and leaves the
surrounding template untouched. Generating the body and the surrounding prose
searches the space of directive-free content — significant whitespace, markdown
structure, non-ASCII — that the single-line and multi-line examples never
covered.

Scope note: the verbatim guarantee is conditional at render level. A body that
itself contains an include/require_skill directive is recursively expanded, and
a body containing the variable delimiter triggers a Jinja pass — so the domain
here is deliberately the directive-free, variable-delimiter-free body. The
unconditional verbatim read lives at expand_include
(test_expand_include.property.l1.py).
"""

from __future__ import annotations

import pytest
from hypothesis import given

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
