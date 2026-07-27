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
    delegating_filename: str | None = None


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
        _TopologyCase(
            "delegating",
            harness.root_instruction_topology_delegating,
            harness.ROOT_AGENTS_BODY,
            delegating_filename=harness.INSTRUCTION_CLAUDE,
        ),
        _TopologyCase(
            "reverse_delegating",
            harness.root_instruction_topology_reverse_delegating,
            harness.ROOT_CLAUDE_BODY,
            delegating_filename=harness.INSTRUCTION_AGENTS,
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


def test_instruction_block_mapping_evidence() -> None:
    assert (
        evidence.mapping_evidence_run().executed
        == evidence.mapping_evidence_declarations()
    )


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
            other_lines = set(outcome.seeds[other].splitlines())
            own_lines = [
                line
                for line in outcome.seeds[filename].splitlines()
                if line.strip() and line not in other_lines
            ]
            if filename == case.delegating_filename:
                assert not any(line in document for line in own_lines), case.name
            elif case.expected_region_body is None:
                assert outcome.seeds[filename].strip() in document, case.name
            else:
                cursor = 0
                for line in own_lines:
                    found = document.find(line, cursor)
                    assert found >= 0, (case.name, line)
                    cursor = found + len(line)
            assert document.startswith(MODULE.ROUTER_MARKER_PREFIX), case.name
            for token in case.removed_tokens:
                assert token not in document, case.name


def test_root_body_shape_maps_to_delegation_verdict() -> None:
    other = harness.INSTRUCTION_AGENTS
    verdicts = {
        case.name: MODULE.delegates_to(case.body, other, case.other_body)
        for case in harness.delegation_shape_cases()
    }
    assert verdicts == {
        "every-substantive-line-references": True,
        "a-substantive-line-does-not-reference": False,
        "a-reference-line-adds-its-own-instruction": False,
        "a-hash-run-without-a-closer-is-not-a-heading": False,
        "a-heading-the-adopted-body-does-not-carry": False,
        "no-substantive-line": False,
        "reference-inside-a-code-fence": False,
    }
