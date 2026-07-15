"""Property harness evidence for the instruction-block render model.

Universal invariants in ``instruction-block.md``: after a render the output's
``template_version`` equals the installed version, every managed surface ends with exactly one
trailing newline, staleness ordering matches dotted-numeric version order (catching
lexicographic defects such as 0.9.0 vs 0.10.0), a reconciled shared region is byte-identical
across both files, the bootstrap pass wraps at most one shared region, and reconciling an
already-identical region is idempotent. Hypothesis owns the generated version and body domains;
Python tuple ordering and string equality are the independent oracles.
"""

from __future__ import annotations

from hypothesis import given, seed, settings

from outcomeeng_testing.generators.instruction_block import (
    dotted_version,
    free_root_contents,
    shared_document,
    shared_region_bodies,
    version_triples,
)

from outcomeeng_testing.harnesses.instruction_block import (
    EvidenceRun,
    ROOT_SHARED_BODY,
    SHARED_REGION_NAME,
    TEMPLATE_HARNESSES,
    TEMPLATE_LANGUAGES,
    build_template,
    load_instruction_block_module,
)


def _assert_render_output_version_equals_installed(
    harness: str,
    installed: tuple[int, int, int],
) -> None:
    module = load_instruction_block_module()
    installed_str = dotted_version(installed)
    rendered = module.render(
        build_template("0.0.0"), TEMPLATE_LANGUAGES, installed_str, harness
    )
    assert module.parse_template_version(rendered) == installed_str


def _assert_managed_surface_ends_with_single_newline(
    installed: tuple[int, int, int],
) -> None:
    module = load_instruction_block_module()
    installed_str = dotted_version(installed)
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


def _assert_is_stale_matches_numeric_version_order(
    left: tuple[int, int, int], right: tuple[int, int, int]
) -> None:
    module = load_instruction_block_module()
    assert module.is_stale(dotted_version(left), dotted_version(right)) is (
        left < right
    )


def _assert_reconcile_makes_shared_region_identical(body_a: str, body_b: str) -> None:
    module = load_instruction_block_module()
    doc_a = shared_document(module, SHARED_REGION_NAME, body_a)
    doc_b = shared_document(module, SHARED_REGION_NAME, body_b)
    for winner in ("a", "b"):
        new_a, new_b = module.reconcile_shared_regions(doc_a, doc_b, winner)
        region_a = module.parse_shared_regions(new_a)[SHARED_REGION_NAME]
        region_b = module.parse_shared_regions(new_b)[SHARED_REGION_NAME]
        assert region_a == region_b


def _assert_reconcile_identical_region_is_idempotent(body: str) -> None:
    module = load_instruction_block_module()
    doc_a = shared_document(module, SHARED_REGION_NAME, body)
    doc_b = shared_document(module, SHARED_REGION_NAME, body)
    for winner in ("a", "b", None):
        assert module.reconcile_shared_regions(doc_a, doc_b, winner) == (doc_a, doc_b)


def _assert_bootstrap_wraps_at_most_one_shared_region(
    content_a: str, content_b: str
) -> None:
    module = load_instruction_block_module()
    wrapped_a, wrapped_b = module.bootstrap_wrap(content_a, content_b)
    assert len(module.parse_shared_regions(wrapped_a)) <= 1
    assert len(module.parse_shared_regions(wrapped_b)) <= 1


def property_evidence_run() -> EvidenceRun:
    """Run every declared generated property domain."""
    declared: list[str] = []
    executed: list[str] = []

    for index, agent_harness in enumerate(TEMPLATE_HARNESSES):
        case_name = f"render-version[{agent_harness}]"
        declared.append(case_name)

        @seed(20260714 + index)
        @settings(max_examples=50, deadline=None)
        @given(installed=version_triples())
        def render_version(installed: tuple[int, int, int]) -> None:
            _assert_render_output_version_equals_installed(agent_harness, installed)

        render_version()
        executed.append(case_name)

    @seed(20260720)
    @settings(max_examples=50, deadline=None)
    @given(installed=version_triples())
    def trailing_newline(installed: tuple[int, int, int]) -> None:
        _assert_managed_surface_ends_with_single_newline(installed)

    @seed(20260721)
    @settings(max_examples=50, deadline=None)
    @given(left=version_triples(), right=version_triples())
    def stale_order(left: tuple[int, int, int], right: tuple[int, int, int]) -> None:
        _assert_is_stale_matches_numeric_version_order(left, right)

    @seed(20260722)
    @settings(max_examples=50, deadline=None)
    @given(body_a=shared_region_bodies(), body_b=shared_region_bodies())
    def reconcile_identity(body_a: str, body_b: str) -> None:
        _assert_reconcile_makes_shared_region_identical(body_a, body_b)

    @seed(20260723)
    @settings(max_examples=50, deadline=None)
    @given(body=shared_region_bodies())
    def reconcile_idempotence(body: str) -> None:
        _assert_reconcile_identical_region_is_idempotent(body)

    @seed(20260724)
    @settings(max_examples=50, deadline=None)
    @given(content_a=free_root_contents(), content_b=free_root_contents())
    def bootstrap_bound(content_a: str, content_b: str) -> None:
        _assert_bootstrap_wraps_at_most_one_shared_region(content_a, content_b)

    properties = (
        ("trailing-newline", trailing_newline),
        ("stale-order", stale_order),
        ("reconcile-identity", reconcile_identity),
        ("reconcile-idempotence", reconcile_idempotence),
        ("bootstrap-bound", bootstrap_bound),
    )
    for name, assertion in properties:
        declared.append(name)
        assertion()
        executed.append(name)
    return EvidenceRun(declared=tuple(declared), executed=tuple(executed))
