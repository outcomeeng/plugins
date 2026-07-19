#!/usr/bin/env python3
"""Resolve one GitHub pull-request review thread."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections.abc import Callable, Iterator
from typing import cast


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
NODE_ID_PATTERN = re.compile(r"[A-Za-z0-9_=-]{8,256}")
REPOSITORY_PATTERN = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+")
NUMBER_PATTERN = re.compile(r"[1-9]\d*")
COMMENT_ID_PATTERN = re.compile(r"[A-Za-z0-9_=-]{1,256}")
HOST_PATTERN = re.compile(r"[A-Za-z0-9.-]+")
THREAD_ID_ARGUMENT = "thread_id"
REPOSITORY_OPTION = "--repo"
HOST_OPTION = "--host"
PULL_REQUEST_OPTION = "--pr"
REVIEW_COMMENT_ID_OPTION = "--review-comment-id"
GH_COMMAND = "gh"
API_COMMAND = "api"
GRAPHQL_RESOURCE = "graphql"
HOSTNAME_OPTION = "--hostname"
SILENT_OPTION = "--silent"
RAW_FIELD_OPTION = "-f"
TYPED_FIELD_OPTION = "-F"
QUERY_FIELD = "query"
ID_FIELD = "id"
DATABASE_ID_FIELD = "databaseId"
OWNER_FIELD = "owner"
REPO_FIELD = "repo"
NUMBER_FIELD = "number"
THREADS_AFTER_FIELD = "threadsAfter"
THREAD_ID_FIELD = "threadId"
COMMENTS_AFTER_FIELD = "commentsAfter"
DATA_FIELD = "data"
REPOSITORY_FIELD = "repository"
PULL_REQUEST_FIELD = "pullRequest"
REVIEW_THREADS_FIELD = "reviewThreads"
NODE_FIELD = "node"
NODES_FIELD = "nodes"
COMMENTS_FIELD = "comments"
PAGE_INFO_FIELD = "pageInfo"
HAS_NEXT_PAGE_FIELD = "hasNextPage"
END_CURSOR_FIELD = "endCursor"
ERROR_COMMENTS_NODES = "GitHub response comments.nodes must be a list"
ERROR_COMMENTS_PAGE_INFO = "GitHub response comments.pageInfo must be an object"
ERROR_COMMENTS_END_CURSOR = "GitHub response comments page is missing endCursor"
ERROR_DATA = "GitHub response data must be an object"
ERROR_NODE = "GitHub response node must be a PullRequestReviewThread object"
ERROR_NODE_COMMENTS = "GitHub response node.comments must be an object"
ERROR_REPOSITORY = "GitHub response repository must be an object"
ERROR_PULL_REQUEST = "GitHub response pullRequest must be an object"
ERROR_REVIEW_THREADS = "GitHub response reviewThreads must be an object"
ERROR_REVIEW_THREADS_NODES = "GitHub response reviewThreads.nodes must be a list"
ERROR_REVIEW_THREADS_PAGE_INFO = (
    "GitHub response reviewThreads.pageInfo must be an object"
)
ERROR_REVIEW_THREADS_END_CURSOR = (
    "GitHub response reviewThreads page is missing endCursor"
)
ERROR_COMMENT_NOT_FOUND = (
    "review comment was not found after complete review-thread pagination"
)
CommandRunner = Callable[..., subprocess.CompletedProcess[str]]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Resolve one GitHub pull-request review thread.",
    )
    parser.add_argument(
        THREAD_ID_ARGUMENT,
        nargs="?",
        help="GitHub review thread node ID to resolve",
    )
    parser.add_argument(REPOSITORY_OPTION, help="Repository in owner/name form")
    parser.add_argument(HOST_OPTION, help="GitHub host for gh api --hostname")
    parser.add_argument(PULL_REQUEST_OPTION, help="Pull request number")
    parser.add_argument(
        REVIEW_COMMENT_ID_OPTION,
        help="Review comment database ID or node ID from the pull-request comments API",
    )
    return parser.parse_args(argv)


def validate_thread_id(thread_id: str) -> str:
    if not NODE_ID_PATTERN.fullmatch(thread_id):
        raise ValueError("thread_id must be a GitHub node ID")
    return thread_id


def validate_repository(repository: str | None) -> tuple[str, str]:
    if repository is None or not REPOSITORY_PATTERN.fullmatch(repository):
        raise ValueError("repo must be in owner/name form")
    owner, repo = repository.split("/", 1)
    return owner, repo


def validate_number(value: str | None, name: str) -> int:
    if value is None or not NUMBER_PATTERN.fullmatch(value):
        raise ValueError(f"{name} must be a positive integer")
    return int(value)


def validate_comment_id(comment_id: str | None) -> str:
    if comment_id is None or not COMMENT_ID_PATTERN.fullmatch(comment_id):
        raise ValueError("review_comment_id must be a database ID or GitHub node ID")
    return comment_id


def validate_host(host: str | None) -> str | None:
    if host is None:
        return None
    if not HOST_PATTERN.fullmatch(host):
        raise ValueError("host must be a GitHub hostname")
    return host


def graphql_argv(
    query: str,
    fields: dict[str, str | int],
    host: str | None,
    *,
    silent: bool = False,
) -> list[str]:
    argv = [GH_COMMAND, API_COMMAND, GRAPHQL_RESOURCE]
    if host is not None:
        argv.extend([HOSTNAME_OPTION, host])
    if silent:
        argv.append(SILENT_OPTION)
    argv.extend([RAW_FIELD_OPTION, f"{QUERY_FIELD}={query}"])
    for key, value in fields.items():
        argv.extend([TYPED_FIELD_OPTION, f"{key}={value}"])
    return argv


def review_comment_payload(comment_id: str, database_id: int) -> dict[str, object]:
    return {ID_FIELD: comment_id, DATABASE_ID_FIELD: database_id}


def comments_connection_payload(
    nodes: list[dict[str, object]],
    *,
    has_next: bool,
    end_cursor: str | None = None,
) -> dict[str, object]:
    return {
        PAGE_INFO_FIELD: {
            HAS_NEXT_PAGE_FIELD: has_next,
            END_CURSOR_FIELD: end_cursor,
        },
        NODES_FIELD: nodes,
    }


def review_thread_payload(
    thread_id: str,
    comments: dict[str, object],
) -> dict[str, object]:
    return {ID_FIELD: thread_id, COMMENTS_FIELD: comments}


def review_threads_connection_payload(
    nodes: list[dict[str, object]],
    *,
    has_next: bool = False,
    end_cursor: str | None = None,
) -> dict[str, object]:
    return {
        PAGE_INFO_FIELD: {
            HAS_NEXT_PAGE_FIELD: has_next,
            END_CURSOR_FIELD: end_cursor,
        },
        NODES_FIELD: nodes,
    }


def review_threads_response_payload(
    review_threads: object,
) -> dict[str, object]:
    return {
        DATA_FIELD: {
            REPOSITORY_FIELD: {
                PULL_REQUEST_FIELD: {REVIEW_THREADS_FIELD: review_threads},
            }
        }
    }


def repository_response_payload(repository: object) -> dict[str, object]:
    return {DATA_FIELD: {REPOSITORY_FIELD: repository}}


def pull_request_response_payload(pull_request: object) -> dict[str, object]:
    return {
        DATA_FIELD: {
            REPOSITORY_FIELD: {PULL_REQUEST_FIELD: pull_request},
        }
    }


def thread_comments_response_payload(node: object) -> dict[str, object]:
    return {DATA_FIELD: {NODE_FIELD: node}}


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
    return cast("dict[str, object]", json.loads(completed.stdout))


def require_object(value: object, message: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError(message)
    return value


def comment_matches(comment: dict[str, object], comment_id: str) -> bool:
    return (
        str(comment.get(DATABASE_ID_FIELD)) == comment_id
        or comment.get(ID_FIELD) == comment_id
    )


def find_comment_in_page(comments: dict[str, object], comment_id: str) -> bool:
    nodes = comments.get(NODES_FIELD)
    if not isinstance(nodes, list):
        raise ValueError(ERROR_COMMENTS_NODES)
    for comment in nodes:
        if isinstance(comment, dict) and comment_matches(comment, comment_id):
            return True
    return False


def thread_has_comment(
    thread_id: str,
    comments: dict[str, object],
    comment_id: str,
    host: str | None,
    runner: CommandRunner,
) -> bool:
    if find_comment_in_page(comments, comment_id):
        return True
    page_info = comments.get(PAGE_INFO_FIELD)
    if not isinstance(page_info, dict):
        raise ValueError(ERROR_COMMENTS_PAGE_INFO)
    while page_info.get(HAS_NEXT_PAGE_FIELD):
        end_cursor = page_info.get(END_CURSOR_FIELD)
        if not isinstance(end_cursor, str) or not end_cursor:
            raise ValueError(ERROR_COMMENTS_END_CURSOR)
        payload = run_graphql(
            THREAD_COMMENTS_QUERY,
            {THREAD_ID_FIELD: thread_id, COMMENTS_AFTER_FIELD: end_cursor},
            host,
            runner,
        )
        data = require_object(payload.get(DATA_FIELD), ERROR_DATA)
        node = require_object(
            data.get(NODE_FIELD),
            ERROR_NODE,
        )
        comments = require_object(
            node.get(COMMENTS_FIELD),
            ERROR_NODE_COMMENTS,
        )
        if find_comment_in_page(comments, comment_id):
            return True
        page_info = comments.get(PAGE_INFO_FIELD)
        if not isinstance(page_info, dict):
            raise ValueError(ERROR_COMMENTS_PAGE_INFO)
    return False


def review_threads_from_payload(payload: dict[str, object]) -> dict[str, object]:
    data = require_object(payload.get(DATA_FIELD), ERROR_DATA)
    repository = require_object(
        data.get(REPOSITORY_FIELD),
        ERROR_REPOSITORY,
    )
    pull_request = require_object(
        repository.get(PULL_REQUEST_FIELD),
        ERROR_PULL_REQUEST,
    )
    return require_object(
        pull_request.get(REVIEW_THREADS_FIELD),
        ERROR_REVIEW_THREADS,
    )


def iter_thread_comments(
    review_threads: dict[str, object],
) -> Iterator[tuple[str, dict[str, object]]]:
    threads = review_threads.get(NODES_FIELD)
    if not isinstance(threads, list):
        raise ValueError(ERROR_REVIEW_THREADS_NODES)
    for thread in threads:
        if not isinstance(thread, dict):
            continue
        thread_id = validate_thread_id(str(thread.get(ID_FIELD)))
        comments = thread.get(COMMENTS_FIELD)
        if isinstance(comments, dict):
            yield thread_id, comments


def next_threads_cursor(review_threads: dict[str, object]) -> str | None:
    page_info = review_threads.get(PAGE_INFO_FIELD)
    if not isinstance(page_info, dict):
        raise ValueError(ERROR_REVIEW_THREADS_PAGE_INFO)
    if not page_info.get(HAS_NEXT_PAGE_FIELD):
        return None
    end_cursor = page_info.get(END_CURSOR_FIELD)
    if not isinstance(end_cursor, str) or not end_cursor:
        raise ValueError(ERROR_REVIEW_THREADS_END_CURSOR)
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
        OWNER_FIELD: owner,
        REPO_FIELD: repo,
        NUMBER_FIELD: pr_number,
    }
    while True:
        payload = run_graphql(THREADS_QUERY, fields, host, runner)
        review_threads = review_threads_from_payload(payload)
        for thread_id, comments in iter_thread_comments(review_threads):
            if thread_has_comment(thread_id, comments, comment_id, host, runner):
                return thread_id
        end_cursor = next_threads_cursor(review_threads)
        if end_cursor is None:
            raise ValueError(ERROR_COMMENT_NOT_FOUND)
        fields[THREADS_AFTER_FIELD] = end_cursor


def main(
    argv: list[str] | None = None,
    runner: CommandRunner | None = None,
) -> int:
    if runner is None:
        runner = cast("CommandRunner", subprocess.run)
    args = parse_args(argv)
    try:
        host = validate_host(args.host)
        if args.thread_id is not None:
            if (
                args.repo is not None
                or args.pr is not None
                or args.review_comment_id is not None
            ):
                raise ValueError(
                    "pass either thread_id or --repo/--pr/--review-comment-id"
                )
            thread_id = validate_thread_id(args.thread_id)
        else:
            owner, repo = validate_repository(args.repo)
            pr_number = validate_number(args.pr, "pr")
            comment_id = validate_comment_id(args.review_comment_id)
            thread_id = find_thread_id(owner, repo, pr_number, comment_id, host, runner)
    except ValueError as exc:
        print(exc, file=sys.stderr)
        return 2
    completed = runner(
        graphql_argv(QUERY, {ID_FIELD: thread_id}, host, silent=True),
        check=False,
    )
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
