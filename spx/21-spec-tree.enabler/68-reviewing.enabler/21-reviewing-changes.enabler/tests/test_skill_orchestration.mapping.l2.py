"""Mapping evidence for the review runner's terminal finding counts.

Covers two clauses in ``../reviewing-changes.md``: ``review_run.py append-finding``
maps a payload's optional ``unit``/``tracked`` onto the finding-reported event
and ``finish`` counts a tracked ``debt`` finding toward ``debt``; and ``review_run.py finish``
maps finding severities into terminal review counts on the run-completed
event — rejecting findings increment ``blocking``, warning findings increment
``debt``. The domain is every ``Severity`` member the ``review_result`` module
declares; the expectation is the spec's own relationship — one finding of a
severity increments exactly the count that carries that severity's name.

The test is ``l2`` because it drives the runner as a subprocess against a
synthetic git repository and a fake ``spx`` journal.
"""

from __future__ import annotations

import json
import pathlib

import pytest

from outcomeeng_testing.harnesses.journal_projection import (
    load_journal_projection_module,
)
from outcomeeng_testing.harnesses.reviewing_changes import (
    REVIEW_RUN_SCRIPT,
    init_repo_with_branch,
    load_review_result_module,
    make_finding_dict,
    open_scoped_review_run,
    run_script,
    runner_env,
)

review_result = load_review_result_module()
jp = load_journal_projection_module()


@pytest.mark.parametrize(
    "severity", list(review_result.Severity), ids=lambda s: s.value
)
def test_finish_counts_one_finding_under_the_count_named_by_its_severity(
    tmp_path: pathlib.Path, severity
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    base_ref = init_repo_with_branch(repo)
    env, journal_path = runner_env(tmp_path, repo, base_ref)

    state_path = open_scoped_review_run(env, repo)
    finding = make_finding_dict(file="README.md", line=2, severity=severity.value)
    appended = run_script(
        REVIEW_RUN_SCRIPT,
        "append-finding",
        "--state",
        state_path,
        stdin=json.dumps(finding),
        env=env,
        cwd=repo,
    )
    assert appended.returncode == 0, appended.stderr
    finished = run_script(
        REVIEW_RUN_SCRIPT, "finish", "--state", state_path, env=env, cwd=repo
    )
    assert finished.returncode == 0, finished.stderr

    journal = json.loads(journal_path.read_text(encoding="utf-8"))
    counts = journal["events"][-1]["data"]["review"]
    expected = {member.value: 0 for member in review_result.Severity}
    expected[severity.value] = 1
    assert {name: counts[name] for name in expected} == expected


# The optional unit/tracked payload fields are a finite state domain: both set
# (the review kind records the enclosing unit and the ISSUES.md match) or both
# absent (the prior event shape). The expected event data derives from the
# payload state: a field present in the payload is carried verbatim onto the
# finding-reported event, a field absent is omitted. A tracked debt finding
# counts toward debt exactly as an untracked one does.
@pytest.mark.parametrize(
    "optional_fields",
    [
        {"unit": "Reviewing Changes", "tracked": True},
        {"unit": "Reviewing Changes", "tracked": False},
        {},
    ],
    ids=["tracked", "untracked", "omitted"],
)
def test_append_finding_maps_unit_and_tracked_onto_event_and_finish_counts_debt(
    tmp_path: pathlib.Path, optional_fields: dict
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    base_ref = init_repo_with_branch(repo)
    env, journal_path = runner_env(tmp_path, repo, base_ref)

    state_path = open_scoped_review_run(env, repo)
    finding = make_finding_dict(
        file="README.md",
        line=2,
        severity=review_result.Severity.DEBT.value,
        **optional_fields,
    )
    appended = run_script(
        REVIEW_RUN_SCRIPT,
        "append-finding",
        "--state",
        state_path,
        stdin=json.dumps(finding),
        env=env,
        cwd=repo,
    )
    assert appended.returncode == 0, appended.stderr
    finished = run_script(
        REVIEW_RUN_SCRIPT, "finish", "--state", state_path, env=env, cwd=repo
    )
    assert finished.returncode == 0, finished.stderr

    events = json.loads(journal_path.read_text(encoding="utf-8"))["events"]
    reported = [e for e in events if e["type"] == jp.FINDING_REPORTED]
    assert len(reported) == 1
    data = reported[0]["data"]
    for field in ("unit", "tracked"):
        assert (field in data) is (field in optional_fields)
        if field in optional_fields:
            assert data[field] == optional_fields[field]
    counts = events[-1]["data"]["review"]
    assert counts[review_result.Severity.DEBT.value] == 1
    assert counts[review_result.Severity.BLOCKING.value] == 0
