"""Generated domains for ``workflow_inspect.py`` evidence."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Literal

from hypothesis import strategies as st
from hypothesis.strategies import SearchStrategy

# Subcommands taking a positional number, each with the argv that precedes the value.
ID_SUBCOMMANDS: Final = ("run", "jobs", "log", "artifacts", "checks")

_NON_DIGIT_ALPHABET: Final = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_.,+ "
_NON_ASCII_DIGITS: Final = "٠١٢٣٤٥٦٧٨٩"
_ASCII_DIGITS: Final = "0123456789"
_SURROGATE_CATEGORY: Final[tuple[Literal["Cs"]]] = ("Cs",)
_TEXT_ALPHABET: Final = st.characters(blacklist_categories=_SURROGATE_CATEGORY)


@dataclass(frozen=True)
class LogCase:
    """Log text and the byte budget it is truncated against."""

    text: str
    max_bytes: int


def id_subcommands() -> SearchStrategy[str]:
    """Subcommands that take a run id or pull request number."""
    return st.sampled_from(ID_SUBCOMMANDS)


def invalid_numbers() -> SearchStrategy[str]:
    """Strings that are not positive integers, each invalid by construction.

    No value starts with a dash: the argument parser treats a dash-led token as an option.
    """
    return st.one_of(
        st.just(""),
        st.text(alphabet="0", min_size=1, max_size=6),
        st.text(alphabet=_NON_DIGIT_ALPHABET, min_size=1, max_size=12),
        st.text(alphabet=_NON_ASCII_DIGITS, min_size=1, max_size=8),
        st.tuples(
            st.text(alphabet=_ASCII_DIGITS, max_size=5),
            st.text(
                alphabet=_NON_DIGIT_ALPHABET.replace(" ", ""), min_size=1, max_size=3
            ),
            st.text(alphabet=_ASCII_DIGITS, max_size=5),
        ).map("".join),
        st.text(alphabet=_ASCII_DIGITS, min_size=1, max_size=6).map(
            lambda digits: f" {digits}"
        ),
    )


def valid_numbers() -> SearchStrategy[str]:
    """Positive integers written as ASCII digit strings."""
    return st.integers(min_value=1, max_value=10**9).map(str)


def non_positive_integers() -> SearchStrategy[int]:
    """Integers below 1, for the limit and byte-budget options."""
    return st.integers(max_value=0)


def failing_exit_codes() -> SearchStrategy[int]:
    """Nonzero ``gh`` exit codes other than the timeout code."""
    return st.one_of(
        st.integers(min_value=1, max_value=123),
        st.integers(min_value=125, max_value=255),
    )


def stderr_texts() -> SearchStrategy[str]:
    """Non-empty single-line diagnostics with no surrounding whitespace."""
    return st.text(
        alphabet=st.characters(blacklist_categories=("Cs", "Cc", "Zs", "Zl", "Zp")),
        min_size=1,
        max_size=40,
    )


def log_cases() -> SearchStrategy[LogCase]:
    """Log text with byte budgets spanning below, at, and above its encoded size."""

    @st.composite
    def build(draw: st.DrawFn) -> LogCase:
        text = draw(st.text(alphabet=_TEXT_ALPHABET, max_size=60))
        size = len(text.encode("utf-8"))
        budget = draw(
            st.one_of(
                st.integers(min_value=1, max_value=2 * size + 2),
                st.sampled_from((size - 1, size, size + 1)).map(
                    lambda value: max(value, 1)
                ),
            )
        )
        return LogCase(text=text, max_bytes=budget)

    return build()
