"""Hypothesis strategies for manage-pr review-thread resolver tests."""

from __future__ import annotations

import importlib.util
import re
import sys
from dataclasses import dataclass
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
MAPPING_IDENTIFIER_COUNT = 10
MAPPING_CURSOR_COUNT = 2


@dataclass(frozen=True)
class ResolverDomain:
    """Generated valid values for resolver interaction mappings."""

    repository: str
    pr_number: int
    host: str
    thread_ids: tuple[str, ...]
    comment_ids: tuple[str, ...]
    database_ids: tuple[int, ...]
    cursors: tuple[str, ...]


def resolver_mapping_domain() -> ResolverDomain:
    """Finite synthetic domain for resolver interaction mappings."""

    domain = ResolverDomain(
        repository="owner/repository",
        pr_number=1,
        host="github.example",
        thread_ids=tuple(
            f"THREAD_{index:08d}" for index in range(MAPPING_IDENTIFIER_COUNT)
        ),
        comment_ids=tuple(
            f"COMMENT_{index:08d}" for index in range(MAPPING_IDENTIFIER_COUNT)
        ),
        database_ids=tuple(range(1, MAPPING_IDENTIFIER_COUNT + 1)),
        cursors=tuple(f"CURSOR_{index:08d}" for index in range(MAPPING_CURSOR_COUNT)),
    )
    _validate_mapping_domain(domain)
    return domain


def resolver_domains() -> SearchStrategy[ResolverDomain]:
    """Variable valid domains used by resolver mapping harnesses."""

    return st.builds(
        ResolverDomain,
        repository=_valid_repositories(),
        pr_number=_valid_numbers().map(int),
        host=_valid_hosts(),
        thread_ids=st.lists(
            _valid_thread_ids(),
            min_size=10,
            max_size=10,
            unique=True,
        ).map(tuple),
        comment_ids=st.lists(
            _valid_thread_ids(),
            min_size=10,
            max_size=10,
            unique=True,
        ).map(tuple),
        database_ids=st.lists(
            _valid_numbers().map(int),
            min_size=10,
            max_size=10,
            unique=True,
        ).map(tuple),
        cursors=st.lists(
            _valid_cursors(),
            min_size=2,
            max_size=2,
            unique=True,
        ).map(tuple),
    )


def malformed_resolver_argvs() -> SearchStrategy[tuple[str, ...]]:
    """Generated malformed CLI argv domains for the resolver boundary."""

    repository_option = _source_string("REPOSITORY_OPTION")
    pull_request_option = _source_string("PULL_REQUEST_OPTION")
    review_comment_id_option = _source_string("REVIEW_COMMENT_ID_OPTION")
    host_option = _source_string("HOST_OPTION")

    return st.one_of(
        st.just(()),
        _valid_repositories().map(lambda repository: (repository_option, repository)),
        st.tuples(_valid_repositories(), _valid_numbers()).map(
            lambda values: (
                repository_option,
                values[0],
                pull_request_option,
                values[1],
            )
        ),
        _valid_numbers().map(lambda number: (pull_request_option, number)),
        _valid_comment_ids().map(
            lambda comment_id: (review_comment_id_option, comment_id)
        ),
        _invalid_thread_ids().map(lambda value: (value,)),
        st.tuples(
            _invalid_repositories(),
            _valid_numbers(),
            _valid_comment_ids(),
        ).map(
            lambda values: (
                repository_option,
                values[0],
                pull_request_option,
                values[1],
                review_comment_id_option,
                values[2],
            )
        ),
        st.tuples(
            _valid_repositories(),
            _invalid_numbers(),
            _valid_comment_ids(),
        ).map(
            lambda values: (
                repository_option,
                values[0],
                pull_request_option,
                values[1],
                review_comment_id_option,
                values[2],
            )
        ),
        st.tuples(
            _valid_repositories(),
            _valid_numbers(),
            _invalid_comment_ids(),
        ).map(
            lambda values: (
                repository_option,
                values[0],
                pull_request_option,
                values[1],
                review_comment_id_option,
                values[2],
            )
        ),
        st.tuples(_invalid_hosts(), _valid_thread_ids()).map(
            lambda values: (
                host_option,
                values[0],
                values[1],
            )
        ),
        st.tuples(
            _valid_thread_ids(),
            _valid_repositories(),
            _valid_numbers(),
            _valid_comment_ids(),
        ).map(
            lambda values: (
                values[0],
                repository_option,
                values[1],
                pull_request_option,
                values[2],
                review_comment_id_option,
                values[3],
            )
        ),
    )


def _validate_mapping_domain(domain: ResolverDomain) -> None:
    values_by_pattern = (
        ("REPOSITORY_PATTERN", (domain.repository,)),
        ("NUMBER_PATTERN", (str(domain.pr_number), *map(str, domain.database_ids))),
        ("HOST_PATTERN", (domain.host,)),
        ("NODE_ID_PATTERN", (*domain.thread_ids, *domain.comment_ids)),
        ("CURSOR_PATTERN", domain.cursors),
    )
    for pattern_name, values in values_by_pattern:
        pattern = _pattern(pattern_name)
        if any(pattern.fullmatch(value) is None for value in values):
            raise RuntimeError(
                f"resolver mapping domain violates source pattern {pattern_name}"
            )


def _invalid_thread_ids() -> SearchStrategy[str]:
    return _strings_outside_pattern(_pattern("NODE_ID_PATTERN"))


def _invalid_repositories() -> SearchStrategy[str]:
    return _strings_outside_pattern(_pattern("REPOSITORY_PATTERN"))


def _invalid_numbers() -> SearchStrategy[str]:
    return _strings_outside_pattern(_pattern("NUMBER_PATTERN"))


def _invalid_comment_ids() -> SearchStrategy[str]:
    number_pattern = _pattern("NUMBER_PATTERN")
    node_id_pattern = _pattern("NODE_ID_PATTERN")
    return st.text(max_size=32).filter(
        lambda value: (
            number_pattern.fullmatch(value) is None
            and node_id_pattern.fullmatch(value) is None
        )
    )


def _invalid_hosts() -> SearchStrategy[str]:
    return _strings_outside_pattern(_pattern("HOST_PATTERN"))


def _valid_thread_ids() -> SearchStrategy[str]:
    return _strings_inside_pattern(_pattern("NODE_ID_PATTERN"))


def _valid_repositories() -> SearchStrategy[str]:
    return _strings_inside_pattern(_pattern("REPOSITORY_PATTERN"))


def _valid_numbers() -> SearchStrategy[str]:
    return _strings_inside_pattern(_pattern("NUMBER_PATTERN"))


def _valid_comment_ids() -> SearchStrategy[str]:
    return st.one_of(_valid_numbers(), _valid_thread_ids())


def _valid_cursors() -> SearchStrategy[str]:
    return _strings_inside_pattern(_pattern("CURSOR_PATTERN"))


def _valid_hosts() -> SearchStrategy[str]:
    return _strings_inside_pattern(_pattern("HOST_PATTERN"))


def _strings_inside_pattern(pattern: re.Pattern[str]) -> SearchStrategy[str]:
    return st.from_regex(pattern, fullmatch=True)


def _strings_outside_pattern(pattern: re.Pattern[str]) -> SearchStrategy[str]:
    return st.text(max_size=32).filter(lambda value: pattern.fullmatch(value) is None)


def _pattern(name: str) -> re.Pattern[str]:
    value = getattr(_load_script(), name)
    if not isinstance(value, re.Pattern):
        raise RuntimeError(f"resolve_review_thread.{name} must be a regex pattern")
    return value


def _source_string(name: str) -> str:
    value = getattr(_load_script(), name)
    if not isinstance(value, str):
        raise RuntimeError(f"resolve_review_thread.{name} must be a string")
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
