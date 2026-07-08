"""Harness for manage-pr review-thread resolver mapping tests."""

from __future__ import annotations

import importlib.util
import io
import json
import subprocess
import sys
from collections.abc import Callable
from contextlib import redirect_stderr, redirect_stdout
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import cast

from hypothesis import given, seed, settings

from outcomeeng_testing.generators.review_thread_resolver import (
    malformed_resolver_argvs,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = (
    REPO_ROOT
    / "src"
    / "plugins"
    / "spec-tree"
    / "skills"
    / "manage-pr"
    / "scripts"
    / "resolve_review_thread.py"
)

ResolverResponder = Callable[
    [list[str], dict[str, object]],
    subprocess.CompletedProcess[str],
]
InjectedCommandRunner = Callable[..., subprocess.CompletedProcess[str]]
MALFORMED_INPUT_PROPERTY_SEED = 20260707
MALFORMED_INPUT_PROPERTY_EXAMPLES = 50


@dataclass(frozen=True)
class ResolverRun:
    returncode: int
    stdout: str
    stderr: str
    calls: tuple[tuple[str, ...], ...]


def load_script() -> ModuleType:
    cached = sys.modules.get("manage_pr_resolve_review_thread")
    if cached is not None:
        return cached
    spec = importlib.util.spec_from_file_location(
        "manage_pr_resolve_review_thread",
        SCRIPT,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load resolve_review_thread from {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["manage_pr_resolve_review_thread"] = module
    spec.loader.exec_module(module)
    return module


def review_comment_id_discovers_thread_before_resolving() -> bool:
    module = load_script()
    threads_payload = _threads_payload(
        _review_threads(
            [
                _thread_node(
                    "PRRT_thread0001",
                    {"nodes": [_comment("PRRC_comment0001", 12345)]},
                )
            ]
        )
    )

    def responder(
        command: list[str],
        kwargs: dict[str, object],
    ) -> subprocess.CompletedProcess[str]:
        if "-F" in command and "number=405" in command:
            if kwargs.get("capture_output") is not True:
                return _completed(command, returncode=98)
            if kwargs.get("text") is not True:
                return _completed(command, returncode=99)
            return _completed(command, stdout=json.dumps(threads_payload))
        return _completed(command)

    run = _run_resolver(
        [
            "--host",
            "ghe.example.com",
            "--repo",
            "outcomeeng/plugins",
            "--pr",
            "405",
            "--review-comment-id",
            "12345",
        ],
        responder,
    )
    return (
        run.returncode == 0
        and len(run.calls) == 2
        and run.calls[0][:3] == ("gh", "api", "graphql")
        and "--hostname" in run.calls[0]
        and "ghe.example.com" in run.calls[0]
        and "owner=outcomeeng" in run.calls[0]
        and "repo=plugins" in run.calls[0]
        and "number=405" in run.calls[0]
        and run.calls[1] == _resolve_call("PRRT_thread0001", module, host=True)
    )


def direct_thread_id_resolves_without_discovery() -> bool:
    module = load_script()
    run = _run_resolver(
        ["--host", "ghe.example.com", "PRRT_thread0002"],
        lambda command, _kwargs: _completed(command),
    )
    return run.returncode == 0 and run.calls == (
        _resolve_call("PRRT_thread0002", module, host=True),
    )


def review_thread_discovery_pages_threads_until_comment_is_found() -> bool:
    first_page = _threads_payload(
        _review_threads(
            [
                _thread_node(
                    "PRRT_thread0003",
                    _comments(
                        [_comment("PRRC_comment0003", 303)],
                        has_next=False,
                    ),
                )
            ],
            has_next=True,
            end_cursor="cursor-1",
        )
    )
    second_page = _threads_payload(
        _review_threads(
            [
                _thread_node(
                    "PRRT_thread0004",
                    _comments(
                        [_comment("PRRC_comment0004", 404)],
                        has_next=False,
                    ),
                )
            ],
            has_next=False,
        )
    )

    def responder(
        command: list[str],
        kwargs: dict[str, object],
    ) -> subprocess.CompletedProcess[str]:
        if "id=PRRT_thread0004" in command:
            return _completed(command)
        if kwargs.get("capture_output") is not True:
            return _completed(command, returncode=98)
        if "threadsAfter=cursor-1" in command:
            return _completed(command, stdout=json.dumps(second_page))
        return _completed(command, stdout=json.dumps(first_page))

    run = _run_resolver(_discovery_argv("404", host=True), responder)
    return (
        run.returncode == 0
        and any("threadsAfter=cursor-1" in call for call in run.calls)
        and run.calls[-1][-1] == "id=PRRT_thread0004"
    )


def review_thread_discovery_pages_comments_until_comment_is_found() -> bool:
    threads_page = _threads_payload(
        _review_threads(
            [
                _thread_node(
                    "PRRT_thread0005",
                    _comments(
                        [_comment("PRRC_comment0005", 505)],
                        has_next=True,
                        end_cursor="comment-cursor-1",
                    ),
                )
            ],
            has_next=False,
        )
    )
    comments_page = {
        "data": {
            "node": {
                "comments": _comments(
                    [_comment("PRRC_comment0006", 606)],
                    has_next=False,
                )
            }
        }
    }

    def responder(
        command: list[str],
        kwargs: dict[str, object],
    ) -> subprocess.CompletedProcess[str]:
        if "id=PRRT_thread0005" in command:
            return _completed(command)
        if kwargs.get("capture_output") is not True:
            return _completed(command, returncode=98)
        if "threadId=PRRT_thread0005" in command:
            if "commentsAfter=comment-cursor-1" not in command:
                return _completed(command, returncode=99)
            return _completed(command, stdout=json.dumps(comments_page))
        return _completed(command, stdout=json.dumps(threads_page))

    run = _run_resolver(_discovery_argv("606", host=True), responder)
    graphql_calls = tuple(
        call for call in run.calls if call[:3] == ("gh", "api", "graphql")
    )
    return (
        run.returncode == 0
        and any("commentsAfter=comment-cursor-1" in call for call in run.calls)
        and len(graphql_calls) == len(run.calls)
        and all(
            "--hostname" in call and "ghe.example.com" in call for call in graphql_calls
        )
        and run.calls[-1][-1] == "id=PRRT_thread0005"
    )


def malformed_inputs_fail_before_github_calls() -> bool:
    @seed(MALFORMED_INPUT_PROPERTY_SEED)
    @settings(max_examples=MALFORMED_INPUT_PROPERTY_EXAMPLES)
    @given(argv=malformed_resolver_argvs())
    def assertion(argv: tuple[str, ...]) -> None:
        run = _run_resolver(
            list(argv),
            lambda command, _kwargs: _completed(command, returncode=97),
        )
        assert run.returncode == 2
        assert run.stderr
        assert not run.calls

    assertion()
    return True


def review_comment_not_found_after_complete_pagination_returns_error() -> bool:
    payload = _threads_payload(
        _review_threads(
            [
                _thread_node(
                    "PRRT_thread0008",
                    _comments(
                        [_comment("PRRC_comment0008", 808)],
                        has_next=False,
                    ),
                )
            ],
            has_next=False,
        )
    )
    run = _run_resolver(
        _discovery_argv("909"),
        lambda command, _kwargs: _completed(command, stdout=json.dumps(payload)),
    )
    return (
        run.returncode == 2
        and "review comment was not found after complete review-thread pagination"
        in run.stderr
        and len(run.calls) == 1
    )


def missing_comment_page_info_returns_error() -> bool:
    payload = _threads_payload(
        _review_threads(
            [
                _thread_node(
                    "PRRT_thread0010",
                    {"nodes": [_comment("PRRC_comment0010", 1010)]},
                )
            ],
            has_next=False,
        )
    )
    run = _run_resolver(
        _discovery_argv("1111"),
        lambda command, _kwargs: _completed(command, stdout=json.dumps(payload)),
    )
    return (
        run.returncode == 2
        and "GitHub response comments.pageInfo must be an object" in run.stderr
    )


def null_review_thread_discovery_payload_returns_error() -> bool:
    return _payload_returns_error(
        {"data": {"repository": None}},
        "GitHub response repository must be an object",
    ) and _payload_returns_error(
        {"data": {"repository": {"pullRequest": None}}},
        "GitHub response pullRequest must be an object",
    )


def missing_review_thread_nodes_returns_error() -> bool:
    return _payload_returns_error(
        _threads_payload(
            {"pageInfo": {"hasNextPage": False, "endCursor": None}},
        ),
        "GitHub response reviewThreads.nodes must be a list",
    )


def null_paginated_thread_node_returns_error() -> bool:
    threads_page = _threads_payload(
        _review_threads(
            [
                _thread_node(
                    "PRRT_thread0009",
                    _comments(
                        [_comment("PRRC_comment0009", 909)],
                        has_next=True,
                        end_cursor="comment-cursor-2",
                    ),
                )
            ],
            has_next=False,
        )
    )
    null_node_page = {"data": {"node": None}}

    def responder(
        command: list[str],
        _kwargs: dict[str, object],
    ) -> subprocess.CompletedProcess[str]:
        if "threadId=PRRT_thread0009" in command:
            return _completed(command, stdout=json.dumps(null_node_page))
        return _completed(command, stdout=json.dumps(threads_page))

    run = _run_resolver(_discovery_argv("1001"), responder)
    return (
        run.returncode == 2
        and "GitHub response node must be a PullRequestReviewThread object"
        in run.stderr
    )


def malformed_paginated_response_returns_error() -> bool:
    payload = _threads_payload(
        {"pageInfo": {"hasNextPage": True, "endCursor": None}, "nodes": []}
    )
    run = _run_resolver(
        _discovery_argv("909"),
        lambda command, _kwargs: _completed(command, stdout=json.dumps(payload)),
    )
    return (
        run.returncode == 2
        and "GitHub response reviewThreads page is missing endCursor" in run.stderr
    )


def _run_resolver(argv: list[str], responder: ResolverResponder) -> ResolverRun:
    module = load_script()
    stdout = io.StringIO()
    stderr = io.StringIO()
    calls: list[tuple[str, ...]] = []

    def fake_run(
        command: list[str],
        **kwargs: object,
    ) -> subprocess.CompletedProcess[str]:
        calls.append(tuple(command))
        return responder(command, kwargs)

    main = cast(
        "Callable[[list[str], InjectedCommandRunner], int]",
        getattr(module, "main"),
    )
    with (
        redirect_stdout(stdout),
        redirect_stderr(stderr),
    ):
        try:
            returncode = main(argv, fake_run)
        except SystemExit as exc:
            code = exc.code
            returncode = code if isinstance(code, int) else 1
    return ResolverRun(
        returncode=returncode,
        stdout=stdout.getvalue(),
        stderr=stderr.getvalue(),
        calls=tuple(calls),
    )


def _payload_returns_error(payload: dict[str, object], message: str) -> bool:
    run = _run_resolver(
        _discovery_argv("909"),
        lambda command, _kwargs: _completed(command, stdout=json.dumps(payload)),
    )
    return run.returncode == 2 and message in run.stderr


def _completed(
    command: list[str],
    *,
    returncode: int = 0,
    stdout: str = "",
    stderr: str = "",
) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(
        args=command,
        returncode=returncode,
        stdout=stdout,
        stderr=stderr,
    )


def _resolve_call(
    thread_id: str,
    module: ModuleType,
    *,
    host: bool,
) -> tuple[str, ...]:
    command = [
        "gh",
        "api",
        "graphql",
    ]
    if host:
        command.extend(["--hostname", "ghe.example.com"])
    command.extend(
        [
            "--silent",
            "-f",
            f"query={_query(module)}",
            "-F",
            f"id={thread_id}",
        ]
    )
    return tuple(command)


def _query(module: ModuleType) -> str:
    return cast("str", getattr(module, "QUERY"))


def _discovery_argv(comment_id: str, *, host: bool = False) -> list[str]:
    argv = []
    if host:
        argv.extend(["--host", "ghe.example.com"])
    argv.extend(
        [
            "--repo",
            "outcomeeng/plugins",
            "--pr",
            "405",
            "--review-comment-id",
            comment_id,
        ]
    )
    return argv


def _comment(comment_id: str, database_id: int) -> dict[str, object]:
    return {"id": comment_id, "databaseId": database_id}


def _comments(
    nodes: list[dict[str, object]],
    *,
    has_next: bool,
    end_cursor: str | None = None,
) -> dict[str, object]:
    return {
        "pageInfo": {"hasNextPage": has_next, "endCursor": end_cursor},
        "nodes": nodes,
    }


def _thread_node(thread_id: str, comments: dict[str, object]) -> dict[str, object]:
    return {"id": thread_id, "comments": comments}


def _review_threads(
    nodes: list[dict[str, object]],
    *,
    has_next: bool = False,
    end_cursor: str | None = None,
) -> dict[str, object]:
    return {
        "pageInfo": {"hasNextPage": has_next, "endCursor": end_cursor},
        "nodes": nodes,
    }


def _threads_payload(review_threads: dict[str, object]) -> dict[str, object]:
    return {
        "data": {
            "repository": {
                "pullRequest": {
                    "reviewThreads": review_threads,
                }
            }
        }
    }
