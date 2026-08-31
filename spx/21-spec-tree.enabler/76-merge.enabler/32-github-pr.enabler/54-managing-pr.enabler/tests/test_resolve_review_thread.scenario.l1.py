"""Scenario evidence for the manage-pr review-thread resolver."""

from __future__ import annotations

import json
import subprocess

from hypothesis import given

from outcomeeng_testing.generators.review_thread_resolver import (
    ResolverInputs,
    resolver_inputs,
)
from outcomeeng_testing.harnesses.review_thread_resolver import (
    GITHUB_RESPONSE,
    RESOLVER,
    completed,
    resolver_generated_evidence,
    run_resolver,
)


@resolver_generated_evidence
@given(inputs=resolver_inputs())
def test_direct_thread_id_resolves_without_discovery(inputs: ResolverInputs) -> None:
    thread_id = inputs.thread_ids[0]
    run = run_resolver(
        [RESOLVER.ResolverOption.HOST.value, inputs.host, thread_id],
        lambda command, _kwargs: completed(
            command,
            stdout=json.dumps(GITHUB_RESPONSE.resolution_payload()),
        ),
    )

    assert run.returncode == RESOLVER.ResolverExitCode.SUCCESS
    assert len(run.interactions) == 1
    mutation = run.interactions[0]
    assert mutation.command[: len(RESOLVER.GRAPHQL_COMMAND)] == (
        RESOLVER.GRAPHQL_COMMAND
    )
    assert RESOLVER.GraphQLOption.HOSTNAME.value in mutation.command
    assert inputs.host in mutation.command
    assert dict(mutation.keyword_arguments)["capture_output"] is True
    thread_field = f"{RESOLVER.GraphQLField.ID.value}={thread_id}"
    thread_field_index = mutation.command.index(thread_field)
    assert (
        mutation.command[thread_field_index - 1]
        == RESOLVER.GraphQLOption.STRING_FIELD.value
    )


@resolver_generated_evidence
@given(inputs=resolver_inputs())
def test_review_comment_database_id_discovers_thread_before_resolving(
    inputs: ResolverInputs,
) -> None:
    thread_id = inputs.thread_ids[0]
    database_id = inputs.database_ids[0]
    payload = GITHUB_RESPONSE.threads_payload(
        GITHUB_RESPONSE.review_threads(
            nodes=[
                GITHUB_RESPONSE.thread(
                    thread_id=thread_id,
                    comments=GITHUB_RESPONSE.comments(
                        nodes=[
                            GITHUB_RESPONSE.comment(
                                node_id=inputs.comment_node_ids[0],
                                database_id=database_id,
                            )
                        ],
                        has_next_page=False,
                    ),
                )
            ]
        )
    )
    mutation_field = f"{RESOLVER.GraphQLField.QUERY.value}={RESOLVER.QUERY}"

    def responder(
        command: list[str],
        _kwargs: dict[str, object],
    ) -> subprocess.CompletedProcess[str]:
        response = (
            GITHUB_RESPONSE.resolution_payload()
            if mutation_field in command
            else payload
        )
        return completed(command, stdout=json.dumps(response))

    run = run_resolver(inputs.discovery_argv(database_id), responder)

    discovery, resolution = run.interactions
    assert run.returncode == RESOLVER.ResolverExitCode.SUCCESS
    owner_field = f"{RESOLVER.GraphQLField.OWNER.value}={inputs.owner}"
    repository_field = (
        f"{RESOLVER.GraphQLField.REPOSITORY.value}={inputs.repository_name}"
    )
    number_field = f"{RESOLVER.GraphQLField.NUMBER.value}={inputs.pull_request}"
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


@resolver_generated_evidence
@given(inputs=resolver_inputs())
def test_review_comment_node_id_discovers_thread_before_resolving(
    inputs: ResolverInputs,
) -> None:
    payload = GITHUB_RESPONSE.threads_payload(
        GITHUB_RESPONSE.review_threads(
            nodes=[
                GITHUB_RESPONSE.thread(
                    thread_id=inputs.thread_ids[0],
                    comments=GITHUB_RESPONSE.comments(
                        nodes=[
                            GITHUB_RESPONSE.comment(
                                node_id=inputs.comment_node_ids[0],
                                database_id=inputs.database_ids[0],
                            )
                        ],
                        has_next_page=True,
                        end_cursor=inputs.cursors[0],
                    ),
                ),
                GITHUB_RESPONSE.thread(
                    thread_id=inputs.thread_ids[1],
                    comments=GITHUB_RESPONSE.comments(
                        nodes=[
                            GITHUB_RESPONSE.comment(
                                node_id=inputs.comment_node_ids[1],
                                database_id=inputs.database_ids[1],
                            )
                        ],
                        has_next_page=False,
                    ),
                ),
            ]
        )
    )
    mutation_field = f"{RESOLVER.GraphQLField.QUERY.value}={RESOLVER.QUERY}"

    def responder(
        command: list[str],
        _kwargs: dict[str, object],
    ) -> subprocess.CompletedProcess[str]:
        response = (
            GITHUB_RESPONSE.resolution_payload()
            if mutation_field in command
            else payload
        )
        return completed(command, stdout=json.dumps(response))

    run = run_resolver(
        inputs.discovery_argv(inputs.comment_node_ids[1]),
        responder,
    )

    discovery, resolution = run.interactions
    assert run.returncode == RESOLVER.ResolverExitCode.SUCCESS
    assert (
        f"{RESOLVER.GraphQLField.NUMBER.value}={inputs.pull_request}"
        in discovery.command
    )
    assert (
        f"{RESOLVER.GraphQLField.ID.value}={inputs.thread_ids[1]}"
        in resolution.command
    )


@resolver_generated_evidence
@given(inputs=resolver_inputs())
def test_review_thread_discovery_pages_threads_until_comment_is_found(
    inputs: ResolverInputs,
) -> None:
    first_page = GITHUB_RESPONSE.threads_payload(
        GITHUB_RESPONSE.review_threads(
            nodes=[
                GITHUB_RESPONSE.thread(
                    thread_id=inputs.thread_ids[0],
                    comments=GITHUB_RESPONSE.comments(
                        nodes=[
                            GITHUB_RESPONSE.comment(
                                node_id=inputs.comment_node_ids[0],
                                database_id=inputs.database_ids[0],
                            )
                        ],
                        has_next_page=False,
                    ),
                )
            ],
            has_next_page=True,
            end_cursor=inputs.cursors[0],
        )
    )
    second_page = GITHUB_RESPONSE.threads_payload(
        GITHUB_RESPONSE.review_threads(
            nodes=[
                GITHUB_RESPONSE.thread(
                    thread_id=inputs.thread_ids[1],
                    comments=GITHUB_RESPONSE.comments(
                        nodes=[
                            GITHUB_RESPONSE.comment(
                                node_id=inputs.comment_node_ids[1],
                                database_id=inputs.database_ids[1],
                            )
                        ],
                        has_next_page=False,
                    ),
                )
            ]
        )
    )
    mutation_field = f"{RESOLVER.GraphQLField.QUERY.value}={RESOLVER.QUERY}"
    cursor_field = (
        f"{RESOLVER.GraphQLField.THREADS_AFTER.value}={inputs.cursors[0]}"
    )

    def responder(
        command: list[str],
        _kwargs: dict[str, object],
    ) -> subprocess.CompletedProcess[str]:
        if mutation_field in command:
            response = GITHUB_RESPONSE.resolution_payload()
        elif cursor_field in command:
            response = second_page
        else:
            response = first_page
        return completed(command, stdout=json.dumps(response))

    run = run_resolver(inputs.discovery_argv(inputs.database_ids[1]), responder)

    first_query, second_query, resolution = run.interactions
    assert run.returncode == RESOLVER.ResolverExitCode.SUCCESS
    assert cursor_field not in first_query.command
    assert cursor_field in second_query.command
    assert second_query.command[second_query.command.index(cursor_field) - 1] == (
        RESOLVER.GraphQLOption.STRING_FIELD.value
    )
    assert (
        f"{RESOLVER.GraphQLField.ID.value}={inputs.thread_ids[1]}"
        in resolution.command
    )


@resolver_generated_evidence
@given(inputs=resolver_inputs())
def test_review_thread_discovery_checks_all_first_pages_before_later_comments(
    inputs: ResolverInputs,
) -> None:
    first_page = GITHUB_RESPONSE.threads_payload(
        GITHUB_RESPONSE.review_threads(
            nodes=[
                GITHUB_RESPONSE.thread(
                    thread_id=inputs.thread_ids[0],
                    comments=GITHUB_RESPONSE.comments(
                        nodes=[
                            GITHUB_RESPONSE.comment(
                                node_id=inputs.comment_node_ids[0],
                                database_id=inputs.database_ids[0],
                            )
                        ],
                        has_next_page=True,
                        end_cursor=inputs.cursors[0],
                    ),
                )
            ],
            has_next_page=True,
            end_cursor=inputs.cursors[1],
        )
    )
    second_page = GITHUB_RESPONSE.threads_payload(
        GITHUB_RESPONSE.review_threads(
            nodes=[
                GITHUB_RESPONSE.thread(
                    thread_id=inputs.thread_ids[1],
                    comments=GITHUB_RESPONSE.comments(
                        nodes=[
                            GITHUB_RESPONSE.comment(
                                node_id=inputs.comment_node_ids[1],
                                database_id=inputs.database_ids[1],
                            )
                        ],
                        has_next_page=False,
                    ),
                )
            ]
        )
    )
    mutation_field = f"{RESOLVER.GraphQLField.QUERY.value}={RESOLVER.QUERY}"
    thread_cursor_field = (
        f"{RESOLVER.GraphQLField.THREADS_AFTER.value}={inputs.cursors[1]}"
    )

    def responder(
        command: list[str],
        _kwargs: dict[str, object],
    ) -> subprocess.CompletedProcess[str]:
        if mutation_field in command:
            response = GITHUB_RESPONSE.resolution_payload()
        elif thread_cursor_field in command:
            response = second_page
        else:
            response = first_page
        return completed(command, stdout=json.dumps(response))

    run = run_resolver(inputs.discovery_argv(inputs.database_ids[1]), responder)

    first_query, second_query, resolution = run.interactions
    assert run.returncode == RESOLVER.ResolverExitCode.SUCCESS
    assert thread_cursor_field not in first_query.command
    assert thread_cursor_field in second_query.command
    assert all(
        not any(
            token.startswith(f"{RESOLVER.GraphQLField.THREAD_ID.value}=")
            for token in interaction.command
        )
        for interaction in run.interactions
    )
    assert (
        f"{RESOLVER.GraphQLField.ID.value}={inputs.thread_ids[1]}"
        in resolution.command
    )


@resolver_generated_evidence
@given(inputs=resolver_inputs())
def test_review_thread_discovery_pages_comments_until_comment_is_found(
    inputs: ResolverInputs,
) -> None:
    threads_page = GITHUB_RESPONSE.threads_payload(
        GITHUB_RESPONSE.review_threads(
            nodes=[
                GITHUB_RESPONSE.thread(
                    thread_id=inputs.thread_ids[0],
                    comments=GITHUB_RESPONSE.comments(
                        nodes=[
                            GITHUB_RESPONSE.comment(
                                node_id=inputs.comment_node_ids[0],
                                database_id=inputs.database_ids[0],
                            )
                        ],
                        has_next_page=True,
                        end_cursor=inputs.cursors[0],
                    ),
                )
            ]
        )
    )
    comments_page = GITHUB_RESPONSE.thread_comments_payload(
        GITHUB_RESPONSE.comments(
            nodes=[
                GITHUB_RESPONSE.comment(
                    node_id=inputs.comment_node_ids[1],
                    database_id=inputs.database_ids[1],
                )
            ],
            has_next_page=False,
        )
    )
    mutation_field = f"{RESOLVER.GraphQLField.QUERY.value}={RESOLVER.QUERY}"
    thread_field = (
        f"{RESOLVER.GraphQLField.THREAD_ID.value}={inputs.thread_ids[0]}"
    )
    cursor_field = (
        f"{RESOLVER.GraphQLField.COMMENTS_AFTER.value}={inputs.cursors[0]}"
    )

    def responder(
        command: list[str],
        _kwargs: dict[str, object],
    ) -> subprocess.CompletedProcess[str]:
        if mutation_field in command:
            response = GITHUB_RESPONSE.resolution_payload()
        elif thread_field in command:
            response = comments_page
        else:
            response = threads_page
        return completed(command, stdout=json.dumps(response))

    run = run_resolver(inputs.discovery_argv(inputs.database_ids[1]), responder)

    threads_query, comments_query, resolution = run.interactions
    assert run.returncode == RESOLVER.ResolverExitCode.SUCCESS
    assert (
        f"{RESOLVER.GraphQLField.NUMBER.value}={inputs.pull_request}"
        in threads_query.command
    )
    assert thread_field in comments_query.command
    assert cursor_field in comments_query.command
    assert comments_query.command[comments_query.command.index(cursor_field) - 1] == (
        RESOLVER.GraphQLOption.STRING_FIELD.value
    )
    assert (
        f"{RESOLVER.GraphQLField.ID.value}={inputs.thread_ids[0]}"
        in resolution.command
    )


@resolver_generated_evidence
@given(inputs=resolver_inputs())
def test_review_thread_discovery_checks_peer_pages_before_deeper_pages(
    inputs: ResolverInputs,
) -> None:
    first_page = GITHUB_RESPONSE.threads_payload(
        GITHUB_RESPONSE.review_threads(
            nodes=[
                GITHUB_RESPONSE.thread(
                    thread_id=inputs.thread_ids[0],
                    comments=GITHUB_RESPONSE.comments(
                        nodes=[
                            GITHUB_RESPONSE.comment(
                                node_id=inputs.comment_node_ids[0],
                                database_id=inputs.database_ids[0],
                            )
                        ],
                        has_next_page=True,
                        end_cursor=inputs.cursors[0],
                    ),
                ),
                GITHUB_RESPONSE.thread(
                    thread_id=inputs.thread_ids[1],
                    comments=GITHUB_RESPONSE.comments(
                        nodes=[
                            GITHUB_RESPONSE.comment(
                                node_id=inputs.comment_node_ids[1],
                                database_id=inputs.database_ids[1],
                            )
                        ],
                        has_next_page=True,
                        end_cursor=inputs.cursors[1],
                    ),
                ),
            ]
        )
    )
    first_thread_second_page = GITHUB_RESPONSE.thread_comments_payload(
        GITHUB_RESPONSE.comments(
            nodes=[
                GITHUB_RESPONSE.comment(
                    node_id=inputs.comment_node_ids[2],
                    database_id=inputs.database_ids[2],
                )
            ],
            has_next_page=True,
            end_cursor=inputs.cursors[2],
        )
    )
    second_thread_second_page = GITHUB_RESPONSE.thread_comments_payload(
        GITHUB_RESPONSE.comments(
            nodes=[
                GITHUB_RESPONSE.comment(
                    node_id=inputs.comment_node_ids[3],
                    database_id=inputs.database_ids[3],
                )
            ],
            has_next_page=False,
        )
    )
    mutation_field = f"{RESOLVER.GraphQLField.QUERY.value}={RESOLVER.QUERY}"
    first_cursor_field = (
        f"{RESOLVER.GraphQLField.COMMENTS_AFTER.value}={inputs.cursors[0]}"
    )
    second_cursor_field = (
        f"{RESOLVER.GraphQLField.COMMENTS_AFTER.value}={inputs.cursors[1]}"
    )

    def responder(
        command: list[str],
        _kwargs: dict[str, object],
    ) -> subprocess.CompletedProcess[str]:
        if mutation_field in command:
            response = GITHUB_RESPONSE.resolution_payload()
        elif first_cursor_field in command:
            response = first_thread_second_page
        elif second_cursor_field in command:
            response = second_thread_second_page
        else:
            response = first_page
        return completed(command, stdout=json.dumps(response))

    run = run_resolver(inputs.discovery_argv(inputs.database_ids[3]), responder)

    discovery, first_second_page, second_second_page, resolution = run.interactions
    assert run.returncode == RESOLVER.ResolverExitCode.SUCCESS
    assert all(
        not token.startswith(f"{RESOLVER.GraphQLField.THREAD_ID.value}=")
        for token in discovery.command
    )
    assert (
        f"{RESOLVER.GraphQLField.THREAD_ID.value}={inputs.thread_ids[0]}"
        in first_second_page.command
    )
    assert (
        f"{RESOLVER.GraphQLField.THREAD_ID.value}={inputs.thread_ids[1]}"
        in second_second_page.command
    )
    assert all(
        inputs.cursors[2] not in interaction.command
        for interaction in run.interactions
    )
    assert (
        f"{RESOLVER.GraphQLField.ID.value}={inputs.thread_ids[1]}"
        in resolution.command
    )
