from outcomeeng_testing.harnesses.change_form_check import (
    DRAFT_WITH_UNNAMED_KEY,
    PASSING_DRAFT,
    checkout_with_one_commit,
    judge_draft,
    loaded_form_check,
)


def test_reachability() -> None:
    with loaded_form_check() as form_check, checkout_with_one_commit() as checkout:
        observation = judge_draft(
            form_check,
            draft=PASSING_DRAFT,
            checkout_root=checkout,
            operation=form_check.Operation.RECORD,
            stored_record=None,
        )

    verdict = form_check.ResultField.VERDICT
    assert observation.function_result[verdict] == form_check.Verdict.PASS
    assert observation.script_result[verdict] == form_check.Verdict.PASS


def test_reachability_fail() -> None:
    with loaded_form_check() as form_check, checkout_with_one_commit() as checkout:
        observation = judge_draft(
            form_check,
            draft=DRAFT_WITH_UNNAMED_KEY,
            checkout_root=checkout,
            operation=form_check.Operation.RECORD,
            stored_record=None,
        )

    for result in (observation.function_result, observation.script_result):
        assert result[form_check.ResultField.VERDICT] == form_check.Verdict.FAIL
        findings = result[form_check.ResultField.FINDINGS]
        assert isinstance(findings, list)
        assert len(findings) == 1
        finding = findings[0]
        assert isinstance(finding, dict)
        assert finding[form_check.FindingField.RULE] == form_check.Rule.RECORD_KEYS
