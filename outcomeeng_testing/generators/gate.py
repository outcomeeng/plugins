"""Hypothesis strategies for validation gate recipe steps."""

from __future__ import annotations

from hypothesis import strategies as st
from hypothesis.strategies import SearchStrategy

from outcomeeng.validation import EVAL_TRIGGER_WORKFLOW, Step
from outcomeeng.validation.agent_disable import DISABLE_VALUE
from outcomeeng.validation.selected_gate import (
    INSTRUCTION_BLOCK_SOURCE_PATH,
    PYPROJECT_PATH,
    ROOT_README_PATH,
    SELECTION_CATEGORY_PATTERNS,
    SPX_CONFIG_PATH,
)

SELECTED_GATE_PYTHON_SOURCE_PATH = "outcomeeng/hygiene/clean.py"
SELECTED_GATE_PYTHON_TEST_PATH = (
    "spx/15-validation.enabler/65-gate.enabler/21-selected-gate.enabler/"
    "tests/test_selected_gate.mapping.l1.py"
)
SELECTED_GATE_MARKDOWN_PATH = (
    "spx/15-validation.enabler/65-gate.enabler/21-selected-gate.enabler/"
    "selected-gate.md"
)
SELECTED_GATE_README_PATH = ROOT_README_PATH
SELECTED_GATE_SPX_CONFIG_PATH = SPX_CONFIG_PATH
SELECTED_GATE_INSTRUCTION_BLOCK_SOURCE_PATH = INSTRUCTION_BLOCK_SOURCE_PATH
SELECTED_GATE_SKILL_PATH = "src/plugins/spec-tree/skills/manage-pr/SKILL.md"
SELECTED_GATE_PLUGIN_SCRIPT_PATH = (
    "src/plugins/spec-tree/skills/manage-pr/scripts/resolve_review_thread.py"
)
SELECTED_GATE_SHARED_SOURCE_PATH = "src/_shared/spec-tree/instruction-block.md"
SELECTED_GATE_TEMPLATE_SCRIPT_PATH = "src/templates/plugin/scripts/place_agents.py"
SELECTED_GATE_WORKFLOW_PATH = "scripts/check.sh"
# An exact-match selection target, so the value comes from the source module
# that owns it rather than a copied literal. The other constants here are
# arbitrary representatives of a glob domain and own their own values.
SELECTED_GATE_EVAL_WORKFLOW_PATH = EVAL_TRIGGER_WORKFLOW
SELECTED_GATE_EVAL_DEFINITION_PATH = (
    "spx/21-spec-tree.enabler/76-merge.enabler/evals/transport-selection/eval.toml"
)
SELECTED_GATE_FULL_GATE_PATH = PYPROJECT_PATH

NON_DISABLING_SWITCH_VALUE = DISABLE_VALUE * 2
"""One value a switch can hold that declares no row optional.

Derived by repeating the source-owned disable value rather than written beside
it, so the value differs from it by construction — its length alone settles the
non-membership the domain below depends on — and it moves with the declaration
instead of standing next to it.
"""

SWITCH_ABSENT = None
"""The state of a switch the environment does not carry at all."""


def agent_switch_states() -> tuple[str | None, ...]:
    """The states an agent's switch can hold for one run.

    The three the run-versus-skip mapping ranges over: the source-owned disable
    value, a value derived to differ from it, and the switch absent. The value
    a state carries is derived from the declaration; what each state maps a row
    to belongs to the case that reads this domain.
    """
    return (DISABLE_VALUE, NON_DISABLING_SWITCH_VALUE, SWITCH_ABSENT)


def changed_path_domain() -> tuple[str, ...]:
    """One path per pattern of every category the selection source enumerates.

    The domain is derived rather than chosen, so a category added to
    `SELECTION_CATEGORY_PATTERNS` enters it without an edit here. Wildcard
    contents stay incidental: the property this domain feeds is insensitivity
    to path order and duplication, not any one path's shape.
    """
    return tuple(
        dict.fromkeys(
            path_from_pattern(pattern)
            for patterns in SELECTION_CATEGORY_PATTERNS
            for pattern in patterns
        )
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
        st.sampled_from(changed_path_domain()),
        min_size=1,
    )


def path_from_pattern(pattern: str) -> str:
    """Construct a path in one source-declared glob category.

    Wildcard contents are incidental; the caller enumerates the complete
    source-owned category set instead of choosing representative categories.
    """
    return pattern.replace("**", "generated/nested").replace("*", "generated")
