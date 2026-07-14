"""Property evidence for the instruction-block render model.

Universal invariants in ``instruction-block.md``: after a render the output's
``template_version`` equals the installed version, every managed surface ends with exactly one
trailing newline, staleness ordering matches dotted-numeric version order (catching
lexicographic defects such as 0.9.0 vs 0.10.0), a reconciled shared region is byte-identical
across both files, the bootstrap pass wraps at most one shared region, and reconciling an
already-identical region is idempotent. Hypothesis owns the generated version and body domains;
Python tuple ordering and string equality are the independent oracles.
"""

from __future__ import annotations

from types import ModuleType

import pytest
from hypothesis import given
from hypothesis import strategies as st

from outcomeeng_testing.harnesses.instruction_block import (
    ROOT_SHARED_BODY,
    SHARED_REGION_NAME,
    TEMPLATE_HARNESSES,
    TEMPLATE_LANGUAGES,
    build_template,
    load_instruction_block_module,
)

_VERSION_PART = st.integers(min_value=0, max_value=999)
_VERSION = st.tuples(_VERSION_PART, _VERSION_PART, _VERSION_PART)

# Region body text: no fence-forming characters (`<`, `>`, `!`, `/`, `:`) and no newlines, so it
# round-trips through a shared fence unambiguously. The domain varies per case; the reconcile and
# idempotence invariants are the oracles.
_REGION_BODY = st.text(
    alphabet=st.characters(
        whitelist_categories=("L", "N"), whitelist_characters=" -_`"
    ),
    min_size=1,
).filter(lambda body: body.strip() != "")
# Free content for bootstrap: may span multiple lines but carries no fence-forming characters.
_FREE_CONTENT = st.text(
    alphabet=st.characters(
        whitelist_categories=("L", "N"), whitelist_characters=" -_`\n"
    ),
    max_size=200,
)


def _to_version(parts: tuple[int, int, int]) -> str:
    return ".".join(str(part) for part in parts)


def _shared_document(module: ModuleType, name: str, body: str) -> str:
    return (
        f"{module.shared_open_marker(name)}\n\n{body}\n\n"
        f"{module.shared_close_marker(name)}\n"
    )


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


@given(installed=_VERSION)
def test_managed_surface_ends_with_single_newline(
    installed: tuple[int, int, int],
) -> None:
    module = load_instruction_block_module()
    installed_str = _to_version(installed)
    blocks = {
        harness: module.render(
            build_template("0.0.0"), TEMPLATE_LANGUAGES, installed_str, harness
        )
        for harness in module.AGENT_HARNESS_INSTRUCTION_FILENAMES
    }
    seeds = {
        harness: ROOT_SHARED_BODY
        for harness in module.AGENT_HARNESS_INSTRUCTION_FILENAMES
    }
    documents = module.build_root_instruction_documents(seeds, blocks)
    for document in documents.values():
        assert document.endswith("\n")
        assert not document.endswith("\n\n")


@given(left=_VERSION, right=_VERSION)
def test_is_stale_matches_numeric_version_order(
    left: tuple[int, int, int], right: tuple[int, int, int]
) -> None:
    module = load_instruction_block_module()
    assert module.is_stale(_to_version(left), _to_version(right)) is (left < right)


@given(body_a=_REGION_BODY, body_b=_REGION_BODY)
def test_reconcile_makes_shared_region_identical(body_a: str, body_b: str) -> None:
    module = load_instruction_block_module()
    doc_a = _shared_document(module, SHARED_REGION_NAME, body_a)
    doc_b = _shared_document(module, SHARED_REGION_NAME, body_b)
    for winner in ("a", "b"):
        new_a, new_b = module.reconcile_shared_regions(doc_a, doc_b, winner)
        region_a = module.parse_shared_regions(new_a)[SHARED_REGION_NAME]
        region_b = module.parse_shared_regions(new_b)[SHARED_REGION_NAME]
        assert region_a == region_b


@given(body=_REGION_BODY)
def test_reconcile_identical_region_is_idempotent(body: str) -> None:
    module = load_instruction_block_module()
    doc_a = _shared_document(module, SHARED_REGION_NAME, body)
    doc_b = _shared_document(module, SHARED_REGION_NAME, body)
    for winner in ("a", "b", None):
        assert module.reconcile_shared_regions(doc_a, doc_b, winner) == (doc_a, doc_b)


@given(content_a=_FREE_CONTENT, content_b=_FREE_CONTENT)
def test_bootstrap_wraps_at_most_one_shared_region(
    content_a: str, content_b: str
) -> None:
    module = load_instruction_block_module()
    wrapped_a, wrapped_b = module.bootstrap_wrap(content_a, content_b)
    assert len(module.parse_shared_regions(wrapped_a)) <= 1
    assert len(module.parse_shared_regions(wrapped_b)) <= 1


@given(content_a=_FREE_CONTENT, content_b=_FREE_CONTENT)
def test_biggest_span_ratio_determines_wrap_decision(
    content_a: str, content_b: str
) -> None:
    module = load_instruction_block_module()
    span, ratio = module.biggest_identical_span(content_a, content_b)
    wrapped_a, wrapped_b = module.bootstrap_wrap(content_a, content_b)
    should_wrap = ratio > module.BOOTSTRAP_SHARED_THRESHOLD and bool(span.strip())
    assert bool(module.parse_shared_regions(wrapped_a)) is should_wrap
    assert bool(module.parse_shared_regions(wrapped_b)) is should_wrap
