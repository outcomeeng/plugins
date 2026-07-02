from outcomeeng_testing.harnesses.audit_tests import (
    audit_verdict_for_test_owned_declaration,
)


def test_rejects_test_owned_declarations() -> None:
    verdict = audit_verdict_for_test_owned_declaration()

    assert verdict.status == "REJECT"
    assert verdict.finding_category == "test-owned declaration"
