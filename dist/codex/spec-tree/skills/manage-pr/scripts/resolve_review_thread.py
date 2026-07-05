#!/usr/bin/env python3
"""Resolve one GitHub pull-request review thread."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections.abc import Iterator


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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Resolve one GitHub pull-request review thread.",
    )
    parser.add_argument(
        "thread_id",
        nargs="?",
        help="GitHub review thread node ID to resolve",
    )
    parser.add_argument("--repo", help="Repository in owner/name form")
    parser.add_argument("--host", help="GitHub host for gh api --hostname")
    parser.add_argument("--pr", help="Pull request number")
    parser.add_argument(
        "--review-comment-id",
        help="Review comment database ID or node ID from the pull-request comments API",
    )
    return parser.parse_args()


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
    argv = ["gh", "api", "graphql"]
    if host is not None:
        argv.extend(["--hostname", host])
    if silent:
        argv.append("--silent")
    argv.extend(["-f", f"query={query}"])
    for key, value in fields.items():
        argv.extend(["-F", f"{key}={value}"])
    return argv


def run_graphql(
    query: str, fields: dict[str, str | int], host: str | None
) -> dict[str, object]:
    argv = graphql_argv(query, fields, host)
    completed = subprocess.run(
        argv,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        print(completed.stderr, file=sys.stderr, end="")
        raise SystemExit(completed.returncode)
    return json.loads(completed.stdout)


def require_object(value: object, message: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError(message)
    return value


def comment_matches(comment: dict[str, object], comment_id: str) -> bool:
    return (
        str(comment.get("databaseId")) == comment_id or comment.get("id") == comment_id
    )


def find_comment_in_page(comments: dict[str, object], comment_id: str) -> bool:
    nodes = comments.get("nodes")
    if not isinstance(nodes, list):
        raise ValueError("GitHub response comments.nodes must be a list")
    for comment in nodes:
        if isinstance(comment, dict) and comment_matches(comment, comment_id):
            return True
    return False


def thread_has_comment(
    thread_id: str, comments: dict[str, object], comment_id: str, host: str | None
) -> bool:
    if find_comment_in_page(comments, comment_id):
        return True
    page_info = comments["pageInfo"]
    if not isinstance(page_info, dict):
        raise ValueError("GitHub response comments.pageInfo must be an object")
    while page_info.get("hasNextPage"):
        end_cursor = page_info.get("endCursor")
        if not isinstance(end_cursor, str) or not end_cursor:
            raise ValueError("GitHub response comments page is missing endCursor")
        payload = run_graphql(
            THREAD_COMMENTS_QUERY,
            {"threadId": thread_id, "commentsAfter": end_cursor},
            host,
        )
        data = require_object(
            payload.get("data"), "GitHub response data must be an object"
        )
        node = require_object(
            data.get("node"),
            "GitHub response node must be a PullRequestReviewThread object",
        )
        comments = require_object(
            node.get("comments"),
            "GitHub response node.comments must be an object",
        )
        if find_comment_in_page(comments, comment_id):
            return True
        page_info = comments.get("pageInfo")
        if not isinstance(page_info, dict):
            raise ValueError("GitHub response comments.pageInfo must be an object")
    return False


def review_threads_from_payload(payload: dict[str, object]) -> dict[str, object]:
    data = require_object(payload.get("data"), "GitHub response data must be an object")
    repository = require_object(
        data.get("repository"),
        "GitHub response repository must be an object",
    )
    pull_request = require_object(
        repository.get("pullRequest"),
        "GitHub response pullRequest must be an object",
    )
    return require_object(
        pull_request.get("reviewThreads"),
        "GitHub response reviewThreads must be an object",
    )


def iter_thread_comments(
    review_threads: dict[str, object],
) -> Iterator[tuple[str, dict[str, object]]]:
    threads = review_threads["nodes"]
    if not isinstance(threads, list):
        raise ValueError("GitHub response reviewThreads.nodes must be a list")
    for thread in threads:
        if not isinstance(thread, dict):
            continue
        thread_id = validate_thread_id(str(thread.get("id")))
        comments = thread.get("comments")
        if isinstance(comments, dict):
            yield thread_id, comments


def next_threads_cursor(review_threads: dict[str, object]) -> str | None:
    page_info = review_threads.get("pageInfo")
    if not isinstance(page_info, dict):
        raise ValueError("GitHub response reviewThreads.pageInfo must be an object")
    if not page_info.get("hasNextPage"):
        return None
    end_cursor = page_info.get("endCursor")
    if not isinstance(end_cursor, str) or not end_cursor:
        raise ValueError("GitHub response reviewThreads page is missing endCursor")
    return end_cursor


def find_thread_id(
    owner: str,
    repo: str,
    pr_number: int,
    comment_id: str,
    host: str | None,
) -> str:
    fields: dict[str, str | int] = {"owner": owner, "repo": repo, "number": pr_number}
    while True:
        payload = run_graphql(THREADS_QUERY, fields, host)
        review_threads = review_threads_from_payload(payload)
        for thread_id, comments in iter_thread_comments(review_threads):
            if thread_has_comment(thread_id, comments, comment_id, host):
                return thread_id
        end_cursor = next_threads_cursor(review_threads)
        if end_cursor is None:
            raise ValueError(
                "review comment was not found after complete review-thread pagination"
            )
        fields["threadsAfter"] = end_cursor


def main() -> int:
    args = parse_args()
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
            thread_id = find_thread_id(owner, repo, pr_number, comment_id, host)
    except ValueError as exc:
        print(exc, file=sys.stderr)
        return 2
    completed = subprocess.run(
        graphql_argv(QUERY, {"id": thread_id}, host, silent=True),
        check=False,
    )
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
