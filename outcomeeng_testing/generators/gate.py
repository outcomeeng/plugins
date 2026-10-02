"""Hypothesis strategies and category paths for validation gate evidence."""

from __future__ import annotations

import re
import string
from typing import Final

from hypothesis import strategies as st
from hypothesis.strategies import SearchStrategy

from outcomeeng.validation import Step
from outcomeeng.validation.selected_gate import PATH_CATEGORY_PATTERNS, PathCategory

RECURSIVE_WILDCARD: Final = "**"
SEGMENT_WILDCARD: Final = "*"
PATH_SEPARATOR: Final = "/"
PLACEHOLDER_SEGMENT: Final = "generated"
PLACEHOLDER_NESTED_SEGMENTS: Final = f"{PLACEHOLDER_SEGMENT}/nested"
_WILDCARD_SPLIT: Final = re.compile(r"(\*\*|\*)")
# Generated wildcard contents: one path segment drawn from characters that carry
# no glob or separator meaning, and one to three such segments for `**`.
SEGMENT_ALPHABET: Final = string.ascii_lowercase + string.digits + "-_."
MAX_SEGMENT_LENGTH: Final = 8
MAX_NESTED_SEGMENTS: Final = 3


def argvs() -> SearchStrategy[tuple[str, ...]]:
    """Command argv tuples for generated recipe steps."""

    return st.lists(st.text()).map(tuple)


def steps() -> SearchStrategy[Step]:
    """Generated validation step records over the Step model domain."""

    return st.builds(Step, label=st.text(), argv=argvs())


def step_lists() -> SearchStrategy[tuple[Step, ...]]:
    """Non-empty step lists."""

    return st.lists(
        steps(),
        min_size=1,
    ).map(tuple)


def path_from_pattern(pattern: str) -> str:
    """Construct a path in one source-declared glob category.

    Wildcard contents are incidental; the caller enumerates the complete
    source-owned category set instead of choosing representative categories.
    """
    return pattern.replace(RECURSIVE_WILDCARD, PLACEHOLDER_NESTED_SEGMENTS).replace(
        SEGMENT_WILDCARD, PLACEHOLDER_SEGMENT
    )


def category_path(category: PathCategory) -> str:
    """Return a path in ``category``, built from the category's first pattern."""

    return path_from_pattern(PATH_CATEGORY_PATTERNS[category][0])


def path_segments() -> SearchStrategy[str]:
    """One path segment free of separator and glob characters."""

    return st.text(
        alphabet=SEGMENT_ALPHABET, min_size=1, max_size=MAX_SEGMENT_LENGTH
    ).filter(lambda segment: segment not in {".", ".."})


def paths_in_pattern(pattern: str) -> SearchStrategy[str]:
    """Paths the glob ``pattern`` matches, with generated wildcard contents."""

    pieces: list[SearchStrategy[str]] = []
    for piece in _WILDCARD_SPLIT.split(pattern):
        if piece == RECURSIVE_WILDCARD:
            pieces.append(
                st.lists(path_segments(), min_size=1, max_size=MAX_NESTED_SEGMENTS).map(
                    PATH_SEPARATOR.join
                )
            )
        elif piece == SEGMENT_WILDCARD:
            pieces.append(path_segments())
        elif piece:
            pieces.append(st.just(piece))
    return st.tuples(*pieces).map("".join)


def category_paths() -> SearchStrategy[str]:
    """Paths in every changed-path category the selector classifies."""

    patterns = tuple(
        sorted(
            {
                pattern
                for category_patterns in PATH_CATEGORY_PATTERNS.values()
                for pattern in category_patterns
            }
        )
    )
    return st.sampled_from(patterns).flatmap(paths_in_pattern)


def selected_gate_changed_paths() -> SearchStrategy[list[str]]:
    """Changed-path lists drawn from every category the selector classifies."""

    return st.lists(category_paths(), min_size=1)


SELECTED_GATE_PYTHON_SOURCE_PATH: Final = category_path(PathCategory.PYTHON_TYPECHECK)
SELECTED_GATE_PYTHON_TEST_PATH: Final = category_path(
    PathCategory.PYTHON_ASSERTION_TEST
)
SELECTED_GATE_MARKDOWN_PATH: Final = category_path(PathCategory.MARKDOWN)
SELECTED_GATE_SKILL_PATH: Final = category_path(PathCategory.SKILL)
SELECTED_GATE_WORKFLOW_PATH: Final = category_path(PathCategory.WORKFLOW)
SELECTED_GATE_FULL_GATE_PATH: Final = category_path(PathCategory.FULL_GATE)
