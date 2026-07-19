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
    ResolverDomain,
    malformed_resolver_argvs,
    resolver_mapping_domain,
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


def _run_mapping_case(assertion: Callable[[ResolverDomain], None]) -> bool:
    assertion(resolver_mapping_domain())
    return True


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
    def assertion(domain: ResolverDomain) -> None:
        module = load_script()
        thread_id = domain.thread_ids[0]
        comment_id = domain.comment_ids[0]
        database_id = domain.database_ids[0]
        threads_payload = _threads_payload(
            _review_threads(
                [
                    _thread_node(
                        thread_id,
                        _comments(
                            [_comment(comment_id, database_id)],
                            has_next=False,
                        ),
                    )
                ]
            )
        )

        def responder(
            command: list[str],
            kwargs: dict[str, object],
        ) -> subprocess.CompletedProcess[str]:
            if command == list(_discovery_call(module, domain, host=True)):
                if kwargs.get("capture_output") is not True:
                    return _completed(command, returncode=98)
                if kwargs.get("text") is not True:
                    return _completed(command, returncode=99)
                return _completed(command, stdout=json.dumps(threads_payload))
            return _completed(command)

        run = _run_resolver(
            _discovery_argv(str(database_id), domain, host=True),
            responder,
        )
        assert run.returncode == 0
        assert len(run.calls) == 2
        assert run.calls[0] == _discovery_call(module, domain, host=True)
        assert run.calls[1] == _resolve_call(
            thread_id,
            module,
            domain,
            host=True,
        )

    return _run_mapping_case(assertion)


def direct_thread_id_resolves_without_discovery() -> bool:
    def assertion(domain: ResolverDomain) -> None:
        module = load_script()
        thread_id = domain.thread_ids[1]
        run = _run_resolver(
            _thread_argv(thread_id, domain, host=True),
            lambda command, _kwargs: _completed(command),
        )
        assert run.returncode == 0
        assert run.calls == (_resolve_call(thread_id, module, domain, host=True),)

    return _run_mapping_case(assertion)


def review_thread_discovery_pages_threads_until_comment_is_found() -> bool:
    def assertion(domain: ResolverDomain) -> None:
        module = load_script()
        first_thread_id = domain.thread_ids[2]
        second_thread_id = domain.thread_ids[3]
        first_comment_id = domain.comment_ids[1]
        second_comment_id = domain.comment_ids[2]
        first_database_id = domain.database_ids[1]
        second_database_id = domain.database_ids[2]
        cursor = domain.cursors[0]
        first_page = _threads_payload(
            _review_threads(
                [
                    _thread_node(
                        first_thread_id,
                        _comments(
                            [_comment(first_comment_id, first_database_id)],
                            has_next=False,
                        ),
                    )
                ],
                has_next=True,
                end_cursor=cursor,
            )
        )
        second_page = _threads_payload(
            _review_threads(
                [
                    _thread_node(
                        second_thread_id,
                        _comments(
                            [_comment(second_comment_id, second_database_id)],
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
            if command == list(
                _resolve_call(second_thread_id, module, domain, host=True)
            ):
                return _completed(command)
            if kwargs.get("capture_output") is not True:
                return _completed(command, returncode=98)
            if command == list(
                _discovery_call(
                    module,
                    domain,
                    host=True,
                    threads_after=cursor,
                )
            ):
                return _completed(command, stdout=json.dumps(second_page))
            return _completed(command, stdout=json.dumps(first_page))

        run = _run_resolver(
            _discovery_argv(str(second_database_id), domain, host=True),
            responder,
        )
        expected_page_call = _discovery_call(
            module,
            domain,
            host=True,
            threads_after=cursor,
        )
        assert run.returncode == 0
        assert expected_page_call in run.calls
        assert run.calls[-1] == _resolve_call(
            second_thread_id,
            module,
            domain,
            host=True,
        )

    return _run_mapping_case(assertion)


def review_thread_discovery_pages_comments_until_comment_is_found() -> bool:
    def assertion(domain: ResolverDomain) -> None:
        module = load_script()
        thread_id = domain.thread_ids[4]
        first_comment_id = domain.comment_ids[3]
        second_comment_id = domain.comment_ids[4]
        first_database_id = domain.database_ids[3]
        second_database_id = domain.database_ids[4]
        cursor = domain.cursors[1]
        threads_page = _threads_payload(
            _review_threads(
                [
                    _thread_node(
                        thread_id,
                        _comments(
                            [_comment(first_comment_id, first_database_id)],
                            has_next=True,
                            end_cursor=cursor,
                        ),
                    )
                ],
                has_next=False,
            )
        )
        comments_page = _thread_comments_response(
            {
                _source_string(module, "COMMENTS_FIELD"): _comments(
                    [_comment(second_comment_id, second_database_id)],
                    has_next=False,
                )
            }
        )

        def responder(
            command: list[str],
            kwargs: dict[str, object],
        ) -> subprocess.CompletedProcess[str]:
            if command == list(_resolve_call(thread_id, module, domain, host=True)):
                return _completed(command)
            if kwargs.get("capture_output") is not True:
                return _completed(command, returncode=98)
            if command == list(
                _thread_comments_call(
                    module,
                    domain,
                    thread_id,
                    cursor,
                    host=True,
                )
            ):
                return _completed(command, stdout=json.dumps(comments_page))
            return _completed(command, stdout=json.dumps(threads_page))

        run = _run_resolver(
            _discovery_argv(str(second_database_id), domain, host=True),
            responder,
        )
        comments_call = _thread_comments_call(
            module,
            domain,
            thread_id,
            cursor,
            host=True,
        )
        graphql_prefix = _graphql_prefix(module)
        graphql_calls = tuple(call for call in run.calls if call[:3] == graphql_prefix)
        assert run.returncode == 0
        assert comments_call in run.calls
        assert len(graphql_calls) == len(run.calls)
        assert all(
            _source_string(module, "HOSTNAME_OPTION") in call and domain.host in call
            for call in graphql_calls
        )
        assert run.calls[-1] == _resolve_call(
            thread_id,
            module,
            domain,
            host=True,
        )

    return _run_mapping_case(assertion)


def malformed_inputs_fail_before_github_calls() -> bool:
    @seed(MALFORMED_INPUT_PROPERTY_SEED)
    @settings(max_examples=MALFORMED_INPUT_PROPERTY_EXAMPLES)
    @given(argv=malformed_resolver_argvs())
    def assertion(argv: tuple[str, ...]) -> None:
        run = _run_resolver(
            list(argv),
            lambda command, _kwargs: _completed(command, returncode=97),
        )
        assert run.returncode == _validation_error_exit_code()
        assert run.stderr
        assert not run.calls

    assertion()
    return True


def review_comment_not_found_after_complete_pagination_returns_error() -> bool:
    def assertion(domain: ResolverDomain) -> None:
        payload = _threads_payload(
            _review_threads(
                [
                    _thread_node(
                        domain.thread_ids[5],
                        _comments(
                            [_comment(domain.comment_ids[5], domain.database_ids[5])],
                            has_next=False,
                        ),
                    )
                ],
                has_next=False,
            )
        )
        run = _run_resolver(
            _discovery_argv(str(domain.database_ids[6]), domain),
            lambda command, _kwargs: _completed(
                command,
                stdout=json.dumps(payload),
            ),
        )
        assert run.returncode == _validation_error_exit_code()
        assert _source_string(load_script(), "ERROR_COMMENT_NOT_FOUND") in run.stderr
        assert len(run.calls) == 1

    return _run_mapping_case(assertion)


def missing_comment_page_info_returns_error() -> bool:
    def assertion(domain: ResolverDomain) -> None:
        payload = _threads_payload(
            _review_threads(
                [
                    _thread_node(
                        domain.thread_ids[6],
                        {
                            _source_string(load_script(), "NODES_FIELD"): [
                                _comment(
                                    domain.comment_ids[6],
                                    domain.database_ids[6],
                                )
                            ]
                        },
                    )
                ],
                has_next=False,
            )
        )
        run = _run_resolver(
            _discovery_argv(str(domain.database_ids[7]), domain),
            lambda command, _kwargs: _completed(
                command,
                stdout=json.dumps(payload),
            ),
        )
        assert run.returncode == _validation_error_exit_code()
        assert (
            _source_string(
                load_script(),
                "ERROR_COMMENTS_PAGE_INFO",
            )
            in run.stderr
        )

    return _run_mapping_case(assertion)


def null_review_thread_discovery_payload_returns_error() -> bool:
    def assertion(domain: ResolverDomain) -> None:
        assert _payload_returns_error(
            _repository_response(None),
            _source_string(load_script(), "ERROR_REPOSITORY"),
            domain,
        )
        assert _payload_returns_error(
            _pull_request_response(None),
            _source_string(load_script(), "ERROR_PULL_REQUEST"),
            domain,
        )

    return _run_mapping_case(assertion)


def missing_review_thread_nodes_returns_error() -> bool:
    def assertion(domain: ResolverDomain) -> None:
        assert _payload_returns_error(
            _threads_payload(
                {
                    _source_string(load_script(), "PAGE_INFO_FIELD"): {
                        _source_string(load_script(), "HAS_NEXT_PAGE_FIELD"): False,
                        _source_string(load_script(), "END_CURSOR_FIELD"): None,
                    }
                },
            ),
            _source_string(load_script(), "ERROR_REVIEW_THREADS_NODES"),
            domain,
        )

    return _run_mapping_case(assertion)


def null_paginated_thread_node_returns_error() -> bool:
    def assertion(domain: ResolverDomain) -> None:
        module = load_script()
        thread_id = domain.thread_ids[7]
        cursor = domain.cursors[0]
        threads_page = _threads_payload(
            _review_threads(
                [
                    _thread_node(
                        thread_id,
                        _comments(
                            [_comment(domain.comment_ids[7], domain.database_ids[7])],
                            has_next=True,
                            end_cursor=cursor,
                        ),
                    )
                ],
                has_next=False,
            )
        )
        null_node_page = _thread_comments_response(None)

        def responder(
            command: list[str],
            _kwargs: dict[str, object],
        ) -> subprocess.CompletedProcess[str]:
            if command == list(
                _thread_comments_call(
                    module,
                    domain,
                    thread_id,
                    cursor,
                    host=False,
                )
            ):
                return _completed(command, stdout=json.dumps(null_node_page))
            return _completed(command, stdout=json.dumps(threads_page))

        run = _run_resolver(
            _discovery_argv(str(domain.database_ids[8]), domain),
            responder,
        )
        assert run.returncode == _validation_error_exit_code()
        assert _source_string(module, "ERROR_NODE") in run.stderr

    return _run_mapping_case(assertion)


def malformed_paginated_response_returns_error() -> bool:
    def assertion(domain: ResolverDomain) -> None:
        module = load_script()
        payload = _threads_payload(
            {
                _source_string(module, "PAGE_INFO_FIELD"): {
                    _source_string(module, "HAS_NEXT_PAGE_FIELD"): True,
                    _source_string(module, "END_CURSOR_FIELD"): None,
                },
                _source_string(module, "NODES_FIELD"): [],
            }
        )
        run = _run_resolver(
            _discovery_argv(str(domain.database_ids[9]), domain),
            lambda command, _kwargs: _completed(
                command,
                stdout=json.dumps(payload),
            ),
        )
        assert run.returncode == _validation_error_exit_code()
        assert (
            _source_string(
                module,
                "ERROR_REVIEW_THREADS_END_CURSOR",
            )
            in run.stderr
        )

    return _run_mapping_case(assertion)


def malformed_payload_shapes_return_errors() -> bool:
    def assertion(domain: ResolverDomain) -> None:
        module = load_script()
        data_field = _source_string(module, "DATA_FIELD")
        review_threads_field = _source_string(module, "REVIEW_THREADS_FIELD")
        nodes_field = _source_string(module, "NODES_FIELD")
        page_info_field = _source_string(module, "PAGE_INFO_FIELD")
        comments_field = _source_string(module, "COMMENTS_FIELD")

        assert _payload_returns_error(
            {data_field: None},
            _source_string(module, "ERROR_DATA"),
            domain,
        )
        assert _payload_returns_error(
            _pull_request_response({review_threads_field: None}),
            _source_string(module, "ERROR_REVIEW_THREADS"),
            domain,
        )
        assert _payload_returns_error(
            _threads_payload({nodes_field: [], page_info_field: None}),
            _source_string(module, "ERROR_REVIEW_THREADS_PAGE_INFO"),
            domain,
        )
        assert _payload_returns_error(
            _threads_payload(
                _review_threads(
                    [
                        _thread_node(
                            domain.thread_ids[8],
                            {
                                nodes_field: None,
                                page_info_field: {
                                    _source_string(
                                        module, "HAS_NEXT_PAGE_FIELD"
                                    ): False,
                                    _source_string(module, "END_CURSOR_FIELD"): None,
                                },
                            },
                        )
                    ]
                )
            ),
            _source_string(module, "ERROR_COMMENTS_NODES"),
            domain,
        )
        assert _payload_returns_error(
            _threads_payload(
                _review_threads(
                    [
                        _thread_node(
                            domain.thread_ids[8],
                            _comments([], has_next=True),
                        )
                    ]
                )
            ),
            _source_string(module, "ERROR_COMMENTS_END_CURSOR"),
            domain,
        )

        thread_id = domain.thread_ids[9]
        cursor = domain.cursors[1]
        threads_page = _threads_payload(
            _review_threads(
                [
                    _thread_node(
                        thread_id,
                        _comments([], has_next=True, end_cursor=cursor),
                    )
                ]
            )
        )
        malformed_comments_page = _thread_comments_response({comments_field: None})

        def responder(
            command: list[str],
            _kwargs: dict[str, object],
        ) -> subprocess.CompletedProcess[str]:
            if command == list(
                _thread_comments_call(
                    module,
                    domain,
                    thread_id,
                    cursor,
                    host=False,
                )
            ):
                return _completed(
                    command,
                    stdout=json.dumps(malformed_comments_page),
                )
            return _completed(command, stdout=json.dumps(threads_page))

        run = _run_resolver(
            _discovery_argv(str(domain.database_ids[9]), domain),
            responder,
        )
        assert run.returncode == _validation_error_exit_code()
        assert _source_string(module, "ERROR_NODE_COMMENTS") in run.stderr

    return _run_mapping_case(assertion)


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


def _payload_returns_error(
    payload: dict[str, object],
    message: str,
    domain: ResolverDomain,
) -> bool:
    run = _run_resolver(
        _discovery_argv(str(domain.database_ids[9]), domain),
        lambda command, _kwargs: _completed(command, stdout=json.dumps(payload)),
    )
    return run.returncode == _validation_error_exit_code() and message in run.stderr


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
    domain: ResolverDomain,
    *,
    host: bool,
) -> tuple[str, ...]:
    return _graphql_argv(
        module,
        _query(module),
        {_source_string(module, "ID_FIELD"): thread_id},
        domain.host if host else None,
        silent=True,
    )


def _discovery_call(
    module: ModuleType,
    domain: ResolverDomain,
    *,
    host: bool,
    threads_after: str | None = None,
) -> tuple[str, ...]:
    owner, repo = domain.repository.split("/", 1)
    fields: dict[str, str | int] = {
        _source_string(module, "OWNER_FIELD"): owner,
        _source_string(module, "REPO_FIELD"): repo,
        _source_string(module, "NUMBER_FIELD"): domain.pr_number,
    }
    if threads_after is not None:
        fields[_source_string(module, "THREADS_AFTER_FIELD")] = threads_after
    return _graphql_argv(
        module,
        _source_string(module, "THREADS_QUERY"),
        fields,
        domain.host if host else None,
    )


def _thread_comments_call(
    module: ModuleType,
    domain: ResolverDomain,
    thread_id: str,
    comments_after: str,
    *,
    host: bool,
) -> tuple[str, ...]:
    return _graphql_argv(
        module,
        _source_string(module, "THREAD_COMMENTS_QUERY"),
        {
            _source_string(module, "THREAD_ID_FIELD"): thread_id,
            _source_string(module, "COMMENTS_AFTER_FIELD"): comments_after,
        },
        domain.host if host else None,
    )


def _graphql_argv(
    module: ModuleType,
    query: str,
    fields: dict[str, str | int],
    host: str | None,
    *,
    silent: bool = False,
) -> tuple[str, ...]:
    argv = list(_graphql_prefix(module))
    if host is not None:
        argv.extend([_source_string(module, "HOSTNAME_OPTION"), host])
    if silent:
        argv.append(_source_string(module, "SILENT_OPTION"))
    argv.extend(
        [
            _source_string(module, "RAW_FIELD_OPTION"),
            f"{_source_string(module, 'QUERY_FIELD')}={query}",
        ]
    )
    for key, value in fields.items():
        argv.extend(
            [
                _source_string(module, "TYPED_FIELD_OPTION"),
                f"{key}={value}",
            ]
        )
    return tuple(argv)


def _graphql_prefix(module: ModuleType) -> tuple[str, ...]:
    return (
        _source_string(module, "GH_COMMAND"),
        _source_string(module, "API_COMMAND"),
        _source_string(module, "GRAPHQL_RESOURCE"),
    )


def _query(module: ModuleType) -> str:
    return cast("str", getattr(module, "QUERY"))


def _discovery_argv(
    comment_id: str,
    domain: ResolverDomain,
    *,
    host: bool = False,
) -> list[str]:
    module = load_script()
    argv = []
    if host:
        argv.extend([_source_string(module, "HOST_OPTION"), domain.host])
    argv.extend(
        [
            _source_string(module, "REPOSITORY_OPTION"),
            domain.repository,
            _source_string(module, "PULL_REQUEST_OPTION"),
            str(domain.pr_number),
            _source_string(module, "REVIEW_COMMENT_ID_OPTION"),
            comment_id,
        ]
    )
    return argv


def _thread_argv(
    thread_id: str,
    domain: ResolverDomain,
    *,
    host: bool = False,
) -> list[str]:
    module = load_script()
    argv = []
    if host:
        argv.extend([_source_string(module, "HOST_OPTION"), domain.host])
    argv.append(thread_id)
    return argv


def _comment(comment_id: str, database_id: int) -> dict[str, object]:
    module = load_script()
    return {
        _source_string(module, "ID_FIELD"): comment_id,
        _source_string(module, "DATABASE_ID_FIELD"): database_id,
    }


def _comments(
    nodes: list[dict[str, object]],
    *,
    has_next: bool,
    end_cursor: str | None = None,
) -> dict[str, object]:
    module = load_script()
    return {
        _source_string(module, "PAGE_INFO_FIELD"): {
            _source_string(module, "HAS_NEXT_PAGE_FIELD"): has_next,
            _source_string(module, "END_CURSOR_FIELD"): end_cursor,
        },
        _source_string(module, "NODES_FIELD"): nodes,
    }


def _thread_node(thread_id: str, comments: dict[str, object]) -> dict[str, object]:
    module = load_script()
    return {
        _source_string(module, "ID_FIELD"): thread_id,
        _source_string(module, "COMMENTS_FIELD"): comments,
    }


def _review_threads(
    nodes: list[dict[str, object]],
    *,
    has_next: bool = False,
    end_cursor: str | None = None,
) -> dict[str, object]:
    module = load_script()
    return {
        _source_string(module, "PAGE_INFO_FIELD"): {
            _source_string(module, "HAS_NEXT_PAGE_FIELD"): has_next,
            _source_string(module, "END_CURSOR_FIELD"): end_cursor,
        },
        _source_string(module, "NODES_FIELD"): nodes,
    }


def _threads_payload(review_threads: dict[str, object]) -> dict[str, object]:
    module = load_script()
    return {
        _source_string(module, "DATA_FIELD"): {
            _source_string(module, "REPOSITORY_FIELD"): {
                _source_string(module, "PULL_REQUEST_FIELD"): {
                    _source_string(module, "REVIEW_THREADS_FIELD"): review_threads,
                }
            }
        }
    }


def _repository_response(repository: object) -> dict[str, object]:
    module = load_script()
    return {
        _source_string(module, "DATA_FIELD"): {
            _source_string(module, "REPOSITORY_FIELD"): repository,
        }
    }


def _pull_request_response(pull_request: object) -> dict[str, object]:
    module = load_script()
    return {
        _source_string(module, "DATA_FIELD"): {
            _source_string(module, "REPOSITORY_FIELD"): {
                _source_string(module, "PULL_REQUEST_FIELD"): pull_request,
            }
        }
    }


def _thread_comments_response(node: object) -> dict[str, object]:
    module = load_script()
    return {
        _source_string(module, "DATA_FIELD"): {
            _source_string(module, "NODE_FIELD"): node,
        }
    }


def _source_string(module: ModuleType, name: str) -> str:
    value = getattr(module, name)
    if not isinstance(value, str):
        raise RuntimeError(f"resolve_review_thread.{name} must be a string")
    return value


def _validation_error_exit_code() -> int:
    value = getattr(load_script(), "VALIDATION_ERROR_EXIT_CODE")
    if not isinstance(value, int):
        raise RuntimeError(
            "resolve_review_thread.VALIDATION_ERROR_EXIT_CODE must be an integer"
        )
    return value
