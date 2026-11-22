"""Compliance test for the form check's row forms and its merged-Leaf Base.

Covers ``form-check-merged-base``, ``form-check-linked-heading`` and
``form-check-scenario-steps`` in ``../changes.md``. Once the default branch
holds a commit whose ``Refs:`` trailer names the Leaf's issue, the check reads
each deletion, move, replacement and edit at the Base of the stored Sliced
record and refuses no publish on a new base. A commit whose trailer names no
issue or another issue, a commit that names the issue only in prose, and a
stored Base that resolves to no commit leave the ``operator-bound-base``
failure standing, and an unmerged edit keeps its ``diff-lines`` failure.
A Mapping heading whose subject is a slug link names that slug, so the
infrastructure line keyed by the slug satisfies the check. The indented
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
MOVED = f"{NODE}/22-reading.adr.md"
RECORD_TEXT = "# Reading\n\nThe thing reads one thing.\n"
REPLACED_TEXT = "# Reading\n\nThe thing reads every thing.\n"


def delete_record(repo: pathlib.Path) -> None:
    git(repo, "rm", "-q", RECORD)


def move_record(repo: pathlib.Path) -> None:
    git(repo, "mv", RECORD, MOVED)


def replace_record(repo: pathlib.Path) -> None:
    (repo / RECORD).write_text(REPLACED_TEXT, encoding="utf-8")
    git(repo, "add", RECORD)


OPERATIONS = {
    "delete": (["```diff", "deleted file", "```"], delete_record),
    "move": (
        ["```diff", f"rename from {RECORD}", f"rename to {MOVED}", "```"],
        move_record,
    ),
    "replace": (["```markdown", *REPLACED_TEXT.splitlines(), "```"], replace_record),
    "edit": (
        [
            "```diff",
            "  # Reading",
            "- The thing reads one thing.",
            "+ The thing reads every thing.",
            "```",
        ],
        replace_record,
    ),
}


def merged_record_fix(
    tmp_path: pathlib.Path,
    operation: str,
    message: str,
    stored_base: str | None = None,
) -> tuple[pathlib.Path, list[str]]:
    """Merge ``operation`` with ``message`` and write the fix Draft and its stored record.

    The Base holds a Decision Record. The stored Sliced record deletes, moves or
    replaces it on that Base. A commit on the default branch carries ``message``
    and applies the operation, and the fix Draft states the same operation on
    the new head. ``stored_base`` replaces the stored record's Base when given.
    Returns the fix Draft and the publish arguments.
    """
    payload, apply = OPERATIONS[operation]
    repo = tmp_path / "repo"
    sliced = commit_base(repo, {**BASE_FILES, RECORD: RECORD_TEXT})
    apply(repo)
    git(repo, "commit", "-q", "-m", message)
    head = git(repo, "rev-parse", "HEAD")
    git(repo, "update-ref", "refs/remotes/origin/main", head)
    published = write_draft(
        tmp_path,
        stored_base or sliced,
        INTENT,
        RECORD,
        payload,
        maturity="Sliced",
        name="stored.md",
    )
    draft = write_draft(tmp_path, head, INTENT, RECORD, payload, maturity="Sliced")
    extra = ["--issue", ISSUE, "--read-edited-at", STAMP, "--published", str(published)]
    return draft, extra


def record_findings(
    tmp_path: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
    draft: pathlib.Path,
    extra: list[str],
) -> list[dict[str, str]]:
    """Run the publish check and return the findings located at the record."""
    reported = findings(
        tmp_path / "repo", draft, capsys, extra, StoreStampRunner(STAMP)
    )
    return [f for f in reported if f["location"] == RECORD]


@pytest.mark.parametrize(
    ("operation", "message"),
    [
        ("delete", f"spec: change reading\n\nRefs: {ISSUE}"),
        ("move", f"spec: change reading\n\nRefs: {ISSUE}"),
        ("replace", f"spec: change reading\n\nRefs: {ISSUE}"),
        (
            "delete",
            "spec: change reading\n\nRefs: https://github.com/outcomeeng/changes/issues/7",
        ),
    ],
)
def test_merged_leaf_reads_its_operation_at_the_sliced_base(
    tmp_path: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
    operation: str,
    message: str,
) -> None:
    draft, extra = merged_record_fix(tmp_path, operation, message)
    assert record_findings(tmp_path, capsys, draft, extra) == []


@pytest.mark.parametrize(
    ("operation", "message"),
    [
        ("delete", "spec: change reading"),
        ("move", "spec: change reading"),
        ("replace", "spec: change reading"),
        ("delete", "spec: change reading\n\nRefs: outcomeeng/changes#70"),
        (
            "delete",
            f"docs: file the audits of {ISSUE}\n\nTwo audits of {ISSUE} differ.",
        ),
    ],
)
def test_unmerged_leaf_keeps_the_operator_bound_base_failure(
    tmp_path: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
    operation: str,
    message: str,
) -> None:
    draft, extra = merged_record_fix(tmp_path, operation, message)
    rules = [f["rule"] for f in record_findings(tmp_path, capsys, draft, extra)]
    assert "operator-bound-base" in rules


def test_merged_leaf_with_an_unresolvable_stored_base_keeps_the_failure(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    draft, extra = merged_record_fix(
        tmp_path, "delete", f"spec: change reading\n\nRefs: {ISSUE}", "f" * 40
    )
    rules = [f["rule"] for f in record_findings(tmp_path, capsys, draft, extra)]
    assert "operator-bound-base" in rules


def test_merged_leaf_reads_an_edit_at_the_sliced_base(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    draft, extra = merged_record_fix(
        tmp_path, "edit", f"spec: change reading\n\nRefs: {ISSUE}"
    )
    assert record_findings(tmp_path, capsys, draft, extra) == []


def test_unmerged_leaf_reads_an_edit_at_the_new_base(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    draft, extra = merged_record_fix(tmp_path, "edit", "spec: change reading")
    rules = [f["rule"] for f in record_findings(tmp_path, capsys, draft, extra)]
    assert "diff-lines" in rules
