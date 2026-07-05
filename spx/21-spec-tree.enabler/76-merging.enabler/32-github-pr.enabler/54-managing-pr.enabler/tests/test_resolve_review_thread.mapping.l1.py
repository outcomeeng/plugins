"""Mapping tests for the manage-pr review-thread resolver."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import Any, Final

import pytest


REPO_ROOT: Final = Path(__file__).resolve().parents[6]
SCRIPT: Final = (
    REPO_ROOT
    / "src"
    / "plugins"
    / "spec-tree"
    / "skills"
    / "manage-pr"
    / "scripts"
    / "resolve_review_thread.py"
)


def load_script() -> ModuleType:
    spec = importlib.util.spec_from_file_location("resolve_review_thread", SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_review_comment_id_discovers_thread_before_resolving(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = load_script()
    calls: list[list[str]] = []
    threads_payload = {
        "data": {
            "repository": {
                "pullRequest": {
                    "reviewThreads": {
                        "nodes": [
                            {
                                "id": "PRRT_thread0001",
                                "comments": {
                                    "nodes": [
                                        {
                                            "id": "PRRC_comment0001",
                                            "databaseId": 12345,
                                        }
                                    ]
                                },
                            }
                        ]
                    }
                }
            }
        }
    }

    def fake_run(argv: list[str], **kwargs: Any) -> SimpleNamespace:
        calls.append(argv)
        if "-F" in argv and "number=405" in argv:
            assert kwargs["capture_output"] is True
            assert kwargs["text"] is True
            return SimpleNamespace(
                returncode=0,
                stdout=json.dumps(threads_payload),
                stderr="",
            )
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            str(SCRIPT),
            "--host",
            "ghe.example.com",
            "--repo",
            "outcomeeng/plugins",
            "--pr",
            "405",
            "--review-comment-id",
            "12345",
        ],
    )

    assert module.main() == 0
    assert calls[0][:3] == ["gh", "api", "graphql"]
    assert "--hostname" in calls[0]
    assert "ghe.example.com" in calls[0]
    assert "owner=outcomeeng" in calls[0]
    assert "repo=plugins" in calls[0]
    assert "number=405" in calls[0]
    assert calls[1] == [
        "gh",
        "api",
        "graphql",
        "--hostname",
        "ghe.example.com",
        "--silent",
        "-f",
        f"query={module.QUERY}",
        "-F",
        "id=PRRT_thread0001",
    ]


def test_direct_thread_id_resolves_without_discovery(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = load_script()
    calls: list[list[str]] = []

    def fake_run(argv: list[str], **_kwargs: Any) -> SimpleNamespace:
        calls.append(argv)
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(
        sys,
        "argv",
        [str(SCRIPT), "--host", "ghe.example.com", "PRRT_thread0002"],
    )

    assert module.main() == 0
    assert calls == [
        [
            "gh",
            "api",
            "graphql",
            "--hostname",
            "ghe.example.com",
            "--silent",
            "-f",
            f"query={module.QUERY}",
            "-F",
            "id=PRRT_thread0002",
        ]
    ]


def test_review_thread_discovery_pages_threads_until_comment_is_found(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = load_script()
    calls: list[list[str]] = []
    first_page = {
        "data": {
            "repository": {
                "pullRequest": {
                    "reviewThreads": {
                        "pageInfo": {"hasNextPage": True, "endCursor": "cursor-1"},
                        "nodes": [
                            {
                                "id": "PRRT_thread0003",
                                "comments": {
                                    "pageInfo": {
                                        "hasNextPage": False,
                                        "endCursor": None,
                                    },
                                    "nodes": [
                                        {
                                            "id": "PRRC_comment0003",
                                            "databaseId": 303,
                                        }
                                    ],
                                },
                            }
                        ],
                    }
                }
            }
        }
    }
    second_page = {
        "data": {
            "repository": {
                "pullRequest": {
                    "reviewThreads": {
                        "pageInfo": {"hasNextPage": False, "endCursor": None},
                        "nodes": [
                            {
                                "id": "PRRT_thread0004",
                                "comments": {
                                    "pageInfo": {
                                        "hasNextPage": False,
                                        "endCursor": None,
                                    },
                                    "nodes": [
                                        {
                                            "id": "PRRC_comment0004",
                                            "databaseId": 404,
                                        }
                                    ],
                                },
                            }
                        ],
                    }
                }
            }
        }
    }

    def fake_run(argv: list[str], **kwargs: Any) -> SimpleNamespace:
        calls.append(argv)
        if "id=PRRT_thread0004" in argv:
            return SimpleNamespace(returncode=0)
        assert kwargs["capture_output"] is True
        if "threadsAfter=cursor-1" in argv:
            return SimpleNamespace(
                returncode=0,
                stdout=json.dumps(second_page),
                stderr="",
            )
        return SimpleNamespace(returncode=0, stdout=json.dumps(first_page), stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            str(SCRIPT),
            "--host",
            "ghe.example.com",
            "--repo",
            "outcomeeng/plugins",
            "--pr",
            "405",
            "--review-comment-id",
            "404",
        ],
    )

    assert module.main() == 0
    assert any("threadsAfter=cursor-1" in call for call in calls)
    assert calls[-1][-1] == "id=PRRT_thread0004"


def test_review_thread_discovery_pages_comments_until_comment_is_found(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = load_script()
    calls: list[list[str]] = []
    threads_page = {
        "data": {
            "repository": {
                "pullRequest": {
                    "reviewThreads": {
                        "pageInfo": {"hasNextPage": False, "endCursor": None},
                        "nodes": [
                            {
                                "id": "PRRT_thread0005",
                                "comments": {
                                    "pageInfo": {
                                        "hasNextPage": True,
                                        "endCursor": "comment-cursor-1",
                                    },
                                    "nodes": [
                                        {
                                            "id": "PRRC_comment0005",
                                            "databaseId": 505,
                                        }
                                    ],
                                },
                            }
                        ],
                    }
                }
            }
        }
    }
    comments_page = {
        "data": {
            "node": {
                "comments": {
                    "pageInfo": {"hasNextPage": False, "endCursor": None},
                    "nodes": [{"id": "PRRC_comment0006", "databaseId": 606}],
                }
            }
        }
    }

    def fake_run(argv: list[str], **kwargs: Any) -> SimpleNamespace:
        calls.append(argv)
        if "id=PRRT_thread0005" in argv:
            return SimpleNamespace(returncode=0)
        assert kwargs["capture_output"] is True
        if "threadId=PRRT_thread0005" in argv:
            assert "commentsAfter=comment-cursor-1" in argv
            return SimpleNamespace(
                returncode=0,
                stdout=json.dumps(comments_page),
                stderr="",
            )
        return SimpleNamespace(returncode=0, stdout=json.dumps(threads_page), stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            str(SCRIPT),
            "--host",
            "ghe.example.com",
            "--repo",
            "outcomeeng/plugins",
            "--pr",
            "405",
            "--review-comment-id",
            "606",
        ],
    )

    assert module.main() == 0
    assert any("commentsAfter=comment-cursor-1" in call for call in calls)
    graphql_calls = [call for call in calls if call[:3] == ["gh", "api", "graphql"]]
    assert graphql_calls
    assert all(
        "--hostname" in call and "ghe.example.com" in call for call in graphql_calls
    )
    assert calls[-1][-1] == "id=PRRT_thread0005"


@pytest.mark.parametrize(
    ("argv", "message"),
    (
        (["bad!"], "thread_id must be a GitHub node ID"),
        (
            ["--repo", "outcomeeng", "--pr", "405", "--review-comment-id", "12345"],
            "repo must be in owner/name form",
        ),
        (
            [
                "--repo",
                "outcomeeng/plugins",
                "--pr",
                "0",
                "--review-comment-id",
                "12345",
            ],
            "pr must be a positive integer",
        ),
        (
            [
                "--repo",
                "outcomeeng/plugins",
                "--pr",
                "405",
                "--review-comment-id",
                "bad!",
            ],
            "review_comment_id must be a database ID or GitHub node ID",
        ),
        (
            [
                "--host",
                "bad/host",
                "PRRT_thread0007",
            ],
            "host must be a GitHub hostname",
        ),
        (
            [
                "PRRT_thread0007",
                "--repo",
                "outcomeeng/plugins",
                "--pr",
                "405",
                "--review-comment-id",
                "12345",
            ],
            "pass either thread_id or --repo/--pr/--review-comment-id",
        ),
    ),
)
def test_invalid_arguments_fail_before_github_calls(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    argv: list[str],
    message: str,
) -> None:
    module = load_script()

    def fail_run(_argv: list[str], **_kwargs: Any) -> SimpleNamespace:
        pytest.fail("invalid arguments must not call GitHub")

    monkeypatch.setattr(subprocess, "run", fail_run)
    monkeypatch.setattr(sys, "argv", [str(SCRIPT), *argv])

    assert module.main() == 2
    assert message in capsys.readouterr().err


def test_review_comment_not_found_after_complete_pagination_returns_error(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    module = load_script()
    calls: list[list[str]] = []
    payload = {
        "data": {
            "repository": {
                "pullRequest": {
                    "reviewThreads": {
                        "pageInfo": {"hasNextPage": False, "endCursor": None},
                        "nodes": [
                            {
                                "id": "PRRT_thread0008",
                                "comments": {
                                    "pageInfo": {
                                        "hasNextPage": False,
                                        "endCursor": None,
                                    },
                                    "nodes": [
                                        {
                                            "id": "PRRC_comment0008",
                                            "databaseId": 808,
                                        }
                                    ],
                                },
                            }
                        ],
                    }
                }
            }
        }
    }

    def fake_run(argv: list[str], **_kwargs: Any) -> SimpleNamespace:
        calls.append(argv)
        return SimpleNamespace(returncode=0, stdout=json.dumps(payload), stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            str(SCRIPT),
            "--repo",
            "outcomeeng/plugins",
            "--pr",
            "405",
            "--review-comment-id",
            "909",
        ],
    )

    assert module.main() == 2
    assert (
        "review comment was not found after complete review-thread pagination"
        in capsys.readouterr().err
    )
    assert len(calls) == 1


@pytest.mark.parametrize(
    ("payload", "message"),
    (
        (
            {"data": {"repository": None}},
            "GitHub response repository must be an object",
        ),
        (
            {"data": {"repository": {"pullRequest": None}}},
            "GitHub response pullRequest must be an object",
        ),
    ),
)
def test_null_review_thread_discovery_payload_returns_error(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    payload: dict[str, object],
    message: str,
) -> None:
    module = load_script()

    def fake_run(_argv: list[str], **_kwargs: Any) -> SimpleNamespace:
        return SimpleNamespace(returncode=0, stdout=json.dumps(payload), stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            str(SCRIPT),
            "--repo",
            "outcomeeng/plugins",
            "--pr",
            "405",
            "--review-comment-id",
            "909",
        ],
    )

    assert module.main() == 2
    assert message in capsys.readouterr().err


def test_null_paginated_thread_node_returns_error(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    module = load_script()
    threads_page = {
        "data": {
            "repository": {
                "pullRequest": {
                    "reviewThreads": {
                        "pageInfo": {"hasNextPage": False, "endCursor": None},
                        "nodes": [
                            {
                                "id": "PRRT_thread0009",
                                "comments": {
                                    "pageInfo": {
                                        "hasNextPage": True,
                                        "endCursor": "comment-cursor-2",
                                    },
                                    "nodes": [
                                        {
                                            "id": "PRRC_comment0009",
                                            "databaseId": 909,
                                        }
                                    ],
                                },
                            }
                        ],
                    }
                }
            }
        }
    }
    null_node_page = {"data": {"node": None}}

    def fake_run(argv: list[str], **_kwargs: Any) -> SimpleNamespace:
        if "threadId=PRRT_thread0009" in argv:
            return SimpleNamespace(
                returncode=0,
                stdout=json.dumps(null_node_page),
                stderr="",
            )
        return SimpleNamespace(returncode=0, stdout=json.dumps(threads_page), stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            str(SCRIPT),
            "--repo",
            "outcomeeng/plugins",
            "--pr",
            "405",
            "--review-comment-id",
            "1001",
        ],
    )

    assert module.main() == 2
    assert (
        "GitHub response node must be a PullRequestReviewThread object"
        in capsys.readouterr().err
    )


def test_malformed_paginated_response_returns_error(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    module = load_script()
    payload = {
        "data": {
            "repository": {
                "pullRequest": {
                    "reviewThreads": {
                        "pageInfo": {"hasNextPage": True, "endCursor": None},
                        "nodes": [],
                    }
                }
            }
        }
    }

    def fake_run(_argv: list[str], **_kwargs: Any) -> SimpleNamespace:
        return SimpleNamespace(returncode=0, stdout=json.dumps(payload), stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            str(SCRIPT),
            "--repo",
            "outcomeeng/plugins",
            "--pr",
            "405",
            "--review-comment-id",
            "909",
        ],
    )

    assert module.main() == 2
    assert (
        "GitHub response reviewThreads page is missing endCursor"
        in capsys.readouterr().err
    )
