"""Hypothesis strategies for validation gate recipe steps."""

from __future__ import annotations

from pathlib import Path, PurePosixPath

from hypothesis import strategies as st
from hypothesis.strategies import SearchStrategy

from outcomeeng.validation import EVAL_TRIGGER_WORKFLOW, Step
from outcomeeng.validation._steps import EVALS_ROOT
from outcomeeng.validation.profile_configuration import eval_configuration_files
from outcomeeng_evals.definition import EVAL_TOML_FILENAME
from outcomeeng.validation.selected_gate import (
    CHECK_WORKFLOW_PATH,
    INSTRUCTION_BLOCK_SOURCE_PATH,
    PYPROJECT_PATH,
    ROOT_README_PATH,
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
# that owns it rather than a copied literal. The literal paths above are
# arbitrary representatives of a glob domain and own their own values.
SELECTED_GATE_EVAL_WORKFLOW_PATH = EVAL_TRIGGER_WORKFLOW
REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


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


# An eval definition the configuration guard reads. Selecting the runtime-token
# step depends on the definition existing in the checkout, so the value comes
# from the guard's own domain rather than an arbitrary glob representative.
SELECTED_GATE_EVAL_DEFINITION_PATH = next(
    path
    for path in guarded_eval_configuration_paths()
    if PurePosixPath(path).name == EVAL_TOML_FILENAME
)
SELECTED_GATE_CHECK_WORKFLOW_PATH = CHECK_WORKFLOW_PATH
SELECTED_GATE_FULL_GATE_PATH = PYPROJECT_PATH

# Representatives whose selection follows from the path-category lanes alone:
# none is a full-gate surface, an assertion test, or test infrastructure.
SELECTED_GATE_LANE_PATH_EXAMPLES = (
    SELECTED_GATE_PYTHON_SOURCE_PATH,
    SELECTED_GATE_MARKDOWN_PATH,
    SELECTED_GATE_README_PATH,
    SELECTED_GATE_SPX_CONFIG_PATH,
    SELECTED_GATE_INSTRUCTION_BLOCK_SOURCE_PATH,
    SELECTED_GATE_SKILL_PATH,
    SELECTED_GATE_PLUGIN_SCRIPT_PATH,
    SELECTED_GATE_SHARED_SOURCE_PATH,
    SELECTED_GATE_TEMPLATE_SCRIPT_PATH,
    SELECTED_GATE_WORKFLOW_PATH,
    SELECTED_GATE_EVAL_WORKFLOW_PATH,
    SELECTED_GATE_EVAL_DEFINITION_PATH,
)

SELECTED_GATE_CHANGED_PATH_EXAMPLES = (
    SELECTED_GATE_PYTHON_SOURCE_PATH,
    SELECTED_GATE_PYTHON_TEST_PATH,
    SELECTED_GATE_MARKDOWN_PATH,
    SELECTED_GATE_README_PATH,
    SELECTED_GATE_SPX_CONFIG_PATH,
    SELECTED_GATE_INSTRUCTION_BLOCK_SOURCE_PATH,
    SELECTED_GATE_SKILL_PATH,
    SELECTED_GATE_PLUGIN_SCRIPT_PATH,
    SELECTED_GATE_SHARED_SOURCE_PATH,
    SELECTED_GATE_WORKFLOW_PATH,
    SELECTED_GATE_EVAL_WORKFLOW_PATH,
    SELECTED_GATE_EVAL_DEFINITION_PATH,
    SELECTED_GATE_CHECK_WORKFLOW_PATH,
    SELECTED_GATE_FULL_GATE_PATH,
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
        st.sampled_from(SELECTED_GATE_CHANGED_PATH_EXAMPLES),
        min_size=1,
    )


def path_from_pattern(pattern: str) -> str:
    """Construct a path in one source-declared glob category.

    Wildcard contents are incidental; the caller enumerates the complete
    source-owned category set instead of choosing representative categories.
    """
    return pattern.replace("**", "generated/nested").replace("*", "generated")
