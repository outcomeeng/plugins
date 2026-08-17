import pytest

from outcomeeng.distribution import instruction_block as source
from outcomeeng_testing.harnesses import (
    instruction_block_compliance_evidence as evidence,
)


def test_rendered_dcg_policy_matches_conforming_rule_fixture() -> None:
    expected_section = (
        evidence.dangerous_command_guard_fixture_path("conforming.md")
        .read_text(encoding="utf-8")
        .rstrip("\n")
    )
    documents = evidence.rendered_instruction_blocks()

    for document in documents.values():
        router = source.managed_router_block(document)
        actual_section = source.dangerous_command_guard_policy_section(router)
        assert actual_section == expected_section
    source.validate_authority_hierarchy_policy(documents)


def test_dcg_policy_rejects_missing_stop_trigger() -> None:
    guard_section = evidence.dangerous_command_guard_fixture_path(
        "missing-stop-trigger.md"
    ).read_text(encoding="utf-8")

    with pytest.raises(source.AuthorityHierarchyPolicyError):
        source.validate_dangerous_command_guard_policy({"fixture": guard_section})


def test_dcg_policy_rejects_missing_retry_prohibition() -> None:
    guard_section = evidence.dangerous_command_guard_fixture_path(
        "missing-retry-prohibition.md"
    ).read_text(encoding="utf-8")

    with pytest.raises(source.AuthorityHierarchyPolicyError):
        source.validate_dangerous_command_guard_policy({"fixture": guard_section})


def test_dcg_policy_rejects_missing_dynamic_branch_prohibition() -> None:
    guard_section = evidence.dangerous_command_guard_fixture_path(
        "missing-dynamic-branch-prohibition.md"
    ).read_text(encoding="utf-8")

    with pytest.raises(source.AuthorityHierarchyPolicyError):
        source.validate_dangerous_command_guard_policy({"fixture": guard_section})


def test_dcg_policy_rejects_missing_dynamic_branch_forms() -> None:
    guard_section = evidence.dangerous_command_guard_fixture_path(
        "missing-dynamic-branch-forms.md"
    ).read_text(encoding="utf-8")

    with pytest.raises(source.AuthorityHierarchyPolicyError):
        source.validate_dangerous_command_guard_policy({"fixture": guard_section})


def test_dcg_policy_rejects_missing_quoted_form_denial() -> None:
    guard_section = evidence.dangerous_command_guard_fixture_path(
        "missing-quoted-form-denial.md"
    ).read_text(encoding="utf-8")

    with pytest.raises(source.AuthorityHierarchyPolicyError):
        source.validate_dangerous_command_guard_policy({"fixture": guard_section})


def test_dcg_policy_rejects_missing_literal_name_requirement() -> None:
    guard_section = evidence.dangerous_command_guard_fixture_path(
        "missing-literal-name-requirement.md"
    ).read_text(encoding="utf-8")

    with pytest.raises(source.AuthorityHierarchyPolicyError):
        source.validate_dangerous_command_guard_policy({"fixture": guard_section})


def test_dcg_policy_rejects_missing_multi_branch_permission() -> None:
    guard_section = evidence.dangerous_command_guard_fixture_path(
        "missing-multi-branch-permission.md"
    ).read_text(encoding="utf-8")

    with pytest.raises(source.AuthorityHierarchyPolicyError):
        source.validate_dangerous_command_guard_policy({"fixture": guard_section})


def test_dcg_policy_rejects_missing_sanctioned_path() -> None:
    guard_section = evidence.dangerous_command_guard_fixture_path(
        "missing-sanctioned-path.md"
    ).read_text(encoding="utf-8")

    with pytest.raises(source.AuthorityHierarchyPolicyError):
        source.validate_dangerous_command_guard_policy({"fixture": guard_section})


def test_dcg_policy_rejects_missing_terminal_report() -> None:
    guard_section = evidence.dangerous_command_guard_fixture_path(
        "missing-terminal-report.md"
    ).read_text(encoding="utf-8")

    with pytest.raises(source.AuthorityHierarchyPolicyError):
        source.validate_dangerous_command_guard_policy({"fixture": guard_section})


def test_dcg_policy_rejects_missing_terminal_purpose() -> None:
    guard_section = evidence.dangerous_command_guard_fixture_path(
        "missing-terminal-purpose.md"
    ).read_text(encoding="utf-8")

    with pytest.raises(source.AuthorityHierarchyPolicyError):
        source.validate_dangerous_command_guard_policy({"fixture": guard_section})


def test_dcg_policy_rejects_missing_terminal_reason() -> None:
    guard_section = evidence.dangerous_command_guard_fixture_path(
        "missing-terminal-reason.md"
    ).read_text(encoding="utf-8")

    with pytest.raises(source.AuthorityHierarchyPolicyError):
        source.validate_dangerous_command_guard_policy({"fixture": guard_section})


def test_dcg_policy_rejects_quoted_guard_section() -> None:
    guard_section = evidence.dangerous_command_guard_fixture_path(
        "quoted-guard.md"
    ).read_text(encoding="utf-8")

    with pytest.raises(source.AuthorityHierarchyPolicyError):
        source.validate_dangerous_command_guard_policy({"fixture": guard_section})
