"""Hypothesis strategies for eval harness contracts."""

from __future__ import annotations

import string
from pathlib import Path

from hypothesis import strategies as st
from hypothesis.strategies import SearchStrategy

from outcomeeng_evals.ci_execution import CiRunSettings
from outcomeeng_evals.ci_plan import EvalPlanItem

_PATH_ALPHABET = string.ascii_lowercase + string.digits + "-_"
_CASE_ID_ALPHABET = string.ascii_letters + string.digits + "-_"


def _path_segments() -> SearchStrategy[str]:
    return st.text(_PATH_ALPHABET, min_size=1, max_size=16)


def _case_ids() -> SearchStrategy[tuple[str, ...]]:
    return st.lists(
        st.text(_CASE_ID_ALPHABET, min_size=1, max_size=24),
        max_size=5,
    ).map(tuple)


def _eval_toml_paths() -> SearchStrategy[Path]:
    return st.lists(_path_segments(), min_size=1, max_size=4).map(
        lambda segments: Path("spx").joinpath(*segments, "eval.toml")
    )


def _plugin_dirs() -> SearchStrategy[Path]:
    return st.lists(_path_segments(), min_size=1, max_size=3).map(
        lambda segments: Path("dist").joinpath(*segments)
    )


def eval_plan_items() -> SearchStrategy[EvalPlanItem]:
    """Generated eval plan items for CI command mapping evidence."""

    return st.builds(
        EvalPlanItem,
        eval_toml=_eval_toml_paths(),
        plugin_dir=_plugin_dirs(),
        case_ids=_case_ids(),
    )


def ci_run_settings() -> SearchStrategy[CiRunSettings]:
    """Generated CI runtime settings for command mapping evidence."""

    return st.builds(
        CiRunSettings,
        workers=st.integers(min_value=1, max_value=64).map(str),
        max_budget_usd=st.decimals(
            min_value="0.01",
            max_value="25.00",
            places=2,
            allow_nan=False,
            allow_infinity=False,
        ).map(str),
        timeout_seconds=st.integers(min_value=1, max_value=3600).map(str),
    )
