"""Scenarios for render_text with include directives.

End-to-end coverage of the spec assertion that an include directive
inlines the named file's body verbatim into the rendered output. Tests
cover both single-line and multi-line fragments.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from outcomeeng.distribution.build import IMPLEMENTED, render_text
from outcomeeng_testing.harnesses.scenarios import (
    SCENARIO_MULTILINE_INCLUDE,
    SCENARIO_SIMPLE_INCLUDE,
)
from outcomeeng_testing.harnesses.src_tree import SrcTreeBuilder


@pytest.fixture(autouse=True)
def _require_module_implemented() -> None:
    if not IMPLEMENTED:
        pytest.fail(
            "outcomeeng.distribution.build is a stub; implement it before "
            "running this test, or filter via `spx test passing` "
            "(node is listed in spx/EXCLUDE)"
        )


PROSE_BEFORE = "Prose before the include directive."
PROSE_AFTER = "Prose after the include directive."


class TestRendersIncludeInline:
    """render_text replaces an include directive with the named file's body."""

    def test_simple_fragment_inlined_into_surrounding_prose(
        self, tmp_path: Path
    ) -> None:
        builder = SrcTreeBuilder(tmp_path)
        SCENARIO_SIMPLE_INCLUDE.apply(builder)

        template = (
            f"{PROSE_BEFORE}\n\n"
            f"{SCENARIO_SIMPLE_INCLUDE.directive_text}\n\n"
            f"{PROSE_AFTER}"
        )
        result = render_text(template, shared_root=builder.shared_root)

        assert PROSE_BEFORE in result
        assert SCENARIO_SIMPLE_INCLUDE.fragment_body in result
        assert PROSE_AFTER in result
        assert SCENARIO_SIMPLE_INCLUDE.directive_text not in result

    def test_multiline_fragment_inlined_preserving_structure(
        self, tmp_path: Path
    ) -> None:
        builder = SrcTreeBuilder(tmp_path)
        SCENARIO_MULTILINE_INCLUDE.apply(builder)

        template = SCENARIO_MULTILINE_INCLUDE.directive_text
        result = render_text(template, shared_root=builder.shared_root)

        assert SCENARIO_MULTILINE_INCLUDE.fragment_body in result
        assert SCENARIO_MULTILINE_INCLUDE.directive_text not in result
