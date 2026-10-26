"""Hypothesis strategies and category paths for validation gate evidence."""

from __future__ import annotations

import re
import string
from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final

from hypothesis import strategies as st
from hypothesis.strategies import SearchStrategy

from outcomeeng.distribution.contracts import INSTRUCTION_BLOCK_ARGV
from outcomeeng.validation import (
    ACTIONLINT_ARGV,
    EVAL_LINKS_ARGV,
    EVAL_PROMPTS_ARGV,
    EVAL_TRIGGERS_ARGV,
    EXECUTION_LEVELS,
    FMT_CHECK_ARGV,
    L3_LEVEL,
    MYPY_ARGV,
    PYRIGHT_ARGV,
    RUFF_CHECK_ARGV,
    RUFF_FORMAT_ARGV,
    SHELLCHECK_ARGV,
    SPX_MARKDOWN_ARGV,
    VALIDATION_STEPS,
    Step,
)
from outcomeeng.validation.infrastructure_index import (
    EXECUTED_TEST_PREFIX,
    PYTHON_SUFFIX,
    PRODUCT_TREE_ROOT,
    TESTS_DIRECTORY_NAME,
)
from outcomeeng.validation.selected_gate import (
    EVAL_REASON,
    EVIDENCE_LINK_REASON,
    INSTRUCTION_BLOCK_REASON,
    MARKDOWN_REASON,
    PATH_CATEGORY_PATTERNS,
    PYTHON_REASON,
    SKILL_REASON,
    SKILL_STEP_LABELS,
    WORKFLOW_REASON,
    PathCategory,
)

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
# A test-file name carries its subject, evidence, level, and runner as
# dot-separated tokens, so a token holds no dot.
TEST_FILE_TOKEN_ALPHABET: Final = string.ascii_lowercase + string.digits + "_"
MAX_TEST_FILE_TOKEN_LENGTH: Final = 8
MAX_TEST_FILES: Final = 12
# The violating L3 fixture composes one test file at every execution
# level, in two nested nodes and in the top-level test root, with and without a
# runner segment.
L3_FIXTURE_DIRECTORIES: Final = (
    f"{PRODUCT_TREE_ROOT}/21-first.enabler",
    f"{PRODUCT_TREE_ROOT}/32-second.enabler/21-nested.enabler",
    f"{PRODUCT_TREE_ROOT}/43-dotted.{L3_LEVEL}.enabler",
    TESTS_DIRECTORY_NAME,
)
L3_FIXTURE_SUBJECT: Final = "case"
L3_DECOY_SUBJECT: Final = "helper"
# Evidence and runner tokens that equal the L3 level sit at every level, so
# a file carries the level in a segment other than the third at the levels
# outside the suite.
L3_FIXTURE_VARIANTS: Final = (
    ("scenario", None),
    ("property", "runner"),
    (L3_LEVEL, None),
    ("scenario", L3_LEVEL),
)


def argvs() -> SearchStrategy[tuple[str, ...]]:
    """Command argv tuples for generated recipe steps."""

    return st.lists(st.text()).map(tuple)


# A step label stays on the one status line and timing row the gate prints for
# it; every character str.splitlines breaks on falls in these categories.
STEP_LABEL_EXCLUDED_CATEGORIES: Final = ("Cc", "Zl", "Zp")


def steps() -> SearchStrategy[Step]:
    """Generated validation step records over the Step model domain."""

    return st.builds(
        Step,
        label=st.text(
            alphabet=st.characters(
                codec="utf-8", exclude_categories=STEP_LABEL_EXCLUDED_CATEGORIES
            )
        ),
        argv=argvs(),
    )


def step_lists() -> SearchStrategy[tuple[Step, ...]]:
    """Non-empty step lists."""

    return st.lists(
        steps(),
        min_size=1,
    ).map(tuple)


# Every interval between two consecutive clock reads spans at least one whole
# second, so a step's elapsed value stays nonzero after rounding to seconds.
MIN_CLOCK_INCREMENT_SECONDS: Final = 1.0
MAX_CLOCK_INCREMENT_SECONDS: Final = 3600.0
MAX_CLOCK_INCREMENTS: Final = 8


def clock_increments() -> SearchStrategy[tuple[float, ...]]:
    """Positive per-read advances of a controlled monotonic clock."""

    return st.lists(
        st.floats(
            min_value=MIN_CLOCK_INCREMENT_SECONDS,
            max_value=MAX_CLOCK_INCREMENT_SECONDS,
            allow_nan=False,
            allow_infinity=False,
        ),
        min_size=1,
        max_size=MAX_CLOCK_INCREMENTS,
    ).map(tuple)


@dataclass(frozen=True)
class GeneratedTestFile:
    """A generated test-file path and the execution level it was composed at."""

    path: str
    level: str


def test_file_tokens() -> SearchStrategy[str]:
    """One dot-free token of a test-file name."""

    return st.text(
        alphabet=TEST_FILE_TOKEN_ALPHABET,
        min_size=1,
        max_size=MAX_TEST_FILE_TOKEN_LENGTH,
    )


def _compose_test_file(
    directory: str, subject: str, evidence: str, level: str, runner: str | None
) -> GeneratedTestFile:
    name = (
        ".".join(
            (
                f"{EXECUTED_TEST_PREFIX}{subject}",
                evidence,
                level,
                *((runner,) if runner is not None else ()),
            )
        )
        + PYTHON_SUFFIX
    )
    return GeneratedTestFile(
        path=PATH_SEPARATOR.join((directory, TESTS_DIRECTORY_NAME, name)), level=level
    )


def l3_fixture_files() -> tuple[GeneratedTestFile, ...]:
    """The violating whole-payload fixture the exclusion must filter.

    Every execution level appears in every directory with and without a runner
    segment, so the files at the L3 level lie beside files of every
    other level in each directory a recipe collects.
    """

    return tuple(
        _compose_test_file(directory, L3_FIXTURE_SUBJECT, evidence, level, runner)
        for directory in L3_FIXTURE_DIRECTORIES
        for level in EXECUTION_LEVELS
        for evidence, runner in L3_FIXTURE_VARIANTS
    )


def l3_decoy_files() -> tuple[GeneratedTestFile, ...]:
    """Python files at the L3 level whose names are not test-file names."""

    return tuple(
        GeneratedTestFile(
            path=PATH_SEPARATOR.join(
                (
                    directory,
                    TESTS_DIRECTORY_NAME,
                    f"{L3_DECOY_SUBJECT}.scenario.{L3_LEVEL}{PYTHON_SUFFIX}",
                )
            ),
            level=L3_LEVEL,
        )
        for directory in L3_FIXTURE_DIRECTORIES
    )


def generated_test_files() -> SearchStrategy[GeneratedTestFile]:
    """Test files composed at every execution level, with and without a runner."""

    return st.builds(
        _compose_test_file,
        directory=st.lists(
            path_segments(), min_size=1, max_size=MAX_NESTED_SEGMENTS
        ).map(PATH_SEPARATOR.join),
        subject=test_file_tokens(),
        evidence=test_file_tokens(),
        level=st.sampled_from(EXECUTION_LEVELS),
        runner=st.none() | test_file_tokens(),
    )


def generated_test_file_sets() -> SearchStrategy[list[GeneratedTestFile]]:
    """Distinct test files drawn across every execution level."""

    return st.lists(
        generated_test_files(),
        max_size=MAX_TEST_FILES,
        unique_by=lambda test_file: test_file.path,
    )


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


def category_patterns() -> tuple[str, ...]:
    """Every glob pattern of every changed-path category, each once, sorted."""

    return tuple(
        sorted(
            {
                pattern
                for category_patterns in PATH_CATEGORY_PATTERNS.values()
                for pattern in category_patterns
            }
        )
    )


def category_paths() -> SearchStrategy[str]:
    """Paths in every changed-path category the selector classifies."""

    return st.sampled_from(category_patterns()).flatmap(paths_in_pattern)


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


LaneSteps = frozenset[tuple[tuple[str, ...], str]]


def _lane(argvs: tuple[tuple[str, ...], ...], reason: str) -> LaneSteps:
    return frozenset((argv, reason) for argv in argvs)


def declared_lane_steps() -> Mapping[PathCategory, LaneSteps]:
    """The validation steps and reason each lane-bearing category selects.

    Each entry transcribes the category-to-step correspondence the selected-gate
    spec declares, built from the exported step commands and reasons and never
    from the planner's own lane table, so a changed lane fails the comparison.
    The skill lane is the set of validation steps the gate names as its skill
    surface.
    """

    skill_argvs = tuple(
        step.argv for step in VALIDATION_STEPS if step.label in SKILL_STEP_LABELS
    )
    return MappingProxyType(
        {
            PathCategory.MARKDOWN: _lane(
                (FMT_CHECK_ARGV, SPX_MARKDOWN_ARGV), MARKDOWN_REASON
            ),
            PathCategory.WORKFLOW: _lane(
                (ACTIONLINT_ARGV, SHELLCHECK_ARGV), WORKFLOW_REASON
            ),
            PathCategory.PYTHON_FORMAT_LINT: _lane(
                (RUFF_FORMAT_ARGV, RUFF_CHECK_ARGV), PYTHON_REASON
            ),
            PathCategory.PYTHON_TYPECHECK: _lane(
                (MYPY_ARGV, PYRIGHT_ARGV), PYTHON_REASON
            ),
            PathCategory.SKILL: _lane(skill_argvs, SKILL_REASON),
            PathCategory.INSTRUCTION_BLOCK: _lane(
                (INSTRUCTION_BLOCK_ARGV,), INSTRUCTION_BLOCK_REASON
            ),
            PathCategory.EVAL_TRIGGER: _lane((EVAL_TRIGGERS_ARGV,), EVAL_REASON),
            PathCategory.EVAL_PROMPT: _lane((EVAL_PROMPTS_ARGV,), EVAL_REASON),
            PathCategory.EVIDENCE_LINK: _lane((EVAL_LINKS_ARGV,), EVIDENCE_LINK_REASON),
        }
    )
