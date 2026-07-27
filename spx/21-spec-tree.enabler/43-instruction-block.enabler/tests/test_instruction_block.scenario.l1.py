import pathlib

from outcomeeng_testing.harnesses import instruction_block as harness
from outcomeeng_testing.harnesses import instruction_block_scenario_evidence as evidence

MODULE = harness.load_instruction_block_module()


def _template(tmp_path: pathlib.Path) -> pathlib.Path:
    return harness.write_template(tmp_path, harness.NEW_VERSION)


def test_instruction_block_scenario_evidence() -> None:
    assert (
        evidence.scenario_evidence_run().executed
        == evidence.scenario_evidence_declarations()
    )


def test_a_pointer_body_survives_a_write_that_carries_no_operator_answer(
    tmp_path: pathlib.Path,
) -> None:
    outcome = harness.observe_bootstrap_outcome(
        tmp_path, harness.root_instruction_topology_delegating
    )
    pointer = outcome.seeds[harness.INSTRUCTION_CLAUDE].strip()

    # Adoption replaces a whole body, so the write never decides it — the pointer stands until the
    # operator answers, and no region is wrapped over two bodies that still differ.
    assert pointer in outcome.claude
    assert harness.ROOT_AGENTS_BODY.strip() in outcome.agents
    assert MODULE.parse_shared_regions(outcome.claude) == {}
    assert MODULE.parse_shared_regions(outcome.agents) == {}
    assert outcome.claude.startswith(MODULE.ROUTER_MARKER_PREFIX)
    assert outcome.agents.startswith(MODULE.ROUTER_MARKER_PREFIX)


def test_an_operator_answer_adopts_the_body_it_names(tmp_path: pathlib.Path) -> None:
    outcome = harness.observe_bootstrap_outcome(
        tmp_path, harness.root_instruction_topology_delegating, adopt_harness="codex"
    )
    pointer = outcome.seeds[harness.INSTRUCTION_CLAUDE].strip()
    shared_body = harness.ROOT_AGENTS_BODY.strip("\n")

    assert MODULE.parse_shared_regions(outcome.claude) == {
        harness.SHARED_REGION_NAME: shared_body
    }
    assert MODULE.parse_shared_regions(outcome.agents) == {
        harness.SHARED_REGION_NAME: shared_body
    }
    assert pointer not in outcome.claude
    assert pointer not in outcome.agents
    assert outcome.claude.startswith(MODULE.ROUTER_MARKER_PREFIX)
    assert outcome.agents.startswith(MODULE.ROUTER_MARKER_PREFIX)


def test_both_pointer_bodies_are_reported_and_neither_is_adopted(
    tmp_path: pathlib.Path,
) -> None:
    repo = tmp_path / "repo"
    seeds = harness.materialize_root_instruction_topology(
        repo, harness.root_instruction_topology_mutual_delegation()
    )

    reported = MODULE.unresolved_delegation(repo)

    # Neither stub carries a body for the other to take, so both are reported rather than one being
    # picked; the write then leaves each file its own pointer.
    assert set(reported) == {harness.INSTRUCTION_CLAUDE, harness.INSTRUCTION_AGENTS}
    harness.run_generator_write_primary(
        repo, harness.write_template(tmp_path, harness.NEW_VERSION)
    )
    claude = (repo / harness.INSTRUCTION_CLAUDE).read_text(encoding="utf-8")
    agents = (repo / harness.INSTRUCTION_AGENTS).read_text(encoding="utf-8")
    assert seeds[harness.INSTRUCTION_CLAUDE].strip() in claude
    assert seeds[harness.INSTRUCTION_AGENTS].strip() in agents
    assert MODULE.parse_shared_regions(claude) == {}
    assert MODULE.parse_shared_regions(agents) == {}


def test_an_unresolved_pointer_keeps_the_surface_stale(tmp_path: pathlib.Path) -> None:
    repo = tmp_path / "repo"
    harness.materialize_root_instruction_topology(
        repo, harness.root_instruction_topology_delegating()
    )
    template = harness.write_template(tmp_path, harness.NEW_VERSION)
    harness.run_generator_write_primary(repo, template)

    # The routers are current after that write, so only the pending answer can hold the surface
    # stale — reporting current here would strand the pointer unresolved forever.
    assert MODULE.unresolved_delegation(repo) == (harness.INSTRUCTION_CLAUDE,)
    assert harness.run_generator_check(repo, template)[1] == "stale"

    harness.run_generator_write_primary(repo, template, adopt_harness="codex")

    assert MODULE.unresolved_delegation(repo) == ()
    assert harness.run_generator_check(repo, template)[1] == "current"


def test_symlinked_root_file_becomes_regular_file(tmp_path: pathlib.Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / harness.INSTRUCTION_AGENTS).write_text(
        harness.ROOT_SHARED_BODY, encoding="utf-8"
    )
    (repo / harness.INSTRUCTION_CLAUDE).symlink_to(harness.INSTRUCTION_AGENTS)
    assert (repo / harness.INSTRUCTION_CLAUDE).is_symlink()

    harness.run_generator_write_primary(repo, _template(tmp_path))

    assert not (repo / harness.INSTRUCTION_CLAUDE).is_symlink()
    assert (repo / harness.INSTRUCTION_CLAUDE).is_file()
    for name in (harness.INSTRUCTION_CLAUDE, harness.INSTRUCTION_AGENTS):
        assert (
            (repo / name)
            .read_text(encoding="utf-8")
            .startswith(MODULE.ROUTER_MARKER_PREFIX)
        )


def test_markerless_generated_body_is_replaced(tmp_path: pathlib.Path) -> None:
    heading = MODULE.RETIRED_GENERATED_INSTRUCTION_HEADINGS[0]
    retired = (
        f'---\n{MODULE.TEMPLATE_VERSION_KEY}: "0.1.0"\n'
        f"{MODULE.TEMPLATE_SOURCE_KEY}: {MODULE.DEFAULT_TEMPLATE_SOURCE}\n---\n"
        f"{heading}\n\nretired generated body\n"
    )
    repo = harness.seed_both_root_files(tmp_path / "repo", retired)

    harness.run_generator_write_primary(repo, _template(tmp_path))

    result = (repo / harness.INSTRUCTION_CLAUDE).read_text(encoding="utf-8")
    assert "retired generated body" not in result
    assert result.startswith(MODULE.ROUTER_MARKER_PREFIX)


def test_retired_marker_block_reported_stale_and_replaced(
    tmp_path: pathlib.Path,
) -> None:
    open_marker, close_marker = MODULE.LEGACY_MANAGED_BLOCK_MARKERS[0]
    retired_doc = (
        f"{open_marker}\n{MODULE.MANAGED_TEMPLATE_VERSION_PREFIX} 0.1.0 -->\n"
        f"retired block body\n{close_marker}\n\nproduct prose kept\n"
    )
    repo = harness.seed_both_root_files(tmp_path / "repo", retired_doc)
    claude = repo / harness.INSTRUCTION_CLAUDE

    assert (
        MODULE.instruction_status(
            claude, harness.NEW_VERSION, (harness.LANG_PRIMARY,), repo
        )
        == "stale"
    )

    harness.run_generator_write_primary(repo, _template(tmp_path))

    result = claude.read_text(encoding="utf-8")
    assert open_marker not in result
    assert result.startswith(MODULE.ROUTER_MARKER_PREFIX)
    assert "product prose kept" in result


def test_blank_run_in_independent_content_preserved(tmp_path: pathlib.Path) -> None:
    repo = harness.seed_both_root_files(
        tmp_path / "repo", "# Product\n\nfirst\n\n\n\nsecond\n"
    )

    harness.run_generator_write_primary(repo, _template(tmp_path))

    result = (repo / harness.INSTRUCTION_CLAUDE).read_text(encoding="utf-8")
    assert "first\n\n\n\nsecond" in result


def test_malformed_shared_fence_is_reported_stale(tmp_path: pathlib.Path) -> None:
    block = MODULE.render(
        harness.build_template(harness.NEW_VERSION),
        (harness.LANG_PRIMARY,),
        harness.NEW_VERSION,
        harness.HARNESS_CLAUDE,
    )
    # A shared open fence with no matching close: parse_shared_regions skips it, so drift and
    # --check would report current unless the malformed fence is surfaced.
    body = f"{MODULE.shared_open_marker('commands')}\n\nbody with no closing fence\n"
    doc = MODULE.prepend_router_block(block, body)
    repo = harness.seed_both_root_files(tmp_path / "repo", doc)
    claude = repo / harness.INSTRUCTION_CLAUDE

    assert MODULE.parse_shared_regions(doc) == {}
    assert (
        MODULE.instruction_status(
            claude, harness.NEW_VERSION, (harness.LANG_PRIMARY,), repo
        )
        == "stale"
    )
    assert "commands" in MODULE.shared_region_drift(repo)


def test_bootstrap_refuses_a_malformed_seed_fence() -> None:
    # Both seeds carry the same malformed (unclosed) shared fence. parse_shared_regions reads them
    # as region-free, so a naive bootstrap would wrap the dangling marker into a new region and bury
    # it in a permanently stuck stale state. The bootstrap refuses and leaves the fence as
    # independent content, which --check and drift surface as malformed.
    open_marker = MODULE.shared_open_marker("commands")
    seed = f"# Head\n\n{open_marker}\n\nbody with no close\n\nmore product content.\n"
    blocks = {
        harness_name: MODULE.render(
            harness.build_template(harness.NEW_VERSION),
            (harness.LANG_PRIMARY,),
            harness.NEW_VERSION,
            harness_name,
        )
        for harness_name in MODULE.AGENT_HARNESS_INSTRUCTION_FILENAMES
    }

    docs = MODULE.build_root_instruction_documents(
        {"claude": seed, "codex": seed}, blocks
    )

    claude_doc = docs["claude"]
    assert MODULE.parse_shared_regions(claude_doc) == {}
    assert "commands" in MODULE.malformed_shared_regions(claude_doc)
    assert claude_doc.startswith(MODULE.ROUTER_MARKER_PREFIX)


def test_duplicate_shared_region_name_is_malformed() -> None:
    open_marker = MODULE.shared_open_marker("commands")
    close_marker = MODULE.shared_close_marker("commands")
    # The same name opened twice: parse_shared_regions silently collapses to the last body, so the
    # duplicate is surfaced as malformed rather than letting a diverged earlier region hide.
    duplicated = (
        f"# Head\n\n{open_marker}\n\nfirst\n\n{close_marker}\n\n"
        f"{open_marker}\n\nsecond\n\n{close_marker}\n"
    )

    assert MODULE.parse_shared_regions(duplicated) == {"commands": "second"}
    assert "commands" in MODULE.malformed_shared_regions(duplicated)


def test_bootstrap_preserves_lines_when_common_span_ends_mid_line() -> None:
    # Two root files more than 80% identical whose longest common span ends mid-line, at a
    # harness-specific word — the case a byte-level span would split across the fence.
    claude = harness.ROOT_NEAR_IDENTICAL_CLAUDE
    codex = harness.ROOT_NEAR_IDENTICAL_CODEX
    _, ratio = MODULE.biggest_identical_span(claude, codex)
    assert ratio > MODULE.BOOTSTRAP_SHARED_THRESHOLD

    wrapped_claude, wrapped_codex = MODULE.bootstrap_wrap(claude, codex)

    region_claude = MODULE.parse_shared_regions(wrapped_claude)[
        MODULE.BOOTSTRAP_SHARED_REGION_NAME
    ]
    region_codex = MODULE.parse_shared_regions(wrapped_codex)[
        MODULE.BOOTSTRAP_SHARED_REGION_NAME
    ]
    # The shared region is byte-identical across the two files.
    assert region_claude == region_codex
    # Every original line survives intact in each wrapped file — no line split across the fence.
    for line in (candidate for candidate in claude.splitlines() if candidate.strip()):
        assert line in wrapped_claude
    for line in (candidate for candidate in codex.splitlines() if candidate.strip()):
        assert line in wrapped_codex
    # Every harness-specific line stays in independent content, outside the shared region.
    claude_only = set(claude.splitlines()) - set(codex.splitlines())
    codex_only = set(codex.splitlines()) - set(claude.splitlines())
    assert claude_only.isdisjoint(region_claude.splitlines())
    assert codex_only.isdisjoint(region_codex.splitlines())


def test_bootstrap_finds_whole_line_block_over_longer_straddling_match() -> None:
    # The byte-level-longest common substring is the long near-duplicate line, which snaps away to
    # nothing at a line boundary; the biggest *whole-line* span is the block elsewhere. The span is
    # that block, not empty — proving the search considers more than the single longest byte match.
    claude = harness.ROOT_STRADDLING_CLAUDE
    codex = harness.ROOT_STRADDLING_CODEX

    span, _ = MODULE.biggest_identical_span(claude, codex)

    shared_lines = set(claude.splitlines()) & set(codex.splitlines())
    divergent_lines = set(claude.splitlines()) ^ set(codex.splitlines())
    assert shared_lines
    assert all(line in span for line in shared_lines)
    assert all(line not in span for line in divergent_lines)


def test_bootstrap_snaps_span_to_line_boundaries_in_both_files() -> None:
    # The shared content starts at a line boundary in one file but mid-line in the other — the
    # second file carries a harness-specific prefix on the otherwise-shared first line. Snapping to
    # line boundaries in only the first file would place the fence mid-line in the second and split
    # its line; the span is whole lines in both files.
    claude = harness.ROOT_MIDLINE_CLAUDE
    codex = harness.ROOT_MIDLINE_CODEX

    wrapped_claude, wrapped_codex = MODULE.bootstrap_wrap(claude, codex)

    region_claude = MODULE.parse_shared_regions(wrapped_claude)[
        MODULE.BOOTSTRAP_SHARED_REGION_NAME
    ]
    region_codex = MODULE.parse_shared_regions(wrapped_codex)[
        MODULE.BOOTSTRAP_SHARED_REGION_NAME
    ]
    assert region_claude == region_codex
    # Every whole line survives intact in both files — the prefixed line is never split.
    for line in (candidate for candidate in claude.splitlines() if candidate.strip()):
        assert line in wrapped_claude
    for line in (candidate for candidate in codex.splitlines() if candidate.strip()):
        assert line in wrapped_codex
    # The divergent prefixed line stays whole in independent content, never inside the region.
    codex_only = set(codex.splitlines()) - set(claude.splitlines())
    assert codex_only.issubset(set(wrapped_codex.splitlines()))
