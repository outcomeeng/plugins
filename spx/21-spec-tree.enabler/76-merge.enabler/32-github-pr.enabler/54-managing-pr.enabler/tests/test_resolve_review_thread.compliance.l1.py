"""Compliance evidence for malformed review-thread resolver payloads."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import cast

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
    run_resolver_with_response,
)


@resolver_generated_evidence
@given(inputs=resolver_inputs())
def test_review_comment_not_found_after_complete_pagination_returns_error(
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
                        has_next_page=False,
                    ),
                )
            ]
        )
    )
    run = run_resolver_with_response(
        inputs.discovery_argv(inputs.database_ids[1]),
        json.dumps(payload),
    )

    assert run.returncode == RESOLVER.ResolverExitCode.INVALID_INPUT
    assert RESOLVER.ResolverErrorMessage.COMMENT_NOT_FOUND.value in run.stderr


@resolver_generated_evidence
@given(inputs=resolver_inputs())
def test_invalid_json_payload_returns_error(inputs: ResolverInputs) -> None:
    run = run_resolver_with_response(
        inputs.discovery_argv(inputs.database_ids[0]),
        Path(
            "outcomeeng_testing/fixtures/review_thread_resolver/invalid.txt"
        ).read_text(encoding="utf-8"),
    )

    assert run.returncode == RESOLVER.ResolverExitCode.INVALID_INPUT
    assert RESOLVER.ResolverErrorMessage.INVALID_JSON.value in run.stderr


@resolver_generated_evidence
@given(inputs=resolver_inputs())
def test_non_object_json_payload_returns_error(inputs: ResolverInputs) -> None:
    run = run_resolver_with_response(
        inputs.discovery_argv(inputs.database_ids[0]),
        Path(
            "outcomeeng_testing/fixtures/review_thread_resolver/non_object.json"
        ).read_text(encoding="utf-8"),
    )

    assert run.returncode == RESOLVER.ResolverExitCode.INVALID_INPUT
    assert RESOLVER.ResolverErrorMessage.RESPONSE_PAYLOAD.value in run.stderr


@resolver_generated_evidence
@given(inputs=resolver_inputs())
def test_non_object_data_payload_returns_error(inputs: ResolverInputs) -> None:
    run = run_resolver_with_response(
        inputs.discovery_argv(inputs.database_ids[0]),
        json.dumps({RESOLVER.GitHubResponseField.DATA.value: None}),
    )

    assert run.returncode == RESOLVER.ResolverExitCode.INVALID_INPUT
    assert RESOLVER.ResolverErrorMessage.DATA_PAYLOAD.value in run.stderr


@resolver_generated_evidence
@given(inputs=resolver_inputs())
def test_null_repository_payload_returns_error(inputs: ResolverInputs) -> None:
    run = run_resolver_with_response(
        inputs.discovery_argv(inputs.database_ids[0]),
        json.dumps(GITHUB_RESPONSE.null_repository_payload()),
    )

    assert run.returncode == RESOLVER.ResolverExitCode.INVALID_INPUT
    assert RESOLVER.ResolverErrorMessage.REPOSITORY_PAYLOAD.value in run.stderr


@resolver_generated_evidence
@given(inputs=resolver_inputs())
def test_null_pull_request_payload_returns_error(inputs: ResolverInputs) -> None:
    run = run_resolver_with_response(
        inputs.discovery_argv(inputs.database_ids[0]),
        json.dumps(GITHUB_RESPONSE.null_pull_request_payload()),
    )

    assert run.returncode == RESOLVER.ResolverExitCode.INVALID_INPUT
    assert RESOLVER.ResolverErrorMessage.PULL_REQUEST_PAYLOAD.value in run.stderr


@resolver_generated_evidence
@given(inputs=resolver_inputs())
def test_non_object_review_threads_payload_returns_error(
    inputs: ResolverInputs,
) -> None:
    run = run_resolver_with_response(
        inputs.discovery_argv(inputs.database_ids[0]),
        json.dumps(GITHUB_RESPONSE.threads_payload(None)),
    )

    assert run.returncode == RESOLVER.ResolverExitCode.INVALID_INPUT
    assert RESOLVER.ResolverErrorMessage.REVIEW_THREADS_PAYLOAD.value in run.stderr


@resolver_generated_evidence
@given(inputs=resolver_inputs())
def test_missing_review_thread_nodes_returns_error(inputs: ResolverInputs) -> None:
    payload = GITHUB_RESPONSE.threads_payload(
        GITHUB_RESPONSE.review_threads(nodes=None)
    )
    run = run_resolver_with_response(
        inputs.discovery_argv(inputs.database_ids[0]),
        json.dumps(payload),
    )

    assert run.returncode == RESOLVER.ResolverExitCode.INVALID_INPUT
    assert RESOLVER.ResolverErrorMessage.THREAD_NODES.value in run.stderr


@resolver_generated_evidence
@given(inputs=resolver_inputs())
def test_non_object_review_thread_node_returns_error(inputs: ResolverInputs) -> None:
    payload = GITHUB_RESPONSE.threads_payload(
        GITHUB_RESPONSE.review_threads(nodes=[None])
    )
    run = run_resolver_with_response(
        inputs.discovery_argv(inputs.database_ids[0]),
        json.dumps(payload),
    )

    assert run.returncode == RESOLVER.ResolverExitCode.INVALID_INPUT
    assert RESOLVER.ResolverErrorMessage.THREAD_NODE.value in run.stderr


@resolver_generated_evidence
@given(inputs=resolver_inputs())
def test_malformed_review_thread_node_id_returns_error(
    inputs: ResolverInputs,
) -> None:
    payload = GITHUB_RESPONSE.threads_payload(
        GITHUB_RESPONSE.review_threads(
            nodes=[
                GITHUB_RESPONSE.thread(
                    thread_id=inputs.comment_node_ids[0],
                    comments=GITHUB_RESPONSE.comments(
                        nodes=[],
                        has_next_page=False,
                    ),
                )
            ]
        )
    )
    run = run_resolver_with_response(
        inputs.discovery_argv(inputs.database_ids[0]),
        json.dumps(payload),
    )

    assert run.returncode == RESOLVER.ResolverExitCode.INVALID_INPUT
    assert RESOLVER.ResolverErrorMessage.THREAD_NODE_ID.value in run.stderr


@resolver_generated_evidence
@given(inputs=resolver_inputs())
def test_non_object_thread_comments_returns_error(inputs: ResolverInputs) -> None:
    payload = GITHUB_RESPONSE.threads_payload(
        GITHUB_RESPONSE.review_threads(
            nodes=[
                GITHUB_RESPONSE.thread(
                    thread_id=inputs.thread_ids[0],
                    comments=None,
                )
            ]
        )
    )
    run = run_resolver_with_response(
        inputs.discovery_argv(inputs.database_ids[0]),
        json.dumps(payload),
    )

    assert run.returncode == RESOLVER.ResolverExitCode.INVALID_INPUT
    assert RESOLVER.ResolverErrorMessage.THREAD_COMMENTS.value in run.stderr


@resolver_generated_evidence
@given(inputs=resolver_inputs())
def test_non_object_comment_node_returns_error(inputs: ResolverInputs) -> None:
    payload = GITHUB_RESPONSE.threads_payload(
        GITHUB_RESPONSE.review_threads(
            nodes=[
                GITHUB_RESPONSE.thread(
                    thread_id=inputs.thread_ids[0],
                    comments=GITHUB_RESPONSE.comments(
                        nodes=[None],
                        has_next_page=False,
                    ),
                )
            ]
        )
    )
    run = run_resolver_with_response(
        inputs.discovery_argv(inputs.database_ids[0]),
        json.dumps(payload),
    )

    assert run.returncode == RESOLVER.ResolverExitCode.INVALID_INPUT
    assert RESOLVER.ResolverErrorMessage.COMMENT_NODE.value in run.stderr


@resolver_generated_evidence
@given(inputs=resolver_inputs())
def test_matching_comment_does_not_hide_later_malformed_node_id(
    inputs: ResolverInputs,
) -> None:
    fields = RESOLVER.GitHubResponseField
    comments = GITHUB_RESPONSE.comments(
        nodes=[
            GITHUB_RESPONSE.comment(
                node_id=inputs.comment_node_ids[0],
                database_id=inputs.database_ids[0],
            ),
            {fields.DATABASE_ID.value: inputs.database_ids[1]},
        ],
        has_next_page=False,
    )
    payload = GITHUB_RESPONSE.threads_payload(
        GITHUB_RESPONSE.review_threads(
            nodes=[
                GITHUB_RESPONSE.thread(
                    thread_id=inputs.thread_ids[0],
                    comments=comments,
                )
            ]
        )
    )
    run = run_resolver_with_response(
        inputs.discovery_argv(inputs.database_ids[0]),
        json.dumps(payload),
    )

    assert run.returncode == RESOLVER.ResolverExitCode.INVALID_INPUT
    assert RESOLVER.ResolverErrorMessage.COMMENT_NODE_ID.value in run.stderr


@resolver_generated_evidence
@given(inputs=resolver_inputs())
def test_non_positive_comment_database_id_returns_error(
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
                                database_id=0,
                            )
                        ],
                        has_next_page=False,
                    ),
                )
            ]
        )
    )
    run = run_resolver_with_response(
        inputs.discovery_argv(inputs.database_ids[0]),
        json.dumps(payload),
    )

    assert run.returncode == RESOLVER.ResolverExitCode.INVALID_INPUT
    assert RESOLVER.ResolverErrorMessage.COMMENT_DATABASE_ID.value in run.stderr


@resolver_generated_evidence
@given(inputs=resolver_inputs())
def test_boolean_comment_database_id_returns_error(inputs: ResolverInputs) -> None:
    payload = GITHUB_RESPONSE.threads_payload(
        GITHUB_RESPONSE.review_threads(
            nodes=[
                GITHUB_RESPONSE.thread(
                    thread_id=inputs.thread_ids[0],
                    comments=GITHUB_RESPONSE.comments(
                        nodes=[
                            GITHUB_RESPONSE.comment(
                                node_id=inputs.comment_node_ids[0],
                                database_id=True,
                            )
                        ],
                        has_next_page=False,
                    ),
                )
            ]
        )
    )
    run = run_resolver_with_response(
        inputs.discovery_argv(inputs.database_ids[0]),
        json.dumps(payload),
    )

    assert run.returncode == RESOLVER.ResolverExitCode.INVALID_INPUT
    assert RESOLVER.ResolverErrorMessage.COMMENT_DATABASE_ID.value in run.stderr


@resolver_generated_evidence
@given(inputs=resolver_inputs())
def test_missing_comment_database_id_returns_error(inputs: ResolverInputs) -> None:
    fields = RESOLVER.GitHubResponseField
    payload = GITHUB_RESPONSE.threads_payload(
        GITHUB_RESPONSE.review_threads(
            nodes=[
                GITHUB_RESPONSE.thread(
                    thread_id=inputs.thread_ids[0],
                    comments=GITHUB_RESPONSE.comments(
                        nodes=[{fields.ID.value: inputs.comment_node_ids[0]}],
                        has_next_page=False,
                    ),
                )
            ]
        )
    )
    run = run_resolver_with_response(
        inputs.discovery_argv(inputs.database_ids[0]),
        json.dumps(payload),
    )

    assert run.returncode == RESOLVER.ResolverExitCode.INVALID_INPUT
    assert RESOLVER.ResolverErrorMessage.COMMENT_DATABASE_ID.value in run.stderr


@resolver_generated_evidence
@given(inputs=resolver_inputs())
def test_string_comment_database_id_returns_error(inputs: ResolverInputs) -> None:
    fields = RESOLVER.GitHubResponseField
    payload = GITHUB_RESPONSE.threads_payload(
        GITHUB_RESPONSE.review_threads(
            nodes=[
                GITHUB_RESPONSE.thread(
                    thread_id=inputs.thread_ids[0],
                    comments=GITHUB_RESPONSE.comments(
                        nodes=[
                            {
                                fields.ID.value: inputs.comment_node_ids[0],
                                fields.DATABASE_ID.value: str(inputs.database_ids[0]),
                            }
                        ],
                        has_next_page=False,
                    ),
                )
            ]
        )
    )
    run = run_resolver_with_response(
        inputs.discovery_argv(inputs.database_ids[1]),
        json.dumps(payload),
    )

    assert run.returncode == RESOLVER.ResolverExitCode.INVALID_INPUT
    assert RESOLVER.ResolverErrorMessage.COMMENT_DATABASE_ID.value in run.stderr


@resolver_generated_evidence
@given(inputs=resolver_inputs())
def test_non_list_comment_nodes_returns_error(inputs: ResolverInputs) -> None:
    fields = RESOLVER.GitHubResponseField
    comments = GITHUB_RESPONSE.comments(nodes=[], has_next_page=False)
    comments[fields.NODES.value] = None
    payload = GITHUB_RESPONSE.threads_payload(
        GITHUB_RESPONSE.review_threads(
            nodes=[
                GITHUB_RESPONSE.thread(
                    thread_id=inputs.thread_ids[0],
                    comments=comments,
                )
            ]
        )
    )
    run = run_resolver_with_response(
        inputs.discovery_argv(inputs.database_ids[0]),
        json.dumps(payload),
    )

    assert run.returncode == RESOLVER.ResolverExitCode.INVALID_INPUT
    assert RESOLVER.ResolverErrorMessage.COMMENTS_NODES.value in run.stderr


@resolver_generated_evidence
@given(inputs=resolver_inputs())
def test_missing_comment_page_info_returns_error(inputs: ResolverInputs) -> None:
    payload = GITHUB_RESPONSE.threads_payload(
        GITHUB_RESPONSE.review_threads(
            nodes=[
                GITHUB_RESPONSE.thread(
                    thread_id=inputs.thread_ids[0],
                    comments=GITHUB_RESPONSE.comments(
                        nodes=[],
                        has_next_page=False,
                        include_page_info=False,
                    ),
                )
            ]
        )
    )
    run = run_resolver_with_response(
        inputs.discovery_argv(inputs.database_ids[0]),
        json.dumps(payload),
    )

    assert run.returncode == RESOLVER.ResolverExitCode.INVALID_INPUT
    assert RESOLVER.ResolverErrorMessage.COMMENTS_PAGE_INFO.value in run.stderr


@resolver_generated_evidence
@given(inputs=resolver_inputs())
def test_non_boolean_comment_has_next_page_returns_error(
    inputs: ResolverInputs,
) -> None:
    fields = RESOLVER.GitHubResponseField
    comments = GITHUB_RESPONSE.comments(nodes=[], has_next_page=False)
    page_info = cast(dict[str, object], comments[fields.PAGE_INFO.value])
    page_info[fields.HAS_NEXT_PAGE.value] = "false"
    payload = GITHUB_RESPONSE.threads_payload(
        GITHUB_RESPONSE.review_threads(
            nodes=[
                GITHUB_RESPONSE.thread(
                    thread_id=inputs.thread_ids[0],
                    comments=comments,
                )
            ]
        )
    )
    run = run_resolver_with_response(
        inputs.discovery_argv(inputs.database_ids[0]),
        json.dumps(payload),
    )

    assert run.returncode == RESOLVER.ResolverExitCode.INVALID_INPUT
    assert RESOLVER.ResolverErrorMessage.COMMENTS_HAS_NEXT_PAGE.value in run.stderr


@resolver_generated_evidence
@given(inputs=resolver_inputs())
def test_missing_comment_page_cursor_returns_error(inputs: ResolverInputs) -> None:
    payload = GITHUB_RESPONSE.threads_payload(
        GITHUB_RESPONSE.review_threads(
            nodes=[
                GITHUB_RESPONSE.thread(
                    thread_id=inputs.thread_ids[0],
                    comments=GITHUB_RESPONSE.comments(
                        nodes=[],
                        has_next_page=True,
                        end_cursor=None,
                    ),
                )
            ]
        )
    )
    run = run_resolver_with_response(
        inputs.discovery_argv(inputs.database_ids[0]),
        json.dumps(payload),
    )

    assert run.returncode == RESOLVER.ResolverExitCode.INVALID_INPUT
    assert RESOLVER.ResolverErrorMessage.COMMENTS_CURSOR.value in run.stderr


@resolver_generated_evidence
@given(inputs=resolver_inputs())
def test_null_paginated_thread_node_returns_error(inputs: ResolverInputs) -> None:
    threads_page = GITHUB_RESPONSE.threads_payload(
        GITHUB_RESPONSE.review_threads(
            nodes=[
                GITHUB_RESPONSE.thread(
                    thread_id=inputs.thread_ids[0],
                    comments=GITHUB_RESPONSE.comments(
                        nodes=[],
                        has_next_page=True,
                        end_cursor=inputs.cursors[0],
                    ),
                )
            ]
        )
    )

    def responder(
        command: list[str],
        _kwargs: dict[str, object],
    ) -> subprocess.CompletedProcess[str]:
        response = (
            GITHUB_RESPONSE.null_thread_payload()
            if f"{RESOLVER.GraphQLField.THREAD_ID.value}={inputs.thread_ids[0]}"
            in command
            else threads_page
        )
        return completed(command, stdout=json.dumps(response))

    run = run_resolver(inputs.discovery_argv(inputs.database_ids[0]), responder)

    assert run.returncode == RESOLVER.ResolverExitCode.INVALID_INPUT
    assert RESOLVER.ResolverErrorMessage.PAGINATED_THREAD.value in run.stderr


@resolver_generated_evidence
@given(inputs=resolver_inputs())
def test_non_object_paginated_node_comments_returns_error(
    inputs: ResolverInputs,
) -> None:
    threads_page = GITHUB_RESPONSE.threads_payload(
        GITHUB_RESPONSE.review_threads(
            nodes=[
                GITHUB_RESPONSE.thread(
                    thread_id=inputs.thread_ids[0],
                    comments=GITHUB_RESPONSE.comments(
                        nodes=[],
                        has_next_page=True,
                        end_cursor=inputs.cursors[0],
                    ),
                )
            ]
        )
    )

    def responder(
        command: list[str],
        _kwargs: dict[str, object],
    ) -> subprocess.CompletedProcess[str]:
        response = (
            GITHUB_RESPONSE.thread_comments_payload(None)
            if f"{RESOLVER.GraphQLField.THREAD_ID.value}={inputs.thread_ids[0]}"
            in command
            else threads_page
        )
        return completed(command, stdout=json.dumps(response))

    run = run_resolver(inputs.discovery_argv(inputs.database_ids[0]), responder)

    assert run.returncode == RESOLVER.ResolverExitCode.INVALID_INPUT
    assert RESOLVER.ResolverErrorMessage.NODE_COMMENTS.value in run.stderr


@resolver_generated_evidence
@given(inputs=resolver_inputs())
def test_missing_thread_page_cursor_returns_error(inputs: ResolverInputs) -> None:
    payload = GITHUB_RESPONSE.threads_payload(
        GITHUB_RESPONSE.review_threads(
            nodes=[],
            has_next_page=True,
            end_cursor=None,
        )
    )
    run = run_resolver_with_response(
        inputs.discovery_argv(inputs.database_ids[0]),
        json.dumps(payload),
    )

    assert run.returncode == RESOLVER.ResolverExitCode.INVALID_INPUT
    assert RESOLVER.ResolverErrorMessage.THREAD_CURSOR.value in run.stderr


@resolver_generated_evidence
@given(inputs=resolver_inputs())
def test_non_object_thread_page_info_returns_error(inputs: ResolverInputs) -> None:
    fields = RESOLVER.GitHubResponseField
    review_threads = GITHUB_RESPONSE.review_threads(nodes=[])
    review_threads[fields.PAGE_INFO.value] = None
    run = run_resolver_with_response(
        inputs.discovery_argv(inputs.database_ids[0]),
        json.dumps(GITHUB_RESPONSE.threads_payload(review_threads)),
    )

    assert run.returncode == RESOLVER.ResolverExitCode.INVALID_INPUT
    assert RESOLVER.ResolverErrorMessage.THREAD_PAGE_INFO.value in run.stderr


@resolver_generated_evidence
@given(inputs=resolver_inputs())
def test_non_boolean_thread_has_next_page_returns_error(
    inputs: ResolverInputs,
) -> None:
    fields = RESOLVER.GitHubResponseField
    review_threads = GITHUB_RESPONSE.review_threads(nodes=[])
    page_info = cast(dict[str, object], review_threads[fields.PAGE_INFO.value])
    page_info[fields.HAS_NEXT_PAGE.value] = "false"
    run = run_resolver_with_response(
        inputs.discovery_argv(inputs.database_ids[0]),
        json.dumps(GITHUB_RESPONSE.threads_payload(review_threads)),
    )

    assert run.returncode == RESOLVER.ResolverExitCode.INVALID_INPUT
    assert RESOLVER.ResolverErrorMessage.THREAD_HAS_NEXT_PAGE.value in run.stderr


@resolver_generated_evidence
@given(inputs=resolver_inputs())
def test_comment_database_id_above_graphql_int_range_returns_error(
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
                                database_id=RESOLVER.GRAPHQL_INT_MAX + 1,
                            )
                        ],
                        has_next_page=False,
                    ),
                )
            ]
        )
    )
    run = run_resolver_with_response(
        inputs.discovery_argv(inputs.database_ids[0]),
        json.dumps(payload),
    )

    assert run.returncode == RESOLVER.ResolverExitCode.INVALID_INPUT
    assert RESOLVER.ResolverErrorMessage.COMMENT_DATABASE_ID.value in run.stderr


@resolver_generated_evidence
@given(inputs=resolver_inputs())
def test_overlong_json_integer_reaches_bounded_database_id_validation(
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
                        has_next_page=False,
                    ),
                )
            ]
        )
    )
    serialized_payload = json.dumps(payload)
    field = f'"databaseId": {inputs.database_ids[0]}'
    maximum_length = RESOLVER.NUMBER_CONTRACT.maximum_length
    assert maximum_length is not None
    overlong_integer = (
        RESOLVER.NUMBER_CONTRACT.first_characters[0] * (maximum_length + 1)
    )
    serialized_payload = serialized_payload.replace(
        field,
        f'"databaseId": {overlong_integer}',
        1,
    )
    run = run_resolver_with_response(
        inputs.discovery_argv(inputs.database_ids[1]),
        serialized_payload,
    )

    assert run.returncode == RESOLVER.ResolverExitCode.INVALID_INPUT
    assert RESOLVER.ResolverErrorMessage.COMMENT_DATABASE_ID.value in run.stderr


@resolver_generated_evidence
@given(inputs=resolver_inputs())
def test_repeated_comment_page_cursor_returns_error(inputs: ResolverInputs) -> None:
    initial_comments = GITHUB_RESPONSE.comments(
        nodes=[],
        has_next_page=True,
        end_cursor=inputs.cursors[0],
    )
    middle_comments = GITHUB_RESPONSE.comments(
        nodes=[],
        has_next_page=True,
        end_cursor=inputs.cursors[1],
    )
    repeated_comments = GITHUB_RESPONSE.comments(
        nodes=[],
        has_next_page=True,
        end_cursor=inputs.cursors[0],
    )
    threads_page = GITHUB_RESPONSE.threads_payload(
        GITHUB_RESPONSE.review_threads(
            nodes=[
                GITHUB_RESPONSE.thread(
                    thread_id=inputs.thread_ids[0],
                    comments=initial_comments,
                )
            ]
        )
    )
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
        if first_cursor_field in command:
            response = GITHUB_RESPONSE.thread_comments_payload(middle_comments)
        elif second_cursor_field in command:
            response = GITHUB_RESPONSE.thread_comments_payload(repeated_comments)
        else:
            response = threads_page
        return completed(command, stdout=json.dumps(response))

    run = run_resolver(inputs.discovery_argv(inputs.database_ids[0]), responder)

    assert run.returncode == RESOLVER.ResolverExitCode.INVALID_INPUT
    assert RESOLVER.ResolverErrorMessage.COMMENTS_CURSOR_PROGRESS.value in run.stderr


@resolver_generated_evidence
@given(inputs=resolver_inputs())
def test_repeated_thread_page_cursor_returns_error(inputs: ResolverInputs) -> None:
    initial_page = GITHUB_RESPONSE.threads_payload(
        GITHUB_RESPONSE.review_threads(
            nodes=[],
            has_next_page=True,
            end_cursor=inputs.cursors[0],
        )
    )
    middle_page = GITHUB_RESPONSE.threads_payload(
        GITHUB_RESPONSE.review_threads(
            nodes=[],
            has_next_page=True,
            end_cursor=inputs.cursors[1],
        )
    )
    repeated_page = GITHUB_RESPONSE.threads_payload(
        GITHUB_RESPONSE.review_threads(
            nodes=[],
            has_next_page=True,
            end_cursor=inputs.cursors[0],
        )
    )
    first_cursor_field = (
        f"{RESOLVER.GraphQLField.THREADS_AFTER.value}={inputs.cursors[0]}"
    )
    second_cursor_field = (
        f"{RESOLVER.GraphQLField.THREADS_AFTER.value}={inputs.cursors[1]}"
    )

    def responder(
        command: list[str],
        _kwargs: dict[str, object],
    ) -> subprocess.CompletedProcess[str]:
        if first_cursor_field in command:
            response = middle_page
        elif second_cursor_field in command:
            response = repeated_page
        else:
            response = initial_page
        return completed(command, stdout=json.dumps(response))

    run = run_resolver(inputs.discovery_argv(inputs.database_ids[0]), responder)

    assert run.returncode == RESOLVER.ResolverExitCode.INVALID_INPUT
    assert RESOLVER.ResolverErrorMessage.THREAD_CURSOR_PROGRESS.value in run.stderr


@resolver_generated_evidence
@given(inputs=resolver_inputs())
def test_null_mutation_result_returns_error(inputs: ResolverInputs) -> None:
    run = run_resolver_with_response(
        [inputs.thread_ids[0]],
        json.dumps(GITHUB_RESPONSE.mutation_payload(None)),
    )

    assert run.returncode == RESOLVER.ResolverExitCode.INVALID_INPUT
    assert (
        RESOLVER.ResolverErrorMessage.RESOLVE_REVIEW_THREAD_PAYLOAD.value
        in run.stderr
    )


@resolver_generated_evidence
@given(inputs=resolver_inputs())
def test_null_resolved_thread_returns_error(inputs: ResolverInputs) -> None:
    fields = RESOLVER.GitHubResponseField
    run = run_resolver_with_response(
        [inputs.thread_ids[0]],
        json.dumps(
            GITHUB_RESPONSE.mutation_payload({fields.THREAD.value: None})
        ),
    )

    assert run.returncode == RESOLVER.ResolverExitCode.INVALID_INPUT
    assert RESOLVER.ResolverErrorMessage.RESOLVED_THREAD_PAYLOAD.value in run.stderr


@resolver_generated_evidence
@given(inputs=resolver_inputs())
def test_unresolved_mutation_result_returns_error(inputs: ResolverInputs) -> None:
    run = run_resolver_with_response(
        [inputs.thread_ids[0]],
        json.dumps(GITHUB_RESPONSE.resolution_payload(is_resolved=False)),
    )

    assert run.returncode == RESOLVER.ResolverExitCode.INVALID_INPUT
    assert RESOLVER.ResolverErrorMessage.RESOLVED_THREAD_STATE.value in run.stderr


@resolver_generated_evidence
@given(inputs=resolver_inputs())
def test_missing_mutation_resolution_state_returns_error(
    inputs: ResolverInputs,
) -> None:
    fields = RESOLVER.GitHubResponseField
    run = run_resolver_with_response(
        [inputs.thread_ids[0]],
        json.dumps(
            GITHUB_RESPONSE.mutation_payload({fields.THREAD.value: {}})
        ),
    )

    assert run.returncode == RESOLVER.ResolverExitCode.INVALID_INPUT
    assert RESOLVER.ResolverErrorMessage.RESOLVED_THREAD_STATE.value in run.stderr
