"""Compliance evidence for whole-pipeline build traceability."""

from __future__ import annotations

from outcomeeng_testing.harnesses.plugin_build import (
    canonical_dist_files_trace_to_source_ancestors,
)


def test_dist_files_trace_to_source_ancestor() -> None:
    assert canonical_dist_files_trace_to_source_ancestors()
