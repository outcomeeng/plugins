"""Direct property predicates for the root instruction-block renderer."""

from __future__ import annotations

from fractions import Fraction

from outcomeeng_testing.generators.instruction_block import (
    BootstrapThresholdRelation,
    BootstrapWrapCase,
    RootContentPair,
    dotted_version,
    shared_document,
)
from outcomeeng_testing.harnesses import instruction_block_property_evidence as evidence
from outcomeeng_testing.harnesses.instruction_block import (
    HARNESS_CLAUDE,
    HARNESS_CODEX,
    OLD_VERSION,
    SHARED_REGION_NAME,
    TEMPLATE_LANGUAGES,
    build_template,
    load_instruction_block_module,
)


def test_render_output_version_equals_installed() -> None:
    def verifies(
        harness: str,
        installed: tuple[int, int, int],
    ) -> None:
        module = load_instruction_block_module()
        installed_str = dotted_version(installed)
        rendered = module.render(
            build_template(OLD_VERSION), TEMPLATE_LANGUAGES, installed_str, harness
        )
        assert module.parse_template_version(rendered) == installed_str

    evidence.for_all_render_output_version_equals_installed(verifies)


def test_managed_surface_ends_with_single_newline() -> None:
    def verifies(
        installed: tuple[int, int, int],
        root_pair: RootContentPair,
    ) -> None:
        module = load_instruction_block_module()
        installed_str = dotted_version(installed)
        blocks = {
            harness: module.render(
                build_template(OLD_VERSION), TEMPLATE_LANGUAGES, installed_str, harness
            )
            for harness in module.AGENT_HARNESS_INSTRUCTION_FILENAMES
        }
        seeds = {
            HARNESS_CLAUDE: root_pair.content_a,
            HARNESS_CODEX: root_pair.content_b,
        }
        documents = module.build_root_instruction_documents(seeds, blocks)
        for document in documents.values():
            assert document.endswith("\n")
            assert not document.endswith("\n\n")

    evidence.for_all_managed_surface_ends_with_single_newline(verifies)


def test_is_stale_matches_numeric_version_order() -> None:
    def verifies(left: tuple[int, int, int], right: tuple[int, int, int]) -> None:
        module = load_instruction_block_module()
        assert module.is_stale(dotted_version(left), dotted_version(right)) is (
            left < right
        )

    evidence.for_all_is_stale_matches_numeric_version_order(verifies)


def test_reconcile_makes_shared_region_identical() -> None:
    def verifies(body_a: str, body_b: str) -> None:
        module = load_instruction_block_module()
        doc_a = shared_document(module, SHARED_REGION_NAME, body_a)
        doc_b = shared_document(module, SHARED_REGION_NAME, body_b)
        for winner in ("a", "b"):
            new_a, new_b = module.reconcile_shared_regions(doc_a, doc_b, winner)
            region_a = module.parse_shared_regions(new_a)[SHARED_REGION_NAME]
            region_b = module.parse_shared_regions(new_b)[SHARED_REGION_NAME]
            assert region_a == region_b

    evidence.for_all_reconcile_makes_shared_region_identical(verifies)


def test_reconcile_identical_region_is_idempotent() -> None:
    def verifies(body: str) -> None:
        module = load_instruction_block_module()
        doc_a = shared_document(module, SHARED_REGION_NAME, body)
        doc_b = shared_document(module, SHARED_REGION_NAME, body)
        for winner in ("a", "b", None):
            assert module.reconcile_shared_regions(doc_a, doc_b, winner) == (
                doc_a,
                doc_b,
            )

    evidence.for_all_reconcile_identical_region_is_idempotent(verifies)


def test_bootstrap_matches_independent_oracle() -> None:
    def verifies(root_pair: RootContentPair) -> None:
        module = load_instruction_block_module()
        maximal_spans = evidence.maximal_common_whole_line_spans(root_pair)
        maximal_length = max((len(span) for span in maximal_spans), default=0)
        larger_length = max(len(root_pair.content_a), len(root_pair.content_b))
        should_wrap = (
            larger_length > 0
            and Fraction(maximal_length, larger_length)
            > Fraction(str(module.BOOTSTRAP_SHARED_THRESHOLD))
            and any(span.strip() for span in maximal_spans)
        )

        wrapped_a, wrapped_b = module.bootstrap_wrap(
            root_pair.content_a,
            root_pair.content_b,
        )
        regions_a = module.parse_shared_regions(wrapped_a)
        regions_b = module.parse_shared_regions(wrapped_b)
        assert len(regions_a) <= 1
        assert len(regions_b) <= 1
        if should_wrap:
            region_name = module.BOOTSTRAP_SHARED_REGION_NAME
            assert tuple(regions_a) == (region_name,)
            assert tuple(regions_b) == (region_name,)
            assert regions_a[region_name] == regions_b[region_name]
            assert regions_a[region_name] in {
                span.strip("\n") for span in maximal_spans
            }
        else:
            assert regions_a == {}
            assert regions_b == {}
            assert (wrapped_a, wrapped_b) == (
                root_pair.content_a,
                root_pair.content_b,
            )

    evidence.for_all_bootstrap_matches_independent_oracle(verifies)


def test_bootstrap_threshold_decision() -> None:
    def verifies(case: BootstrapWrapCase) -> None:
        module = load_instruction_block_module()
        threshold = Fraction(str(module.BOOTSTRAP_SHARED_THRESHOLD))
        shared_ratio = Fraction(
            len(case.shared_body) + 1,
            max(len(case.content_a), len(case.content_b)),
        )
        if case.relation is BootstrapThresholdRelation.ABOVE:
            assert shared_ratio > threshold
        elif case.relation is BootstrapThresholdRelation.AT:
            assert shared_ratio == threshold
        else:
            assert shared_ratio < threshold

        wrapped_a, wrapped_b = module.bootstrap_wrap(case.content_a, case.content_b)
        regions_a = module.parse_shared_regions(wrapped_a)
        regions_b = module.parse_shared_regions(wrapped_b)
        if case.relation is BootstrapThresholdRelation.ABOVE:
            expected = {module.BOOTSTRAP_SHARED_REGION_NAME: case.shared_body}
            assert regions_a == expected
            assert regions_b == expected
        else:
            assert regions_a == {}
            assert regions_b == {}
            assert (wrapped_a, wrapped_b) == (case.content_a, case.content_b)

    evidence.for_all_bootstrap_threshold_decision(verifies)
