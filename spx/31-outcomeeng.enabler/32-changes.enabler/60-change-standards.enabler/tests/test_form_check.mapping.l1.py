"""Mapping evidence: the form check judges a Draft against the Change record.

Each ``Test.Mapping`` subsection of the change-standards spec maps a finite set
of cases to the form check's verdict. The metadata keys and the operations are
the complete source-owned domains the script declares, so the key tests range
over them. Every other subsection ranges over the Draft fixtures declared for
it: a fixture named ``<rule>.<case>.<verdict>.md`` is one whole Draft, and its
name states the rule it exercises and the verdict the check gives it.

Assertion design, for every test below:
- Production subject: ``check`` of ``form_check.py``, crossed at the result it
  returns for one request; the request carries the Draft text and a checkout
  root whose Base commit holds the fixture tree.
- Case provenance: the spec's table rows (one fixture or one key each) and the
  script's declared key and operation domains.
- Oracle: the fixture name for the verdict, and the key or fixture name for the
  place a finding names; the keys, their listed values, the title word limit and
  the operations each key's row names come from the spec table, read through the
  generator and its vocabulary from the spec's phrases to operation names. The
  script's own tables supply no expected result.
- Rejected mutation: dropping a key's value check, a key's operation row, or
  the rule a fixture exercises makes the matching case pass a Draft it must
  fail.
"""

from __future__ import annotations

import pytest

from outcomeeng_testing.generators.change_standards_form_check import (
    GROUP_MAPPING,
    GROUP_MAPPING_NO_TREE,
    FixtureCase,
    Verdict,
    covering_fixtures,
    declared_values,
    draft_keys,
    enumerated_values,
    fixture_cases,
    fixtures_of,
    foreign_values,
    non_value,
    operations,
    operations_of,
    spec_compliance_rules,
    spec_key_values,
    spec_mapping_rules,
    spec_row_cases,
    stored_record_changed_at,
    table_row_name,
    title_of_words,
    title_word_limit,
    with_value,
    without_key,
)
from outcomeeng_testing.harnesses.change_standards_form_check import (
    NO_TREE_REPOSITORY_DIR,
    VALID_DRAFT,
    base_workspace,
    check_draft,
    check_text,
    draft_text,
    load_form_check,
)

form = load_form_check()
Rule = form.Rule
Status = form.Status

MAPPING_CASES = fixture_cases(GROUP_MAPPING)
NO_TREE_CASES = fixture_cases(GROUP_MAPPING_NO_TREE)


def test_the_conforming_draft_passes_with_no_finding() -> None:
    with base_workspace() as workspace:
        observation = check_draft(workspace, VALID_DRAFT)

    assert observation.status == Status.PASS
    assert observation.findings == ()


@pytest.mark.parametrize("key", draft_keys())
def test_a_draft_missing_a_key_fails_and_names_that_key(key: str) -> None:
    with base_workspace() as workspace:
        text = without_key(draft_text(workspace, VALID_DRAFT), key)
        observation = check_text(workspace, text)

    assert observation.status == Status.FAIL
    assert (Rule.RECORD_KEYS, key) in observation.located


@pytest.mark.parametrize("key", draft_keys())
def test_a_draft_with_a_value_outside_a_keys_domain_fails_and_names_that_key(
    key: str,
) -> None:
    with base_workspace() as workspace:
        text = with_value(draft_text(workspace, VALID_DRAFT), key, non_value(key))
        observation = check_text(workspace, text)

    assert observation.status == Status.FAIL
    assert (Rule.RECORD_KEYS, key) in observation.located


@pytest.mark.parametrize(
    ("key", "value"),
    enumerated_values(),
    ids=[f"{key}={value}" for key, value in enumerated_values()],
)
def test_a_draft_holding_each_listed_value_of_an_enumerated_key_passes_that_key(
    key: str, value: str
) -> None:
    with base_workspace() as workspace:
        text = with_value(draft_text(workspace, VALID_DRAFT), key, value)
        observation = check_text(workspace, text)

    assert (Rule.RECORD_KEYS, key) not in observation.located


@pytest.mark.parametrize(
    ("key", "value"),
    foreign_values(),
    ids=[f"{key}={value}" for key, value in foreign_values()],
)
def test_a_draft_holding_a_value_of_another_keys_domain_fails_that_key(
    key: str, value: str
) -> None:
    with base_workspace() as workspace:
        text = with_value(draft_text(workspace, VALID_DRAFT), key, value)
        observation = check_text(workspace, text)

    assert (Rule.RECORD_KEYS, key) in observation.located


@pytest.mark.parametrize(
    "key", list(dict.fromkeys(key for key, _ in enumerated_values()))
)
def test_the_values_the_script_declares_for_an_enumerated_key_are_those_the_spec_row_lists(
    key: str,
) -> None:
    assert declared_values(key) == spec_key_values(key)


def test_a_title_of_exactly_the_word_limit_passes_the_title_key() -> None:
    with base_workspace() as workspace:
        text = with_value(
            draft_text(workspace, VALID_DRAFT),
            "title",
            title_of_words(title_word_limit()),
        )
        observation = check_text(workspace, text)

    assert (Rule.RECORD_KEYS, "title") not in observation.located


@pytest.mark.parametrize("rule", spec_mapping_rules())
def test_every_case_the_spec_table_lists_is_a_case_of_its_mapping(rule: str) -> None:
    uncovered = [
        case for case in spec_row_cases(rule) if not covering_fixtures(rule, case)
    ]

    assert uncovered == []


@pytest.mark.parametrize("rule", spec_compliance_rules())
def test_every_rule_the_spec_lists_for_compliance_has_a_violating_fixture(
    rule: str,
) -> None:
    violating = [
        fixture for fixture in fixtures_of(rule) if fixture.verdict is Verdict.FAIL
    ]

    assert violating != []


@pytest.mark.parametrize("operation", operations())
@pytest.mark.parametrize("key", draft_keys())
def test_an_operation_changes_a_key_only_when_the_keys_row_names_it(
    key: str, operation: str
) -> None:
    with base_workspace() as workspace:
        text = draft_text(workspace, VALID_DRAFT)
        observation = check_text(
            workspace,
            text,
            operation=operation,
            stored_record=stored_record_changed_at(text, key),
        )

    named = (Rule.RECORD_KEYS, key) in observation.located
    allowed = operation in operations_of(key)
    assert named is not allowed


@pytest.mark.parametrize(
    "case", MAPPING_CASES, ids=[case.identity for case in MAPPING_CASES]
)
def test_each_mapping_case_gets_the_verdict_its_fixture_declares(
    case: FixtureCase,
) -> None:
    with base_workspace() as workspace:
        observation = check_draft(workspace, case.name)

    if case.verdict is Verdict.PASS:
        assert observation.findings == ()
        assert observation.status == Status.PASS
        assert observation.rules == ()
    else:
        assert observation.status == Status.FAIL
        assert case.rule in observation.rules


@pytest.mark.parametrize(
    "case", NO_TREE_CASES, ids=[case.identity for case in NO_TREE_CASES]
)
def test_each_mapping_case_of_a_product_with_no_tree_gets_its_declared_verdict(
    case: FixtureCase,
) -> None:
    with base_workspace(NO_TREE_REPOSITORY_DIR) as workspace:
        observation = check_draft(workspace, case.name)

    if case.verdict is Verdict.PASS:
        assert observation.findings == ()
        assert observation.status == Status.PASS
        assert observation.rules == ()
    else:
        assert observation.status == Status.FAIL
        assert case.rule in observation.rules


def test_a_table_row_absent_at_the_base_is_named_by_subsection_slug_and_case() -> None:
    fixture = f"{GROUP_MAPPING}/diff-lines.removed-table-row-absent.fail"
    with base_workspace() as workspace:
        observation = check_draft(workspace, fixture)

    assert (Rule.DIFF_LINES, table_row_name(fixture, "-")) in observation.located
