"""Mapping evidence for the instruction-block render model.

Each mapping asserts a total input->output correspondence over a finite, source-owned domain:
test extension to language, enabled language to rendered block, ``--check`` state to report
word, shared-region state to report word, initial topology to bootstrap outcome, and span
ratio to the wrap decision. The domains come from the generator's own constants and the
harness's topology fixtures; the test file owns no boundary values.
"""

from __future__ import annotations

import pathlib
from collections.abc import Callable

import pytest

from outcomeeng_testing.harnesses import instruction_block as harness

MODULE = harness.load_instruction_block_module()


@pytest.mark.parametrize(
    "extension,language", sorted(MODULE.LANGUAGE_BY_EXTENSION.items())
)
def test_extension_maps_to_language(extension: str, language: str) -> None:
    assert MODULE.language_for_extension(extension) == language
    assert MODULE.language_for_extension(f".{extension}") == language


def test_detected_language_set_is_the_mapped_extensions() -> None:
    extensions = tuple(MODULE.LANGUAGE_BY_EXTENSION)
    assert MODULE.detect_languages(extensions) == MODULE.normalize_languages(
        MODULE.LANGUAGE_BY_EXTENSION.values()
    )


@pytest.mark.parametrize("language", harness.TEMPLATE_LANGUAGES)
def test_language_block_appears_iff_enabled(language: str) -> None:
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


def test_check_maps_router_state_to_report(tmp_path: pathlib.Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    template = harness.write_template(tmp_path, harness.NEW_VERSION)
    harness.run_generator_write_primary(repo, template)
    claude = repo / harness.INSTRUCTION_CLAUDE

    def check() -> str:
        return MODULE.instruction_status(
            claude, harness.NEW_VERSION, (harness.LANG_PRIMARY,), repo
        )

    # current: freshly written at the installed version and language
    assert check() == "current"
    # absent: the file removed
    claude.unlink()
    assert check() == "absent"
    # stale: a version numerically behind the installed one
    stale_block = MODULE.render(
        harness.build_template(harness.OLD_VERSION),
        (harness.LANG_PRIMARY,),
        harness.OLD_VERSION,
        harness.HARNESS_CLAUDE,
    )
    claude.write_text(MODULE.prepend_router_block(stale_block, ""), encoding="utf-8")
    assert check() == "stale"


def test_check_maps_shared_region_state_to_report(tmp_path: pathlib.Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()

    # byte-identical shared regions -> no drift
    harness.write_both_root_files_with_shared_region(
        MODULE, repo, languages=(harness.LANG_PRIMARY,), version=harness.NEW_VERSION
    )
    assert MODULE.shared_region_drift(repo) == ()

    # diverged bodies -> drift names the region
    harness.write_both_root_files_with_shared_region(
        MODULE,
        repo,
        languages=(harness.LANG_PRIMARY,),
        version=harness.NEW_VERSION,
        claude_region=harness.SHARED_REGION_BODY,
        agents_region=harness.SHARED_REGION_BODY_ALT,
    )
    assert harness.SHARED_REGION_NAME in MODULE.shared_region_drift(repo)

    # one-sided region -> drift names the region
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
    assert harness.SHARED_REGION_NAME in MODULE.shared_region_drift(repo)


@pytest.mark.parametrize(
    "topology_factory",
    [
        harness.root_instruction_topology_only_claude,
        harness.root_instruction_topology_only_agents,
        harness.root_instruction_topology_separate,
        harness.root_instruction_topology_symlinked,
    ],
)
def test_topology_maps_to_bootstrap_outcome(
    tmp_path: pathlib.Path,
    topology_factory: Callable[[], harness.RootInstructionTopology],
) -> None:
    repo = tmp_path / "repo"
    seeds = harness.materialize_root_instruction_topology(repo, topology_factory())
    template = harness.write_template(tmp_path, harness.NEW_VERSION)
    harness.run_generator_write_primary(repo, template)

    claude = (repo / harness.INSTRUCTION_CLAUDE).read_text(encoding="utf-8")
    agents = (repo / harness.INSTRUCTION_AGENTS).read_text(encoding="utf-8")
    seeds_identical = (
        seeds[harness.INSTRUCTION_CLAUDE] == seeds[harness.INSTRUCTION_AGENTS]
    )
    # bootstrap wraps one shared region exactly when the two seeded bodies are identical
    assert bool(MODULE.parse_shared_regions(claude)) == seeds_identical
    if seeds_identical:
        assert set(MODULE.parse_shared_regions(claude)) == set(
            MODULE.parse_shared_regions(agents)
        )
    # the router block is always first, whatever the topology
    assert claude.startswith(MODULE.ROUTER_MARKER_PREFIX)
    assert agents.startswith(MODULE.ROUTER_MARKER_PREFIX)


def test_span_ratio_maps_to_wrap_decision() -> None:
    identical = harness.ROOT_SHARED_BODY
    _, ratio_identical = MODULE.biggest_identical_span(identical, identical)
    assert ratio_identical > MODULE.BOOTSTRAP_SHARED_THRESHOLD
    wrapped_a, wrapped_b = MODULE.bootstrap_wrap(identical, identical)
    assert MODULE.parse_shared_regions(wrapped_a)
    assert MODULE.parse_shared_regions(wrapped_b)

    _, ratio_divergent = MODULE.biggest_identical_span(
        harness.ROOT_CLAUDE_BODY, harness.ROOT_AGENTS_BODY
    )
    assert ratio_divergent <= MODULE.BOOTSTRAP_SHARED_THRESHOLD
    no_wrap_a, no_wrap_b = MODULE.bootstrap_wrap(
        harness.ROOT_CLAUDE_BODY, harness.ROOT_AGENTS_BODY
    )
    assert not MODULE.parse_shared_regions(no_wrap_a)
    assert not MODULE.parse_shared_regions(no_wrap_b)
