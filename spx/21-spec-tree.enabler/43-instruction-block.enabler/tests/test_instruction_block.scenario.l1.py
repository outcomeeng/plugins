"""Scenario evidence for the instruction-block render model.

Each scenario exercises one concrete interaction of the generator and its shared-region
reconcile: rendering both root files, preserving a shared region and independent prose across a
re-render, the router marker format, per-harness divergence, new-section propagation, template
path rejection, staleness of an unparseable version, symlink and legacy-block migration,
quoted-marker safety, blank-run preservation, and the git-recency reconcile of a diverged shared
region. The harness owns all fixture setup — templates, topologies, git commits at fixed dates.
"""

from __future__ import annotations

import pathlib

import pytest

from outcomeeng_testing.harnesses import instruction_block as harness

MODULE = harness.load_instruction_block_module()


def _template(tmp_path: pathlib.Path, *, extra_section: bool = False) -> pathlib.Path:
    return harness.write_template(
        tmp_path, harness.NEW_VERSION, extra_section=extra_section
    )


def test_write_produces_both_files_language_and_harness_filtered(
    tmp_path: pathlib.Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    harness.run_generator_write_primary(repo, _template(tmp_path))
    claude = (repo / harness.INSTRUCTION_CLAUDE).read_text(encoding="utf-8")
    agents = (repo / harness.INSTRUCTION_AGENTS).read_text(encoding="utf-8")

    assert f"### {harness.LANG_PRIMARY.capitalize()}" in claude
    assert f"### {harness.LANG_SECONDARY.capitalize()}" not in claude
    assert harness.harness_line(harness.HARNESS_CLAUDE) in claude
    assert harness.harness_line(harness.HARNESS_CODEX) not in claude
    assert harness.harness_line(harness.HARNESS_CODEX) in agents
    assert harness.harness_line(harness.HARNESS_CLAUDE) not in agents


def test_write_preserves_shared_region_and_independent_prose(
    tmp_path: pathlib.Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    harness.write_both_root_files_with_shared_region(
        MODULE, repo, languages=(harness.LANG_PRIMARY,), version=harness.NEW_VERSION
    )
    marker = "INDEPENDENT PROSE MARKER"
    claude = repo / harness.INSTRUCTION_CLAUDE
    claude.write_text(
        claude.read_text(encoding="utf-8") + f"\n{marker}\n", encoding="utf-8"
    )

    harness.run_generator_write_primary(repo, _template(tmp_path))
    result = claude.read_text(encoding="utf-8")
    assert marker in result
    assert (
        MODULE.parse_shared_regions(result)[harness.SHARED_REGION_NAME]
        == harness.SHARED_REGION_BODY
    )


def test_router_marker_format(tmp_path: pathlib.Path) -> None:
    rendered = MODULE.render(
        harness.build_template(harness.NEW_VERSION),
        (harness.LANG_PRIMARY,),
        harness.NEW_VERSION,
        harness.HARNESS_CLAUDE,
    )
    assert rendered.startswith(
        MODULE.router_marker(harness.NEW_VERSION, (harness.LANG_PRIMARY,))
    )
    assert MODULE.ROUTER_BLOCK_END in rendered
    assert MODULE.TEMPLATE_SOURCE_KEY not in rendered


def test_both_files_identical_except_harness_spans(tmp_path: pathlib.Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    harness.run_generator_write_primary(repo, _template(tmp_path))
    claude = (repo / harness.INSTRUCTION_CLAUDE).read_text(encoding="utf-8")
    agents = (repo / harness.INSTRUCTION_AGENTS).read_text(encoding="utf-8")
    placeholder = "HARNESS-SPAN"
    claude_norm = claude.replace(
        harness.harness_line(harness.HARNESS_CLAUDE), placeholder
    )
    agents_norm = agents.replace(
        harness.harness_line(harness.HARNESS_CODEX), placeholder
    )
    assert claude_norm == agents_norm


def test_newer_template_adds_section_preserving_shared_region(
    tmp_path: pathlib.Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    harness.write_both_root_files_with_shared_region(
        MODULE, repo, languages=(harness.LANG_PRIMARY,), version=harness.NEW_VERSION
    )
    harness.run_generator_write_primary(repo, _template(tmp_path, extra_section=True))
    claude = (repo / harness.INSTRUCTION_CLAUDE).read_text(encoding="utf-8")
    assert f"## {harness.NEW_SECTION}" in claude
    assert (
        MODULE.parse_shared_regions(claude)[harness.SHARED_REGION_NAME]
        == harness.SHARED_REGION_BODY
    )


def test_template_symlink_is_rejected(tmp_path: pathlib.Path) -> None:
    real = _template(tmp_path)
    link = tmp_path / "link-template.md"
    link.symlink_to(real)
    repo = tmp_path / "repo"
    repo.mkdir()
    code = MODULE.main(
        [
            "--template",
            str(link),
            "--repo-root",
            str(repo),
            "--languages",
            harness.LANG_PRIMARY,
            "--write",
        ]
    )
    assert code == 2


def test_unparseable_version_is_stale(tmp_path: pathlib.Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    block = MODULE.render(
        harness.build_template(harness.NEW_VERSION),
        (harness.LANG_PRIMARY,),
        harness.NEW_VERSION,
        harness.HARNESS_CLAUDE,
    )
    corrupted = block.replace(f"v{harness.NEW_VERSION}", "vNOT-NUMERIC")
    claude = repo / harness.INSTRUCTION_CLAUDE
    claude.write_text(MODULE.prepend_router_block(corrupted, ""), encoding="utf-8")
    assert (
        MODULE.instruction_status(
            claude, harness.NEW_VERSION, (harness.LANG_PRIMARY,), repo
        )
        == "stale"
    )


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
    repo = tmp_path / "repo"
    repo.mkdir()
    heading = MODULE.RETIRED_GENERATED_INSTRUCTION_HEADINGS[0]
    legacy = (
        f'---\n{MODULE.TEMPLATE_VERSION_KEY}: "0.1.0"\n'
        f"{MODULE.TEMPLATE_SOURCE_KEY}: {MODULE.DEFAULT_TEMPLATE_SOURCE}\n---\n"
        f"{heading}\n\nretired generated body\n"
    )
    for name in (harness.INSTRUCTION_CLAUDE, harness.INSTRUCTION_AGENTS):
        (repo / name).write_text(legacy, encoding="utf-8")

    harness.run_generator_write_primary(repo, _template(tmp_path))
    result = (repo / harness.INSTRUCTION_CLAUDE).read_text(encoding="utf-8")
    assert "retired generated body" not in result
    assert result.startswith(MODULE.ROUTER_MARKER_PREFIX)


def test_legacy_marker_block_reported_stale_and_replaced(
    tmp_path: pathlib.Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    open_marker, close_marker = MODULE.LEGACY_MANAGED_BLOCK_MARKERS[0]
    legacy_doc = (
        f"{open_marker}\n{MODULE.MANAGED_TEMPLATE_VERSION_PREFIX} 0.1.0 -->\n"
        f"retired block body\n{close_marker}\n\nproduct prose kept\n"
    )
    for name in (harness.INSTRUCTION_CLAUDE, harness.INSTRUCTION_AGENTS):
        (repo / name).write_text(legacy_doc, encoding="utf-8")

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


def test_quoted_router_marker_in_prose_is_preserved(tmp_path: pathlib.Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    quoted = (
        f"The router opening marker is "
        f"`{MODULE.router_marker(harness.NEW_VERSION, (harness.LANG_PRIMARY,))}` in prose.\n"
    )
    for name in (harness.INSTRUCTION_CLAUDE, harness.INSTRUCTION_AGENTS):
        (repo / name).write_text(quoted, encoding="utf-8")

    harness.run_generator_write_primary(repo, _template(tmp_path))
    result = (repo / harness.INSTRUCTION_CLAUDE).read_text(encoding="utf-8")
    assert "in prose." in result
    assert result.count(MODULE.ROUTER_BLOCK_END) == 1


def test_quoted_shared_fence_in_prose_is_not_a_region() -> None:
    inline = f"Use `{MODULE.shared_open_marker('example')}` inline to open a region.\n"
    assert MODULE.parse_shared_regions(inline) == {}


def test_blank_run_in_independent_content_preserved(tmp_path: pathlib.Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    seed = "# Product\n\nfirst\n\n\n\nsecond\n"
    for name in (harness.INSTRUCTION_CLAUDE, harness.INSTRUCTION_AGENTS):
        (repo / name).write_text(seed, encoding="utf-8")

    harness.run_generator_write_primary(repo, _template(tmp_path))
    result = (repo / harness.INSTRUCTION_CLAUDE).read_text(encoding="utf-8")
    assert "first\n\n\n\nsecond" in result


def _init_repo_with_committed_shared_region(
    tmp_path: pathlib.Path,
    *,
    claude_region: str,
    agents_region: str,
    timestamp: int,
) -> pathlib.Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    harness.init_git_identity(repo)
    harness.write_both_root_files_with_shared_region(
        MODULE,
        repo,
        languages=(harness.LANG_PRIMARY,),
        version=harness.NEW_VERSION,
        claude_region=claude_region,
        agents_region=agents_region,
    )
    harness.git_commit_at(
        repo, timestamp, harness.INSTRUCTION_CLAUDE, harness.INSTRUCTION_AGENTS
    )
    return repo


def test_diverged_shared_region_reconciles_to_more_recent_side(
    tmp_path: pathlib.Path,
) -> None:
    repo = _init_repo_with_committed_shared_region(
        tmp_path,
        claude_region=harness.SHARED_REGION_BODY,
        agents_region=harness.SHARED_REGION_BODY,
        timestamp=1000,
    )
    # diverge CLAUDE's region and commit only CLAUDE at a later date, making it the newer side
    claude = repo / harness.INSTRUCTION_CLAUDE
    claude.write_text(
        MODULE.set_shared_region(
            claude.read_text(encoding="utf-8"),
            harness.SHARED_REGION_NAME,
            harness.SHARED_REGION_BODY_ALT,
        ),
        encoding="utf-8",
    )
    harness.git_commit_at(repo, 2000, harness.INSTRUCTION_CLAUDE)

    report = MODULE.reconcile_root_shared_regions(repo)
    assert harness.SHARED_REGION_NAME in report.reconciled
    agents_regions = MODULE.parse_shared_regions(
        (repo / harness.INSTRUCTION_AGENTS).read_text(encoding="utf-8")
    )
    assert agents_regions[harness.SHARED_REGION_NAME] == harness.SHARED_REGION_BODY_ALT


def test_reconcile_replaces_losing_region_whole_without_blending(
    tmp_path: pathlib.Path,
) -> None:
    repo = _init_repo_with_committed_shared_region(
        tmp_path,
        claude_region=harness.SHARED_REGION_BODY,
        agents_region=harness.SHARED_REGION_BODY,
        timestamp=1000,
    )
    claude = repo / harness.INSTRUCTION_CLAUDE
    claude.write_text(
        MODULE.set_shared_region(
            claude.read_text(encoding="utf-8"),
            harness.SHARED_REGION_NAME,
            harness.SHARED_REGION_BODY_ALT,
        ),
        encoding="utf-8",
    )
    harness.git_commit_at(repo, 2000, harness.INSTRUCTION_CLAUDE)

    MODULE.reconcile_root_shared_regions(repo)
    agents_region = MODULE.parse_shared_regions(
        (repo / harness.INSTRUCTION_AGENTS).read_text(encoding="utf-8")
    )[harness.SHARED_REGION_NAME]
    # the winning body is present whole; no trace of the losing body survives
    assert agents_region == harness.SHARED_REGION_BODY_ALT
    assert harness.SHARED_REGION_BODY not in agents_region


def test_recency_tie_is_reported_ambiguous(tmp_path: pathlib.Path) -> None:
    repo = _init_repo_with_committed_shared_region(
        tmp_path,
        claude_region=harness.SHARED_REGION_BODY,
        agents_region=harness.SHARED_REGION_BODY_ALT,
        timestamp=1000,
    )
    report = MODULE.reconcile_root_shared_regions(repo)
    assert harness.SHARED_REGION_NAME in report.tie
    assert report.reconciled == ()


def test_one_sided_shared_region_is_reported_ambiguous(
    tmp_path: pathlib.Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    harness.init_git_identity(repo)
    (repo / harness.INSTRUCTION_CLAUDE).write_text(
        harness.root_document_with_shared_region(
            MODULE,
            harness.HARNESS_CLAUDE,
            harness.SHARED_REGION_BODY,
            languages=(harness.LANG_PRIMARY,),
            version=harness.NEW_VERSION,
        ),
        encoding="utf-8",
    )
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
    harness.git_commit_at(
        repo, 1000, harness.INSTRUCTION_CLAUDE, harness.INSTRUCTION_AGENTS
    )

    report = MODULE.reconcile_root_shared_regions(repo)
    assert harness.SHARED_REGION_NAME in report.one_sided
    assert report.reconciled == ()


def test_reconcile_makes_no_change_to_a_dirty_file(tmp_path: pathlib.Path) -> None:
    repo = _init_repo_with_committed_shared_region(
        tmp_path,
        claude_region=harness.SHARED_REGION_BODY,
        agents_region=harness.SHARED_REGION_BODY,
        timestamp=1000,
    )
    # diverge CLAUDE in the working tree WITHOUT committing -> dirty
    claude = repo / harness.INSTRUCTION_CLAUDE
    claude.write_text(
        MODULE.set_shared_region(
            claude.read_text(encoding="utf-8"),
            harness.SHARED_REGION_NAME,
            harness.SHARED_REGION_BODY_ALT,
        ),
        encoding="utf-8",
    )
    report = MODULE.reconcile_root_shared_regions(repo)
    assert harness.INSTRUCTION_CLAUDE in report.dirty
    # AGENTS untouched, still carrying its committed body
    agents_region = MODULE.parse_shared_regions(
        (repo / harness.INSTRUCTION_AGENTS).read_text(encoding="utf-8")
    )[harness.SHARED_REGION_NAME]
    assert agents_region == harness.SHARED_REGION_BODY
