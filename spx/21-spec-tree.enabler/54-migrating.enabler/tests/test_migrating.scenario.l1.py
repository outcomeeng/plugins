from __future__ import annotations

from outcomeeng_testing.harnesses.link_conversion import (
    INPUT_TREE,
    OUTSIDE_SPEC_TREE_FIXTURE,
    convert_product_root,
    converted_copy,
    copied_tree,
    tree_files,
)


def test_two_product_roots_holding_one_tree_convert_to_the_same_tree() -> None:
    with converted_copy(INPUT_TREE) as first, converted_copy(INPUT_TREE) as second:
        assert first.root != second.root
        assert tree_files(first.root) == tree_files(second.root)
        assert first.observation == second.observation


def test_a_root_without_a_spec_tree_fails_and_changes_nothing() -> None:
    with copied_tree(OUTSIDE_SPEC_TREE_FIXTURE) as root:
        before = tree_files(root)
        observation = convert_product_root(root)
        after = tree_files(root)

    assert observation.exit_code != 0
    assert after == before
