"""Hypothesis strategy for changesets every changed path of which a Markdown lane covers."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Final

from hypothesis import strategies as st
from hypothesis.strategies import SearchStrategy

from outcomeeng.validation.selected_gate import PATH_CATEGORY_PATTERNS
from outcomeeng_testing.generators.gate import (
    MAX_NESTED_SEGMENTS,
    PATH_SEPARATOR,
    RECURSIVE_WILDCARD,
    path_from_pattern,
    path_segments,
)

MARKDOWN_SUFFIX: Final = ".md"
MIN_CHANGESET_PATHS: Final = 1
MAX_CHANGESET_PATHS: Final = 6


def markdown_lane_path(prefixes: Sequence[str]) -> SearchStrategy[str]:
    """One Markdown path under a prefix a declared Markdown lane scopes.

    Each prefix is a directory prefix the lane declaration names, or the empty
    prefix for a Markdown file at the repository root. The path varies the
    prefix, the nesting depth, and every segment, and always ends in the
    Markdown suffix the lanes cover.
    """

    return st.builds(
        lambda prefix, directories, name: (
            PATH_SEPARATOR.join(
                (
                    *([prefix.rstrip(PATH_SEPARATOR)] if prefix else []),
                    *directories,
                    name,
                )
            )
            + MARKDOWN_SUFFIX
        ),
        st.sampled_from(tuple(prefixes)),
        st.lists(path_segments(), max_size=MAX_NESTED_SEGMENTS),
        path_segments(),
    )


def _under_lane_scope(path: str, prefixes: Sequence[str]) -> bool:
    return any(
        path.startswith(prefix) if prefix else PATH_SEPARATOR not in path
        for prefix in prefixes
    )


def category_markdown_paths(prefixes: Sequence[str]) -> tuple[str, ...]:
    """Markdown paths the selector's category patterns name inside a lane scope.

    Each pattern of every category yields one path when it names a Markdown
    file or a recursive directory, so fixed names such as the instruction-block
    source are reached alongside the free-form paths.
    """

    candidates = (
        path_from_pattern(pattern)
        + (MARKDOWN_SUFFIX if pattern.endswith(RECURSIVE_WILDCARD) else "")
        for patterns in PATH_CATEGORY_PATTERNS.values()
        for pattern in patterns
    )
    return tuple(
        path
        for path in candidates
        if path.endswith(MARKDOWN_SUFFIX) and _under_lane_scope(path, prefixes)
    )


def markdown_lane_changesets(prefixes: Sequence[str]) -> SearchStrategy[list[str]]:
    """Changesets whose every path lies under a declared Markdown lane scope."""

    return st.lists(
        st.one_of(
            markdown_lane_path(prefixes),
            st.sampled_from(category_markdown_paths(prefixes)),
        ),
        min_size=MIN_CHANGESET_PATHS,
        max_size=MAX_CHANGESET_PATHS,
    )
