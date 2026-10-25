"""Compliance test for region-bounded outputs in ``review_run.py start``.

NEVER: the runner treats a relation's region-bounded output (a ``file`` with ``begin``
and ``end`` markers) as a declared generated extent. Each violating case declares a
region-bounded output beside a whole-file relation, so the whole-file extent proves the
declaration is read while the region-bounded file must stay ordinary: ``finish`` refuses
to seal it without a scope-advanced event or an unread mark and accepts it with an unread
mark. The runner and ``git`` run as real subprocesses over synthetic repositories under
``tmp_path``, hence ``l2``.
"""

from __future__ import annotations

import pathlib

import pytest

from outcomeeng_testing.generators.reviewing_changes_runs import (
    RegionOutputCase,
    region_output_cases,
)
from outcomeeng_testing.harnesses.reviewing_changes_runs import (
    MANIFEST_SECTIONS_KEY,
    build_changeset_repo,
    completed_unread,
    finish_changeset_review,
    jp,
    nodes_mentioning,
    render_generated_sources,
    run_completed_event,
    run_state_listing,
    start_changeset_review,
    without_keys,
)


@pytest.mark.parametrize(
    "case", list(region_output_cases()), ids=lambda case: case.label
)
def test_region_bounded_output_stays_an_ordinary_changed_file(
    case: RegionOutputCase, tmp_path: pathlib.Path
) -> None:
    repo = tmp_path / "repo"
    base_ref = build_changeset_repo(
        repo,
        declaration=render_generated_sources([case.region, case.control]),
        changed_paths=[case.region_path, case.control_extent],
    )

    started = start_changeset_review(tmp_path / "unscoped-run", repo, base_ref)
    listing = run_state_listing(started)
    manifest = without_keys(started.manifest, MANIFEST_SECTIONS_KEY)
    assert nodes_mentioning(listing, case.control_extent, case.control.regenerate)
    assert not nodes_mentioning(listing, case.region_path)
    assert not nodes_mentioning(manifest, case.region_path)
    assert not nodes_mentioning(listing, case.region.regenerate)
    assert not nodes_mentioning(manifest, case.region.regenerate)

    unscoped = finish_changeset_review(started)
    assert unscoped.finished.returncode != 0
    assert case.region_path in unscoped.finished.stderr
    assert case.control_extent not in unscoped.finished.stderr

    marked = finish_changeset_review(
        start_changeset_review(tmp_path / "unread-run", repo, base_ref),
        unread=[case.region_path],
    )
    assert marked.finished.returncode == 0, marked.finished.stderr
    completed = run_completed_event(marked.events)
    assert completed_unread(completed) == [case.region_path]
    assert completed["data"]["status"] == str(jp.JournalRunStatus.FAILED)
