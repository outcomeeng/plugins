"""Compliance evidence: the form check fails every Draft that breaks a rule.

Each ``Test.Compliance`` rule of the change-standards spec is a boundary the
form check enforces. The evidence for a rule is a whole Draft fixture that
breaks it, named ``<rule>.<case>.fail.md``, which the check must fail with a
finding that names the rule, and a conforming fixture named
``<rule>.<case>.pass.md`` where the rule has a boundary the check must not
cross, which the check must pass with no finding. The Base tree the fixtures
read is committed in a temporary Git repository per test.

Assertion design, for every test below:
- Production subject: ``check`` and ``main`` of ``form_check.py``, crossed at
  the result they return or print for one request.
- Case provenance: the rule text of the spec, one fixture per violation of it,
  and the script's declared request fields and size limit.
- Oracle: the fixture name for the rule and verdict; the declared limit for the
  size boundary; the snapshot of the workspace before and after for the rule
  that the check writes nothing.
- Rejected mutation: disabling the enforcement of a rule makes its violating
  fixture pass, and writing a file or a record makes the snapshot differ.
"""

from __future__ import annotations

import json

import pytest

from outcomeeng_testing.generators.change_standards_form_check import (
    GROUP_COMPLIANCE,
    GROUP_COMPLIANCE_NO_TREE,
    UNKNOWN_FIELD,
    FixtureCase,
    Verdict,
    fixture_cases,
    padded_to,
    table_row_name,
    unreadable_requests,
)
from outcomeeng_testing.harnesses.change_standards_form_check import (
    NO_TREE_REPOSITORY_DIR,
    VALID_DRAFT,
    base_workspace,
    check_draft,
    check_text,
    draft_on_disk,
    draft_text,
    load_form_check,
    observe,
    request_for,
    run_cli,
    run_main,
)

form = load_form_check()
Rule = form.Rule
Status = form.Status
Result = form.ResultField
Request = form.RequestField

COMPLIANCE_CASES = fixture_cases(GROUP_COMPLIANCE)
CASE_IDS = [case.identity for case in COMPLIANCE_CASES]
NO_TREE_CASES = fixture_cases(GROUP_COMPLIANCE_NO_TREE)
NO_TREE_CASE_IDS = [case.identity for case in NO_TREE_CASES]


@pytest.mark.parametrize("case", COMPLIANCE_CASES, ids=CASE_IDS)
def test_each_compliance_case_gets_the_verdict_its_fixture_declares(
    case: FixtureCase,
) -> None:
    with base_workspace() as workspace:
        observation = check_draft(workspace, case.name)

    if case.verdict is Verdict.PASS:
        assert observation.status == Status.PASS
        assert observation.rules == ()
    else:
        assert observation.status == Status.FAIL
        assert case.rule in observation.rules


@pytest.mark.parametrize("case", NO_TREE_CASES, ids=NO_TREE_CASE_IDS)
def test_each_compliance_case_of_a_product_with_no_tree_gets_its_declared_verdict(
    case: FixtureCase,
) -> None:
    with base_workspace(NO_TREE_REPOSITORY_DIR) as workspace:
        observation = check_draft(workspace, case.name)

    if case.verdict is Verdict.PASS:
        assert observation.status == Status.PASS
        assert observation.rules == ()
    else:
        assert observation.status == Status.FAIL
        assert case.rule in observation.rules


def test_an_added_table_row_whose_case_is_no_slug_is_named_by_subsection_slug_and_case() -> (
    None
):
    fixture = f"{GROUP_COMPLIANCE}/table-case.case-not-a-slug.fail"
    with base_workspace() as workspace:
        observation = check_draft(workspace, fixture)

    assert (Rule.TABLE_CASE, table_row_name(fixture, "+")) in observation.located


def test_a_body_of_exactly_the_github_limit_passes_the_size_rule() -> None:
    with base_workspace() as workspace:
        text = padded_to(draft_text(workspace, VALID_DRAFT), form.GITHUB_SIZE_LIMIT)
        observation = check_text(workspace, text, size_limit=form.GITHUB_STORE)

    assert Rule.SIZE_LIMIT not in observation.rules


def test_a_body_one_character_over_the_github_limit_fails_the_size_rule_naming_the_limit() -> (
    None
):
    with base_workspace() as workspace:
        text = padded_to(draft_text(workspace, VALID_DRAFT), form.GITHUB_SIZE_LIMIT + 1)
        observation = check_text(workspace, text, size_limit=form.GITHUB_STORE)

    details = [
        finding[form.FindingField.DETAIL]
        for finding in observation.findings
        if finding[form.FindingField.RULE] == Rule.SIZE_LIMIT
    ]
    assert len(details) == 1
    assert str(form.GITHUB_SIZE_LIMIT) in details[0]


def test_a_request_that_breaks_the_request_shape_yields_invalid_request_and_no_finding() -> (
    None
):
    with base_workspace() as workspace:
        valid = request_for(workspace, draft_text(workspace, VALID_DRAFT))
        for field, request in unreadable_requests(valid):
            observation = observe(workspace, request)

            assert observation.status == Status.INVALID_REQUEST, field
            assert observation.findings == (), field
            assert field in observation.result[Result.DETAIL], field


def test_a_request_naming_the_draft_by_path_gets_the_result_of_its_text() -> None:
    with base_workspace() as workspace:
        by_text = check_draft(workspace, "compliance/no-tag.test-tag-added.fail")
        with draft_on_disk(workspace, "compliance/no-tag.test-tag-added.fail") as path:
            request = request_for(workspace, "")
            del request[Request.DRAFT_TEXT]
            request[Request.DRAFT_PATH] = str(path)
            by_path = observe(workspace, request)

    assert by_path.result == by_text.result


def test_the_script_writes_one_json_result_and_exits_by_the_status_of_the_check() -> (
    None
):
    with base_workspace() as workspace:
        conforming = request_for(workspace, draft_text(workspace, VALID_DRAFT))
        breaking = request_for(
            workspace, draft_text(workspace, "compliance/no-tag.test-tag-added.fail")
        )
        unreadable = {**conforming, UNKNOWN_FIELD: 1}
        passed = run_cli(json.dumps(conforming))
        failed = run_cli(json.dumps(breaking))
        invalid = run_cli(json.dumps(unreadable))
        not_json = run_cli("not a json document")

    assert (passed.exit_code, passed.result[Result.STATUS]) == (
        form.EXIT_PASS,
        Status.PASS,
    )
    assert (failed.exit_code, failed.result[Result.STATUS]) == (
        form.EXIT_FAIL,
        Status.FAIL,
    )
    assert (invalid.exit_code, invalid.result[Result.STATUS]) == (
        form.EXIT_INVALID_REQUEST,
        Status.INVALID_REQUEST,
    )
    assert not_json.exit_code == form.EXIT_INVALID_REQUEST
    for run in (passed, failed, invalid, not_json):
        assert run.stdout.count("\n") == 1


def test_the_check_function_returns_the_result_the_script_writes_for_a_request() -> (
    None
):
    assert callable(form.check)
    with base_workspace() as workspace:
        for name in (VALID_DRAFT, "compliance/no-tag.test-tag-added.fail"):
            request = request_for(workspace, draft_text(workspace, name))
            returned = json.loads(json.dumps(form.check(request)))
            written = run_main(json.dumps(request)).result

            assert returned == written, name


@pytest.mark.parametrize("case", COMPLIANCE_CASES, ids=CASE_IDS)
def test_the_check_writes_no_file_and_runs_only_git_in_the_checkout_root(
    case: FixtureCase,
) -> None:
    with base_workspace() as workspace:
        observation = check_draft(workspace, case.name)

    assert observation.files_after == observation.files_before
    assert all(command[0] == "git" for command in observation.commands)
