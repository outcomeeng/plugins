"""Scenario tests for the /merge changeset-classification script.

Covers the `merging.md` Conformance clause that /merge classifies a changeset
through the canonical `changeset_scope` primitives rather than hand-rolled git:

- `classify` counts the full unique path set and reports the
  non-coordination-note count, so coordination-note-only is `total>0` and
  `non-coordination-note==0`.
- `is_coordination_note` recognizes `PLAN.md` / `ISSUES.md` basenames at any
  depth and nothing else.
- `_load_changeset_scope` resolves and loads the sibling `changeset_scope`
  module by the co-location convention, exposing `detect_base_ref` and
  `branch_scope` — the base-ref and committed-diff primitives the script
  delegates to instead of re-deriving them.

These are `l1` — direct in-process calls into the real source script. The pure
classification logic needs no git; the module-load assertion exercises the real
importlib resolution against the marketplace tree.
"""

from __future__ import annotations

import importlib.util
import pathlib
from types import ModuleType

import pytest
from outcomeeng_testing.harnesses.changeset_scope import (
    build_repo_with_modified_spaced_note,
    build_stale_local_base_repo,
)


def _marketplace_root() -> pathlib.Path:
    for parent in pathlib.Path(__file__).resolve().parents:
        if (parent / ".claude-plugin" / "marketplace.json").is_file():
            return parent
    raise RuntimeError("marketplace root (.claude-plugin/marketplace.json) not found")


CLASSIFY_SCRIPT = (
    _marketplace_root()
    / "src"
    / "plugins"
    / "spec-tree"
    / "skills"
    / "merge"
    / "scripts"
    / "classify_changeset.py"
)


def _load_classify() -> ModuleType:
    spec = importlib.util.spec_from_file_location("classify_changeset", CLASSIFY_SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


classify_changeset = _load_classify()


class TestClassify:
    def test_coordination_note_only_changeset(self) -> None:
        total, noncoord = classify_changeset.classify(
            ["spx/a/PLAN.md", "spx/b/ISSUES.md"]
        )
        assert (total, noncoord) == (2, 0)

    def test_mixed_changeset_is_not_coordination_note_only(self) -> None:
        total, noncoord = classify_changeset.classify(["spx/a/PLAN.md", "src/foo.py"])
        assert total == 2
        assert noncoord == 1

    def test_empty_changeset(self) -> None:
        assert classify_changeset.classify([]) == (0, 0)

    def test_counts_are_over_the_unique_set(self) -> None:
        # Duplicates (committed + working-tree overlap) collapse to one entry.
        total, noncoord = classify_changeset.classify(
            ["src/foo.py", "src/foo.py", "a/PLAN.md"]
        )
        assert (total, noncoord) == (2, 1)


class TestIsCoordinationNote:
    @pytest.mark.parametrize(
        "path",
        ["PLAN.md", "ISSUES.md", "spx/21-x.enabler/PLAN.md", "deep/nested/ISSUES.md"],
    )
    def test_recognizes_coordination_notes(self, path: str) -> None:
        assert classify_changeset.is_coordination_note(path) is True

    @pytest.mark.parametrize(
        "path",
        ["src/foo.py", "PLANS.md", "ISSUE.md", "plan.md", "a/PLAN.md.bak", "README.md"],
    )
    def test_rejects_non_coordination_notes(self, path: str) -> None:
        assert classify_changeset.is_coordination_note(path) is False

    def test_recognizes_every_source_owned_basename(self) -> None:
        # Tie the cases to the script's source-owned vocabulary rather than
        # re-declared literals: adding or removing a basename in the script
        # changes what this test covers.
        for basename in classify_changeset.COORDINATION_NOTE_BASENAMES:
            assert classify_changeset.is_coordination_note(basename)
            assert classify_changeset.is_coordination_note(
                f"spx/21-x.enabler/{basename}"
            )


class TestCanonicalChangesetScopeIntegration:
    """The script delegates base-ref and committed-diff derivation, never re-derives."""

    def test_loads_canonical_changeset_scope_module(self) -> None:
        module = classify_changeset._load_changeset_scope()
        # The canonical primitives the Codex/audit convention requires — present
        # only because the script loaded the real changeset-scope module, not a
        # hand-rolled stand-in.
        assert hasattr(module, "detect_base_ref")
        assert hasattr(module, "branch_scope")

    def test_changed_paths_delegates_to_canonical_primitives_end_to_end(
        self, tmp_path: pathlib.Path
    ) -> None:
        # End-to-end against a real git repo: prove changed_paths() actually
        # CALLS detect_base_ref + branch_scope (not just that the module exposes
        # them). A regression that hand-rolled git inline would change which
        # paths come back, so this is falsifiable behavioral evidence for the
        # "never re-deriving the base ref or diff range inline" clause.
        repo = tmp_path / "repo"
        repo.mkdir()
        stale = build_stale_local_base_repo(repo)
        # An uncommitted working-tree file alongside the committed feature change.
        (stale.repo / "working_dirty.py").write_text("x = 1\n", encoding="utf-8")

        paths = set(classify_changeset.changed_paths(stale.repo))

        # The committed feature change is in scope only via branch_scope against
        # the remote-tracking base (origin/<base>...HEAD, three-dot).
        assert stale.feature_file in paths
        # The merged-into-base file is excluded — proving the base ref came from
        # detect_base_ref (origin/HEAD) and the three-dot scope, not a stale
        # local ref or a two-dot diff.
        assert stale.merged_file not in paths
        # The uncommitted file is in scope only via the working-tree union.
        assert "working_dirty.py" in paths

    def test_working_tree_path_with_space_is_unquoted_and_classified(
        self, tmp_path: pathlib.Path
    ) -> None:
        # Regression for the porcelain-quoting bug: without `-z`, git C-quotes a
        # path containing a space (`"spx dir/PLAN.md"` with literal quotes), and
        # the trailing quote both defeats the coordination-note match and breaks
        # de-dup against the committed scope.
        repo = tmp_path / "repo"
        repo.mkdir()
        spaced = build_repo_with_modified_spaced_note(repo)

        working = classify_changeset._working_tree_paths(spaced.repo)

        # Path comes back unquoted (no surrounding double-quotes) and is therefore
        # recognized as a coordination note.
        assert spaced.note_path in working
        assert classify_changeset.is_coordination_note(spaced.note_path)
