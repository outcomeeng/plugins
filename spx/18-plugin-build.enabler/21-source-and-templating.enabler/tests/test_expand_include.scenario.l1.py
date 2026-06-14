"""Scenario: an include whose target fragment is absent fails loudly.

expand_include raises IncludeResolutionError when the referenced file does not
exist, so an unresolved include fails the build instead of emitting empty or
partial output. Verbatim body preservation is a property
(test_expand_include.property.l1.py), not a named example.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from outcomeeng.distribution.build import (
    IMPLEMENTED,
    IncludeDirective,
    IncludeResolutionError,
    expand_include,
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


MISSING_FRAGMENT_PATH = "no-such-scope/no-such-topic/fragment.md"


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
