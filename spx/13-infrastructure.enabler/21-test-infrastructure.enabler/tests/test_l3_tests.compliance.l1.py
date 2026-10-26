"""Compliance evidence that no tracked file carries the retired name of the L3 tests."""

from __future__ import annotations

from outcomeeng.validation.retired_names import retired_name_lines
from outcomeeng_testing.generators.retired_names import (
    GENERATED_TEXT_PATH,
    joined_retired_name_forms,
    separated_retired_name_forms,
)
from outcomeeng_testing.harnesses.spec_tree import (
    marketplace_root_for_spec_tree_root_test,
    marketplace_tracked_texts,
)


def test_no_tracked_file_carries_the_retired_name() -> None:
    root = marketplace_root_for_spec_tree_root_test(__file__)

    assert retired_name_lines(marketplace_tracked_texts(root)) == ()


def test_every_joined_form_of_the_retired_name_is_detected() -> None:
    forms = joined_retired_name_forms()

    assert retired_name_lines({GENERATED_TEXT_PATH: "\n".join(forms)}) == tuple(
        f"{GENERATED_TEXT_PATH}:{number}" for number in range(1, len(forms) + 1)
    )


def test_the_two_words_apart_are_not_the_retired_name() -> None:
    forms = separated_retired_name_forms()

    assert forms
    assert retired_name_lines({GENERATED_TEXT_PATH: "\n".join(forms)}) == ()
