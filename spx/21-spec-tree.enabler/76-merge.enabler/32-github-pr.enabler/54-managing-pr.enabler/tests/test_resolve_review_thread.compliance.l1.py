"""Compliance evidence for malformed review-thread resolver payloads."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from outcomeeng_testing.harnesses.review_thread_resolver import (
    GITHUB_RESPONSE,
    RESOLVER,
    completed,
    run_resolver,
)


def test_review_comment_not_found_after_complete_pagination_returns_error() -> None:
    run = run_resolver(
        [
            RESOLVER.ResolverOption.REPOSITORY.value,
            "outcomeeng/plugins",
            RESOLVER.ResolverOption.PULL_REQUEST.value,
            "405",
            RESOLVER.ResolverOption.REVIEW_COMMENT_ID.value,
            "909",
        ],
        lambda command, _kwargs: completed(
            command,
            stdout=json.dumps(
                GITHUB_RESPONSE.threads_payload(
                    GITHUB_RESPONSE.review_threads(
                        nodes=[
                            GITHUB_RESPONSE.thread(
                                thread_id=RESOLVER.format_thread_id("thread0008"),
                                comments=GITHUB_RESPONSE.comments(
                                    nodes=[
                                        GITHUB_RESPONSE.comment(
                                            node_id=RESOLVER.format_review_comment_node_id(
                                                "comment0008"
                                            ),
                                            database_id=808,
                                        )
                                    ],
                                    has_next_page=False,
                                ),
                            )
                        ]
                    )
                )
            ),
        ),
    )

    assert run.returncode == RESOLVER.ResolverExitCode.INVALID_INPUT
    assert RESOLVER.ResolverErrorMessage.COMMENT_NOT_FOUND.value in run.stderr


def test_invalid_json_payload_returns_error() -> None:
    run = run_resolver(
        [
            RESOLVER.ResolverOption.REPOSITORY.value,
            "outcomeeng/plugins",
            RESOLVER.ResolverOption.PULL_REQUEST.value,
            "405",
            RESOLVER.ResolverOption.REVIEW_COMMENT_ID.value,
            "909",
        ],
        lambda command, _kwargs: completed(
            command,
            stdout=Path(
                "outcomeeng_testing/fixtures/review_thread_resolver/invalid.txt"
            ).read_text(encoding="utf-8"),
        ),
    )

    assert run.returncode == RESOLVER.ResolverExitCode.INVALID_INPUT
    assert RESOLVER.ResolverErrorMessage.INVALID_JSON.value in run.stderr


def test_non_object_json_payload_returns_error() -> None:
    run = run_resolver(
        [
            RESOLVER.ResolverOption.REPOSITORY.value,
            "outcomeeng/plugins",
            RESOLVER.ResolverOption.PULL_REQUEST.value,
            "405",
            RESOLVER.ResolverOption.REVIEW_COMMENT_ID.value,
            "909",
        ],
        lambda command, _kwargs: completed(
            command,
            stdout=Path(
                "outcomeeng_testing/fixtures/review_thread_resolver/non_object.json"
            ).read_text(encoding="utf-8"),
        ),
    )

    assert run.returncode == RESOLVER.ResolverExitCode.INVALID_INPUT
    assert RESOLVER.ResolverErrorMessage.RESPONSE_PAYLOAD.value in run.stderr


def test_non_object_data_payload_returns_error() -> None:
    run = run_resolver(
        [
            RESOLVER.ResolverOption.REPOSITORY.value,
            "outcomeeng/plugins",
            RESOLVER.ResolverOption.PULL_REQUEST.value,
            "405",
            RESOLVER.ResolverOption.REVIEW_COMMENT_ID.value,
            "909",
        ],
        lambda command, _kwargs: completed(
            command,
            stdout=json.dumps({RESOLVER.GitHubResponseField.DATA.value: None}),
        ),
    )

    assert run.returncode == RESOLVER.ResolverExitCode.INVALID_INPUT
    assert RESOLVER.ResolverErrorMessage.DATA_PAYLOAD.value in run.stderr


def test_null_repository_payload_returns_error() -> None:
    run = run_resolver(
        [
            RESOLVER.ResolverOption.REPOSITORY.value,
            "outcomeeng/plugins",
            RESOLVER.ResolverOption.PULL_REQUEST.value,
            "405",
            RESOLVER.ResolverOption.REVIEW_COMMENT_ID.value,
            "909",
        ],
        lambda command, _kwargs: completed(
            command,
            stdout=json.dumps(GITHUB_RESPONSE.null_repository_payload()),
        ),
    )

    assert run.returncode == RESOLVER.ResolverExitCode.INVALID_INPUT
    assert RESOLVER.ResolverErrorMessage.REPOSITORY_PAYLOAD.value in run.stderr


def test_null_pull_request_payload_returns_error() -> None:
    run = run_resolver(
        [
            RESOLVER.ResolverOption.REPOSITORY.value,
            "outcomeeng/plugins",
            RESOLVER.ResolverOption.PULL_REQUEST.value,
            "405",
            RESOLVER.ResolverOption.REVIEW_COMMENT_ID.value,
            "909",
        ],
        lambda command, _kwargs: completed(
            command,
            stdout=json.dumps(GITHUB_RESPONSE.null_pull_request_payload()),
        ),
    )

    assert run.returncode == RESOLVER.ResolverExitCode.INVALID_INPUT
    assert RESOLVER.ResolverErrorMessage.PULL_REQUEST_PAYLOAD.value in run.stderr


def test_non_object_review_threads_payload_returns_error() -> None:
    run = run_resolver(
        [
            RESOLVER.ResolverOption.REPOSITORY.value,
            "outcomeeng/plugins",
            RESOLVER.ResolverOption.PULL_REQUEST.value,
            "405",
            RESOLVER.ResolverOption.REVIEW_COMMENT_ID.value,
            "909",
        ],
        lambda command, _kwargs: completed(
            command,
            stdout=json.dumps(GITHUB_RESPONSE.threads_payload(None)),
        ),
    )

    assert run.returncode == RESOLVER.ResolverExitCode.INVALID_INPUT
    assert RESOLVER.ResolverErrorMessage.REVIEW_THREADS_PAYLOAD.value in run.stderr


def test_missing_review_thread_nodes_returns_error() -> None:
    run = run_resolver(
        [
            RESOLVER.ResolverOption.REPOSITORY.value,
            "outcomeeng/plugins",
            RESOLVER.ResolverOption.PULL_REQUEST.value,
            "405",
            RESOLVER.ResolverOption.REVIEW_COMMENT_ID.value,
            "909",
        ],
        lambda command, _kwargs: completed(
            command,
            stdout=json.dumps(
                GITHUB_RESPONSE.threads_payload(
                    GITHUB_RESPONSE.review_threads(nodes=None)
                )
            ),
        ),
    )

    assert run.returncode == RESOLVER.ResolverExitCode.INVALID_INPUT
    assert RESOLVER.ResolverErrorMessage.THREAD_NODES.value in run.stderr


def test_non_object_review_thread_node_returns_error() -> None:
    run = run_resolver(
        [
            RESOLVER.ResolverOption.REPOSITORY.value,
            "outcomeeng/plugins",
            RESOLVER.ResolverOption.PULL_REQUEST.value,
            "405",
            RESOLVER.ResolverOption.REVIEW_COMMENT_ID.value,
            "909",
        ],
        lambda command, _kwargs: completed(
            command,
            stdout=json.dumps(
                GITHUB_RESPONSE.threads_payload(
                    GITHUB_RESPONSE.review_threads(nodes=[None])
                )
            ),
        ),
    )

    assert run.returncode == RESOLVER.ResolverExitCode.INVALID_INPUT
    assert RESOLVER.ResolverErrorMessage.THREAD_NODE.value in run.stderr


def test_malformed_review_thread_node_id_returns_error() -> None:
    run = run_resolver(
        [
            RESOLVER.ResolverOption.REPOSITORY.value,
            "outcomeeng/plugins",
            RESOLVER.ResolverOption.PULL_REQUEST.value,
            "405",
            RESOLVER.ResolverOption.REVIEW_COMMENT_ID.value,
            "909",
        ],
        lambda command, _kwargs: completed(
            command,
            stdout=json.dumps(
                GITHUB_RESPONSE.threads_payload(
                    GITHUB_RESPONSE.review_threads(
                        nodes=[
                            GITHUB_RESPONSE.thread(
                                thread_id=RESOLVER.format_review_comment_node_id(
                                    "comment0023"
                                ),
                                comments=GITHUB_RESPONSE.comments(
                                    nodes=[],
                                    has_next_page=False,
                                ),
                            )
                        ]
                    )
                )
            ),
        ),
    )

    assert run.returncode == RESOLVER.ResolverExitCode.INVALID_INPUT
    assert RESOLVER.ResolverErrorMessage.THREAD_NODE_ID.value in run.stderr


def test_non_object_thread_comments_returns_error() -> None:
    run = run_resolver(
        [
            RESOLVER.ResolverOption.REPOSITORY.value,
            "outcomeeng/plugins",
            RESOLVER.ResolverOption.PULL_REQUEST.value,
            "405",
            RESOLVER.ResolverOption.REVIEW_COMMENT_ID.value,
            "909",
        ],
        lambda command, _kwargs: completed(
            command,
            stdout=json.dumps(
                GITHUB_RESPONSE.threads_payload(
                    GITHUB_RESPONSE.review_threads(
                        nodes=[
                            GITHUB_RESPONSE.thread(
                                thread_id=RESOLVER.format_thread_id("thread0011"),
                                comments=None,
                            )
                        ]
                    )
                )
            ),
        ),
    )

    assert run.returncode == RESOLVER.ResolverExitCode.INVALID_INPUT
    assert RESOLVER.ResolverErrorMessage.THREAD_COMMENTS.value in run.stderr


def test_non_object_comment_node_returns_error() -> None:
    run = run_resolver(
        [
            RESOLVER.ResolverOption.REPOSITORY.value,
            "outcomeeng/plugins",
            RESOLVER.ResolverOption.PULL_REQUEST.value,
            "405",
            RESOLVER.ResolverOption.REVIEW_COMMENT_ID.value,
            "909",
        ],
        lambda command, _kwargs: completed(
            command,
            stdout=json.dumps(
                GITHUB_RESPONSE.threads_payload(
                    GITHUB_RESPONSE.review_threads(
                        nodes=[
                            GITHUB_RESPONSE.thread(
                                thread_id=RESOLVER.format_thread_id("thread0012"),
                                comments=GITHUB_RESPONSE.comments(
                                    nodes=[None],
                                    has_next_page=False,
                                ),
                            )
                        ]
                    )
                )
            ),
        ),
    )

    assert run.returncode == RESOLVER.ResolverExitCode.INVALID_INPUT
    assert RESOLVER.ResolverErrorMessage.COMMENT_NODE.value in run.stderr


def test_matching_comment_does_not_hide_later_malformed_node_id() -> None:
    fields = RESOLVER.GitHubResponseField
    comments = GITHUB_RESPONSE.comments(
        nodes=[
            GITHUB_RESPONSE.comment(
                node_id=RESOLVER.format_review_comment_node_id("comment0020"),
                database_id=2020,
            ),
            {fields.DATABASE_ID.value: 2121},
        ],
        has_next_page=False,
    )
    run = run_resolver(
        [
            RESOLVER.ResolverOption.REPOSITORY.value,
            "outcomeeng/plugins",
            RESOLVER.ResolverOption.PULL_REQUEST.value,
            "405",
            RESOLVER.ResolverOption.REVIEW_COMMENT_ID.value,
            "2020",
        ],
        lambda command, _kwargs: completed(
            command,
            stdout=json.dumps(
                GITHUB_RESPONSE.threads_payload(
                    GITHUB_RESPONSE.review_threads(
                        nodes=[
                            GITHUB_RESPONSE.thread(
                                thread_id=RESOLVER.format_thread_id("thread0020"),
                                comments=comments,
                            )
                        ]
                    )
                )
            ),
        ),
    )

    assert run.returncode == RESOLVER.ResolverExitCode.INVALID_INPUT
    assert RESOLVER.ResolverErrorMessage.COMMENT_NODE_ID.value in run.stderr


def test_non_positive_comment_database_id_returns_error() -> None:
    run = run_resolver(
        [
            RESOLVER.ResolverOption.REPOSITORY.value,
            "outcomeeng/plugins",
            RESOLVER.ResolverOption.PULL_REQUEST.value,
            "405",
            RESOLVER.ResolverOption.REVIEW_COMMENT_ID.value,
            "909",
        ],
        lambda command, _kwargs: completed(
            command,
            stdout=json.dumps(
                GITHUB_RESPONSE.threads_payload(
                    GITHUB_RESPONSE.review_threads(
                        nodes=[
                            GITHUB_RESPONSE.thread(
                                thread_id=RESOLVER.format_thread_id("thread0021"),
                                comments=GITHUB_RESPONSE.comments(
                                    nodes=[
                                        GITHUB_RESPONSE.comment(
                                            node_id=RESOLVER.format_review_comment_node_id(
                                                "comment0021"
                                            ),
                                            database_id=0,
                                        )
                                    ],
                                    has_next_page=False,
                                ),
                            )
                        ]
                    )
                )
            ),
        ),
    )

    assert run.returncode == RESOLVER.ResolverExitCode.INVALID_INPUT
    assert RESOLVER.ResolverErrorMessage.COMMENT_DATABASE_ID.value in run.stderr


def test_non_list_comment_nodes_returns_error() -> None:
    comments = GITHUB_RESPONSE.comments(
        nodes=[],
        has_next_page=False,
    )
    comments[RESOLVER.GitHubResponseField.NODES.value] = None
    run = run_resolver(
        [
            RESOLVER.ResolverOption.REPOSITORY.value,
            "outcomeeng/plugins",
            RESOLVER.ResolverOption.PULL_REQUEST.value,
            "405",
            RESOLVER.ResolverOption.REVIEW_COMMENT_ID.value,
            "909",
        ],
        lambda command, _kwargs: completed(
            command,
            stdout=json.dumps(
                GITHUB_RESPONSE.threads_payload(
                    GITHUB_RESPONSE.review_threads(
                        nodes=[
                            GITHUB_RESPONSE.thread(
                                thread_id=RESOLVER.format_thread_id("thread0013"),
                                comments=comments,
                            )
                        ]
                    )
                )
            ),
        ),
    )

    assert run.returncode == RESOLVER.ResolverExitCode.INVALID_INPUT
    assert RESOLVER.ResolverErrorMessage.COMMENTS_NODES.value in run.stderr


def test_missing_comment_page_info_returns_error() -> None:
    run = run_resolver(
        [
            RESOLVER.ResolverOption.REPOSITORY.value,
            "outcomeeng/plugins",
            RESOLVER.ResolverOption.PULL_REQUEST.value,
            "405",
            RESOLVER.ResolverOption.REVIEW_COMMENT_ID.value,
            "1111",
        ],
        lambda command, _kwargs: completed(
            command,
            stdout=json.dumps(
                GITHUB_RESPONSE.threads_payload(
                    GITHUB_RESPONSE.review_threads(
                        nodes=[
                            GITHUB_RESPONSE.thread(
                                thread_id=RESOLVER.format_thread_id("thread0010"),
                                comments=GITHUB_RESPONSE.comments(
                                    nodes=[
                                        GITHUB_RESPONSE.comment(
                                            node_id=RESOLVER.format_review_comment_node_id(
                                                "comment0010"
                                            ),
                                            database_id=1010,
                                        )
                                    ],
                                    has_next_page=False,
                                    include_page_info=False,
                                ),
                            )
                        ]
                    )
                )
            ),
        ),
    )

    assert run.returncode == RESOLVER.ResolverExitCode.INVALID_INPUT
    assert RESOLVER.ResolverErrorMessage.COMMENTS_PAGE_INFO.value in run.stderr


def test_non_boolean_comment_has_next_page_returns_error() -> None:
    fields = RESOLVER.GitHubResponseField
    comments = GITHUB_RESPONSE.comments(nodes=[], has_next_page=False)
    page_info = comments[fields.PAGE_INFO.value]
    assert isinstance(page_info, dict)
    page_info[fields.HAS_NEXT_PAGE.value] = "false"
    run = run_resolver(
        [
            RESOLVER.ResolverOption.REPOSITORY.value,
            "outcomeeng/plugins",
            RESOLVER.ResolverOption.PULL_REQUEST.value,
            "405",
            RESOLVER.ResolverOption.REVIEW_COMMENT_ID.value,
            "909",
        ],
        lambda command, _kwargs: completed(
            command,
            stdout=json.dumps(
                GITHUB_RESPONSE.threads_payload(
                    GITHUB_RESPONSE.review_threads(
                        nodes=[
                            GITHUB_RESPONSE.thread(
                                thread_id=RESOLVER.format_thread_id("thread0022"),
                                comments=comments,
                            )
                        ]
                    )
                )
            ),
        ),
    )

    assert run.returncode == RESOLVER.ResolverExitCode.INVALID_INPUT
    assert RESOLVER.ResolverErrorMessage.COMMENTS_HAS_NEXT_PAGE.value in run.stderr


def test_missing_comment_page_cursor_returns_error() -> None:
    run = run_resolver(
        [
            RESOLVER.ResolverOption.REPOSITORY.value,
            "outcomeeng/plugins",
            RESOLVER.ResolverOption.PULL_REQUEST.value,
            "405",
            RESOLVER.ResolverOption.REVIEW_COMMENT_ID.value,
            "1111",
        ],
        lambda command, _kwargs: completed(
            command,
            stdout=json.dumps(
                GITHUB_RESPONSE.threads_payload(
                    GITHUB_RESPONSE.review_threads(
                        nodes=[
                            GITHUB_RESPONSE.thread(
                                thread_id=RESOLVER.format_thread_id("thread0014"),
                                comments=GITHUB_RESPONSE.comments(
                                    nodes=[],
                                    has_next_page=True,
                                    end_cursor=None,
                                ),
                            )
                        ]
                    )
                )
            ),
        ),
    )

    assert run.returncode == RESOLVER.ResolverExitCode.INVALID_INPUT
    assert RESOLVER.ResolverErrorMessage.COMMENTS_CURSOR.value in run.stderr


def test_null_paginated_thread_node_returns_error() -> None:
    thread_id = RESOLVER.format_thread_id("thread0009")
    comment_node_id = RESOLVER.format_review_comment_node_id("comment0009")
    threads_page = GITHUB_RESPONSE.threads_payload(
        GITHUB_RESPONSE.review_threads(
            nodes=[
                GITHUB_RESPONSE.thread(
                    thread_id=thread_id,
                    comments=GITHUB_RESPONSE.comments(
                        nodes=[
                            GITHUB_RESPONSE.comment(
                                node_id=comment_node_id,
                                database_id=909,
                            )
                        ],
                        has_next_page=True,
                        end_cursor="comment-cursor-2",
                    ),
                )
            ]
        )
    )

    def responder(
        command: list[str],
        _kwargs: dict[str, object],
    ) -> subprocess.CompletedProcess[str]:
        if f"{RESOLVER.GraphQLField.THREAD_ID.value}={thread_id}" in command:
            return completed(
                command,
                stdout=json.dumps(GITHUB_RESPONSE.null_thread_payload()),
            )
        return completed(command, stdout=json.dumps(threads_page))

    run = run_resolver(
        [
            RESOLVER.ResolverOption.REPOSITORY.value,
            "outcomeeng/plugins",
            RESOLVER.ResolverOption.PULL_REQUEST.value,
            "405",
            RESOLVER.ResolverOption.REVIEW_COMMENT_ID.value,
            "1001",
        ],
        responder,
    )

    assert run.returncode == RESOLVER.ResolverExitCode.INVALID_INPUT
    assert RESOLVER.ResolverErrorMessage.PAGINATED_THREAD.value in run.stderr


def test_non_object_paginated_node_comments_returns_error() -> None:
    thread_id = RESOLVER.format_thread_id("thread0015")
    threads_page = GITHUB_RESPONSE.threads_payload(
        GITHUB_RESPONSE.review_threads(
            nodes=[
                GITHUB_RESPONSE.thread(
                    thread_id=thread_id,
                    comments=GITHUB_RESPONSE.comments(
                        nodes=[],
                        has_next_page=True,
                        end_cursor="comment-cursor-3",
                    ),
                )
            ]
        )
    )

    def responder(
        command: list[str],
        _kwargs: dict[str, object],
    ) -> subprocess.CompletedProcess[str]:
        if f"{RESOLVER.GraphQLField.THREAD_ID.value}={thread_id}" in command:
            return completed(
                command,
                stdout=json.dumps(GITHUB_RESPONSE.thread_comments_payload(None)),
            )
        return completed(command, stdout=json.dumps(threads_page))

    run = run_resolver(
        [
            RESOLVER.ResolverOption.REPOSITORY.value,
            "outcomeeng/plugins",
            RESOLVER.ResolverOption.PULL_REQUEST.value,
            "405",
            RESOLVER.ResolverOption.REVIEW_COMMENT_ID.value,
            "1111",
        ],
        responder,
    )

    assert run.returncode == RESOLVER.ResolverExitCode.INVALID_INPUT
    assert RESOLVER.ResolverErrorMessage.NODE_COMMENTS.value in run.stderr


def test_missing_thread_page_cursor_returns_error() -> None:
    run = run_resolver(
        [
            RESOLVER.ResolverOption.REPOSITORY.value,
            "outcomeeng/plugins",
            RESOLVER.ResolverOption.PULL_REQUEST.value,
            "405",
            RESOLVER.ResolverOption.REVIEW_COMMENT_ID.value,
            "909",
        ],
        lambda command, _kwargs: completed(
            command,
            stdout=json.dumps(
                GITHUB_RESPONSE.threads_payload(
                    GITHUB_RESPONSE.review_threads(
                        nodes=[],
                        has_next_page=True,
                        end_cursor=None,
                    )
                )
            ),
        ),
    )

    assert run.returncode == RESOLVER.ResolverExitCode.INVALID_INPUT
    assert RESOLVER.ResolverErrorMessage.THREAD_CURSOR.value in run.stderr


def test_non_object_thread_page_info_returns_error() -> None:
    review_threads = GITHUB_RESPONSE.review_threads(nodes=[])
    review_threads[RESOLVER.GitHubResponseField.PAGE_INFO.value] = None
    run = run_resolver(
        [
            RESOLVER.ResolverOption.REPOSITORY.value,
            "outcomeeng/plugins",
            RESOLVER.ResolverOption.PULL_REQUEST.value,
            "405",
            RESOLVER.ResolverOption.REVIEW_COMMENT_ID.value,
            "909",
        ],
        lambda command, _kwargs: completed(
            command,
            stdout=json.dumps(GITHUB_RESPONSE.threads_payload(review_threads)),
        ),
    )

    assert run.returncode == RESOLVER.ResolverExitCode.INVALID_INPUT
    assert RESOLVER.ResolverErrorMessage.THREAD_PAGE_INFO.value in run.stderr


def test_non_boolean_thread_has_next_page_returns_error() -> None:
    fields = RESOLVER.GitHubResponseField
    review_threads = GITHUB_RESPONSE.review_threads(nodes=[])
    page_info = review_threads[fields.PAGE_INFO.value]
    assert isinstance(page_info, dict)
    page_info[fields.HAS_NEXT_PAGE.value] = "false"
    run = run_resolver(
        [
            RESOLVER.ResolverOption.REPOSITORY.value,
            "outcomeeng/plugins",
            RESOLVER.ResolverOption.PULL_REQUEST.value,
            "405",
            RESOLVER.ResolverOption.REVIEW_COMMENT_ID.value,
            "909",
        ],
        lambda command, _kwargs: completed(
            command,
            stdout=json.dumps(GITHUB_RESPONSE.threads_payload(review_threads)),
        ),
    )

    assert run.returncode == RESOLVER.ResolverExitCode.INVALID_INPUT
    assert RESOLVER.ResolverErrorMessage.THREAD_HAS_NEXT_PAGE.value in run.stderr
