"""Hypothesis strategies for validation gate recipe steps."""

from __future__ import annotations

from hypothesis import strategies as st
from hypothesis.strategies import SearchStrategy

from outcomeeng.validation import Step
from outcomeeng.validation.selected_gate import (
    PYTHON_ASSERTION_TEST_PATTERNS,
    PYTHON_PATTERNS,
    SKILL_PATTERNS,
    WORKFLOW_PATTERNS,
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


def selected_gate_changed_paths() -> SearchStrategy[list[str]]:
    """Changed-path lists that exercise selected local gate routing."""

    return st.lists(
        st.sampled_from(
            (
                PYTHON_PATTERNS[2],
                WORKFLOW_PATTERNS[0],
                PYTHON_ASSERTION_TEST_PATTERNS[0],
                SKILL_PATTERNS[0],
            )
        ),
        min_size=1,
    )
