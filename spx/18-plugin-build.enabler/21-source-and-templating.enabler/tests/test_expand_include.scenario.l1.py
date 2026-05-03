"""Scenarios for expand_include.

Verifies that expand_include reads the included file's body verbatim,
preserves multi-line structure, and raises IncludeResolutionError when
the target file does not exist.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from outcomeeng.scripts.build_plugins import (
    IMPLEMENTED,
    IncludeDirective,
    IncludeResolutionError,
    expand_include,
)
from outcomeeng_testing.harnesses.scenarios import (
    SCENARIO_MULTILINE_INCLUDE,
    SCENARIO_SIMPLE_INCLUDE,
)
from outcomeeng_testing.harnesses.src_tree import SrcTreeBuilder

if not IMPLEMENTED:
    pytest.skip(
        "outcomeeng.scripts.build_plugins is a stub — see spx/EXCLUDE",
        allow_module_level=True,
    )

MISSING_FRAGMENT_PATH = "no-such-scope/no-such-topic/fragment.md"


class TestReturnsBodyVerbatim:
    """expand_include returns the included file's body unchanged."""

    def test_simple_fragment_body_returned_verbatim(self, tmp_path: Path) -> None:
        builder = SrcTreeBuilder(tmp_path)
        SCENARIO_SIMPLE_INCLUDE.apply(builder)

        result = expand_include(
            SCENARIO_SIMPLE_INCLUDE.directive,
            shared_root=builder.shared_root,
        )

        assert result == SCENARIO_SIMPLE_INCLUDE.fragment_body

    def test_multiline_fragment_preserves_structure(self, tmp_path: Path) -> None:
        builder = SrcTreeBuilder(tmp_path)
        SCENARIO_MULTILINE_INCLUDE.apply(builder)

        result = expand_include(
            SCENARIO_MULTILINE_INCLUDE.directive,
            shared_root=builder.shared_root,
        )

        assert result == SCENARIO_MULTILINE_INCLUDE.fragment_body


class TestRaisesOnMissingFile:
    """expand_include raises IncludeResolutionError when the file is absent."""

    def test_missing_fragment_raises_include_resolution_error(
        self, tmp_path: Path
    ) -> None:
        builder = SrcTreeBuilder(tmp_path)
        builder.shared_root.mkdir(parents=True, exist_ok=True)

        with pytest.raises(IncludeResolutionError):
            expand_include(
                IncludeDirective(path=MISSING_FRAGMENT_PATH),
                shared_root=builder.shared_root,
            )
