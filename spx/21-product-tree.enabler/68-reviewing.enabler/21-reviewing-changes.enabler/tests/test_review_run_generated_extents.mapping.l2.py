"""Mapping test for declared generated extents in ``review_run.py start``.

Each changed file a relation's whole-file output pattern matches maps to a declared
generated extent, listed in the manifest and the returned run state under its relation
together with the relation's sources, generator, and regenerate command. A changed
file no pattern matches is not listed. The finite domain is the set of whole-file
output pattern forms the declaration uses, each in a synthetic repository under
``tmp_path``; the runner and ``git`` run as real subprocesses, hence ``l2``.
"""

from __future__ import annotations

import json
import pathlib

import pytest

from outcomeeng_testing.generators.reviewing_changes_runs import (
    ExtentMappingCase,
    extent_mapping_cases,
)
from outcomeeng_testing.harnesses.reviewing_changes_runs import (
    MANIFEST_SECTIONS_KEY,
    build_changeset_repo,
    nodes_mentioning,
    render_generated_sources,
    run_state_listing,
    start_changeset_review,
    without_keys,
)


@pytest.mark.parametrize(
    "case", list(extent_mapping_cases()), ids=lambda case: case.label
)
def test_changed_files_map_to_extents_under_their_relation(
    case: ExtentMappingCase, tmp_path: pathlib.Path
) -> None:
    repo = tmp_path / "repo"
    base_ref = build_changeset_repo(
        repo,
        declaration=render_generated_sources(case.relations),
        changed_paths=[*(path for path, _ in case.extents), *case.ordinary],
    )
    started = start_changeset_review(tmp_path / "run", repo, base_ref)

    documents = (
        run_state_listing(started),
        without_keys(started.manifest, MANIFEST_SECTIONS_KEY),
    )
    for path, relation_index in case.extents:
        relation = case.relations[relation_index]
        others = [
            other
            for index, other in enumerate(case.relations)
            if index != relation_index
        ]
        for document in documents:
            carrying = nodes_mentioning(
                document,
                path,
                relation.regenerate,
                *relation.sources,
                *relation.generator,
            )
            assert carrying, (path, relation.regenerate)
            for other in others:
                assert all(
                    other.regenerate not in json.dumps(node) for node in carrying
                ), (path, other.regenerate)
    for path in case.ordinary:
        assert not nodes_mentioning(run_state_listing(started), path), path
        assert not nodes_mentioning(
            without_keys(started.manifest, MANIFEST_SECTIONS_KEY), path
        ), path
