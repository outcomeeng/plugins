from outcomeeng_testing.harnesses.runtime_tokens import (
    authored_tree_default_enforcement_matches_contract,
    every_enforced_registry_name_is_rejected,
    forbidden_names_derive_from_enforced_registry_kinds,
    review_only_names_are_excluded,
    shared_fragment_raw_token_is_reported,
)


def test_every_enforced_registry_name_is_rejected() -> None:
    assert every_enforced_registry_name_is_rejected()


def test_forbidden_names_derive_from_enforced_registry_kinds() -> None:
    assert forbidden_names_derive_from_enforced_registry_kinds()


def test_review_only_names_are_excluded() -> None:
    assert review_only_names_are_excluded()


def test_shared_fragment_raw_token_is_reported() -> None:
    assert shared_fragment_raw_token_is_reported()


def test_authored_tree_default_enforcement_matches_contract() -> None:
    assert authored_tree_default_enforcement_matches_contract()
