"""Property evidence for the instruction-block render helper.

Universal invariants in ``instruction-block.md``: after a render the output's
``template_version`` equals the installed version, every render ends with exactly one
trailing newline, and staleness ordering matches dotted-numeric version order (catching
lexicographic defects such as 0.9.0 vs 0.10.0). Hypothesis owns the generated version
domain; Python tuple ordering is the independent oracle.
"""

from __future__ import annotations

import pytest
from hypothesis import given
from hypothesis import strategies as st

from outcomeeng_testing.harnesses.instruction_block import (
    TEMPLATE_LANGUAGES,
    TEMPLATE_HARNESSES,
    build_template,
    load_instruction_block_module,
)

_VERSION_PART = st.integers(min_value=0, max_value=999)
_VERSION = st.tuples(_VERSION_PART, _VERSION_PART, _VERSION_PART)


def _to_version(parts: tuple[int, int, int]) -> str:
    return ".".join(str(part) for part in parts)


@pytest.mark.parametrize("harness", TEMPLATE_HARNESSES)
@given(installed=_VERSION)
def test_render_output_version_equals_installed(
    harness: str,
    installed: tuple[int, int, int],
) -> None:
    module = load_instruction_block_module()
    installed_str = _to_version(installed)
    rendered = module.render(
        build_template("0.0.0"), TEMPLATE_LANGUAGES, installed_str, harness
    )
    assert module.parse_template_version(rendered) == installed_str


@pytest.mark.parametrize("harness", TEMPLATE_HARNESSES)
@given(installed=_VERSION)
def test_render_output_ends_with_single_newline(
    harness: str,
    installed: tuple[int, int, int],
) -> None:
    module = load_instruction_block_module()
    rendered = module.render(
        build_template("0.0.0"),
        TEMPLATE_LANGUAGES,
        _to_version(installed),
        harness,
    )
    assert rendered.endswith("\n")
    assert not rendered.endswith("\n\n")


@given(left=_VERSION, right=_VERSION)
def test_is_stale_matches_numeric_version_order(
    left: tuple[int, int, int], right: tuple[int, int, int]
) -> None:
    module = load_instruction_block_module()
    assert module.is_stale(_to_version(left), _to_version(right)) is (left < right)
