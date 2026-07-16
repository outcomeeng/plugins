"""Property harness evidence for the instruction-block render model.

Universal invariants in ``instruction-block.md``: after a render the output's
``template_version`` equals the installed version, every managed surface ends with exactly one
trailing newline, staleness ordering matches dotted-numeric version order (catching
lexicographic defects such as 0.9.0 vs 0.10.0), a reconciled shared region is byte-identical
across both files, the bootstrap pass wraps at most one shared region, and reconciling an
already-identical region is idempotent. Broad whole-document domains cover independent,
identical, and already-shared root topologies. A dynamic-programming oracle finds every maximal
common whole-line span independently of the production span finder, including competing spans;
exact above, at, and below-threshold cases retain dedicated boundary evidence. Hypothesis owns
the generated version, body, and document domains.
"""

from __future__ import annotations

from fractions import Fraction

from hypothesis import given

from outcomeeng_testing.generators.instruction_block import (
    BootstrapThresholdRelation,
    BootstrapWrapCase,
    RootContentPair,
    bootstrap_content_pairs,
    bootstrap_wrap_cases,
    dotted_version,
    root_content_pairs,
    shared_document,
    shared_region_bodies,
    version_triples,
)

from outcomeeng_testing.harnesses.instruction_block import (
    EvidenceRun,
    HARNESS_CLAUDE,
    HARNESS_CODEX,
    SHARED_REGION_NAME,
    TEMPLATE_HARNESSES,
    TEMPLATE_LANGUAGES,
    build_template,
    load_instruction_block_module,
    property_evidence_contract,
    run_instruction_block_property,
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
    root_pair: RootContentPair,
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
        HARNESS_CLAUDE: root_pair.content_a,
        HARNESS_CODEX: root_pair.content_b,
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


def _assert_bootstrap_threshold_decision(case: BootstrapWrapCase) -> None:
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


def _maximal_common_whole_line_spans(root_pair: RootContentPair) -> tuple[str, ...]:
    """Find maximal contiguous common line spans without production algorithms."""
    lines_a = root_pair.content_a.splitlines(keepends=True)
    lines_b = root_pair.content_b.splitlines(keepends=True)
    previous = [""] * (len(lines_b) + 1)
    maximal: set[str] = set()
    maximal_length = 0
    for line_a in lines_a:
        current = [""] * (len(lines_b) + 1)
        for index_b, line_b in enumerate(lines_b, start=1):
            if line_a != line_b:
                continue
            candidate = previous[index_b - 1] + line_a
            current[index_b] = candidate
            candidate_length = len(candidate)
            if candidate_length > maximal_length:
                maximal = {candidate}
                maximal_length = candidate_length
            elif candidate_length == maximal_length:
                maximal.add(candidate)
        previous = current
    return tuple(sorted(maximal))


def _assert_bootstrap_matches_independent_oracle(root_pair: RootContentPair) -> None:
    module = load_instruction_block_module()
    maximal_spans = _maximal_common_whole_line_spans(root_pair)
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
        assert regions_a[region_name] in {span.strip("\n") for span in maximal_spans}
    else:
        assert regions_a == {}
        assert regions_b == {}
        assert (wrapped_a, wrapped_b) == (
            root_pair.content_a,
            root_pair.content_b,
        )


def property_evidence_declarations() -> tuple[str, ...]:
    """Return every generated property identity in execution order."""
    return property_evidence_contract()


def property_evidence_run() -> EvidenceRun:
    """Run every declared generated property domain."""
    declared: list[str] = []
    executed: list[str] = []

    for agent_harness in TEMPLATE_HARNESSES:
        case_name = f"render-version[{agent_harness}]"
        declared.append(case_name)

        @given(installed=version_triples())
        def render_version(installed: tuple[int, int, int]) -> None:
            _assert_render_output_version_equals_installed(agent_harness, installed)

        run_instruction_block_property(render_version)
        executed.append(case_name)

    module = load_instruction_block_module()

    @given(
        installed=version_triples(),
        root_pair=root_content_pairs(module, SHARED_REGION_NAME),
    )
    def trailing_newline(
        installed: tuple[int, int, int],
        root_pair: RootContentPair,
    ) -> None:
        _assert_managed_surface_ends_with_single_newline(installed, root_pair)

    @given(left=version_triples(), right=version_triples())
    def stale_order(left: tuple[int, int, int], right: tuple[int, int, int]) -> None:
        _assert_is_stale_matches_numeric_version_order(left, right)

    @given(body_a=shared_region_bodies(), body_b=shared_region_bodies())
    def reconcile_identity(body_a: str, body_b: str) -> None:
        _assert_reconcile_makes_shared_region_identical(body_a, body_b)

    @given(body=shared_region_bodies())
    def reconcile_idempotence(body: str) -> None:
        _assert_reconcile_identical_region_is_idempotent(body)

    @given(root_pair=bootstrap_content_pairs())
    def bootstrap_general_domain(root_pair: RootContentPair) -> None:
        _assert_bootstrap_matches_independent_oracle(root_pair)

    properties = (
        ("trailing-newline", trailing_newline),
        ("stale-order", stale_order),
        ("reconcile-identity", reconcile_identity),
        ("reconcile-idempotence", reconcile_idempotence),
        ("bootstrap-general-domain", bootstrap_general_domain),
    )
    for name, assertion in properties:
        declared.append(name)
        run_instruction_block_property(assertion)
        executed.append(name)

    for relation in BootstrapThresholdRelation:
        case_name = f"bootstrap-threshold[{relation.value}]"
        declared.append(case_name)

        @given(case=bootstrap_wrap_cases(module.BOOTSTRAP_SHARED_THRESHOLD, relation))
        def bootstrap_threshold(case: BootstrapWrapCase) -> None:
            _assert_bootstrap_threshold_decision(case)

        run_instruction_block_property(bootstrap_threshold)
        executed.append(case_name)
    return EvidenceRun(declared=tuple(declared), executed=tuple(executed))
