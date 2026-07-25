"""Mapping harness evidence for the instruction-block render model.

Each mapping asserts a total input->output correspondence over a finite, source-owned domain:
test extension to language, enabled language to rendered block, ``--check`` state to report
word, shared-region state to report word, initial topology to bootstrap outcome, and span
ratio to the wrap decision. The domains come from the generator's own constants and the
harness's topology fixtures; the test file owns no boundary values.
"""

from __future__ import annotations

import pathlib
from collections.abc import Callable
from contextlib import redirect_stderr
from io import StringIO
from tempfile import TemporaryDirectory

from outcomeeng_testing.harnesses import instruction_block as harness

MODULE = harness.load_instruction_block_module()


def _assert_duplicate_cli_flag_maps_to_rejection(option: str) -> None:
    assert MODULE.duplicate_cli_option((option, option)) == option
    with redirect_stderr(StringIO()) as stderr:
        assert MODULE.main([option, option]) == 2
    assert stderr.getvalue().strip() == f"{MODULE.DUPLICATE_FLAG_ERROR_PREFIX}{option}"


def _assert_extension_maps_to_language(extension: str, language: str) -> None:
    assert MODULE.language_for_extension(extension) == language
    assert MODULE.language_for_extension(f".{extension}") == language


def _assert_detected_language_set_is_the_mapped_extensions(
    spx_dir: pathlib.Path,
) -> None:
    extensions = tuple(MODULE.LANGUAGE_BY_EXTENSION)
    harness.write_spx_tree_with_tests(spx_dir, extensions)
    assert MODULE.detect_languages_from_tree(spx_dir) == MODULE.normalize_languages(
        MODULE.LANGUAGE_BY_EXTENSION.values()
    )


def _assert_language_block_appears_iff_enabled(language: str) -> None:
    template = harness.build_template(harness.NEW_VERSION)
    heading = f"### {language.capitalize()}"
    enabled = MODULE.render(
        template, (language,), harness.NEW_VERSION, harness.HARNESS_CLAUDE
    )
    others = tuple(name for name in harness.TEMPLATE_LANGUAGES if name != language)
    disabled = MODULE.render(
        template, others, harness.NEW_VERSION, harness.HARNESS_CLAUDE
    )
    assert heading in enabled
    assert heading not in disabled


def _assert_check_maps_router_state_to_report(tmp_path: pathlib.Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    template = harness.write_template(tmp_path, harness.NEW_VERSION)
    harness.run_generator_write_primary(repo, template)
    claude = repo / harness.INSTRUCTION_CLAUDE
    current = MODULE.InstructionStatus.CURRENT.value
    absent = MODULE.InstructionStatus.ABSENT.value
    stale = MODULE.InstructionStatus.STALE.value

    # current: freshly written at the installed version and language
    assert harness.run_generator_check(repo, template) == (0, current)
    # absent: the file removed
    claude.unlink()
    assert harness.run_generator_check(repo, template) == (0, absent)
    # stale: a version numerically behind the installed one
    stale_block = MODULE.render(
        harness.build_template(harness.OLD_VERSION),
        (harness.LANG_PRIMARY,),
        harness.OLD_VERSION,
        harness.HARNESS_CLAUDE,
    )
    claude.write_text(MODULE.prepend_router_block(stale_block, ""), encoding="utf-8")
    assert harness.run_generator_check(repo, template) == (0, stale)
    # stale: the recorded language set differs from the detected/expected set
    current_block = MODULE.render(
        harness.build_template(harness.NEW_VERSION),
        (harness.LANG_PRIMARY,),
        harness.NEW_VERSION,
        harness.HARNESS_CLAUDE,
    )
    claude.write_text(MODULE.prepend_router_block(current_block, ""), encoding="utf-8")
    assert harness.run_generator_check(
        repo,
        template,
        languages=harness.LANG_SECONDARY,
    ) == (0, stale)


def _assert_check_maps_shared_region_state_to_report(tmp_path: pathlib.Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    template = harness.write_template(tmp_path, harness.NEW_VERSION)
    current = MODULE.InstructionStatus.CURRENT.value
    stale = MODULE.InstructionStatus.STALE.value

    # byte-identical shared regions -> current report
    harness.write_both_root_files_with_shared_region(
        MODULE, repo, languages=(harness.LANG_PRIMARY,), version=harness.NEW_VERSION
    )
    assert harness.run_generator_check(repo, template) == (0, current)

    # diverged bodies -> stale report
    harness.write_both_root_files_with_shared_region(
        MODULE,
        repo,
        languages=(harness.LANG_PRIMARY,),
        version=harness.NEW_VERSION,
        claude_region=harness.SHARED_REGION_BODY,
        agents_region=harness.SHARED_REGION_BODY_ALT,
    )
    assert harness.run_generator_check(repo, template) == (0, stale)

    # one-sided region -> stale report
    codex_block = MODULE.render(
        harness.build_template(harness.NEW_VERSION),
        (harness.LANG_PRIMARY,),
        harness.NEW_VERSION,
        harness.HARNESS_CODEX,
    )
    (repo / harness.INSTRUCTION_AGENTS).write_text(
        MODULE.prepend_router_block(codex_block, harness.ROOT_AGENTS_BODY),
        encoding="utf-8",
    )
    assert harness.run_generator_check(repo, template) == (0, stale)


def _assert_topology_maps_to_bootstrap_outcome(
    tmp_path: pathlib.Path,
    topology_factory: Callable[[], harness.RootInstructionTopology],
    expected_region_body: str | None,
    removed_tokens: tuple[str, ...] = (),
    delegating_filename: str | None = None,
) -> None:
    repo = tmp_path / "repo"
    seeds = harness.materialize_root_instruction_topology(repo, topology_factory())
    template = harness.write_template(tmp_path, harness.NEW_VERSION)
    harness.run_generator_write_primary(repo, template)

    claude = (repo / harness.INSTRUCTION_CLAUDE).read_text(encoding="utf-8")
    agents = (repo / harness.INSTRUCTION_AGENTS).read_text(encoding="utf-8")
    claude_regions = MODULE.parse_shared_regions(claude)
    agents_regions = MODULE.parse_shared_regions(agents)
    if expected_region_body is None:
        assert claude_regions == {}
        assert agents_regions == {}
        assert seeds[harness.INSTRUCTION_CLAUDE].strip() in claude
        assert seeds[harness.INSTRUCTION_AGENTS].strip() in agents
    else:
        expected_body = expected_region_body.strip("\n")
        assert claude_regions == {harness.SHARED_REGION_NAME: expected_body}
        assert agents_regions == {harness.SHARED_REGION_NAME: expected_body}
        for filename, document in (
            (harness.INSTRUCTION_CLAUDE, claude),
            (harness.INSTRUCTION_AGENTS, agents),
        ):
            other = (
                harness.INSTRUCTION_AGENTS
                if filename == harness.INSTRUCTION_CLAUDE
                else harness.INSTRUCTION_CLAUDE
            )
            exclusive_lines = set(seeds[filename].splitlines()) - set(
                seeds[other].splitlines()
            )
            if filename == delegating_filename:
                # A delegating file adopts the other body, so its own lines are gone.
                assert not any(
                    line.strip() and line in document for line in exclusive_lines
                )
            else:
                assert all(line in document for line in exclusive_lines)
    assert all(token not in claude and token not in agents for token in removed_tokens)
    # the router block is always first, whatever the topology
    assert claude.startswith(MODULE.ROUTER_MARKER_PREFIX)
    assert agents.startswith(MODULE.ROUTER_MARKER_PREFIX)


def _assert_span_ratio_maps_to_wrap_decision() -> None:
    identical = harness.ROOT_SHARED_BODY
    span_identical, ratio_identical = MODULE.biggest_identical_span(
        identical, identical
    )
    assert span_identical == identical
    assert ratio_identical > MODULE.BOOTSTRAP_SHARED_THRESHOLD
    wrapped_a, wrapped_b = MODULE.bootstrap_wrap(identical, identical)
    assert MODULE.parse_shared_regions(wrapped_a)
    assert MODULE.parse_shared_regions(wrapped_b)

    span_near, ratio_near = MODULE.biggest_identical_span(
        harness.ROOT_NEAR_IDENTICAL_CLAUDE,
        harness.ROOT_NEAR_IDENTICAL_CODEX,
    )
    assert span_near == harness.ROOT_NEAR_IDENTICAL_SHARED
    assert ratio_near > MODULE.BOOTSTRAP_SHARED_THRESHOLD

    _, ratio_divergent = MODULE.biggest_identical_span(
        harness.ROOT_CLAUDE_BODY, harness.ROOT_AGENTS_BODY
    )
    assert ratio_divergent <= MODULE.BOOTSTRAP_SHARED_THRESHOLD
    no_wrap_a, no_wrap_b = MODULE.bootstrap_wrap(
        harness.ROOT_CLAUDE_BODY, harness.ROOT_AGENTS_BODY
    )
    assert not MODULE.parse_shared_regions(no_wrap_a)
    assert not MODULE.parse_shared_regions(no_wrap_b)


def mapping_evidence_declarations() -> tuple[str, ...]:
    """Return every finite mapping case identity in execution order."""
    return harness.mapping_evidence_contract()


def mapping_evidence_run() -> harness.EvidenceRun:
    """Run every declared finite source-owned mapping."""
    declared: list[str] = []
    executed: list[str] = []
    for option in MODULE.CLI_OPTION_NAMES:
        case_name = f"duplicate-flag[{option}]"
        declared.append(case_name)
        _assert_duplicate_cli_flag_maps_to_rejection(option)
        executed.append(case_name)
    for extension, language in sorted(MODULE.LANGUAGE_BY_EXTENSION.items()):
        case_name = f"extension[{extension}]"
        declared.append(case_name)
        _assert_extension_maps_to_language(extension, language)
        executed.append(case_name)
    for language in harness.TEMPLATE_LANGUAGES:
        case_name = f"language-block[{language}]"
        declared.append(case_name)
        _assert_language_block_appears_iff_enabled(language)
        executed.append(case_name)

    legacy_markers = tuple(
        marker for pair in MODULE.LEGACY_MANAGED_BLOCK_MARKERS for marker in pair
    )
    legacy_metadata_prefixes = (
        MODULE.MANAGED_TEMPLATE_VERSION_PREFIX,
        MODULE.MANAGED_TEMPLATE_SOURCE_PREFIX,
        MODULE.MANAGED_LANGUAGES_PREFIX,
    )
    topology_cases = (
        (
            harness.root_instruction_topology_only_claude,
            harness.ROOT_CLAUDE_BODY,
            (),
            None,
        ),
        (
            harness.root_instruction_topology_only_agents,
            harness.ROOT_AGENTS_BODY,
            (),
            None,
        ),
        (
            harness.root_instruction_topology_symlinked,
            harness.ROOT_SHARED_BODY,
            (),
            None,
        ),
        (
            harness.root_instruction_topology_identical,
            harness.ROOT_SHARED_BODY,
            (),
            None,
        ),
        (
            harness.root_instruction_topology_legacy_managed,
            harness.ROOT_SHARED_BODY,
            legacy_markers + legacy_metadata_prefixes,
            None,
        ),
        (
            harness.root_instruction_topology_near_identical,
            harness.ROOT_NEAR_IDENTICAL_SHARED,
            (),
            None,
        ),
        (harness.root_instruction_topology_separate, None, (), None),
        (
            harness.root_instruction_topology_delegating,
            harness.ROOT_AGENTS_BODY,
            (),
            harness.INSTRUCTION_CLAUDE,
        ),
        (harness.root_instruction_topology_mutual_delegation, None, (), None),
    )
    with TemporaryDirectory() as directory:
        root = pathlib.Path(directory).resolve()
        declared.append("detected-language-set")
        _assert_detected_language_set_is_the_mapped_extensions(root / "spx")
        executed.append("detected-language-set")
        router_path = root / "router-state"
        router_path.mkdir()
        declared.append("router-state-report")
        _assert_check_maps_router_state_to_report(router_path)
        executed.append("router-state-report")
        shared_path = root / "shared-state"
        shared_path.mkdir()
        declared.append("shared-region-state-report")
        _assert_check_maps_shared_region_state_to_report(shared_path)
        executed.append("shared-region-state-report")
        for index, (
            topology_factory,
            expected_body,
            removed_tokens,
            delegating_filename,
        ) in enumerate(topology_cases):
            case_name = f"topology[{topology_factory.__name__}]"
            declared.append(case_name)
            topology_path = root / f"topology-{index}"
            topology_path.mkdir()
            _assert_topology_maps_to_bootstrap_outcome(
                topology_path,
                topology_factory,
                expected_body,
                removed_tokens,
                delegating_filename,
            )
            executed.append(case_name)

    declared.append("span-ratio-wrap-decision")
    _assert_span_ratio_maps_to_wrap_decision()
    executed.append("span-ratio-wrap-decision")
    return harness.EvidenceRun(declared=tuple(declared), executed=tuple(executed))
