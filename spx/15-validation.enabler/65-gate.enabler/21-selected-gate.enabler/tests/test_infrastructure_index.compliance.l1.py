"""Compliance evidence that building the static import index executes nothing."""

from __future__ import annotations

import sys

from outcomeeng_testing.harnesses.infrastructure_index import (
    side_effect_layout,
    synthetic_repository,
)


def test_indexing_a_module_with_an_import_side_effect_leaves_no_trace() -> None:
    with synthetic_repository() as repo:
        layout = side_effect_layout(repo)

        index = repo.index()

        assert layout.module in index.modules
        assert index.reaching_tests(layout.module) == (layout.test,)
        assert not layout.marker.exists()
        assert layout.module not in sys.modules
