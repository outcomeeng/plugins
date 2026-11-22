"""Compliance test for the author-change publish command.

Covers ``publish-checked`` and ``github-clear`` in ``../54-change-record.pdr.md``.
A Draft that fails the form check writes nothing to the Change Store. A Draft
that passes writes its title, body, Product, Parent, Predecessors, Base and
blockers, clears each of them the Draft empties or leaves out, and leaves
Priority, Maturity and Lifecycle as the store holds them; recording a new Change
also writes its Maturity and Lifecycle. Each case runs the command against a
recording store and a synthetic checkout under ``tmp_path``. The test is ``l2``
because the form check spawns ``git``.
"""

from __future__ import annotations

import pathlib
import re

from outcomeeng_testing.harnesses.change_publish import (
    STAMP,
    STORE,
    RecordingStore,
    load_publish,
)
from outcomeeng_testing.harnesses.form_check import commit_base, write_record

FILES = {"README.md": "a checkout\n"}
INTENT = (
    "## Statement of Intent\n\n"
    "- Output: The thing reads things.\n"
    "- Why: Readers need things.\n"
    "- Verification: Test: a test reads a thing.\n"
)
TWO_PARTS = (
    "## Statement of Intent\n\n"
    "- Output: The thing reads things.\n"
    "- Why: Readers need things.\n"
)


def run_publish(
    tmp_path: pathlib.Path,
    body: str,
    store: RecordingStore,
    issue: str | None = f"{STORE}#7",
    edits: dict[str, str] | None = None,
) -> tuple[int, dict[str, object]]:
    """Publish a Proposed Draft holding ``body`` with front-matter ``edits``."""
    repo = tmp_path / "repo"
    base = commit_base(repo, FILES)
    draft = write_record(tmp_path, base, body)
    text = draft.read_text(encoding="utf-8")
    for key, value in (edits or {}).items():
        text = re.sub(rf"^{key}: .*$", f"{key}: {value}", text, count=1, flags=re.M)
    draft.write_text(text, encoding="utf-8")
    code: int
    result: dict[str, object]
    code, result = load_publish().publish(
        repo, draft, STORE, issue, STAMP if issue else None, None, store
    )
    return code, result


def test_a_draft_that_fails_the_form_check_writes_nothing(
    tmp_path: pathlib.Path,
) -> None:
    store = RecordingStore()
    code, result = run_publish(tmp_path, TWO_PARTS, store)
    assert code != 0
    assert result["status"] == "refused"
    assert store.writes() == []


def test_a_publish_writes_held_fields_and_clears_emptied_ones(
    tmp_path: pathlib.Path,
) -> None:
    store = RecordingStore()
    code, result = run_publish(tmp_path, INTENT, store)
    assert (code, result["status"]) == (0, "published")
    assert set(store.mutations("setIssueFieldValue")) == {"F_product", "F_base"}
    assert set(store.mutations("deleteIssueFieldValue")) == {
        "F_parent",
        "F_predecessors",
    }


def test_a_publish_leaves_priority_maturity_and_lifecycle_alone(
    tmp_path: pathlib.Path,
) -> None:
    store = RecordingStore()
    run_publish(tmp_path, INTENT, store, edits={"priority": "Normal"})
    written = set(store.mutations("setIssueFieldValue")) | set(
        store.mutations("deleteIssueFieldValue")
    )
    assert not written & {"F_priority", "F_maturity", "F_lifecycle"}


def test_recording_a_change_writes_its_maturity_and_lifecycle(
    tmp_path: pathlib.Path,
) -> None:
    store = RecordingStore()
    code, result = run_publish(tmp_path, INTENT, store, issue=None)
    assert (code, result["issue"]) == (0, f"{STORE}#7")
    assert {"F_maturity", "F_lifecycle"} <= set(store.mutations("setIssueFieldValue"))


def test_a_publish_brings_the_blockers_to_the_draft(tmp_path: pathlib.Path) -> None:
    store = RecordingStore(blocked_by=[6])
    run_publish(tmp_path, INTENT, store, edits={"blockers": f"[{STORE}#5]"})
    posts = [call for call in store.writes() if "POST" in call]
    deletes = [call for call in store.writes() if "DELETE" in call]
    assert len(posts) == 1
    assert len(deletes) == 1
    assert deletes[0][2].endswith("/blocked_by/9006")


def test_recording_a_child_writes_its_parents_priority(
    tmp_path: pathlib.Path,
) -> None:
    store = RecordingStore()
    code, _ = run_publish(
        tmp_path,
        INTENT,
        store,
        issue=None,
        edits={"parent": f"{STORE}#26", "lifecycle": "Available"},
    )
    priority_writes = [
        call
        for call in store.writes()
        if "f=F_priority" in call and "v=O_normal" in call
    ]
    assert code == 0
    assert len(priority_writes) == 1


def test_a_parents_draft_without_base_clears_the_base_field(
    tmp_path: pathlib.Path,
) -> None:
    store = RecordingStore()
    repo = tmp_path / "repo"
    commit_base(repo, FILES)
    draft = write_record(tmp_path, "a" * 40, INTENT)
    text = draft.read_text(encoding="utf-8")
    draft.write_text(re.sub(r"^base: .*\n", "", text, flags=re.M), encoding="utf-8")
    code, result = load_publish().publish(
        repo, draft, STORE, f"{STORE}#7", STAMP, None, store
    )
    assert (code, result["status"]) == (0, "published")
    assert "F_base" in store.mutations("deleteIssueFieldValue")


def test_a_blocker_outside_the_store_fails_before_any_write(
    tmp_path: pathlib.Path,
) -> None:
    store = RecordingStore()
    code, result = run_publish(
        tmp_path, INTENT, store, issue=None, edits={"blockers": "[other/repo#5]"}
    )
    assert (code, result["status"]) == (1, "failed")
    assert store.writes() == []


def test_a_failed_recording_names_the_created_issue(tmp_path: pathlib.Path) -> None:
    store = RecordingStore(fail_mutation="setIssueFieldValue")
    code, result = run_publish(tmp_path, INTENT, store, issue=None)
    assert (code, result["status"]) == (1, "failed")
    assert result["issue"] == f"{STORE}#7"
