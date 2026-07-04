#!/usr/bin/env python3
"""Resolve one GitHub pull-request review thread."""

from __future__ import annotations

import argparse
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
NODE_ID_PATTERN = re.compile(r"[A-Za-z0-9_=-]{8,256}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Resolve one GitHub pull-request review thread.",
    )
    parser.add_argument("thread_id", help="GitHub review thread node ID to resolve")
    return parser.parse_args()


def validate_thread_id(thread_id: str) -> str:
    if not NODE_ID_PATTERN.fullmatch(thread_id):
        raise ValueError("thread_id must be a GitHub node ID")
    return thread_id


def main() -> int:
    args = parse_args()
    try:
        thread_id = validate_thread_id(args.thread_id)
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
