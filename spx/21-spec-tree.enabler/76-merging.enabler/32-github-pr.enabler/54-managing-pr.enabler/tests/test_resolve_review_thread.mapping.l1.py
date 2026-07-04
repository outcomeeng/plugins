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
    assert "owner=outcomeeng" in calls[0]
    assert "repo=plugins" in calls[0]
    assert "number=405" in calls[0]
    assert calls[1] == [
        "gh",
        "api",
        "graphql",
        "--silent",
        "-f",
        f"query={module.QUERY}",
        "-F",
        "id=PRRT_thread0001",
    ]
