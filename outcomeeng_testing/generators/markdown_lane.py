"""Hypothesis strategy for changesets every changed path of which a Markdown lane covers."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Final

from hypothesis import strategies as st
from hypothesis.strategies import SearchStrategy

from outcomeeng_testing.generators.gate import (
    MAX_NESTED_SEGMENTS,
    PATH_SEPARATOR,
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


def markdown_lane_changesets(prefixes: Sequence[str]) -> SearchStrategy[list[str]]:
    """Changesets whose every path lies under a declared Markdown lane scope."""

    return st.lists(
        markdown_lane_path(prefixes),
        min_size=MIN_CHANGESET_PATHS,
        max_size=MAX_CHANGESET_PATHS,
    )
