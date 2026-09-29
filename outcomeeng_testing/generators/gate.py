"""Generated domains for validation gate steps and selected-gate changed paths.

Every changed path is constructed from a source-declared selection pattern,
exact path, or real repository module, so no path here is a hand-picked
representative. Wildcard segments carry generator-owned fill text.
"""

from __future__ import annotations

import os
import string
from collections.abc import Sequence
from pathlib import Path, PurePosixPath
from typing import Final, TypeVar

from hypothesis import strategies as st
from hypothesis.strategies import SearchStrategy

from outcomeeng.validation import (
    PURPOSE_CONFORMANCE,
    VERIFICATION_TYPE_VALIDATION,
    Recipe,
    Step,
)
from outcomeeng.validation._steps import EVALS_ROOT
from outcomeeng.validation.infrastructure_index import (
    EXECUTED_TEST_PREFIX,
    PYTHON_SUFFIX,
    SPEC_TREE_ROOT,
    InfrastructureIndex,
)
from outcomeeng.validation.profile_configuration import eval_configuration_files
from outcomeeng.validation.selected_gate import (
    DEFAULT_BASE_REF,
    DELETED_GIT_STATUS_PREFIX,
    FULL_GATE_PATTERNS,
    LIVE_DISCOVERY_PATTERNS,
    PYTHON_ASSERTION_TEST_PATTERNS,
    RENAMED_GIT_STATUS_PREFIX,
    COPIED_GIT_STATUS_PREFIX,
    SELECTION_LANES,
    TEST_INFRASTRUCTURE_PATTERNS,
    SelectionLane,
)
from outcomeeng_evals.definition import EVAL_TOML_FILENAME

REPOSITORY_ROOT: Final = Path(__file__).resolve().parents[2]

# Generator-owned fill text for glob wildcards. The characters are incidental;
# only the source-declared pattern around them decides the path's category.
GENERATED_SEGMENT: Final = "generated"
NESTED_SEGMENT: Final = "nested"
WHITESPACE_FILL: Final = " generated segment "
FILL_ALPHABET: Final = string.ascii_lowercase + string.digits
MAX_FILL_LENGTH: Final = 8

# Git's name-status vocabulary: `M` marks a modification, and a rename or copy
# carries its similarity score after the source-owned status prefix.
MODIFIED_GIT_STATUS: Final = "M"
FULL_SIMILARITY_SCORE: Final = "100"
RENAMED_GIT_STATUS: Final = f"{RENAMED_GIT_STATUS_PREFIX}{FULL_SIMILARITY_SCORE}"
COPIED_GIT_STATUS: Final = f"{COPIED_GIT_STATUS_PREFIX}{FULL_SIMILARITY_SCORE}"
DELETED_GIT_STATUS: Final = DELETED_GIT_STATUS_PREFIX

# Scripted child behavior for recording spawners. The text and the non-zero
# code are incidental: the orchestrator treats any output as opaque and any
# non-zero code as failure.
PASS_EXIT_CODE: Final = os.EX_OK
FAIL_EXIT_CODE: Final = 2
PASSING_CHILD_OUTPUT: Final = "passing validator output"
FAILING_CHILD_OUTPUT_PREFIX: Final = "failing validator output line"
SPAWN_FAILURE_MESSAGE: Final = "missing executable"
HIGH_VOLUME_LINE: Final = "captured child output"
HIGH_VOLUME_LINE_COUNT: Final = 200

# Scripted diagnostics for a failing git discovery command.
GIT_DISCOVERY_FAILURE_STDOUT: Final = "fatal: bad revision"
GIT_DISCOVERY_FAILURE_STDERR: Final = "fatal: ambiguous argument"


_Member = TypeVar("_Member")


class EmptyGeneratedDomain(RuntimeError):
    """A generated case domain came out empty, so it would collect no case."""

    def __init__(self, domain: str) -> None:
        self.domain = domain
        super().__init__(f"generated domain {domain!r} holds no case")


def required_domain(
    members: Sequence[_Member], domain: str = "cases"
) -> tuple[_Member, ...]:
    """Return ``members`` as a tuple, raising when it holds no case."""

    cases = tuple(members)
    if not cases:
        raise EmptyGeneratedDomain(domain)
    return cases


def high_volume_child_output() -> str:
    """Child output whose line count exceeds any per-step live status output."""

    return "\n".join(HIGH_VOLUME_LINE for _ in range(HIGH_VOLUME_LINE_COUNT))


def path_from_pattern(pattern: str, fill: str = GENERATED_SEGMENT) -> str:
    """Construct a path in one source-declared glob category.

    A recursive wildcard becomes two segments and a single wildcard becomes
    ``fill``; the surrounding pattern text is kept verbatim.
    """

    return pattern.replace("**", f"{fill}/{NESTED_SEGMENT}").replace("*", fill)


def pattern_representatives(patterns: Sequence[str]) -> tuple[str, ...]:
    """One constructed path per source-declared pattern, in declaration order."""

    return required_domain(
        tuple(dict.fromkeys(path_from_pattern(pattern) for pattern in patterns)),
        "pattern representatives",
    )


def selection_lane_paths(lane: SelectionLane) -> tuple[str, ...]:
    """Every path ``lane`` declares: one per glob pattern, then its exact paths."""

    return required_domain(
        tuple(
            dict.fromkeys(
                (
                    *(path_from_pattern(pattern) for pattern in lane.patterns),
                    *sorted(lane.paths),
                )
            )
        ),
        f"paths of the {lane.reason!r} lane",
    )


def lane_patterns() -> tuple[str, ...]:
    """Every glob pattern a selection lane declares, in lane order."""

    return tuple(
        dict.fromkeys(pattern for lane in SELECTION_LANES for pattern in lane.patterns)
    )


def selection_patterns() -> tuple[str, ...]:
    """Every source-declared changed-path pattern the planner consults."""

    return tuple(
        dict.fromkeys(
            (
                *lane_patterns(),
                *PYTHON_ASSERTION_TEST_PATTERNS,
                *FULL_GATE_PATTERNS,
                *LIVE_DISCOVERY_PATTERNS,
                *TEST_INFRASTRUCTURE_PATTERNS,
            )
        )
    )


def lane_paths() -> tuple[str, ...]:
    """One constructed path for each selection-lane pattern."""

    return pattern_representatives(lane_patterns())


def selection_paths() -> tuple[str, ...]:
    """One constructed path for every source-declared changed-path pattern."""

    return pattern_representatives(selection_patterns())


def assertion_test_paths(count: int) -> tuple[str, ...]:
    """``count`` distinct executed assertion-test paths.

    Paths cycle through the source-declared assertion-test patterns with a
    numbered fill, so every path is an assertion test and no two coincide.
    """

    patterns = required_domain(
        PYTHON_ASSERTION_TEST_PATTERNS, "assertion-test patterns"
    )
    return required_domain(
        tuple(
            path_from_pattern(
                patterns[index % len(patterns)], fill=f"{GENERATED_SEGMENT}{index}"
            )
            for index in range(count)
        ),
        "assertion-test paths",
    )


def distinct_changed_paths(count: int) -> tuple[str, ...]:
    """``count`` distinct changed paths cycling through every declared pattern."""

    patterns = required_domain(selection_patterns(), "selection patterns")
    return required_domain(
        tuple(
            path_from_pattern(
                patterns[index % len(patterns)], fill=f"{GENERATED_SEGMENT}{index}"
            )
            for index in range(count)
        ),
        "changed paths",
    )


def renamed_away_path(test_path: str) -> str:
    """The same directory entry without the executed-test filename prefix.

    Renaming an executed test to this path leaves no assertion test behind.
    """

    posix = PurePosixPath(test_path)
    return posix.with_name(posix.name.removeprefix(EXECUTED_TEST_PREFIX)).as_posix()


def whitespace_paths() -> tuple[str, ...]:
    """Each declared pattern filled with a space-bearing segment and padded."""

    return required_domain(
        tuple(
            dict.fromkeys(
                f" {path_from_pattern(pattern, fill=WHITESPACE_FILL)} "
                for pattern in selection_patterns()
            )
        ),
        "whitespace paths",
    )


def alternate_base_ref() -> str:
    """A remote-tracking base ref on the default remote other than the default."""

    remote = PurePosixPath(DEFAULT_BASE_REF).parts[0]
    return f"{remote}/{GENERATED_SEGMENT}"


def full_gate_paths() -> tuple[str, ...]:
    """One constructed path per full-gate surface pattern."""

    return pattern_representatives(FULL_GATE_PATTERNS)


def discovery_full_gate_paths() -> tuple[str, ...]:
    """Full-gate surfaces the live-discovery patterns also declare."""

    return pattern_representatives(
        tuple(
            pattern
            for pattern in FULL_GATE_PATTERNS
            if pattern in LIVE_DISCOVERY_PATTERNS
        )
    )


def unrelated_full_gate_paths() -> tuple[str, ...]:
    """Full-gate surfaces no live-discovery pattern declares."""

    return pattern_representatives(
        tuple(
            pattern
            for pattern in FULL_GATE_PATTERNS
            if pattern not in LIVE_DISCOVERY_PATTERNS
        )
    )


def spec_tree_paths(paths: Sequence[str]) -> tuple[str, ...]:
    """The members of ``paths`` under the spec-tree root."""

    return required_domain(
        tuple(path for path in paths if path.startswith(f"{SPEC_TREE_ROOT}/")),
        "spec-tree paths",
    )


def outside_spec_tree_paths(paths: Sequence[str]) -> tuple[str, ...]:
    """The members of ``paths`` outside the spec-tree root."""

    return required_domain(
        tuple(path for path in paths if not path.startswith(f"{SPEC_TREE_ROOT}/")),
        "paths outside the spec tree",
    )


class GuardedEvalConfigurationMissing(RuntimeError):
    """The checkout holds no file the runtime-token configuration guard reads."""

    def __init__(self, spec_root: Path) -> None:
        self.spec_root = spec_root
        super().__init__(
            f"no eval definition or declared prompt template under {spec_root}"
        )


def guarded_eval_configuration_paths() -> tuple[str, ...]:
    """Repository-relative files the runtime-token configuration guard reads.

    The domain comes from the guard's own file reader anchored at the repository
    root, so it does not depend on the working directory, and an empty domain
    raises rather than collecting no case.
    """
    spec_root = REPOSITORY_ROOT / EVALS_ROOT
    paths = tuple(
        path.relative_to(REPOSITORY_ROOT).as_posix()
        for path in eval_configuration_files(spec_root)
    )
    if not any(PurePosixPath(path).name == EVAL_TOML_FILENAME for path in paths):
        raise GuardedEvalConfigurationMissing(spec_root)
    return paths


def guarded_eval_definition_paths() -> tuple[str, ...]:
    """The eval definitions among the files the configuration guard reads."""

    return required_domain(
        tuple(
            path
            for path in guarded_eval_configuration_paths()
            if PurePosixPath(path).name == EVAL_TOML_FILENAME
        ),
        "eval definitions",
    )


def infrastructure_module_paths(index: InfrastructureIndex) -> tuple[str, ...]:
    """Repository-relative paths of the real test-infrastructure modules indexed."""

    return required_domain(
        tuple(
            sorted(
                path.relative_to(REPOSITORY_ROOT).as_posix()
                for path in (REPOSITORY_ROOT / index.package).rglob(f"*{PYTHON_SUFFIX}")
                if index.module_for_path(path.relative_to(REPOSITORY_ROOT).as_posix())
                in index.modules
            )
        ),
        "test-infrastructure modules",
    )


def validation_module_path(module_file: str) -> str:
    """Repository-relative path of a real validation-package module file."""

    return Path(module_file).resolve().relative_to(REPOSITORY_ROOT).as_posix()


def three_no_op_steps() -> tuple[Step, ...]:
    """Three distinct steps for orchestrator scenario tests."""

    return tuple(
        Step(
            label=f"{GENERATED_SEGMENT}-{index}", argv=(f"{GENERATED_SEGMENT}-{index}",)
        )
        for index in range(3)
    )


def single_step_recipe(name: str) -> Recipe:
    """Recipe named ``name`` with one preflight and one recipe step."""

    return Recipe(
        name=name,
        verification_type=VERIFICATION_TYPE_VALIDATION,
        purpose=PURPOSE_CONFORMANCE,
        preflight_steps=(Step(label=f"{name}-preflight", argv=(f"{name}-preflight",)),),
        steps=(Step(label=f"{name}-step", argv=(f"{name}-step",)),),
    )


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


def filled_pattern_paths() -> SearchStrategy[str]:
    """A declared selection pattern with generated wildcard fill text."""

    return st.tuples(
        st.sampled_from(selection_patterns()),
        st.text(alphabet=FILL_ALPHABET, min_size=1, max_size=MAX_FILL_LENGTH),
    ).map(lambda case: path_from_pattern(case[0], fill=case[1]))


def selected_gate_changed_paths(
    infrastructure_paths: Sequence[str],
) -> SearchStrategy[list[str]]:
    """Changed-path lists over every declared category and real module.

    Paths come from the declared selection patterns with generated fills, the
    files the eval configuration guard reads, and ``infrastructure_paths`` —
    real test-infrastructure modules whose reach the index decides.
    """

    return st.lists(
        st.one_of(
            filled_pattern_paths(),
            st.sampled_from(guarded_eval_configuration_paths()),
            st.sampled_from(tuple(infrastructure_paths)),
        ),
        min_size=1,
    )
