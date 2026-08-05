import pathlib
from collections.abc import Callable
from dataclasses import dataclass

from outcomeeng_testing.harnesses import instruction_block as harness
from outcomeeng_testing.harnesses import instruction_block_mapping_evidence as evidence

MODULE = harness.load_instruction_block_module()


@dataclass(frozen=True)
class _TopologyCase:
    """One initial topology paired with the bootstrap outcome this test requires of it."""

    name: str
    factory: Callable[[], harness.RootInstructionTopology]
    expected_region_body: str | None
    removed_tokens: tuple[str, ...] = ()


def _topology_cases() -> tuple[_TopologyCase, ...]:
    """Pair every member of the finite initial-topology domain with its required outcome."""
    return (
        _TopologyCase(
            "only_claude",
            harness.root_instruction_topology_only_claude,
            harness.ROOT_CLAUDE_BODY,
        ),
        _TopologyCase(
            "only_agents",
            harness.root_instruction_topology_only_agents,
            harness.ROOT_AGENTS_BODY,
        ),
        _TopologyCase(
            "symlinked",
            harness.root_instruction_topology_symlinked,
            harness.ROOT_SHARED_BODY,
        ),
        # A body that only points at the other file is reported for the operator, never adopted by
        # the write itself, so the default run leaves both bodies standing and wraps no region.
        _TopologyCase(
            "delegating",
            harness.root_instruction_topology_delegating,
            None,
        ),
        _TopologyCase(
            "reverse_delegating",
            harness.root_instruction_topology_reverse_delegating,
            None,
        ),
        _TopologyCase(
            "mutual_delegation",
            harness.root_instruction_topology_mutual_delegation,
            None,
        ),
        _TopologyCase(
            "identical",
            harness.root_instruction_topology_identical,
            harness.ROOT_SHARED_BODY,
        ),
        _TopologyCase(
            "legacy_managed",
            harness.root_instruction_topology_legacy_managed,
            harness.ROOT_SHARED_BODY,
            removed_tokens=harness.retired_managed_block_tokens(),
        ),
        _TopologyCase(
            "near_identical",
            harness.root_instruction_topology_near_identical,
            harness.ROOT_NEAR_IDENTICAL_SHARED,
        ),
        _TopologyCase(
            "separate",
            harness.root_instruction_topology_separate,
            None,
        ),
    )


def test_repeated_cli_flag_maps_to_its_rejection() -> None:
    for option in MODULE.CLI_OPTION_NAMES:
        observed = evidence.observe_duplicate_cli_flag(option)
        assert observed.detected == option, option
        assert observed.exit_code == 2, option
        assert observed.stderr == f"{MODULE.DUPLICATE_FLAG_ERROR_PREFIX}{option}", (
            option
        )


def test_test_file_extension_maps_to_its_language() -> None:
    for extension, language in sorted(MODULE.LANGUAGE_BY_EXTENSION.items()):
        assert evidence.observe_extension_language(extension) == (language, language), (
            extension
        )


def test_detected_language_set_is_the_mapped_extensions(
    tmp_path: pathlib.Path,
) -> None:
    detected, mapped = evidence.observe_detected_language_set(tmp_path / "spx")
    assert detected == mapped


def test_language_block_appears_exactly_when_the_language_is_enabled() -> None:
    for language in harness.TEMPLATE_LANGUAGES:
        observed = evidence.observe_language_block(language)
        assert observed.heading in observed.enabled, language
        assert observed.heading not in observed.disabled, language


def test_router_block_state_maps_to_its_check_report(tmp_path: pathlib.Path) -> None:
    current = MODULE.InstructionStatus.CURRENT.value
    absent = MODULE.InstructionStatus.ABSENT.value
    stale = MODULE.InstructionStatus.STALE.value
    assert evidence.observe_check_router_states(tmp_path) == {
        "current": (0, current),
        "absent": (0, absent),
        "version-behind": (0, stale),
        "language-set-differs": (0, stale),
    }


def test_shared_region_state_maps_to_its_check_report(tmp_path: pathlib.Path) -> None:
    current = MODULE.InstructionStatus.CURRENT.value
    stale = MODULE.InstructionStatus.STALE.value
    assert evidence.observe_check_shared_region_states(tmp_path) == {
        "byte-identical": (0, current),
        "diverged": (0, stale),
        "one-sided": (0, stale),
    }


def test_span_ratio_maps_to_the_wrap_decision() -> None:
    identical = evidence.observe_span_ratio(
        harness.ROOT_SHARED_BODY, harness.ROOT_SHARED_BODY
    )
    assert identical.span == harness.ROOT_SHARED_BODY
    assert identical.ratio > MODULE.BOOTSTRAP_SHARED_THRESHOLD
    assert all(regions for regions in identical.wrapped_regions)

    near = evidence.observe_span_ratio(
        harness.ROOT_NEAR_IDENTICAL_CLAUDE, harness.ROOT_NEAR_IDENTICAL_CODEX
    )
    assert near.span == harness.ROOT_NEAR_IDENTICAL_SHARED
    assert near.ratio > MODULE.BOOTSTRAP_SHARED_THRESHOLD

    divergent = evidence.observe_span_ratio(
        harness.ROOT_CLAUDE_BODY, harness.ROOT_AGENTS_BODY
    )
    assert divergent.ratio <= MODULE.BOOTSTRAP_SHARED_THRESHOLD
    assert not any(regions for regions in divergent.wrapped_regions)


def test_root_topology_maps_to_bootstrap_outcome(tmp_path: pathlib.Path) -> None:
    for case in _topology_cases():
        outcome = harness.observe_bootstrap_outcome(tmp_path / case.name, case.factory)
        documents = {
            harness.INSTRUCTION_CLAUDE: outcome.claude,
            harness.INSTRUCTION_AGENTS: outcome.agents,
        }

        if case.expected_region_body is None:
            assert MODULE.parse_shared_regions(outcome.claude) == {}, case.name
            assert MODULE.parse_shared_regions(outcome.agents) == {}, case.name
        else:
            expected = {
                harness.SHARED_REGION_NAME: case.expected_region_body.strip("\n")
            }
            assert MODULE.parse_shared_regions(outcome.claude) == expected, case.name
            assert MODULE.parse_shared_regions(outcome.agents) == expected, case.name

        for filename, document in documents.items():
            other = (
                harness.INSTRUCTION_AGENTS
                if filename == harness.INSTRUCTION_CLAUDE
                else harness.INSTRUCTION_CLAUDE
            )
            # Every topology ends at two regular files, whichever side the generator had to
            # create for itself or convert from a symlink.
            assert (outcome.repo / filename).is_file(), (case.name, filename)
            assert not (outcome.repo / filename).is_symlink(), (case.name, filename)
            assert document.startswith(MODULE.ROUTER_MARKER_PREFIX), case.name
            for token in case.removed_tokens:
                assert token not in document, case.name

            own_seed = outcome.seeds.get(filename)
            if own_seed is None:
                # The topology placed no body here, so this side is the generator's own work
                # and the region assertion above already states what it must carry.
                continue
            other_lines = set(outcome.seeds.get(other, "").splitlines())
            own_lines = [
                line
                for line in own_seed.splitlines()
                if line.strip() and line not in other_lines
            ]
            if case.expected_region_body is None:
                assert own_seed.strip() in document, case.name
            else:
                cursor = 0
                for line in own_lines:
                    found = document.find(line, cursor)
                    assert found >= 0, (case.name, line)
                    cursor = found + len(line)


def test_root_body_shape_maps_to_delegation_candidacy() -> None:
    verdicts = {
        case.name: MODULE.is_delegation_candidate(case.body, case.other_filename)
        for case in harness.delegation_candidate_cases()
    }
    assert verdicts == {
        "names-the-other-file-well-inside-the-bound": True,
        "names-the-other-file-at-the-bound": True,
        "names-the-other-file-one-character-past-the-bound": False,
        "omits-the-other-file": False,
    }
