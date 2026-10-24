"""Mapping tests for the manage-pr review-thread resolver."""

from __future__ import annotations

from outcomeeng_testing.harnesses.review_thread_resolver import (
    direct_thread_id_resolves_without_discovery,
    malformed_paginated_response_returns_error,
    missing_comment_page_info_returns_error,
    missing_review_thread_nodes_returns_error,
    null_paginated_thread_node_returns_error,
    null_review_thread_discovery_payload_returns_error,
    review_comment_id_discovers_thread_before_resolving,
    review_comment_not_found_after_complete_pagination_returns_error,
    review_thread_discovery_pages_comments_until_comment_is_found,
    review_thread_discovery_pages_threads_until_comment_is_found,
)


def test_review_comment_id_discovers_thread_before_resolving() -> None:
    assert review_comment_id_discovers_thread_before_resolving()


def test_direct_thread_id_resolves_without_discovery() -> None:
    assert direct_thread_id_resolves_without_discovery()


def test_review_thread_discovery_pages_threads_until_comment_is_found() -> None:
    assert review_thread_discovery_pages_threads_until_comment_is_found()


def test_review_thread_discovery_pages_comments_until_comment_is_found() -> None:
    assert review_thread_discovery_pages_comments_until_comment_is_found()


def test_review_comment_not_found_after_complete_pagination_returns_error() -> None:
    assert review_comment_not_found_after_complete_pagination_returns_error()


def test_missing_comment_page_info_returns_error() -> None:
    assert missing_comment_page_info_returns_error()


def test_null_review_thread_discovery_payload_returns_error() -> None:
    assert null_review_thread_discovery_payload_returns_error()


def test_missing_review_thread_nodes_returns_error() -> None:
    assert missing_review_thread_nodes_returns_error()


def test_null_paginated_thread_node_returns_error() -> None:
    assert null_paginated_thread_node_returns_error()


def test_malformed_paginated_response_returns_error() -> None:
    assert malformed_paginated_response_returns_error()
