"""Execution harness for manage-pr review-thread resolver tests."""

from __future__ import annotations

import importlib.util
import io
import subprocess
import sys
from collections.abc import Callable
from contextlib import redirect_stderr, redirect_stdout
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Literal, ParamSpec, Protocol, TypeVar, cast

from hypothesis import seed, settings

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
MALFORMED_INPUT_PROPERTY_SEED = 20260707
MALFORMED_INPUT_PROPERTY_EXAMPLES = 50
P = ParamSpec("P")
R = TypeVar("R")


class ResolverEntrypoint(Protocol):
    """Describe the two arguments the dynamic harness invokes."""

    def __call__(
        self,
        argv: list[str],
        runner: ResolverCommandRunner,
        /,
    ) -> int: ...


class ResolverCommandRunner(Protocol):
    """Match the resolver's injected external-command boundary."""

    def __call__(
        self,
        command: list[str],
        *,
        check: bool,
        capture_output: bool = False,
        text: Literal[True] = True,
    ) -> subprocess.CompletedProcess[str]: ...


@dataclass(frozen=True)
class CommandObservation:
    command: tuple[str, ...]
    keyword_arguments: tuple[tuple[str, object], ...]
    returncode: int
    stdout: str
    stderr: str


@dataclass(frozen=True)
class ResolverRun:
    argv: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str
    interactions: tuple[CommandObservation, ...]


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


class GitHubResponseFactory:
    """Build GitHub payloads from the resolver's source-owned field vocabulary."""

    @staticmethod
    def comment(*, node_id: str, database_id: int) -> dict[str, object]:
        fields = RESOLVER.GitHubResponseField
        return {fields.ID.value: node_id, fields.DATABASE_ID.value: database_id}

    @staticmethod
    def comments(
        *,
        nodes: list[object],
        has_next_page: bool,
        end_cursor: str | None = None,
        include_page_info: bool = True,
    ) -> dict[str, object]:
        fields = RESOLVER.GitHubResponseField
        response: dict[str, object] = {fields.NODES.value: nodes}
        if include_page_info:
            response[fields.PAGE_INFO.value] = {
                fields.HAS_NEXT_PAGE.value: has_next_page,
                fields.END_CURSOR.value: end_cursor,
            }
        return response

    @staticmethod
    def thread(*, thread_id: str, comments: object) -> dict[str, object]:
        fields = RESOLVER.GitHubResponseField
        return {fields.ID.value: thread_id, fields.COMMENTS.value: comments}

    @staticmethod
    def review_threads(
        *,
        nodes: list[object] | None,
        has_next_page: bool = False,
        end_cursor: str | None = None,
    ) -> dict[str, object]:
        fields = RESOLVER.GitHubResponseField
        response: dict[str, object] = {
            fields.PAGE_INFO.value: {
                fields.HAS_NEXT_PAGE.value: has_next_page,
                fields.END_CURSOR.value: end_cursor,
            }
        }
        if nodes is not None:
            response[fields.NODES.value] = nodes
        return response

    @staticmethod
    def threads_payload(review_threads: object) -> dict[str, object]:
        fields = RESOLVER.GitHubResponseField
        return {
            fields.DATA.value: {
                fields.REPOSITORY.value: {
                    fields.PULL_REQUEST.value: {
                        fields.REVIEW_THREADS.value: review_threads
                    }
                }
            }
        }

    @staticmethod
    def null_repository_payload() -> dict[str, object]:
        fields = RESOLVER.GitHubResponseField
        return {fields.DATA.value: {fields.REPOSITORY.value: None}}

    @staticmethod
    def null_pull_request_payload() -> dict[str, object]:
        fields = RESOLVER.GitHubResponseField
        return {
            fields.DATA.value: {
                fields.REPOSITORY.value: {fields.PULL_REQUEST.value: None}
            }
        }

    @staticmethod
    def thread_comments_payload(comments: object) -> dict[str, object]:
        fields = RESOLVER.GitHubResponseField
        return {
            fields.DATA.value: {fields.NODE.value: {fields.COMMENTS.value: comments}}
        }

    @staticmethod
    def null_thread_payload() -> dict[str, object]:
        fields = RESOLVER.GitHubResponseField
        return {fields.DATA.value: {fields.NODE.value: None}}


GITHUB_RESPONSE = GitHubResponseFactory()
RESOLVER = load_script()


def resolver_property(test: Callable[P, R]) -> Callable[P, R]:
    configured = settings(
        max_examples=MALFORMED_INPUT_PROPERTY_EXAMPLES,
        print_blob=True,
    )(test)
    return seed(MALFORMED_INPUT_PROPERTY_SEED)(configured)


def run_resolver(
    argv: list[str] | tuple[str, ...],
    responder: ResolverResponder,
) -> ResolverRun:
    stdout = io.StringIO()
    stderr = io.StringIO()
    interactions: list[CommandObservation] = []

    def recording_runner(
        command: list[str],
        **kwargs: object,
    ) -> subprocess.CompletedProcess[str]:
        result = responder(command, kwargs)
        interactions.append(
            CommandObservation(
                command=tuple(command),
                keyword_arguments=tuple(sorted(kwargs.items())),
                returncode=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
            )
        )
        return result

    main = cast(
        "ResolverEntrypoint",
        getattr(RESOLVER, "main"),
    )
    with redirect_stdout(stdout), redirect_stderr(stderr):
        try:
            returncode = main(list(argv), recording_runner)
        except SystemExit as exc:
            returncode = exc.code if isinstance(exc.code, int) else 1
    return ResolverRun(
        argv=tuple(argv),
        returncode=returncode,
        stdout=stdout.getvalue(),
        stderr=stderr.getvalue(),
        interactions=tuple(interactions),
    )


def completed(
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
