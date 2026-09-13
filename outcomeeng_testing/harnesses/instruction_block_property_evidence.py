"""Generated property inputs and an independent whole-line span oracle."""

from __future__ import annotations

from collections.abc import Callable
from hypothesis import given
from outcomeeng_testing.generators.instruction_block import (
    BootstrapThresholdRelation,
    BootstrapWrapCase,
    RootContentPair,
    bootstrap_content_pairs,
    bootstrap_wrap_cases,
    root_content_pairs,
    shared_region_bodies,
    version_triples,
)
from outcomeeng_testing.harnesses.instruction_block import (
    SHARED_REGION_NAME,
    TEMPLATE_HARNESSES,
    load_instruction_block_module,
    run_instruction_block_property,
)


def maximal_common_whole_line_spans(root_pair: RootContentPair) -> tuple[str, ...]:
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


def for_all_render_output_version_equals_installed(
    assertion: Callable[[str, tuple[int, int, int]], None],
) -> None:
    for agent_harness in TEMPLATE_HARNESSES:

        @given(installed=version_triples())
        def generated(installed: tuple[int, int, int]) -> None:
            assertion(agent_harness, installed)

        run_instruction_block_property(generated)


def for_all_managed_surface_ends_with_single_newline(
    assertion: Callable[[tuple[int, int, int], RootContentPair], None],
) -> None:
    module = load_instruction_block_module()

    @given(
        installed=version_triples(),
        root_pair=root_content_pairs(module, SHARED_REGION_NAME),
    )
    def generated(installed: tuple[int, int, int], root_pair: RootContentPair) -> None:
        assertion(installed, root_pair)

    run_instruction_block_property(generated)


def for_all_is_stale_matches_numeric_version_order(
    assertion: Callable[[tuple[int, int, int], tuple[int, int, int]], None],
) -> None:
    @given(left=version_triples(), right=version_triples())
    def generated(left: tuple[int, int, int], right: tuple[int, int, int]) -> None:
        assertion(left, right)

    run_instruction_block_property(generated)


def for_all_reconcile_makes_shared_region_identical(
    assertion: Callable[[str, str], None],
) -> None:
    @given(body_a=shared_region_bodies(), body_b=shared_region_bodies())
    def generated(body_a: str, body_b: str) -> None:
        assertion(body_a, body_b)

    run_instruction_block_property(generated)


def for_all_reconcile_identical_region_is_idempotent(
    assertion: Callable[[str], None],
) -> None:
    @given(body=shared_region_bodies())
    def generated(body: str) -> None:
        assertion(body)

    run_instruction_block_property(generated)


def for_all_bootstrap_matches_independent_oracle(
    assertion: Callable[[RootContentPair], None],
) -> None:
    @given(root_pair=bootstrap_content_pairs())
    def generated(root_pair: RootContentPair) -> None:
        assertion(root_pair)

    run_instruction_block_property(generated)


def for_all_bootstrap_threshold_decision(
    assertion: Callable[[BootstrapWrapCase], None],
) -> None:
    module = load_instruction_block_module()
    for relation in BootstrapThresholdRelation:

        @given(case=bootstrap_wrap_cases(module.BOOTSTRAP_SHARED_THRESHOLD, relation))
        def generated(case: BootstrapWrapCase) -> None:
            assertion(case)

        run_instruction_block_property(generated)
