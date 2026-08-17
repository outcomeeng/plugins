"""Scenario evidence for the manage-pr review-thread resolver."""

from __future__ import annotations

import json
import subprocess

from outcomeeng_testing.harnesses.review_thread_resolver import (
    GITHUB_RESPONSE,
    RESOLVER,
    completed,
    run_resolver,
)


def test_direct_thread_id_resolves_without_discovery() -> None:
    thread_id = RESOLVER.format_thread_id("thread0002")
    run = run_resolver(
        [
            RESOLVER.ResolverOption.HOST.value,
            "ghe.example.com",
            thread_id,
        ],
        lambda command, _kwargs: completed(command),
    )

    assert run.returncode == RESOLVER.ResolverExitCode.SUCCESS
    assert len(run.interactions) == 1
    assert run.interactions[0].command[: len(RESOLVER.GRAPHQL_COMMAND)] == (
        RESOLVER.GRAPHQL_COMMAND
    )
    assert RESOLVER.GraphQLOption.HOSTNAME.value in run.interactions[0].command
    assert "ghe.example.com" in run.interactions[0].command
    assert RESOLVER.GraphQLOption.SILENT.value in run.interactions[0].command
    assert (
        f"{RESOLVER.GraphQLField.ID.value}={thread_id}" in run.interactions[0].command
    )


def test_review_comment_database_id_discovers_thread_before_resolving() -> None:
    thread_id = RESOLVER.format_thread_id("thread0001")
    comment_node_id = RESOLVER.format_review_comment_node_id("comment0001")
    payload = GITHUB_RESPONSE.threads_payload(
        GITHUB_RESPONSE.review_threads(
            nodes=[
                GITHUB_RESPONSE.thread(
                    thread_id=thread_id,
                    comments=GITHUB_RESPONSE.comments(
                        nodes=[
                            GITHUB_RESPONSE.comment(
                                node_id=comment_node_id,
                                database_id=12345,
                            )
                        ],
                        has_next_page=False,
                    ),
                )
            ]
        )
    )

    def responder(
        command: list[str],
        kwargs: dict[str, object],
    ) -> subprocess.CompletedProcess[str]:
        if kwargs.get("capture_output") is True:
            return completed(command, stdout=json.dumps(payload))
        return completed(command)

    run = run_resolver(
        [
            RESOLVER.ResolverOption.HOST.value,
            "ghe.example.com",
            RESOLVER.ResolverOption.REPOSITORY.value,
            "outcomeeng/plugins",
            RESOLVER.ResolverOption.PULL_REQUEST.value,
            "405",
            RESOLVER.ResolverOption.REVIEW_COMMENT_ID.value,
            "12345",
        ],
        responder,
    )

    discovery, resolution = run.interactions
    assert run.returncode == RESOLVER.ResolverExitCode.SUCCESS
    assert f"{RESOLVER.GraphQLField.OWNER.value}=outcomeeng" in discovery.command
    assert f"{RESOLVER.GraphQLField.REPOSITORY.value}=plugins" in discovery.command
    assert f"{RESOLVER.GraphQLField.NUMBER.value}=405" in discovery.command
    assert dict(discovery.keyword_arguments)["capture_output"] is True
    assert dict(discovery.keyword_arguments)["text"] is True
    assert f"{RESOLVER.GraphQLField.ID.value}={thread_id}" in resolution.command


def test_review_comment_node_id_discovers_thread_before_resolving() -> None:
    thread_id = RESOLVER.format_thread_id("thread0016")
    comment_node_id = RESOLVER.format_review_comment_node_id("comment0016")
    payload = GITHUB_RESPONSE.threads_payload(
        GITHUB_RESPONSE.review_threads(
            nodes=[
                GITHUB_RESPONSE.thread(
                    thread_id=thread_id,
                    comments=GITHUB_RESPONSE.comments(
                        nodes=[
                            GITHUB_RESPONSE.comment(
                                node_id=comment_node_id,
                                database_id=1616,
                            )
                        ],
                        has_next_page=False,
                    ),
                )
            ]
        )
    )

    def responder(
        command: list[str],
        kwargs: dict[str, object],
    ) -> subprocess.CompletedProcess[str]:
        if kwargs.get("capture_output") is True:
            return completed(command, stdout=json.dumps(payload))
        return completed(command)

    run = run_resolver(
        [
            RESOLVER.ResolverOption.REPOSITORY.value,
            "outcomeeng/plugins",
            RESOLVER.ResolverOption.PULL_REQUEST.value,
            "405",
            RESOLVER.ResolverOption.REVIEW_COMMENT_ID.value,
            comment_node_id,
        ],
        responder,
    )

    discovery, resolution = run.interactions
    assert run.returncode == RESOLVER.ResolverExitCode.SUCCESS
    assert f"{RESOLVER.GraphQLField.NUMBER.value}=405" in discovery.command
    assert f"{RESOLVER.GraphQLField.ID.value}={thread_id}" in resolution.command


def test_review_thread_discovery_pages_threads_until_comment_is_found() -> None:
    first_thread_id = RESOLVER.format_thread_id("thread0003")
    first_comment_node_id = RESOLVER.format_review_comment_node_id("comment0003")
    second_thread_id = RESOLVER.format_thread_id("thread0004")
    second_comment_node_id = RESOLVER.format_review_comment_node_id("comment0004")
    first_page = GITHUB_RESPONSE.threads_payload(
        GITHUB_RESPONSE.review_threads(
            nodes=[
                GITHUB_RESPONSE.thread(
                    thread_id=first_thread_id,
                    comments=GITHUB_RESPONSE.comments(
                        nodes=[
                            GITHUB_RESPONSE.comment(
                                node_id=first_comment_node_id,
                                database_id=303,
                            )
                        ],
                        has_next_page=False,
                    ),
                )
            ],
            has_next_page=True,
            end_cursor="cursor-1",
        )
    )
    second_page = GITHUB_RESPONSE.threads_payload(
        GITHUB_RESPONSE.review_threads(
            nodes=[
                GITHUB_RESPONSE.thread(
                    thread_id=second_thread_id,
                    comments=GITHUB_RESPONSE.comments(
                        nodes=[
                            GITHUB_RESPONSE.comment(
                                node_id=second_comment_node_id,
                                database_id=404,
                            )
                        ],
                        has_next_page=False,
                    ),
                )
            ]
        )
    )

    def responder(
        command: list[str],
        kwargs: dict[str, object],
    ) -> subprocess.CompletedProcess[str]:
        if kwargs.get("capture_output") is not True:
            return completed(command)
        if f"{RESOLVER.GraphQLField.THREADS_AFTER.value}=cursor-1" in command:
            return completed(command, stdout=json.dumps(second_page))
        return completed(command, stdout=json.dumps(first_page))

    run = run_resolver(
        [
            RESOLVER.ResolverOption.REPOSITORY.value,
            "outcomeeng/plugins",
            RESOLVER.ResolverOption.PULL_REQUEST.value,
            "405",
            RESOLVER.ResolverOption.REVIEW_COMMENT_ID.value,
            "404",
        ],
        responder,
    )

    first_query, second_query, resolution = run.interactions
    assert run.returncode == RESOLVER.ResolverExitCode.SUCCESS
    assert (
        f"{RESOLVER.GraphQLField.THREADS_AFTER.value}=cursor-1"
        not in first_query.command
    )
    assert (
        f"{RESOLVER.GraphQLField.THREADS_AFTER.value}=cursor-1" in second_query.command
    )
    assert f"{RESOLVER.GraphQLField.ID.value}={second_thread_id}" in resolution.command


def test_review_thread_discovery_pages_comments_until_comment_is_found() -> None:
    thread_id = RESOLVER.format_thread_id("thread0005")
    first_comment_node_id = RESOLVER.format_review_comment_node_id("comment0005")
    second_comment_node_id = RESOLVER.format_review_comment_node_id("comment0006")
    threads_page = GITHUB_RESPONSE.threads_payload(
        GITHUB_RESPONSE.review_threads(
            nodes=[
                GITHUB_RESPONSE.thread(
                    thread_id=thread_id,
                    comments=GITHUB_RESPONSE.comments(
                        nodes=[
                            GITHUB_RESPONSE.comment(
                                node_id=first_comment_node_id,
                                database_id=505,
                            )
                        ],
                        has_next_page=True,
                        end_cursor="comment-cursor-1",
                    ),
                )
            ]
        )
    )
    comments_page = GITHUB_RESPONSE.thread_comments_payload(
        GITHUB_RESPONSE.comments(
            nodes=[
                GITHUB_RESPONSE.comment(
                    node_id=second_comment_node_id,
                    database_id=606,
                )
            ],
            has_next_page=False,
        )
    )

    def responder(
        command: list[str],
        kwargs: dict[str, object],
    ) -> subprocess.CompletedProcess[str]:
        if kwargs.get("capture_output") is not True:
            return completed(command)
        if f"{RESOLVER.GraphQLField.THREAD_ID.value}={thread_id}" in command:
            return completed(command, stdout=json.dumps(comments_page))
        return completed(command, stdout=json.dumps(threads_page))

    run = run_resolver(
        [
            RESOLVER.ResolverOption.HOST.value,
            "ghe.example.com",
            RESOLVER.ResolverOption.REPOSITORY.value,
            "outcomeeng/plugins",
            RESOLVER.ResolverOption.PULL_REQUEST.value,
            "405",
            RESOLVER.ResolverOption.REVIEW_COMMENT_ID.value,
            "606",
        ],
        responder,
    )

    threads_query, comments_query, resolution = run.interactions
    assert run.returncode == RESOLVER.ResolverExitCode.SUCCESS
    assert f"{RESOLVER.GraphQLField.NUMBER.value}=405" in threads_query.command
    assert (
        f"{RESOLVER.GraphQLField.THREAD_ID.value}={thread_id}" in comments_query.command
    )
    assert (
        f"{RESOLVER.GraphQLField.COMMENTS_AFTER.value}=comment-cursor-1"
        in comments_query.command
    )
    assert f"{RESOLVER.GraphQLField.ID.value}={thread_id}" in resolution.command
