import pathlib
from fractions import Fraction

from outcomeeng_testing.harnesses import instruction_block as harness
from outcomeeng_testing.harnesses import instruction_block_mapping_evidence as evidence

MODULE = harness.load_instruction_block_module()


def _version_tuple(version: str) -> tuple[int, ...]:
    return tuple(int(part) for part in version.split("."))


def _without_retired_managed_block(body: str) -> str:
    stripped = body
    for open_marker, close_marker in MODULE.LEGACY_MANAGED_BLOCK_MARKERS:
        start = stripped.find(open_marker)
        if start < 0:
            continue
        end = stripped.find(close_marker, start + len(open_marker))
        if end < 0:
            continue
        stripped = stripped[:start] + stripped[end + len(close_marker) :]
    return stripped.strip("\n")


def _maximal_common_whole_line_spans(left: str, right: str) -> tuple[str, ...]:
    left_lines = left.splitlines(keepends=True)
    right_lines = right.splitlines(keepends=True)
    spans: set[str] = set()
    for left_start in range(len(left_lines)):
        for right_start in range(len(right_lines)):
            length = 0
            while (
                left_start + length < len(left_lines)
                and right_start + length < len(right_lines)
                and left_lines[left_start + length] == right_lines[right_start + length]
            ):
                length += 1
                spans.add("".join(left_lines[left_start : left_start + length]))
    return tuple(
        sorted(
            span
            for span in spans
            if not any(span in other for other in spans if span != other)
        )
    )


def _topology_seed_law(
    topology: harness.RootInstructionTopology,
) -> tuple[str, str]:
    placed = dict(topology.files)
    for link, target in topology.symlinks.items():
        placed[link] = placed[target]
    claude = placed.get(harness.INSTRUCTION_CLAUDE)
    agents = placed.get(harness.INSTRUCTION_AGENTS, claude)
    if claude is None:
        claude = agents
    return claude or "", agents or ""


def _shared_region_law(topology: harness.RootInstructionTopology) -> str | None:
    claude, agents = _topology_seed_law(topology)
    if (
        harness.INSTRUCTION_AGENTS in claude
        and len(claude) <= MODULE.DELEGATION_STUB_MAX_CHARACTERS
    ) or (
        harness.INSTRUCTION_CLAUDE in agents
        and len(agents) <= MODULE.DELEGATION_STUB_MAX_CHARACTERS
    ):
        return None

    claude = _without_retired_managed_block(claude)
    agents = _without_retired_managed_block(agents)
    spans = _maximal_common_whole_line_spans(claude, agents)
    if not spans:
        return None
    span = max(spans, key=len)
    larger_length = max(len(claude), len(agents))
    if (
        larger_length == 0
        or Fraction(len(span), larger_length)
        <= Fraction(str(MODULE.BOOTSTRAP_SHARED_THRESHOLD))
        or not span.strip()
    ):
        return None
    return span.strip("\n")


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
    observations = evidence.observe_check_router_states(tmp_path)

    assert len(observations) == 4
    for observation in observations:
        if not observation.block_present:
            expected = MODULE.InstructionStatus.ABSENT.value
        elif (
            observation.block_version is None
            or _version_tuple(observation.block_version)
            < _version_tuple(observation.installed_version)
            or observation.recorded_languages != observation.detected_languages
        ):
            expected = MODULE.InstructionStatus.STALE.value
        else:
            expected = MODULE.InstructionStatus.CURRENT.value
        assert observation.exit_code == 0, observation.name
        assert observation.report == expected, observation.name


def test_shared_region_state_maps_to_its_check_report(tmp_path: pathlib.Path) -> None:
    observations = evidence.observe_check_shared_region_states(tmp_path)

    assert len(observations) == 3
    for observation in observations:
        regions_match = (
            observation.claude_region is not None
            and observation.agents_region is not None
            and observation.claude_region == observation.agents_region
        )
        expected = (
            MODULE.InstructionStatus.CURRENT.value
            if regions_match
            else MODULE.InstructionStatus.STALE.value
        )
        assert observation.exit_code == 0, observation.name
        assert observation.report == expected, observation.name


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
    for case in harness.bootstrap_topology_cases():
        topology = case.factory()
        expected_region_body = _shared_region_law(topology)
        outcome = harness.observe_bootstrap_outcome(tmp_path / case.name, case.factory)
        documents = {
            harness.INSTRUCTION_CLAUDE: outcome.claude,
            harness.INSTRUCTION_AGENTS: outcome.agents,
        }

        if expected_region_body is None:
            assert MODULE.parse_shared_regions(outcome.claude) == {}, case.name
            assert MODULE.parse_shared_regions(outcome.agents) == {}, case.name
        else:
            expected = {harness.SHARED_REGION_NAME: expected_region_body}
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
            for token in harness.retired_managed_block_tokens():
                if any(token in body for body in topology.files.values()):
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
            if expected_region_body is None:
                assert own_seed.strip() in document, case.name
            else:
                cursor = 0
                for line in own_lines:
                    found = document.find(line, cursor)
                    assert found >= 0, (case.name, line)
                    cursor = found + len(line)


def test_enabled_language_set_maps_to_presence_of_the_gated_section() -> None:
    observations = harness.canonical_language_presence_observations()

    assert any(o.languages for o in observations)
    assert any(not o.languages for o in observations)
    # The assertion is general, so it is judged against every gated section the template
    # carries rather than one instance standing in for the class.
    assert len(observations[0].gated_sections) > 1
    for observation in observations:
        for section in observation.gated_sections:
            # Each section introduces per-language tables and carries none of its own, so it
            # belongs in the render exactly when some language block survives to follow it.
            present = section in observation.rendered
            assert present == bool(observation.languages), (
                observation.languages,
                section[:60],
            )


def test_root_body_shape_maps_to_delegation_candidacy() -> None:
    cases = harness.delegation_candidate_cases()

    assert len(cases) == 4
    for case in cases:
        expected = (
            case.other_filename in case.body
            and len(case.body) <= MODULE.DELEGATION_STUB_MAX_CHARACTERS
        )
        assert (
            MODULE.is_delegation_candidate(case.body, case.other_filename) is expected
        ), case.name
