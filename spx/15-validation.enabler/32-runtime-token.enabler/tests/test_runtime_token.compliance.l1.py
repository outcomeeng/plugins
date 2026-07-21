from outcomeeng_testing.harnesses.runtime_tokens import (
    authored_tree_enforcement,
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
    enforcement = authored_tree_enforcement()

    assert enforcement.gate_files, "the gate selects no authored file at all"
    assert enforcement.gate_files == enforcement.expected_files, (
        "gate selection differs from the authored-tree inventory: "
        f"{sorted(enforcement.gate_files ^ enforcement.expected_files)}"
    )
    # Every enforced root contributes, so widening the contract to a new tree
    # fails here if the selector was not widened with it.
    for root in enforcement.enforced_roots:
        if not root.is_dir():
            continue
        assert any(path.is_relative_to(root) for path in enforcement.gate_files), (
            f"no file under the enforced root {root} is selected by the gate"
        )
    assert not enforcement.raw_token_violations, (
        f"authored source carries raw runtime tokens: "
        f"{enforcement.raw_token_violations}"
    )
    assert enforcement.ignored_files == enforcement.ignore_listed_files, (
        "ignore status disagrees with the declared ignore-list: "
        f"{sorted(enforcement.ignored_files ^ enforcement.ignore_listed_files)}"
    )
