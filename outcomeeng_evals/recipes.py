"""Contract of the repository-local eval Just recipes.

The ``justfile`` recipes that run and materialize evals take their names,
environment overrides, default plugin directory, and printed ``Running:`` line
from this module, so the recipe file and every reader of its output share one
owner.
"""

from __future__ import annotations

import shlex
from collections.abc import Sequence
from typing import Final

from outcomeeng_evals.definition import parse_profile, profile_model_selection

EVAL_RECIPE: Final = "eval"
EVAL_CASE_RECIPE: Final = "eval-case"
EVAL_NODE_RECIPE: Final = "eval-node"
MATERIALIZE_PROMPTS_RECIPE: Final = "eval-materialize-prompts"
MATERIALIZE_PROMPTS_CHECK_RECIPE: Final = "eval-materialize-prompts-check"

# Environment variables that override a suite's declared profile and plugin dir.
EVAL_PROFILE_ENV: Final = "EVAL_PROFILE"
PLUGIN_DIR_ENV: Final = "PLUGIN_DIR"
# Plugin directory the recipes use when an eval.toml declares none.
DEFAULT_RECIPE_PLUGIN_DIR: Final = "dist/claude/spec-tree"

RUNNING_LINE_PREFIX: Final = "Running:"
PROFILE_SELECTION_SEGMENT: Final = (
    "  # profile {profile}: model {model}, effort {effort}"
)


def render_running_line(command: Sequence[str], profile_text: str) -> str:
    """Render the line a recipe prints before it runs ``command``.

    The line quotes every argument for the shell and names the selected
    profile with the Claude model and effort the eval definition holds for it.
    An unsupported profile raises ``ValueError`` naming ``EVAL_PROFILE_ENV``,
    so the recipe stops before it prints or runs anything.
    """

    profile = parse_profile(profile_text, EVAL_PROFILE_ENV)
    selection = profile_model_selection(profile)
    quoted = "".join(f" {shlex.quote(argument)}" for argument in command)
    segment = PROFILE_SELECTION_SEGMENT.format(
        profile=profile, model=selection.model, effort=selection.effort
    )
    return f"{RUNNING_LINE_PREFIX}{quoted}{segment}"
