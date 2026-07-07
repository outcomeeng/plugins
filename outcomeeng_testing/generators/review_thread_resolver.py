"""Hypothesis strategies for manage-pr review-thread resolver tests."""

from __future__ import annotations

import importlib.util
import re
import sys
from enum import StrEnum
from pathlib import Path
from types import ModuleType

from hypothesis import strategies as st
from hypothesis.strategies import SearchStrategy

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
VALID_THREAD_ID = "PRRT_valid001"
VALID_REPOSITORY = "outcomeeng/plugins"
VALID_PR_NUMBER = "405"
VALID_REVIEW_COMMENT_ID = "12345"
VALID_HOST = "ghe.example.com"


class InvalidResolverInput(StrEnum):
    THREAD_ID = "thread_id"
    REPOSITORY = "repository"
    PR_NUMBER = "pr_number"
    REVIEW_COMMENT_ID = "review_comment_id"
    HOST = "host"
    MIXED_MODE = "mixed_mode"


def malformed_resolver_argvs() -> SearchStrategy[tuple[str, ...]]:
    """Generated malformed CLI argv domains for the resolver boundary."""

    return st.one_of(
        _invalid_thread_ids().map(lambda value: (value,)),
        _invalid_repositories().map(
            lambda value: (
                "--repo",
                value,
                "--pr",
                VALID_PR_NUMBER,
                "--review-comment-id",
                VALID_REVIEW_COMMENT_ID,
            )
        ),
        _invalid_numbers().map(
            lambda value: (
                "--repo",
                VALID_REPOSITORY,
                "--pr",
                value,
                "--review-comment-id",
                VALID_REVIEW_COMMENT_ID,
            )
        ),
        _invalid_comment_ids().map(
            lambda value: (
                "--repo",
                VALID_REPOSITORY,
                "--pr",
                VALID_PR_NUMBER,
                "--review-comment-id",
                value,
            )
        ),
        _invalid_hosts().map(
            lambda value: (
                "--host",
                value,
                VALID_THREAD_ID,
            )
        ),
        st.just(
            (
                VALID_THREAD_ID,
                "--repo",
                VALID_REPOSITORY,
                "--pr",
                VALID_PR_NUMBER,
                "--review-comment-id",
                VALID_REVIEW_COMMENT_ID,
            )
        ),
    )


def _invalid_thread_ids() -> SearchStrategy[str]:
    return _strings_outside_pattern(_pattern("NODE_ID_PATTERN"))


def _invalid_repositories() -> SearchStrategy[str]:
    return _strings_outside_pattern(_pattern("REPOSITORY_PATTERN"))


def _invalid_numbers() -> SearchStrategy[str]:
    return _strings_outside_pattern(_pattern("NUMBER_PATTERN"))


def _invalid_comment_ids() -> SearchStrategy[str]:
    return _strings_outside_pattern(_pattern("COMMENT_ID_PATTERN"))


def _invalid_hosts() -> SearchStrategy[str]:
    return _strings_outside_pattern(_pattern("HOST_PATTERN"))


def _strings_outside_pattern(pattern: re.Pattern[str]) -> SearchStrategy[str]:
    return st.text(max_size=32).filter(lambda value: pattern.fullmatch(value) is None)


def _pattern(name: str) -> re.Pattern[str]:
    value = getattr(_load_script(), name)
    if not isinstance(value, re.Pattern):
        raise RuntimeError(f"resolve_review_thread.{name} must be a regex pattern")
    return value


def _load_script() -> ModuleType:
    cached = sys.modules.get("manage_pr_resolve_review_thread_generator")
    if cached is not None:
        return cached
    spec = importlib.util.spec_from_file_location(
        "manage_pr_resolve_review_thread_generator",
        SCRIPT,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load resolve_review_thread from {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["manage_pr_resolve_review_thread_generator"] = module
    spec.loader.exec_module(module)
    return module
