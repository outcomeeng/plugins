"""Conformance tests for the evidence-link-integrity walker."""

from __future__ import annotations

from outcomeeng.validation.link_integrity import (
    REASON_EVAL_NOT_TOML,
    REASON_EVAL_OUTSIDE_EVALS_DIR,
    REASON_TARGET_MISSING,
    REASON_TEST_NOT_COLLECTABLE,
    REASON_TEST_OUTSIDE_TESTS_DIR,
    BrokenEvalLink,
    BrokenTestLink,
    EvalLink,
    TestLink,
    find_eval_links,
    find_test_links,
    validate_eval_links,
    validate_test_links,
)
from outcomeeng_testing.harnesses.link_integrity import (
    deep_eval_layout,
    deep_test_layout,
    fenced_block_eval_layout,
    fenced_block_test_layout,
    inline_code_span_eval_layout,
    inline_code_span_test_layout,
    link_integrity_root,
    longer_closing_fence_test_layout,
    loose_eval_toml_layout,
    loose_test_layout,
    missing_eval_toml_layout,
    missing_test_target_layout,
    multi_backtick_inline_eval_layout,
    multi_backtick_inline_test_layout,
    non_eval_markdown_link_layout,
    non_python_test_target_layout,
    non_test_filename_layout,
    non_toml_eval_target_layout,
    resolvable_eval_layout,
    resolvable_test_layout,
    tilde_fenced_test_layout,
    two_node_eval_layout,
)


# --- [eval](path) links --------------------------------------------------


def test_find_eval_links_finds_a_resolvable_link() -> None:
    with link_integrity_root() as root:
        layout = resolvable_eval_layout(root)

        links = find_eval_links(root)

        assert len(links) == 1
        assert isinstance(links[0], EvalLink)
        assert links[0].source.resolve() == layout.source.resolve()
        assert links[0].target.resolve() == layout.target.resolve()


def test_find_eval_links_ignores_non_eval_markdown_links() -> None:
    with link_integrity_root() as root:
        non_eval_markdown_link_layout(root)

        assert find_eval_links(root) == []


def test_find_eval_links_ignores_inline_code_spans() -> None:
    with link_integrity_root() as root:
        inline_code_span_eval_layout(root)

        assert find_eval_links(root) == []


def test_find_eval_links_ignores_multi_backtick_inline_code_spans() -> None:
    with link_integrity_root() as root:
        multi_backtick_inline_eval_layout(root)

        assert find_eval_links(root) == []


def test_find_eval_links_ignores_fenced_code_blocks() -> None:
    with link_integrity_root() as root:
        fenced_block_eval_layout(root)

        assert find_eval_links(root) == []


def test_find_eval_links_returns_all_links_across_files() -> None:
    with link_integrity_root() as root:
        first, second = two_node_eval_layout(root)

        links = find_eval_links(root)

        assert {link.source.resolve() for link in links} == {
            first.source.resolve(),
            second.source.resolve(),
        }


def test_validate_eval_links_returns_empty_when_all_resolve() -> None:
    with link_integrity_root() as root:
        resolvable_eval_layout(root)

        assert validate_eval_links(root) == []


def test_validate_eval_links_reports_a_missing_eval_toml() -> None:
    with link_integrity_root() as root:
        layout = missing_eval_toml_layout(root)

        broken = validate_eval_links(root)

        assert len(broken) == 1
        assert isinstance(broken[0], BrokenEvalLink)
        assert broken[0].target == layout.target.resolve()
        assert broken[0].reason == REASON_TARGET_MISSING


def test_validate_eval_links_rejects_a_link_to_a_non_eval_toml_file() -> None:
    with link_integrity_root() as root:
        layout = non_toml_eval_target_layout(root)

        broken = validate_eval_links(root)

        assert len(broken) == 1
        assert broken[0].target == layout.target.resolve()
        assert broken[0].reason == REASON_EVAL_NOT_TOML


def test_validate_eval_links_resolves_paths_relative_to_the_source() -> None:
    with link_integrity_root() as root:
        deep_eval_layout(root)

        assert validate_eval_links(root) == []


def test_validate_eval_links_rejects_a_target_outside_an_evals_rule_dir() -> None:
    with link_integrity_root() as root:
        layout = loose_eval_toml_layout(root)

        broken = validate_eval_links(root)

        assert len(broken) == 1
        assert broken[0].target == layout.target.resolve()
        assert broken[0].reason == REASON_EVAL_OUTSIDE_EVALS_DIR


# --- [test](path) links --------------------------------------------------


def test_find_test_links_finds_a_resolvable_link() -> None:
    with link_integrity_root() as root:
        layout = resolvable_test_layout(root)

        links = find_test_links(root)

        assert len(links) == 1
        assert isinstance(links[0], TestLink)
        assert links[0].source.resolve() == layout.source.resolve()
        assert links[0].target.resolve() == layout.target.resolve()


def test_find_test_links_ignores_inline_code_spans() -> None:
    with link_integrity_root() as root:
        inline_code_span_test_layout(root)

        assert find_test_links(root) == []


def test_find_test_links_ignores_multi_backtick_inline_code_spans() -> None:
    with link_integrity_root() as root:
        multi_backtick_inline_test_layout(root)

        assert find_test_links(root) == []


def test_find_test_links_ignores_fenced_code_blocks() -> None:
    with link_integrity_root() as root:
        fenced_block_test_layout(root)

        assert find_test_links(root) == []


def test_find_test_links_resume_after_a_fence_closed_by_a_longer_run() -> None:
    with link_integrity_root() as root:
        layout = longer_closing_fence_test_layout(root)

        links = find_test_links(root)

        assert [link.target.resolve() for link in links] == [layout.target.resolve()]


def test_find_test_links_ignores_tilde_fenced_code_blocks() -> None:
    with link_integrity_root() as root:
        tilde_fenced_test_layout(root)

        assert find_test_links(root) == []


def test_validate_test_links_returns_empty_when_all_resolve() -> None:
    with link_integrity_root() as root:
        resolvable_test_layout(root)

        assert validate_test_links(root) == []


def test_validate_test_links_reports_a_missing_target() -> None:
    with link_integrity_root() as root:
        layout = missing_test_target_layout(root)

        broken = validate_test_links(root)

        assert len(broken) == 1
        assert isinstance(broken[0], BrokenTestLink)
        assert broken[0].target == layout.target.resolve()
        assert broken[0].reason == REASON_TARGET_MISSING


def test_validate_test_links_rejects_a_non_test_filename() -> None:
    with link_integrity_root() as root:
        layout = non_test_filename_layout(root)

        broken = validate_test_links(root)

        assert len(broken) == 1
        assert broken[0].target == layout.target.resolve()
        assert broken[0].reason == REASON_TEST_NOT_COLLECTABLE


def test_validate_test_links_rejects_a_non_python_target() -> None:
    with link_integrity_root() as root:
        layout = non_python_test_target_layout(root)

        broken = validate_test_links(root)

        assert len(broken) == 1
        assert broken[0].target == layout.target.resolve()
        assert broken[0].reason == REASON_TEST_NOT_COLLECTABLE


def test_validate_test_links_resolves_paths_relative_to_the_source() -> None:
    with link_integrity_root() as root:
        deep_test_layout(root)

        assert validate_test_links(root) == []


def test_validate_test_links_rejects_a_target_outside_a_tests_dir() -> None:
    with link_integrity_root() as root:
        layout = loose_test_layout(root)

        broken = validate_test_links(root)

        assert len(broken) == 1
        assert isinstance(broken[0], BrokenTestLink)
        assert broken[0].target == layout.target.resolve()
        assert broken[0].reason == REASON_TEST_OUTSIDE_TESTS_DIR
