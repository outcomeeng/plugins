"""Compliance evidence for whole-pipeline build traceability."""

from __future__ import annotations

import pytest

from outcomeeng.distribution.build import IMPLEMENTED
from outcomeeng_testing.harnesses.plugin_build import (
    canonical_dist_files_trace_to_source_ancestors,
)


@pytest.fixture(autouse=True)
def _require_module_implemented() -> None:
    if not IMPLEMENTED:
        pytest.fail(
            "outcomeeng.distribution.build is a stub; implement it before "
            "running this test, or filter via `spx test passing` "
            "(node is listed in spx/EXCLUDE)"
        )


def test_dist_files_trace_to_source_ancestor() -> None:
    assert canonical_dist_files_trace_to_source_ancestors()
