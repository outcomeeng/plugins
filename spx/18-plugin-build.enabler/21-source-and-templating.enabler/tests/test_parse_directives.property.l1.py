"""Round-trip property: parse(format(d)) == (d,) for every directive d.

If parse_directives and format_directive are inverses, then formatting a
directive and parsing the result must yield the original directive. This
property catches representation drift between the two functions.
"""

from __future__ import annotations

import pytest
from hypothesis import given

from outcomeeng.scripts.build_plugins import (
    IMPLEMENTED,
    Directive,
    format_directive,
    parse_directives,
)
from outcomeeng_testing.generators.directives import directives

if not IMPLEMENTED:
    pytest.skip(
        "outcomeeng.scripts.build_plugins is a stub — see spx/EXCLUDE",
        allow_module_level=True,
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
