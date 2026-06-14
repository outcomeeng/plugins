"""Property: expand_include returns the referenced file's body verbatim.

expand_include reads the included file and returns its bytes unchanged — no
parsing, no normalization. The invariant holds for every body, including one
that contains the custom directive or variable delimiters, significant
whitespace, or non-ASCII. Searching that space catches a reader that would
mangle delimiter-like content or collapse whitespace; two hand-picked example
bodies would not.
"""

from __future__ import annotations

import pytest
from hypothesis import given

from outcomeeng.distribution.build import (
    IMPLEMENTED,
    SHARED_FRAGMENT_FILENAME,
    IncludeDirective,
    expand_include,
)
from outcomeeng_testing.generators.fragments import fragment_bodies
from outcomeeng_testing.harnesses.src_tree import src_tree

# Arbitrary kebab-case labels for the shared topic; the body, not the path, is
# the varying domain under test.
SCOPE = "samplescope"
TOPIC = "sampletopic"


@pytest.fixture(autouse=True)
def _require_module_implemented() -> None:
    if not IMPLEMENTED:
        pytest.fail(
            "outcomeeng.distribution.build is a stub; implement it before "
            "running this test, or filter via `spx test passing` "
            "(node is listed in spx/EXCLUDE)"
        )


class TestReturnsBodyVerbatim:
    """expand_include reproduces any fragment body unchanged."""

    @given(fragment_bodies())
    def test_body_returned_verbatim(self, body: str) -> None:
        with src_tree() as builder:
            builder.add_shared_topic(SCOPE, TOPIC, body)
            directive = IncludeDirective(
                path=f"{SCOPE}/{TOPIC}/{SHARED_FRAGMENT_FILENAME}"
            )

            result = expand_include(directive, shared_root=builder.shared_root)

            assert result == body
