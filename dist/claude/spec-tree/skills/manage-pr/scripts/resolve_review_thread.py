#!/usr/bin/env python3
"""Resolve one GitHub pull-request review thread."""

from __future__ import annotations

import argparse
import subprocess


QUERY = (
    "mutation($id: ID!) { "
    "resolveReviewThread(input: {threadId: $id}) { "
    "thread { isResolved } "
    "} "
    "}"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Resolve one GitHub pull-request review thread.",
    )
    parser.add_argument("thread_id", help="GitHub review thread node ID to resolve")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    completed = subprocess.run(
        [
            "gh",
            "api",
            "graphql",
            "--silent",
            "-f",
            f"query={QUERY}",
            "-F",
            f"id={args.thread_id}",
        ],
        check=False,
    )
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
