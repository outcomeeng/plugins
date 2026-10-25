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
CommandRunner = Callable[..., subprocess.CompletedProcess[str]]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
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
    return parser.parse_args(argv)


def validate_thread_id(thread_id: str) -> str:
    if not NODE_ID_PATTERN.fullmatch(thread_id):
        raise ValueError(
            "positional argument thread_id must be a GitHub node ID matching "
            f"{NODE_ID_PATTERN.pattern}, got {thread_id!r}. Pass the review-thread node ID, for example "
            "PRRT_kwDOABCDEF, from the pull-request review-thread listing."
        )
    return thread_id


def validate_repository(repository: str | None) -> tuple[str, str]:
    if repository is None or not REPOSITORY_PATTERN.fullmatch(repository):
        raise ValueError(
            f"--repo must be in owner/name form matching {REPOSITORY_PATTERN.pattern}, "
            f"got {repository!r}. Pass --repo <owner>/<repo>, for example "
            "outcomeeng/plugins."
        )
    owner, repo = repository.split("/", 1)
    return owner, repo


def validate_number(value: str | None, name: str) -> int:
    if value is None or not NUMBER_PATTERN.fullmatch(value):
        raise ValueError(
            f"--{name} must be a positive integer matching {NUMBER_PATTERN.pattern}, "
            f"got {value!r}. Pass --{name} <number> with the number from the "
            "pull-request URL, for example 405."
        )
    return int(value)


def validate_comment_id(comment_id: str | None) -> str:
    if comment_id is None or not COMMENT_ID_PATTERN.fullmatch(comment_id):
        raise ValueError(
            "--review-comment-id must be a database ID or GitHub node ID matching "
            f"{COMMENT_ID_PATTERN.pattern}, got {comment_id!r}. Pass the id field "
            "of a review comment from "
            "gh api repos/<owner>/<repo>/pulls/<pr-number>/comments, "
            "for example 12345."
        )
    return comment_id


def validate_host(host: str | None) -> str | None:
    if host is None:
        return None
    if not HOST_PATTERN.fullmatch(host):
        raise ValueError(
            f"--host must be a GitHub hostname matching {HOST_PATTERN.pattern}, "
            f"got {host!r}. Pass the bare hostname without scheme or path, for "
            "example ghe.example.com."
        )
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


RETRY_HINT = (
    "Re-run the command; if the error persists, check that the GitHub host "
    "returns the GraphQL schema this script queries."
)


def shape_error(field: str, expected: str, value: object, where: str) -> ValueError:
    return ValueError(
        f"GitHub response {field} must be {expected}, got {value!r} "
        f"while reading {where}. {RETRY_HINT}"
    )


def require_object(value: object, field: str, where: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise shape_error(field, "an object", value, where)
    return value


def comment_matches(comment: dict[str, object], comment_id: str) -> bool:
    return (
        str(comment.get("databaseId")) == comment_id or comment.get("id") == comment_id
    )


def find_comment_in_page(
    comments: dict[str, object], comment_id: str, where: str
) -> bool:
    nodes = comments.get("nodes")
    if not isinstance(nodes, list):
        raise shape_error("comments.nodes", "a list", nodes, where)
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
    where = f"comments of review thread {thread_id}"
    if find_comment_in_page(comments, comment_id, where):
        return True
    page_info = comments.get("pageInfo")
    if not isinstance(page_info, dict):
        raise shape_error("comments.pageInfo", "an object", page_info, where)
    while page_info.get("hasNextPage"):
        end_cursor = page_info.get("endCursor")
        if not isinstance(end_cursor, str) or not end_cursor:
            raise shape_error(
                "comments.pageInfo.endCursor", "a non-empty string", end_cursor, where
            )
        payload = run_graphql(
            THREAD_COMMENTS_QUERY,
            {"threadId": thread_id, "commentsAfter": end_cursor},
            host,
            runner,
        )
        data = require_object(payload.get("data"), "data", where)
        node = require_object(
            data.get("node"), "node (a PullRequestReviewThread)", where
        )
        comments = require_object(node.get("comments"), "node.comments", where)
        if find_comment_in_page(comments, comment_id, where):
            return True
        page_info = comments.get("pageInfo")
        if not isinstance(page_info, dict):
            raise shape_error("comments.pageInfo", "an object", page_info, where)
    return False


def review_threads_from_payload(
    payload: dict[str, object], where: str
) -> dict[str, object]:
    data = require_object(payload.get("data"), "data", where)
    repository = require_object(data.get("repository"), "repository", where)
    pull_request = require_object(repository.get("pullRequest"), "pullRequest", where)
    return require_object(pull_request.get("reviewThreads"), "reviewThreads", where)


def iter_thread_comments(
    review_threads: dict[str, object], where: str
) -> Iterator[tuple[str, dict[str, object]]]:
    threads = review_threads.get("nodes")
    if not isinstance(threads, list):
        raise shape_error("reviewThreads.nodes", "a list", threads, where)
    for thread in threads:
        if not isinstance(thread, dict):
            continue
        response_id = str(thread.get("id"))
        if not NODE_ID_PATTERN.fullmatch(response_id):
            raise ValueError(
                "GitHub response reviewThreads.nodes[].id must be a node ID "
                f"matching {NODE_ID_PATTERN.pattern}, got {response_id!r} "
                f"while reading {where}. {RETRY_HINT}"
            )
        thread_id = response_id
        comments = thread.get("comments")
        if isinstance(comments, dict):
            yield thread_id, comments


def next_threads_cursor(review_threads: dict[str, object], where: str) -> str | None:
    page_info = review_threads.get("pageInfo")
    if not isinstance(page_info, dict):
        raise shape_error("reviewThreads.pageInfo", "an object", page_info, where)
    if not page_info.get("hasNextPage"):
        return None
    end_cursor = page_info.get("endCursor")
    if not isinstance(end_cursor, str) or not end_cursor:
        raise shape_error(
            "reviewThreads.pageInfo.endCursor", "a non-empty string", end_cursor, where
        )
    return end_cursor


def find_thread_id(
    owner: str,
    repo: str,
    pr_number: int,
    comment_id: str,
    host: str | None,
    runner: CommandRunner,
) -> str:
    fields: dict[str, str | int] = {"owner": owner, "repo": repo, "number": pr_number}
    where = f"review threads of {owner}/{repo} pull request {pr_number}"
    while True:
        payload = run_graphql(THREADS_QUERY, fields, host, runner)
        review_threads = review_threads_from_payload(payload, where)
        for thread_id, comments in iter_thread_comments(review_threads, where):
            if thread_has_comment(thread_id, comments, comment_id, host, runner):
                return thread_id
        end_cursor = next_threads_cursor(review_threads, where)
        if end_cursor is None:
            raise ValueError(
                "review comment was not found after complete review-thread pagination: "
                f"searched repo {owner}/{repo}, pull request {pr_number}, "
                f"review comment id {comment_id!r}. Check the id against "
                f"gh api repos/{owner}/{repo}/pulls/{pr_number}/comments, "
                "or pass the thread node ID directly."
            )
        fields["threadsAfter"] = end_cursor


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
                    "pass either thread_id or --repo/--pr/--review-comment-id, "
                    f"got thread_id {args.thread_id!r} together with "
                    f"--repo {args.repo!r}, --pr {args.pr!r}, "
                    f"--review-comment-id {args.review_comment_id!r}. "
                    "Drop the thread_id argument to discover the thread, or drop "
                    "the three discovery options to resolve it directly."
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
        graphql_argv(QUERY, {"id": thread_id}, host, silent=True),
        check=False,
    )
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
