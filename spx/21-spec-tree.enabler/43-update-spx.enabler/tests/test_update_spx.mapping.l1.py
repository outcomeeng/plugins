"""Mapping evidence: a language block renders exactly when the language is enabled.

Over the languages the template defines blocks for (``TEMPLATE_LANGUAGES``),
parametrize every enabled subset and assert each language's heading is present in the
rendered guide iff that language is in the enabled set. The expected output is derived
from the input subset, not hand-picked.
"""

from __future__ import annotations

import itertools

import pytest

from outcomeeng_testing.harnesses.update_spx import (
    RUNTIME_CLAUDE,
    TEMPLATE_LANGUAGES,
    build_template,
    load_update_spx_module,
)

VERSION = "0.18.0"


def _all_language_subsets() -> list[tuple[str, ...]]:
    subsets: list[tuple[str, ...]] = []
    for size in range(len(TEMPLATE_LANGUAGES) + 1):
        subsets.extend(itertools.combinations(TEMPLATE_LANGUAGES, size))
    return subsets


@pytest.mark.parametrize("enabled", _all_language_subsets())
def test_language_block_present_iff_enabled(enabled: tuple[str, ...]) -> None:
    module = load_update_spx_module()
    rendered = module.render(build_template(VERSION), enabled, VERSION, RUNTIME_CLAUDE)
    for language in TEMPLATE_LANGUAGES:
        heading = f"### {language.capitalize()}"
        assert (heading in rendered) is (language in enabled)


def test_each_test_extension_maps_to_its_language() -> None:
    module = load_update_spx_module()
    for extension, language in module.LANGUAGE_BY_EXTENSION.items():
        assert module.language_for_extension(extension) == language
        assert module.language_for_extension(f".{extension}") == language
        assert module.detect_languages((extension,)) == (language,)


def test_detected_language_set_is_the_mapped_extensions() -> None:
    module = load_update_spx_module()
    all_extensions = tuple(module.LANGUAGE_BY_EXTENSION)
    expected = tuple(sorted(set(module.LANGUAGE_BY_EXTENSION.values())))
    assert module.detect_languages(all_extensions) == expected
    # An extension with no language mapping contributes nothing.
    assert module.detect_languages(("md", "txt")) == ()
