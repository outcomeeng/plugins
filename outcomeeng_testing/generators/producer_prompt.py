"""Generated domains for producer-derived prompt properties."""

from __future__ import annotations

from dataclasses import dataclass

from hypothesis import strategies as st
from hypothesis.strategies import SearchStrategy

from outcomeeng_evals.producer_prompt import MATERIALIZED_PROMPT_FILENAME


@dataclass(frozen=True)
class ProducerFileMutation:
    """One generated mutation of a producer in an ordered source set."""

    producer_index: int
    suffix: str


@dataclass(frozen=True)
class SelectedSectionMutation:
    """Generated selected-section and surrounding-section changes."""

    selected_rule: str
    updated_selected_rule: str
    unrelated_rule: str
    updated_unrelated_rule: str


@dataclass(frozen=True)
class NoncanonicalPromptPath:
    """One generated noncanonical materialized-prompt path."""

    prompt_path: str


@dataclass(frozen=True)
class WholeProducerMutation:
    """One generated whole-producer text mutation."""

    suffix: str


_PRODUCER_TEXT = st.text(
    alphabet=st.characters(
        blacklist_categories=("Cc", "Cs"),
        blacklist_characters=["\x00"],
    ),
    min_size=1,
    max_size=64,
)
_RULE_TEXT = st.text(
    alphabet=st.characters(
        blacklist_categories=("Cc", "Cs"),
        blacklist_characters=["<", ">", "\x00"],
    ),
    min_size=1,
    max_size=80,
)
_RULE_TOKEN = st.text(
    alphabet=st.characters(whitelist_categories=("Ll", "Lu", "Nd")),
    min_size=1,
    max_size=32,
)


def producer_file_mutations(
    producer_count: int,
) -> SearchStrategy[ProducerFileMutation]:
    """Mutations selecting every valid producer index and variable suffix text."""
    return st.builds(
        ProducerFileMutation,
        producer_index=st.integers(min_value=0, max_value=producer_count - 1),
        suffix=_PRODUCER_TEXT,
    )


def selected_section_mutations() -> SearchStrategy[SelectedSectionMutation]:
    """Mutations that vary selected and unrelated producer-section text."""

    def build(
        token: str, unrelated: str, updated_unrelated: str
    ) -> SelectedSectionMutation:
        return SelectedSectionMutation(
            selected_rule=f"selected-token-{token}-end",
            updated_selected_rule=f"updated-token-{token}-end",
            unrelated_rule=unrelated,
            updated_unrelated_rule=updated_unrelated,
        )

    return st.builds(build, _RULE_TOKEN, _RULE_TEXT, _RULE_TEXT)


def noncanonical_prompt_paths() -> SearchStrategy[NoncanonicalPromptPath]:
    """Repository-local markdown names other than the canonical prompt name."""
    return st.builds(
        NoncanonicalPromptPath,
        prompt_path=st.from_regex(
            r"[a-z][a-z0-9_-]{0,20}\.md",
            fullmatch=True,
        ).filter(lambda value: value != MATERIALIZED_PROMPT_FILENAME),
    )


def whole_producer_mutations() -> SearchStrategy[WholeProducerMutation]:
    """Variable text mutations for one complete producer body."""
    return st.builds(WholeProducerMutation, suffix=_RULE_TEXT)
