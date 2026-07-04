#!/usr/bin/env python3
"""Resolve one GitHub pull-request review thread."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys


QUERY = (
    "mutation($id: ID!) { "
    "resolveReviewThread(input: {threadId: $id}) { "
    "thread { isResolved } "
    "} "
    "}"
)
THREADS_QUERY = (
    "query($owner: String!, $repo: String!, $number: Int!) { "
    "repository(owner: $owner, name: $repo) { "
    "pullRequest(number: $number) { "
    "reviewThreads(first: 100) { "
    "nodes { id comments(first: 100) { nodes { id databaseId } } } "
    "} "
    "} "
    "} "
    "}"
)
NODE_ID_PATTERN = re.compile(r"[A-Za-z0-9_=-]{8,256}")
REPOSITORY_PATTERN = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+")
NUMBER_PATTERN = re.compile(r"[1-9][0-9]*")
COMMENT_ID_PATTERN = re.compile(r"[A-Za-z0-9_=-]{1,256}")


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


def find_thread_id(owner: str, repo: str, pr_number: int, comment_id: str) -> str:
    completed = subprocess.run(
        [
            "gh",
            "api",
            "graphql",
            "-f",
            f"query={THREADS_QUERY}",
            "-F",
            f"owner={owner}",
            "-F",
            f"repo={repo}",
            "-F",
            f"number={pr_number}",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        print(completed.stderr, file=sys.stderr, end="")
        raise SystemExit(completed.returncode)
    payload = json.loads(completed.stdout)
    threads = payload["data"]["repository"]["pullRequest"]["reviewThreads"]["nodes"]
    for thread in threads:
        for comment in thread["comments"]["nodes"]:
            if (
                str(comment.get("databaseId")) == comment_id
                or comment.get("id") == comment_id
            ):
                return validate_thread_id(thread["id"])
    raise ValueError("review comment was not found in a pull-request review thread")


def main() -> int:
    args = parse_args()
    try:
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
            thread_id = find_thread_id(owner, repo, pr_number, comment_id)
    except ValueError as exc:
        print(exc, file=sys.stderr)
        return 2
    completed = subprocess.run(
        [
            "gh",
            "api",
            "graphql",
            "--silent",
            "-f",
            f"query={QUERY}",
            "-F",
            f"id={thread_id}",
        ],
        check=False,
    )
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
