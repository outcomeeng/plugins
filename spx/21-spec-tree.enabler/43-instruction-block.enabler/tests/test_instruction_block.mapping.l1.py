import pathlib

from outcomeeng_testing.harnesses import instruction_block as harness
from outcomeeng_testing.harnesses import instruction_block_mapping_evidence as evidence

MODULE = harness.load_instruction_block_module()


def test_instruction_block_mapping_evidence() -> None:
    assert (
        evidence.mapping_evidence_run().executed
        == evidence.mapping_evidence_declarations()
    )


def test_root_topology_maps_to_bootstrap_outcome(tmp_path: pathlib.Path) -> None:
    for case in harness.bootstrap_topology_cases():
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
        case.name: MODULE.delegates_to(case.body, other)
        for case in harness.delegation_shape_cases()
    }
    assert verdicts == {
        "every-substantive-line-references": True,
        "a-substantive-line-does-not-reference": False,
        "a-reference-line-adds-its-own-instruction": False,
        "a-hash-run-without-a-closer-is-not-a-heading": False,
        "no-substantive-line": False,
        "reference-inside-a-code-fence": False,
    }
