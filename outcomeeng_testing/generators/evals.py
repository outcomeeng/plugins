"""Hypothesis strategies for eval harness contracts."""

from __future__ import annotations

import string
from pathlib import Path
from typing import Any

from hypothesis import strategies as st
from hypothesis.strategies import SearchStrategy

from outcomeeng_evals.ci_execution import CiRunSettings
from outcomeeng_evals.ci_plan import EvalPlanItem
from outcomeeng_evals.case import (
    CASE_ID_FIELD,
    CASE_INPUT_FIELD,
    EXPECTED_VERDICT_FIELD,
    MAX_EXPECTED_LIST_LENGTH,
    MUST_CONTAIN_FIELD,
)
from outcomeeng_evals.definition import (
    OWNED_PATH_ALPHABET,
    OWNED_PATH_RECURSIVE_SUFFIX,
)
from outcomeeng_evals.producer_prompt import MATERIALIZED_PROMPT_FILENAME

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


def owned_path_violating_characters() -> SearchStrategy[str]:
    """Characters an owned path may not carry, drawn from the open complement.

    The alphabet is an allowlist, so the domain it rejects is every character
    outside it rather than an enumerable set of globs. The strategy searches
    that domain instead of naming members of it, and it is bounded only by what
    UTF-8 encodes — the reachable input, since a TOML basic string carries
    control characters, `NUL`, and non-ASCII alike into the loader.
    """

    return st.characters(codec="utf-8").filter(
        lambda character: OWNED_PATH_ALPHABET.fullmatch(character) is None
    )


def owned_paths_violating_alphabet() -> SearchStrategy[str]:
    """Owned paths whose body carries a character outside the alphabet."""

    return st.builds(
        lambda prefix, character, suffix: (
            f"{prefix}/{character}/{suffix}{OWNED_PATH_RECURSIVE_SUFFIX}"
        ),
        prefix=_path_segments(),
        character=owned_path_violating_characters(),
        suffix=_path_segments(),
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


def expected_list_boundary_record(*, over_limit: bool) -> dict[str, Any]:
    """Build the exact and first-invalid expectation-list boundary records."""

    length = MAX_EXPECTED_LIST_LENGTH + int(over_limit)
    return {
        CASE_ID_FIELD: f"expected-list-{length}",
        CASE_INPUT_FIELD: {},
        EXPECTED_VERDICT_FIELD: {
            MUST_CONTAIN_FIELD: [
                {
                    "findings": [
                        {"rule": f"generated-rule-{index}"} for index in range(length)
                    ]
                }
            ]
        },
    }


def producer_rule_texts() -> SearchStrategy[str]:
    """Generated producer-section prose without XML delimiter characters."""

    return st.text(
        alphabet=st.characters(
            blacklist_categories=("Cc", "Cs"),
            blacklist_characters=("<", ">", "\x00"),
        ),
        min_size=1,
        max_size=80,
    )


def distinct_producer_rule_texts() -> SearchStrategy[tuple[str, str, str]]:
    """Three distinct generated producer-section bodies."""

    return st.tuples(
        producer_rule_texts(),
        producer_rule_texts(),
        producer_rule_texts(),
    ).filter(lambda values: len(set(values)) == len(values))


def noncanonical_prompt_filenames() -> SearchStrategy[str]:
    """Generated Markdown names outside the source-owned prompt filename."""

    return st.from_regex(
        r"[a-z][a-z0-9_-]{0,20}\.md",
        fullmatch=True,
    ).filter(lambda value: value != MATERIALIZED_PROMPT_FILENAME)


def absent_section_name(section_name: str, producer_text: str) -> str:
    """Derive a section name outside one producer's observed names."""

    candidate = section_name + section_name
    while candidate in producer_text:
        candidate += section_name
    return candidate


def unsupported_prompt_source_kind(supported_kinds: tuple[str, ...]) -> str:
    """Derive a non-empty kind outside the complete source-owned kind set."""

    candidate = "".join(supported_kinds)
    if candidate in supported_kinds:
        candidate += candidate
    return candidate


def missing_producer_path(existing_path: str) -> str:
    """Derive an absent sibling path from one existing producer path."""

    path = Path(existing_path)
    return str(path.with_name(path.name + path.name))


def outside_repository_path(existing_path: str) -> str:
    """Derive a parent-traversing path from one existing producer path."""

    return str(Path("..") / Path(existing_path).name)


def outside_eval_prompt_path(prompt_filename: str) -> str:
    """Derive a prompt path outside its eval directory."""

    return str(Path("..") / ".." / prompt_filename)
