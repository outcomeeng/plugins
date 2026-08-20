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
    thread_field = f"{RESOLVER.GraphQLField.ID.value}={thread_id}"
    thread_field_index = run.interactions[0].command.index(thread_field)
    assert (
        run.interactions[0].command[thread_field_index - 1]
        == RESOLVER.GraphQLOption.STRING_FIELD.value
    )


def test_review_comment_database_id_discovers_thread_before_resolving() -> None:
    thread_id = RESOLVER.format_thread_id("thread0001")
    comment_node_id = RESOLVER.format_review_comment_node_id("comment0001")
    database_id = RESOLVER.GRAPHQL_INT_MAX
    payload = GITHUB_RESPONSE.threads_payload(
        GITHUB_RESPONSE.review_threads(
            nodes=[
                GITHUB_RESPONSE.thread(
                    thread_id=thread_id,
                    comments=GITHUB_RESPONSE.comments(
                        nodes=[
                            GITHUB_RESPONSE.comment(
                                node_id=comment_node_id,
                                database_id=database_id,
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
            str(RESOLVER.GRAPHQL_INT_MAX),
            RESOLVER.ResolverOption.REVIEW_COMMENT_ID.value,
            str(database_id),
        ],
        responder,
    )

    discovery, resolution = run.interactions
    assert run.returncode == RESOLVER.ResolverExitCode.SUCCESS
    owner_field = f"{RESOLVER.GraphQLField.OWNER.value}=outcomeeng"
    repository_field = f"{RESOLVER.GraphQLField.REPOSITORY.value}=plugins"
    number_field = f"{RESOLVER.GraphQLField.NUMBER.value}={RESOLVER.GRAPHQL_INT_MAX}"
    assert discovery.command[discovery.command.index(owner_field) - 1] == (
        RESOLVER.GraphQLOption.STRING_FIELD.value
    )
    assert discovery.command[discovery.command.index(repository_field) - 1] == (
        RESOLVER.GraphQLOption.STRING_FIELD.value
    )
    assert discovery.command[discovery.command.index(number_field) - 1] == (
        RESOLVER.GraphQLOption.TYPED_FIELD.value
    )
    assert dict(discovery.keyword_arguments)["capture_output"] is True
    assert dict(discovery.keyword_arguments)["text"] is True
    assert f"{RESOLVER.GraphQLField.ID.value}={thread_id}" in resolution.command


def test_review_comment_node_id_discovers_thread_before_resolving() -> None:
    first_thread_id = RESOLVER.format_thread_id("thread0015")
    first_comment_node_id = RESOLVER.format_review_comment_node_id("comment0015")
    thread_id = RESOLVER.format_thread_id("thread0016")
    comment_node_id = RESOLVER.format_review_comment_node_id("comment0016")
    payload = GITHUB_RESPONSE.threads_payload(
        GITHUB_RESPONSE.review_threads(
            nodes=[
                GITHUB_RESPONSE.thread(
                    thread_id=first_thread_id,
                    comments=GITHUB_RESPONSE.comments(
                        nodes=[
                            GITHUB_RESPONSE.comment(
                                node_id=first_comment_node_id,
                                database_id=1515,
                            )
                        ],
                        has_next_page=True,
                        end_cursor="@unused-cursor-file",
                    ),
                ),
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
                ),
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
            end_cursor="@cursor-file",
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
        if f"{RESOLVER.GraphQLField.THREADS_AFTER.value}=@cursor-file" in command:
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
        f"{RESOLVER.GraphQLField.THREADS_AFTER.value}=@cursor-file"
        not in first_query.command
    )
    assert (
        f"{RESOLVER.GraphQLField.THREADS_AFTER.value}=@cursor-file"
        in second_query.command
    )
    cursor_field = f"{RESOLVER.GraphQLField.THREADS_AFTER.value}=@cursor-file"
    assert second_query.command[second_query.command.index(cursor_field) - 1] == (
        RESOLVER.GraphQLOption.STRING_FIELD.value
    )
    assert f"{RESOLVER.GraphQLField.ID.value}={second_thread_id}" in resolution.command


def test_review_thread_discovery_checks_all_first_pages_before_later_comments() -> None:
    first_thread_id = RESOLVER.format_thread_id("thread0017")
    first_comment_node_id = RESOLVER.format_review_comment_node_id("comment0017")
    second_thread_id = RESOLVER.format_thread_id("thread0018")
    second_comment_node_id = RESOLVER.format_review_comment_node_id("comment0018")
    first_page = GITHUB_RESPONSE.threads_payload(
        GITHUB_RESPONSE.review_threads(
            nodes=[
                GITHUB_RESPONSE.thread(
                    thread_id=first_thread_id,
                    comments=GITHUB_RESPONSE.comments(
                        nodes=[
                            GITHUB_RESPONSE.comment(
                                node_id=first_comment_node_id,
                                database_id=1717,
                            )
                        ],
                        has_next_page=True,
                        end_cursor="@unused-comment-cursor-file",
                    ),
                )
            ],
            has_next_page=True,
            end_cursor="@thread-cursor-file",
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
                                database_id=1818,
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
        if any(
            token.startswith(f"{RESOLVER.GraphQLField.THREAD_ID.value}=")
            for token in command
        ):
            return completed(command, stdout="null")
        if (
            f"{RESOLVER.GraphQLField.THREADS_AFTER.value}=@thread-cursor-file"
            in command
        ):
            return completed(command, stdout=json.dumps(second_page))
        return completed(command, stdout=json.dumps(first_page))

    run = run_resolver(
        [
            RESOLVER.ResolverOption.REPOSITORY.value,
            "outcomeeng/plugins",
            RESOLVER.ResolverOption.PULL_REQUEST.value,
            "405",
            RESOLVER.ResolverOption.REVIEW_COMMENT_ID.value,
            "1818",
        ],
        responder,
    )

    first_query, second_query, resolution = run.interactions
    assert run.returncode == RESOLVER.ResolverExitCode.SUCCESS
    thread_cursor_field = (
        f"{RESOLVER.GraphQLField.THREADS_AFTER.value}=@thread-cursor-file"
    )
    assert thread_cursor_field not in first_query.command
    assert thread_cursor_field in second_query.command
    assert all(
        not any(
            token.startswith(f"{RESOLVER.GraphQLField.THREAD_ID.value}=")
            for token in interaction.command
        )
        for interaction in run.interactions
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
                        end_cursor="@comment-cursor-file",
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
        f"{RESOLVER.GraphQLField.COMMENTS_AFTER.value}=@comment-cursor-file"
        in comments_query.command
    )
    cursor_field = f"{RESOLVER.GraphQLField.COMMENTS_AFTER.value}=@comment-cursor-file"
    assert comments_query.command[comments_query.command.index(cursor_field) - 1] == (
        RESOLVER.GraphQLOption.STRING_FIELD.value
    )
    assert f"{RESOLVER.GraphQLField.ID.value}={thread_id}" in resolution.command


def test_review_thread_discovery_checks_peer_pages_before_deeper_pages() -> None:
    first_thread_id = RESOLVER.format_thread_id("thread0019")
    first_comment_node_id = RESOLVER.format_review_comment_node_id("comment0019")
    first_later_comment_node_id = RESOLVER.format_review_comment_node_id("comment0022")
    second_thread_id = RESOLVER.format_thread_id("thread0020")
    second_first_comment_node_id = RESOLVER.format_review_comment_node_id("comment0020")
    target_comment_node_id = RESOLVER.format_review_comment_node_id("comment0021")
    first_cursor = "first-comment-page-2"
    first_deeper_cursor = "first-comment-page-3"
    second_cursor = "second-comment-page-2"
    first_page = GITHUB_RESPONSE.threads_payload(
        GITHUB_RESPONSE.review_threads(
            nodes=[
                GITHUB_RESPONSE.thread(
                    thread_id=first_thread_id,
                    comments=GITHUB_RESPONSE.comments(
                        nodes=[
                            GITHUB_RESPONSE.comment(
                                node_id=first_comment_node_id,
                                database_id=1919,
                            )
                        ],
                        has_next_page=True,
                        end_cursor=first_cursor,
                    ),
                ),
                GITHUB_RESPONSE.thread(
                    thread_id=second_thread_id,
                    comments=GITHUB_RESPONSE.comments(
                        nodes=[
                            GITHUB_RESPONSE.comment(
                                node_id=second_first_comment_node_id,
                                database_id=2020,
                            )
                        ],
                        has_next_page=True,
                        end_cursor=second_cursor,
                    ),
                ),
            ]
        )
    )
    first_thread_second_page = GITHUB_RESPONSE.thread_comments_payload(
        GITHUB_RESPONSE.comments(
            nodes=[
                GITHUB_RESPONSE.comment(
                    node_id=first_later_comment_node_id,
                    database_id=1920,
                )
            ],
            has_next_page=True,
            end_cursor=first_deeper_cursor,
        )
    )
    second_thread_second_page = GITHUB_RESPONSE.thread_comments_payload(
        GITHUB_RESPONSE.comments(
            nodes=[
                GITHUB_RESPONSE.comment(
                    node_id=target_comment_node_id,
                    database_id=2021,
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
        if f"{RESOLVER.GraphQLField.COMMENTS_AFTER.value}={first_cursor}" in command:
            return completed(command, stdout=json.dumps(first_thread_second_page))
        if f"{RESOLVER.GraphQLField.COMMENTS_AFTER.value}={second_cursor}" in command:
            return completed(command, stdout=json.dumps(second_thread_second_page))
        if (
            f"{RESOLVER.GraphQLField.COMMENTS_AFTER.value}={first_deeper_cursor}"
            in command
        ):
            return completed(command, stdout="null")
        return completed(command, stdout=json.dumps(first_page))

    run = run_resolver(
        [
            RESOLVER.ResolverOption.REPOSITORY.value,
            "outcomeeng/plugins",
            RESOLVER.ResolverOption.PULL_REQUEST.value,
            "405",
            RESOLVER.ResolverOption.REVIEW_COMMENT_ID.value,
            "2021",
        ],
        responder,
    )

    discovery, first_second_page, second_second_page, resolution = run.interactions
    assert run.returncode == RESOLVER.ResolverExitCode.SUCCESS
    assert all(
        not token.startswith(f"{RESOLVER.GraphQLField.THREAD_ID.value}=")
        for token in discovery.command
    )
    assert f"{RESOLVER.GraphQLField.THREAD_ID.value}={first_thread_id}" in (
        first_second_page.command
    )
    assert f"{RESOLVER.GraphQLField.THREAD_ID.value}={second_thread_id}" in (
        second_second_page.command
    )
    assert all(
        first_deeper_cursor not in interaction.command
        for interaction in run.interactions
    )
    assert f"{RESOLVER.GraphQLField.ID.value}={second_thread_id}" in resolution.command
