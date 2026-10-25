"""Scenario tests for declared generated extents in ``review_run.py``.

Covers the scenarios in ``../reviewing-changes.md`` that govern how the runner treats
a changed file a generated-source declaration marks as a generated extent:

1. No declaration -> no extent is listed and every changed file stays ordinary.
2. A declared extent needs neither a scope-advanced event nor an unread mark; ``finish``
   records it as skipped by declaration with its relation's regenerate command and
   seals the run by its findings.
3. A relation whose declared source or generator the changeset also changes is flagged
   in the returned run state, and its extent still needs neither event nor mark.

The tests are ``l2`` because they spawn ``git`` and the runner against synthetic git
repositories under ``tmp_path``. The runner's field names for extents are its own, so
the predicates locate the smallest JSON objects that carry the values under judgment.
"""

from __future__ import annotations

import json
import pathlib

from outcomeeng_testing.generators.reviewing_changes_runs import (
    flagged_relation_cases,
    single_relation_case,
)
from outcomeeng_testing.harnesses.reviewing_changes_runs import (
    build_changeset_repo,
    completed_unread,
    finish_changeset_review,
    jp,
    nodes_mentioning,
    render_generated_sources,
    run_completed_event,
    run_state_listing,
    scope_advanced_units,
    start_changeset_review,
)


class TestGeneratedExtentScenarios:
    def test_without_declaration_every_changed_file_is_ordinary(
        self, tmp_path: pathlib.Path
    ) -> None:
        case = single_relation_case()
        extent_paths = [path for path, _ in case.extents]
        changed = [*extent_paths, *case.ordinary]

        undeclared_repo = tmp_path / "undeclared-repo"
        undeclared_base = build_changeset_repo(
            undeclared_repo, declaration=None, changed_paths=changed
        )
        undeclared = start_changeset_review(
            tmp_path / "undeclared-run", undeclared_repo, undeclared_base
        )

        declared_repo = tmp_path / "declared-repo"
        declared_base = build_changeset_repo(
            declared_repo,
            declaration=render_generated_sources(case.relations),
            changed_paths=changed,
        )
        declared = start_changeset_review(
            tmp_path / "declared-run", declared_repo, declared_base
        )

        for path in extent_paths:
            assert nodes_mentioning(run_state_listing(declared), path)
            assert not nodes_mentioning(run_state_listing(undeclared), path)
        assert sorted(undeclared.start_payload["changedFiles"]) == sorted(changed)

        finished = finish_changeset_review(undeclared, scope=case.ordinary)
        assert finished.finished.returncode != 0
        for path in extent_paths:
            assert path in finished.finished.stderr

    def test_finish_skips_declared_extents_and_seals_by_findings(
        self, tmp_path: pathlib.Path
    ) -> None:
        case = single_relation_case()
        relation = case.relations[0]
        extent_paths = [path for path, _ in case.extents]
        repo = tmp_path / "repo"
        base_ref = build_changeset_repo(
            repo,
            declaration=render_generated_sources(case.relations),
            changed_paths=[*extent_paths, *case.ordinary],
        )
        started = start_changeset_review(tmp_path / "run", repo, base_ref)

        finished = finish_changeset_review(started, scope=case.ordinary)

        assert finished.finished.returncode == 0, finished.finished.stderr
        assert finished.sealed is True
        completed = run_completed_event(finished.events)
        assert completed["data"]["status"] == str(jp.JournalRunStatus.APPROVED)
        advanced = scope_advanced_units(finished.events)
        for path in extent_paths:
            assert path not in advanced
            assert path not in completed_unread(completed)
            assert nodes_mentioning(completed, path, relation.regenerate)

    def test_relation_with_changed_input_is_flagged_and_extent_needs_no_review_event(
        self, tmp_path: pathlib.Path
    ) -> None:
        for index, case in enumerate(flagged_relation_cases()):
            workspace = tmp_path / f"case-{index}"
            declaration = render_generated_sources([case.relation])

            flagged_repo = workspace / "flagged-repo"
            flagged_base = build_changeset_repo(
                flagged_repo,
                declaration=declaration,
                changed_paths=[case.extent_path, case.input_path],
            )
            flagged = start_changeset_review(
                workspace / "flagged-run", flagged_repo, flagged_base
            )

            control_repo = workspace / "control-repo"
            control_base = build_changeset_repo(
                control_repo, declaration=declaration, changed_paths=[case.extent_path]
            )
            control = start_changeset_review(
                workspace / "control-run", control_repo, control_base
            )

            flagged_nodes = nodes_mentioning(
                run_state_listing(flagged), case.extent_path, case.relation.regenerate
            )
            control_nodes = nodes_mentioning(
                run_state_listing(control), case.extent_path, case.relation.regenerate
            )
            assert flagged_nodes, case.input_kind
            assert control_nodes, case.input_kind
            assert json.dumps(flagged_nodes, sort_keys=True) != json.dumps(
                control_nodes, sort_keys=True
            ), case.input_kind

            finished = finish_changeset_review(flagged, scope=[case.input_path])
            assert finished.finished.returncode == 0, finished.finished.stderr
            assert case.extent_path not in scope_advanced_units(finished.events)
            assert case.extent_path not in completed_unread(
                run_completed_event(finished.events)
            )
