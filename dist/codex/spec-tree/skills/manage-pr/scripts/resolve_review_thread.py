#!/usr/bin/env python3
"""Resolve one GitHub pull-request review thread."""

from __future__ import annotations

import argparse
import json
import string
import subprocess
import sys
from collections.abc import Iterator
from dataclasses import dataclass
from enum import IntEnum, StrEnum
from typing import Literal, Protocol


QUERY = (
    "mutation($id: ID!) { "
    "resolveReviewThread(input: {threadId: $id}) { "
    "thread { isResolved } "
    "} "
    "}"
)
THREADS_QUERY = (
    "query($owner: String!, $repo: String!, $number: Int!, $threadsAfter: String) { "
    "repository(owner: $owner, name: $repo) { "
    "pullRequest(number: $number) { "
    "reviewThreads(first: 100, after: $threadsAfter) { "
    "pageInfo { hasNextPage endCursor } "
    "nodes { "
    "id "
    "comments(first: 100) { "
    "pageInfo { hasNextPage endCursor } "
    "nodes { id databaseId } "
    "} "
    "} "
    "} "
    "} "
    "} "
    "}"
)
THREAD_COMMENTS_QUERY = (
    "query($threadId: ID!, $commentsAfter: String) { "
    "node(id: $threadId) { "
    "... on PullRequestReviewThread { "
    "comments(first: 100, after: $commentsAfter) { "
    "pageInfo { hasNextPage endCursor } "
    "nodes { id databaseId } "
    "} "
    "} "
    "} "
    "}"
)
GRAPHQL_COMMAND = ("gh", "api", "graphql")
THREAD_ID_ARGUMENT = "thread_id"


class ResolverOption(StrEnum):
    REPOSITORY = "--repo"
    HOST = "--host"
    PULL_REQUEST = "--pr"
    REVIEW_COMMENT_ID = "--review-comment-id"


@dataclass(frozen=True)
class DiscoverySelectorContract:
    option: ResolverOption
    argument_name: str


DISCOVERY_SELECTOR_CONTRACTS = (
    DiscoverySelectorContract(ResolverOption.REPOSITORY, "repo"),
    DiscoverySelectorContract(ResolverOption.PULL_REQUEST, "pr"),
    DiscoverySelectorContract(ResolverOption.REVIEW_COMMENT_ID, "review_comment_id"),
)


class GraphQLOption(StrEnum):
    HOSTNAME = "--hostname"
    SILENT = "--silent"
    STRING_FIELD = "-f"
    TYPED_FIELD = "-F"


class GraphQLField(StrEnum):
    QUERY = "query"
    ID = "id"
    OWNER = "owner"
    REPOSITORY = "repo"
    NUMBER = "number"
    THREADS_AFTER = "threadsAfter"
    THREAD_ID = "threadId"
    COMMENTS_AFTER = "commentsAfter"


class GitHubResponseField(StrEnum):
    DATA = "data"
    REPOSITORY = "repository"
    PULL_REQUEST = "pullRequest"
    REVIEW_THREADS = "reviewThreads"
    NODE = "node"
    COMMENTS = "comments"
    NODES = "nodes"
    PAGE_INFO = "pageInfo"
    HAS_NEXT_PAGE = "hasNextPage"
    END_CURSOR = "endCursor"
    ID = "id"
    DATABASE_ID = "databaseId"


class ResolverErrorMessage(StrEnum):
    THREAD_ID = "thread_id must be a GitHub node ID"
    REPOSITORY = "repo must be in owner/name form"
    POSITIVE_INTEGER = "{name} must be a positive GraphQL Int"
    REVIEW_COMMENT_ID = "review_comment_id must be a database ID or GitHub node ID"
    HOST = "host must be a GitHub hostname"
    MIXED_MODE = "pass either thread_id or --repo/--pr/--review-comment-id"
    INVALID_JSON = "GitHub response must be valid JSON"
    RESPONSE_PAYLOAD = "GitHub response must be an object"
    COMMENT_NOT_FOUND = (
        "review comment was not found after complete review-thread pagination"
    )
    DATA_PAYLOAD = "GitHub response data must be an object"
    COMMENTS_NODES = "GitHub response comments.nodes must be a list"
    COMMENT_NODE = "GitHub response comments.nodes entries must be objects"
    COMMENT_NODE_ID = (
        "GitHub response comments.nodes id must be a review-comment node ID"
    )
    COMMENT_DATABASE_ID = (
        "GitHub response comments.nodes databaseId must be a positive GraphQL Int"
    )
    COMMENTS_PAGE_INFO = "GitHub response comments.pageInfo must be an object"
    COMMENTS_HAS_NEXT_PAGE = (
        "GitHub response comments.pageInfo.hasNextPage must be a boolean"
    )
    COMMENTS_CURSOR = "GitHub response comments page is missing endCursor"
    COMMENTS_CURSOR_PROGRESS = "GitHub response comments page repeated endCursor"
    REPOSITORY_PAYLOAD = "GitHub response repository must be an object"
    PULL_REQUEST_PAYLOAD = "GitHub response pullRequest must be an object"
    REVIEW_THREADS_PAYLOAD = "GitHub response reviewThreads must be an object"
    THREAD_NODES = "GitHub response reviewThreads.nodes must be a list"
    THREAD_NODE = "GitHub response reviewThreads.nodes entries must be objects"
    THREAD_NODE_ID = (
        "GitHub response reviewThreads.nodes id must be a review-thread node ID"
    )
    THREAD_COMMENTS = "GitHub response reviewThreads node comments must be an object"
    THREAD_PAGE_INFO = "GitHub response reviewThreads.pageInfo must be an object"
    THREAD_HAS_NEXT_PAGE = (
        "GitHub response reviewThreads.pageInfo.hasNextPage must be a boolean"
    )
    PAGINATED_THREAD = "GitHub response node must be a PullRequestReviewThread object"
    NODE_COMMENTS = "GitHub response node.comments must be an object"
    THREAD_CURSOR = "GitHub response reviewThreads page is missing endCursor"
    THREAD_CURSOR_PROGRESS = "GitHub response reviewThreads page repeated endCursor"


class ResolverExitCode(IntEnum):
    SUCCESS = 0
    INVALID_INPUT = 2


class _ParsedJsonInteger(str):
    """Preserve JSON integer spelling until its field contract validates it."""


@dataclass(frozen=True)
class TextInputContract:
    allowed_characters: str
    minimum_length: int
    maximum_length: int | None


@dataclass(frozen=True)
class RepositoryInputContract:
    separator: str
    segment_count: int
    segment: TextInputContract


@dataclass(frozen=True)
class DecimalInputContract:
    first_characters: str
    remaining_characters: str
    minimum_length: int
    maximum_length: int | None
    maximum_value: int | None


@dataclass(frozen=True)
class HostnameInputContract:
    separator: str
    maximum_length: int
    label: TextInputContract
    endpoint_characters: str


@dataclass(frozen=True)
class PrefixedTextInputContract:
    prefix: str
    suffix: TextInputContract


@dataclass(frozen=True)
class CommentIdInputContract:
    database_id: DecimalInputContract
    node_id: PrefixedTextInputContract


NODE_ID_SUFFIX_CONTRACT = TextInputContract(
    allowed_characters=string.ascii_letters + string.digits + "_=-",
    minimum_length=3,
    maximum_length=251,
)
GRAPHQL_INT_MAX = 2**31 - 1
THREAD_ID_CONTRACT = PrefixedTextInputContract(
    prefix="PRRT_",
    suffix=NODE_ID_SUFFIX_CONTRACT,
)
REPOSITORY_CONTRACT = RepositoryInputContract(
    separator="/",
    segment_count=2,
    segment=TextInputContract(
        allowed_characters=string.ascii_letters + string.digits + "_.-",
        minimum_length=1,
        maximum_length=None,
    ),
)
NUMBER_CONTRACT = DecimalInputContract(
    first_characters=string.digits[1:],
    remaining_characters=string.digits,
    minimum_length=1,
    maximum_length=len(str(GRAPHQL_INT_MAX)),
    maximum_value=GRAPHQL_INT_MAX,
)
COMMENT_ID_CONTRACT = CommentIdInputContract(
    database_id=NUMBER_CONTRACT,
    node_id=PrefixedTextInputContract(
        prefix="PRRC_",
        suffix=NODE_ID_SUFFIX_CONTRACT,
    ),
)
HOST_CONTRACT = HostnameInputContract(
    separator=".",
    maximum_length=253,
    label=TextInputContract(
        allowed_characters=string.ascii_letters + string.digits + "-",
        minimum_length=1,
        maximum_length=63,
    ),
    endpoint_characters=string.ascii_letters + string.digits,
)


class CommandRunner(Protocol):
    """Run one external command at the resolver orchestration boundary."""

    def __call__(
        self,
        command: list[str],
        *,
        check: bool,
        capture_output: bool = False,
        text: Literal[True] = True,
    ) -> subprocess.CompletedProcess[str]: ...


def default_command_runner(
    command: list[str],
    *,
    check: bool,
    capture_output: bool = False,
    text: Literal[True] = True,
) -> subprocess.CompletedProcess[str]:
    """Run a resolver command through the process boundary."""

    return subprocess.run(
        command,
        check=check,
        capture_output=capture_output,
        text=text,
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Resolve one GitHub pull-request review thread.",
    )
    parser.add_argument(
        THREAD_ID_ARGUMENT,
        nargs="?",
        help="GitHub review thread node ID to resolve",
    )
    parser.add_argument(
        ResolverOption.REPOSITORY.value, help="Repository in owner/name form"
    )
    parser.add_argument(
        ResolverOption.HOST.value, help="GitHub host for gh api --hostname"
    )
    parser.add_argument(ResolverOption.PULL_REQUEST.value, help="Pull request number")
    parser.add_argument(
        ResolverOption.REVIEW_COMMENT_ID.value,
        help="Review comment database ID or node ID from the pull-request comments API",
    )
    return parser.parse_args(argv)


def validate_thread_id(thread_id: str) -> str:
    if not _matches_prefixed_text_contract(thread_id, THREAD_ID_CONTRACT):
        raise ValueError(ResolverErrorMessage.THREAD_ID.value)
    return thread_id


def validate_repository(repository: str | None) -> tuple[str, str]:
    if repository is None:
        raise ValueError(ResolverErrorMessage.REPOSITORY.value)
    segments = repository.split(REPOSITORY_CONTRACT.separator)
    if len(segments) != REPOSITORY_CONTRACT.segment_count or not all(
        _matches_text_contract(segment, REPOSITORY_CONTRACT.segment)
        for segment in segments
    ):
        raise ValueError(ResolverErrorMessage.REPOSITORY.value)
    owner, repo = segments
    return owner, repo


def validate_number(value: str | None, name: str) -> int:
    if value is None or not _matches_decimal_contract(value, NUMBER_CONTRACT):
        raise ValueError(ResolverErrorMessage.POSITIVE_INTEGER.value.format(name=name))
    return int(value)


def validate_comment_id(comment_id: str | None) -> str:
    if comment_id is None or not (
        _matches_decimal_contract(comment_id, COMMENT_ID_CONTRACT.database_id)
        or _matches_prefixed_text_contract(comment_id, COMMENT_ID_CONTRACT.node_id)
    ):
        raise ValueError(ResolverErrorMessage.REVIEW_COMMENT_ID.value)
    return comment_id


def validate_host(host: str | None) -> str | None:
    if host is None:
        return None
    if not _matches_hostname_contract(host, HOST_CONTRACT):
        raise ValueError(ResolverErrorMessage.HOST.value)
    return host


def _matches_text_contract(value: str, contract: TextInputContract) -> bool:
    if len(value) < contract.minimum_length:
        return False
    if contract.maximum_length is not None and len(value) > contract.maximum_length:
        return False
    return all(character in contract.allowed_characters for character in value)


def _matches_decimal_contract(value: str, contract: DecimalInputContract) -> bool:
    if len(value) < contract.minimum_length:
        return False
    if contract.maximum_length is not None and len(value) > contract.maximum_length:
        return False
    if not (
        value[0] in contract.first_characters
        and all(character in contract.remaining_characters for character in value[1:])
    ):
        return False
    if contract.maximum_value is not None:
        maximum_value = str(contract.maximum_value)
        if len(value) > len(maximum_value) or (
            len(value) == len(maximum_value) and value > maximum_value
        ):
            return False
    return True


def _matches_hostname_contract(
    value: str,
    contract: HostnameInputContract,
) -> bool:
    if not value or len(value) > contract.maximum_length:
        return False
    labels = value.split(contract.separator)
    return all(
        _matches_text_contract(label, contract.label)
        and label[0] in contract.endpoint_characters
        and label[-1] in contract.endpoint_characters
        for label in labels
    )


def _matches_prefixed_text_contract(
    value: str,
    contract: PrefixedTextInputContract,
) -> bool:
    return value.startswith(contract.prefix) and _matches_text_contract(
        value[len(contract.prefix) :],
        contract.suffix,
    )


def format_thread_id(suffix: str) -> str:
    """Build one valid review-thread node ID from its source-owned contract."""

    value = f"{THREAD_ID_CONTRACT.prefix}{suffix}"
    return validate_thread_id(value)


def format_review_comment_node_id(suffix: str) -> str:
    """Build one valid review-comment node ID from its source-owned contract."""

    value = f"{COMMENT_ID_CONTRACT.node_id.prefix}{suffix}"
    return validate_comment_id(value)


def graphql_argv(
    query: str,
    fields: dict[str, str | int],
    host: str | None,
    *,
    silent: bool = False,
) -> list[str]:
    argv = list(GRAPHQL_COMMAND)
    if host is not None:
        argv.extend([GraphQLOption.HOSTNAME.value, host])
    if silent:
        argv.append(GraphQLOption.SILENT.value)
    argv.extend(
        [GraphQLOption.STRING_FIELD.value, f"{GraphQLField.QUERY.value}={query}"]
    )
    for key, value in fields.items():
        if isinstance(value, str):
            option = GraphQLOption.STRING_FIELD
        elif isinstance(value, int) and not isinstance(value, bool):
            option = GraphQLOption.TYPED_FIELD
        else:
            raise TypeError(
                f"GraphQL field {key} must be a string or non-boolean integer"
            )
        argv.extend([option.value, f"{key}={value}"])
    return argv


def run_graphql(
    query: str,
    fields: dict[str, str | int],
    host: str | None,
    runner: CommandRunner,
) -> dict[str, object]:
    argv = graphql_argv(query, fields, host)
    completed = runner(
        argv,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        print(completed.stderr, file=sys.stderr, end="")
        raise SystemExit(completed.returncode)
    try:
        payload = json.loads(completed.stdout, parse_int=_ParsedJsonInteger)
    except json.JSONDecodeError as exc:
        raise ValueError(ResolverErrorMessage.INVALID_JSON.value) from exc
    return require_object(payload, ResolverErrorMessage.RESPONSE_PAYLOAD.value)


def require_object(value: object, message: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError(message)
    return value


def comment_matches(comment: dict[str, object], comment_id: str) -> bool:
    node_id = comment.get(GitHubResponseField.ID.value)
    if not isinstance(node_id, str) or not _matches_prefixed_text_contract(
        node_id,
        COMMENT_ID_CONTRACT.node_id,
    ):
        raise ValueError(ResolverErrorMessage.COMMENT_NODE_ID.value)
    database_id = comment.get(GitHubResponseField.DATABASE_ID.value)
    if not isinstance(
        database_id,
        _ParsedJsonInteger,
    ) or not _matches_decimal_contract(database_id, NUMBER_CONTRACT):
        raise ValueError(ResolverErrorMessage.COMMENT_DATABASE_ID.value)
    return database_id == comment_id or node_id == comment_id


def find_comment_in_page(comments: dict[str, object], comment_id: str) -> bool:
    nodes = comments.get(GitHubResponseField.NODES.value)
    if not isinstance(nodes, list):
        raise ValueError(ResolverErrorMessage.COMMENTS_NODES.value)
    matched = False
    for comment in nodes:
        if not isinstance(comment, dict):
            raise ValueError(ResolverErrorMessage.COMMENT_NODE.value)
        if comment_matches(comment, comment_id):
            matched = True
    return matched


def next_comments_cursor(comments: dict[str, object]) -> str | None:
    page_info = comments.get(GitHubResponseField.PAGE_INFO.value)
    if not isinstance(page_info, dict):
        raise ValueError(ResolverErrorMessage.COMMENTS_PAGE_INFO.value)
    has_next_page = page_info.get(GitHubResponseField.HAS_NEXT_PAGE.value)
    if not isinstance(has_next_page, bool):
        raise ValueError(ResolverErrorMessage.COMMENTS_HAS_NEXT_PAGE.value)
    if not has_next_page:
        return None
    end_cursor = page_info.get(GitHubResponseField.END_CURSOR.value)
    if not isinstance(end_cursor, str) or not end_cursor:
        raise ValueError(ResolverErrorMessage.COMMENTS_CURSOR.value)
    return end_cursor


def reject_seen_cursor(
    cursor: str | None,
    seen_cursors: set[str],
    message: ResolverErrorMessage,
) -> None:
    if cursor is not None and cursor in seen_cursors:
        raise ValueError(message.value)


def find_thread_in_later_comment_pages(
    first_page_cursors: list[tuple[str, str | None]],
    comment_id: str,
    host: str | None,
    runner: CommandRunner,
) -> str | None:
    pending_pages = [
        (thread_id, end_cursor, {end_cursor})
        for thread_id, end_cursor in first_page_cursors
        if end_cursor is not None
    ]
    while pending_pages:
        next_pages: list[tuple[str, str, set[str]]] = []
        for thread_id, end_cursor, seen_cursors in pending_pages:
            payload = run_graphql(
                THREAD_COMMENTS_QUERY,
                {
                    GraphQLField.THREAD_ID.value: thread_id,
                    GraphQLField.COMMENTS_AFTER.value: end_cursor,
                },
                host,
                runner,
            )
            data = require_object(
                payload.get(GitHubResponseField.DATA.value),
                ResolverErrorMessage.DATA_PAYLOAD.value,
            )
            node = require_object(
                data.get(GitHubResponseField.NODE.value),
                ResolverErrorMessage.PAGINATED_THREAD.value,
            )
            comments = require_object(
                node.get(GitHubResponseField.COMMENTS.value),
                ResolverErrorMessage.NODE_COMMENTS.value,
            )
            next_cursor = next_comments_cursor(comments)
            reject_seen_cursor(
                next_cursor,
                seen_cursors,
                ResolverErrorMessage.COMMENTS_CURSOR_PROGRESS,
            )
            if find_comment_in_page(comments, comment_id):
                return thread_id
            if next_cursor is not None:
                next_pages.append(
                    (thread_id, next_cursor, seen_cursors | {next_cursor})
                )
        pending_pages = next_pages
    return None


def review_threads_from_payload(payload: dict[str, object]) -> dict[str, object]:
    data = require_object(
        payload.get(GitHubResponseField.DATA.value),
        ResolverErrorMessage.DATA_PAYLOAD.value,
    )
    repository = require_object(
        data.get(GitHubResponseField.REPOSITORY.value),
        ResolverErrorMessage.REPOSITORY_PAYLOAD.value,
    )
    pull_request = require_object(
        repository.get(GitHubResponseField.PULL_REQUEST.value),
        ResolverErrorMessage.PULL_REQUEST_PAYLOAD.value,
    )
    return require_object(
        pull_request.get(GitHubResponseField.REVIEW_THREADS.value),
        ResolverErrorMessage.REVIEW_THREADS_PAYLOAD.value,
    )


def iter_thread_comments(
    review_threads: dict[str, object],
) -> Iterator[tuple[str, dict[str, object]]]:
    threads = review_threads.get(GitHubResponseField.NODES.value)
    if not isinstance(threads, list):
        raise ValueError(ResolverErrorMessage.THREAD_NODES.value)
    for thread in threads:
        if not isinstance(thread, dict):
            raise ValueError(ResolverErrorMessage.THREAD_NODE.value)
        thread_id = thread.get(GitHubResponseField.ID.value)
        if not isinstance(thread_id, str) or not _matches_prefixed_text_contract(
            thread_id,
            THREAD_ID_CONTRACT,
        ):
            raise ValueError(ResolverErrorMessage.THREAD_NODE_ID.value)
        comments = require_object(
            thread.get(GitHubResponseField.COMMENTS.value),
            ResolverErrorMessage.THREAD_COMMENTS.value,
        )
        yield thread_id, comments


def next_threads_cursor(review_threads: dict[str, object]) -> str | None:
    page_info = review_threads.get(GitHubResponseField.PAGE_INFO.value)
    if not isinstance(page_info, dict):
        raise ValueError(ResolverErrorMessage.THREAD_PAGE_INFO.value)
    has_next_page = page_info.get(GitHubResponseField.HAS_NEXT_PAGE.value)
    if not isinstance(has_next_page, bool):
        raise ValueError(ResolverErrorMessage.THREAD_HAS_NEXT_PAGE.value)
    if not has_next_page:
        return None
    end_cursor = page_info.get(GitHubResponseField.END_CURSOR.value)
    if not isinstance(end_cursor, str) or not end_cursor:
        raise ValueError(ResolverErrorMessage.THREAD_CURSOR.value)
    return end_cursor


def find_thread_id(
    owner: str,
    repo: str,
    pr_number: int,
    comment_id: str,
    host: str | None,
    runner: CommandRunner,
) -> str:
    fields: dict[str, str | int] = {
        GraphQLField.OWNER.value: owner,
        GraphQLField.REPOSITORY.value: repo,
        GraphQLField.NUMBER.value: pr_number,
    }
    seen_cursors: set[str] = set()
    first_page_cursors: list[tuple[str, str | None]] = []
    while True:
        payload = run_graphql(THREADS_QUERY, fields, host, runner)
        review_threads = review_threads_from_payload(payload)
        threads_end_cursor = next_threads_cursor(review_threads)
        reject_seen_cursor(
            threads_end_cursor,
            seen_cursors,
            ResolverErrorMessage.THREAD_CURSOR_PROGRESS,
        )
        thread_comments = tuple(iter_thread_comments(review_threads))
        matching_thread_id: str | None = None
        for thread_id, comments in thread_comments:
            first_page_cursors.append((thread_id, next_comments_cursor(comments)))
            if (
                find_comment_in_page(comments, comment_id)
                and matching_thread_id is None
            ):
                matching_thread_id = thread_id
        if matching_thread_id is not None:
            return matching_thread_id
        if threads_end_cursor is None:
            break
        seen_cursors.add(threads_end_cursor)
        fields[GraphQLField.THREADS_AFTER.value] = threads_end_cursor
    matching_thread_id = find_thread_in_later_comment_pages(
        first_page_cursors,
        comment_id,
        host,
        runner,
    )
    if matching_thread_id is not None:
        return matching_thread_id
    raise ValueError(ResolverErrorMessage.COMMENT_NOT_FOUND.value)


def main(
    argv: list[str] | None = None,
    runner: CommandRunner = default_command_runner,
) -> int:
    args = parse_args(argv)
    try:
        host = validate_host(args.host)
        if args.thread_id is not None:
            if any(
                getattr(args, selector.argument_name) is not None
                for selector in DISCOVERY_SELECTOR_CONTRACTS
            ):
                raise ValueError(ResolverErrorMessage.MIXED_MODE.value)
            thread_id = validate_thread_id(args.thread_id)
        else:
            owner, repo = validate_repository(args.repo)
            pr_number = validate_number(args.pr, "pr")
            comment_id = validate_comment_id(args.review_comment_id)
            thread_id = find_thread_id(owner, repo, pr_number, comment_id, host, runner)
    except ValueError as exc:
        print(exc, file=sys.stderr)
        return ResolverExitCode.INVALID_INPUT
    completed = runner(
        graphql_argv(
            QUERY,
            {GraphQLField.ID.value: thread_id},
            host,
            silent=True,
        ),
        check=False,
        text=True,
    )
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
