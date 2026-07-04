"""Property evidence for the instruction-block render helper.

Universal invariants in ``instruction-block.md``: after a render the output's
``template_version`` equals the installed version, every render ends with exactly one
trailing newline, staleness ordering matches dotted-numeric version order (catching
lexicographic defects such as 0.9.0 vs 0.10.0), and after sibling-fill each fixed command
slot's body is identical across the two root files. Hypothesis owns the generated version and
slot-body domains; Python tuple ordering and string equality are the independent oracles.
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


# Command-slot body text: non-empty, no fence markers or newlines, so it round-trips through a
# slot fence unambiguously. The domain varies per case; the sibling-fill invariant is the oracle.
_SLOT_BODY = st.text(
    alphabet=st.characters(
        whitelist_categories=("L", "N"), whitelist_characters=" -_`"
    ),
    min_size=1,
).filter(lambda body: body.strip() != "")
_SLOT_SIDE = st.sampled_from(("claude", "agents", "both", "neither"))


@given(data=st.data())
def test_sibling_fill_makes_each_slot_body_identical_across_files(
    data: st.DataObject,
) -> None:
    module = load_instruction_block_module()
    base = module.ensure_slot_fences("")
    claude, agents = base, base
    # Fill each slot on one side, both sides with the same body, or neither — never both sides
    # with different bodies, which is the conflict case sibling-fill deliberately leaves alone.
    for slot in module.FIXED_COMMAND_SLOTS:
        side = data.draw(_SLOT_SIDE)
        if side == "neither":
            continue
        body = data.draw(_SLOT_BODY)
        if side in ("claude", "both"):
            claude = module.set_command_slot(claude, slot, body)
        if side in ("agents", "both"):
            agents = module.set_command_slot(agents, slot, body)

    reconciled_claude, reconciled_agents = module.reconcile_command_slots(
        claude, agents
    )

    for slot in module.FIXED_COMMAND_SLOTS:
        assert module.parse_command_slot(
            reconciled_claude, slot
        ) == module.parse_command_slot(reconciled_agents, slot)
