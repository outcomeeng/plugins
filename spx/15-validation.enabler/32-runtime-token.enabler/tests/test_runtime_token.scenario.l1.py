from outcomeeng_testing.harnesses.runtime_tokens import (
    ignored_file_matches_contract,
    raw_token_report_matches_contract,
    token_expression_matches_contract,
)


def test_raw_token_report_matches_contract() -> None:
    assert raw_token_report_matches_contract()


def test_token_expression_matches_contract() -> None:
    assert token_expression_matches_contract()


def test_ignored_file_matches_contract() -> None:
    assert ignored_file_matches_contract()
