from __future__ import annotations

from outcomeeng_testing.harnesses.link_conversion import (
    CONVERTIBLE_ONLY_TREE,
    INPUT_TREE,
    OUTSIDE_SPEC_TREE_FIXTURE,
    convert_product_root,
    converted_copy,
    copied_tree,
    load_link_conversion_module,
    tree_files,
)


def test_two_product_roots_holding_one_tree_convert_to_the_same_tree() -> None:
    with converted_copy(INPUT_TREE) as first, converted_copy(INPUT_TREE) as second:
        assert first.root != second.root
        assert tree_files(first.root) == tree_files(second.root)
        assert first.observation == second.observation


def test_a_root_without_a_spec_tree_exits_with_the_error_status() -> None:
    conversion = load_link_conversion_module()

    with copied_tree(OUTSIDE_SPEC_TREE_FIXTURE) as root:
        before = tree_files(root)
        observation = convert_product_root(root)
        after = tree_files(root)

    assert observation.exit_code == conversion.EXIT_ERROR
    assert after == before


def test_unconvertible_citations_exit_with_the_unconvertible_status() -> None:
    conversion = load_link_conversion_module()

    with converted_copy(INPUT_TREE) as converted:
        observation = converted.observation

    assert observation.unconvertible
    assert observation.exit_code == conversion.EXIT_UNCONVERTIBLE


def test_a_fully_converted_tree_exits_with_the_success_status() -> None:
    conversion = load_link_conversion_module()

    with converted_copy(CONVERTIBLE_ONLY_TREE) as converted:
        observation = converted.observation

    assert observation.rewritten
    assert observation.unconvertible == ()
    assert observation.exit_code == conversion.EXIT_OK
