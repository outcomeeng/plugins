"""Compliance test for the form check's row forms and its merged-Leaf Base.

Covers ``form-check-merged-base``, ``form-check-linked-heading`` and
``form-check-scenario-steps`` in ``../changes.md``. Once the default branch
holds a commit that references the Leaf's issue, the check reads a deletion at
the Base of the stored Sliced record and refuses no publish on a new base; a
commit that references no issue, or another issue, leaves the
``operator-bound-base`` failure standing. A Mapping heading whose subject is a slug link names that slug,
so the infrastructure line keyed by the slug satisfies the check. The indented
Given, When, Then and And lines after a ``+`` Scenario row belong to that row, so
the check asks no slug of them. Each case builds a synthetic repository with one
implementation-malleable Node, commits it as the Base, and checks one Draft. The
test is ``l2`` because it spawns ``git`` against synthetic repositories under
``tmp_path``.
"""

from __future__ import annotations

import pathlib

import pytest

from outcomeeng_testing.harnesses.form_check import (
    Intent,
    StoreStampRunner,
    commit_base,
    findings,
    git,
    write_draft,
)

NODE = "spx/21-thing.capability"
BASE_FILES = {
    "spx/example.spec.md": (
        "---\nid: 01a1e000-0000-7000-8000-000000000001\nkind: product\n---\n\n"
        "# Example\n"
    ),
    f"{NODE}/thing.spec.md": (
        "---\nid: 01a1e000-0000-7000-8000-000000000003\n---\n\n# Thing\n\n"
        "PROVIDES things\nSO THAT readers\nCAN read them\n\n## Assertions\n"
    ),
    f"{NODE}/tests/test_thing.mapping.l1.py": (
        "def test_thing() -> None:\n    assert True\n"
    ),
}
INTENT = Intent(
    title="The thing reads things",
    output="The thing reads things.",
    why="Readers need things.",
    verification="A test reads a thing.",
)


def draft_on_base(tmp_path: pathlib.Path, payload: list[str]) -> pathlib.Path:
    """Commit the one-Node Base under ``tmp_path`` and write a Draft holding ``payload``."""
    base = commit_base(tmp_path / "repo", BASE_FILES)
    return write_draft(tmp_path, base, INTENT, NODE, payload)


LINKED_MAPPING = [
    "```diff",
    "  ## Assertions",
    "+ ### Test.Mapping: [thing-kinds](tests/test_thing.mapping.l1.py)",
    "+ Each kind of thing maps to its reader.",
    "+ | Case | Kind | Reader |",
    "+ | ---- | ---- | ------ |",
    "+ | small | small | quick reader |",
    "```",
    "",
    "Infrastructure: thing-kinds none",
]

MULTI_LINE_SCENARIO = [
    "```diff",
    "  ## Assertions",
    "+ ### Test.Scenario: reading",
    "+ - read-one:",
    "+   - Given one thing",
    "+   - When a reader reads it",
    "+   - Then the reader holds exactly one thing",
    "+   - And the thing stays unchanged",
    "```",
    "",
    "Infrastructure: read-one none",
]

UNSLUGGED_ROW = [
    "```diff",
    "  ## Assertions",
    "+ ### Test.Scenario: reading",
    "+ - a reader reads a thing",
    "```",
    "",
    "Infrastructure: read-one none",
]


def test_linked_mapping_heading_takes_its_slugs_infrastructure_line(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = tmp_path / "repo"
    draft = draft_on_base(tmp_path, LINKED_MAPPING)
    rules = [finding["rule"] for finding in findings(repo, draft, capsys)]
    assert "infrastructure-line" not in rules


def test_linked_mapping_heading_without_its_line_still_fails(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = tmp_path / "repo"
    draft = draft_on_base(tmp_path, LINKED_MAPPING[:-2])
    details = [
        finding["detail"]
        for finding in findings(repo, draft, capsys)
        if finding["rule"] == "infrastructure-line"
    ]
    assert any("thing-kinds" in detail for detail in details)


def test_scenario_step_lines_belong_to_their_row(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = tmp_path / "repo"
    draft = draft_on_base(tmp_path, MULTI_LINE_SCENARIO)
    rules = [finding["rule"] for finding in findings(repo, draft, capsys)]
    assert "body-lines-only" not in rules


def test_unslugged_row_still_fails(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = tmp_path / "repo"
    draft = draft_on_base(tmp_path, UNSLUGGED_ROW)
    rules = [finding["rule"] for finding in findings(repo, draft, capsys)]
    assert "body-lines-only" in rules


ISSUE = "outcomeeng/changes#7"
STAMP = "2026-01-01T00:00:00Z"
RECORD = f"{NODE}/21-reading.adr.md"
DELETION = ["```diff", "deleted file", "```"]


def merged_record_fix(
    tmp_path: pathlib.Path, message: str
) -> tuple[pathlib.Path, list[str]]:
    """Merge a deletion with ``message`` and write the fix Draft and its stored record.

    The Base holds a Decision Record. The stored Sliced record deletes it on that
    Base. A commit on the default branch carries ``message`` and deletes the
    record, and the fix Draft deletes it on the new head. Returns the fix Draft
    and the publish arguments.
    """
    repo = tmp_path / "repo"
    files = {**BASE_FILES, RECORD: "# Reading\n\nThe thing reads one thing.\n"}
    sliced = commit_base(repo, files)
    git(repo, "rm", "-q", RECORD)
    git(repo, "commit", "-q", "-m", message)
    head = git(repo, "rev-parse", "HEAD")
    git(repo, "update-ref", "refs/remotes/origin/main", head)
    published = write_draft(
        tmp_path, sliced, INTENT, RECORD, DELETION, maturity="Sliced", name="stored.md"
    )
    draft = write_draft(tmp_path, head, INTENT, RECORD, DELETION, maturity="Sliced")
    extra = ["--issue", ISSUE, "--read-edited-at", STAMP, "--published", str(published)]
    return draft, extra


@pytest.mark.parametrize(
    "message",
    [
        f"spec: delete reading\n\nRefs: {ISSUE}",
        "spec: delete reading\n\nRefs: https://github.com/outcomeeng/changes/issues/7",
    ],
)
def test_merged_leaf_reads_its_deletion_at_the_sliced_base(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str], message: str
) -> None:
    draft, extra = merged_record_fix(tmp_path, message)
    reported = findings(tmp_path / "repo", draft, capsys, extra, StoreStampRunner(STAMP))
    assert [f for f in reported if f["location"] == RECORD] == []


@pytest.mark.parametrize(
    "message",
    [
        "spec: delete reading",
        "spec: delete reading\n\nRefs: outcomeeng/changes#70",
    ],
)
def test_unmerged_leaf_keeps_the_operator_bound_base_failure(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str], message: str
) -> None:
    draft, extra = merged_record_fix(tmp_path, message)
    reported = findings(tmp_path / "repo", draft, capsys, extra, StoreStampRunner(STAMP))
    rules = [f["rule"] for f in reported if f["location"] == RECORD]
    assert "operator-bound-base" in rules
