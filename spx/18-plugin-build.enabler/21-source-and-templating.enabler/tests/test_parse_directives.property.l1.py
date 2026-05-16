"""Round-trip property: parse(format(d)) == (d,) for every directive d.

If parse_directives and format_directive are inverses, then formatting a
directive and parsing the result must yield the original directive. This
property catches representation drift between the two functions.
"""

from __future__ import annotations

import pytest
from hypothesis import given

from outcomeeng.distribution.build import (
    IMPLEMENTED,
    Directive,
    format_directive,
    parse_directives,
)
from outcomeeng_testing.generators.directives import directives


@pytest.fixture(autouse=True)
def _require_module_implemented() -> None:
    if not IMPLEMENTED:
        pytest.fail(
            "outcomeeng.distribution.build is a stub; implement it before "
            "running this test, or filter via `spx test passing` "
            "(node is listed in spx/EXCLUDE)"
        )


class TestParseFormatRoundtrip:
    """Every directive survives a format-then-parse cycle unchanged."""

    @given(directives())
    def test_parse_of_format_yields_original_directive(
        self, directive: Directive
    ) -> None:
        text = format_directive(directive)
        parsed = parse_directives(text)
        assert parsed == (directive,)
