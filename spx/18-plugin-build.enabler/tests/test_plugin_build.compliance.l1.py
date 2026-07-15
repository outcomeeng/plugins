"""Compliance evidence for whole-pipeline build traceability."""

from __future__ import annotations

from outcomeeng_testing.harnesses.plugin_build import (
    canonical_dist_files_trace_to_source_ancestors,
    orphaned_dist_artifact_is_rejected,
)


def test_dist_files_trace_to_source_ancestor() -> None:
    assert canonical_dist_files_trace_to_source_ancestors()


def test_orphaned_dist_artifact_is_rejected() -> None:
    assert orphaned_dist_artifact_is_rejected()
