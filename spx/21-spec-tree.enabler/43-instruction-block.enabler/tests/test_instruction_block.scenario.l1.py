import pathlib

import pytest

from outcomeeng_testing.harnesses import instruction_block as harness
from outcomeeng_testing.harnesses import instruction_block_scenario_evidence as evidence

MODULE = harness.load_instruction_block_module()


def _template(tmp_path: pathlib.Path) -> pathlib.Path:
    return harness.write_template(tmp_path, harness.NEW_VERSION)


def test_write_produces_both_files_language_and_harness_filtered(
    tmp_path: pathlib.Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    harness.run_generator_write_primary(repo, evidence.scenario_template(tmp_path))
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

    template = evidence.scenario_template(tmp_path)
    harness.run_generator_write_primary(repo, template)
    result = claude.read_text(encoding="utf-8")
    expected_router = MODULE.render(
        template.read_text(encoding="utf-8"),
        (harness.LANG_PRIMARY,),
        harness.NEW_VERSION,
        harness.HARNESS_CLAUDE,
    )
    assert result.startswith(expected_router.rstrip("\n") + "\n\n")
    assert marker in result
    assert (
        MODULE.parse_shared_regions(result)[harness.SHARED_REGION_NAME]
        == harness.SHARED_REGION_BODY
    )


def test_router_marker_format() -> None:
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
    harness.run_generator_write_primary(repo, evidence.scenario_template(tmp_path))
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
        MODULE, repo, languages=(harness.LANG_PRIMARY,), version=harness.OLD_VERSION
    )
    harness.run_generator_write_primary(
        repo, evidence.scenario_template(tmp_path, extra_section=True)
    )
    for name in harness.INSTRUCTION_CLAUDE, harness.INSTRUCTION_AGENTS:
        rendered = (repo / name).read_text(encoding="utf-8")
        assert f"## {harness.NEW_SECTION}" in rendered, name
        assert MODULE.parse_instruction_languages(rendered) == (
            harness.LANG_PRIMARY,
        ), name
        assert (
            MODULE.parse_shared_regions(rendered)[harness.SHARED_REGION_NAME]
            == harness.SHARED_REGION_BODY
        ), name


def test_template_symlink_is_rejected(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    home = tmp_path / "home"
    home.mkdir()
    real = evidence.scenario_template(home)
    link = home / "link-template.md"
    link.symlink_to(real)
    repo = tmp_path / "repo"
    repo.mkdir()
    arguments = [
        "--repo-root",
        str(repo),
        "--languages",
        harness.LANG_PRIMARY,
        "--write",
    ]
    assert MODULE.main(["--template", str(link), *arguments]) == 2
    monkeypatch.setenv("HOME", str(home))
    assert MODULE.main(["--template", "~/link-template.md", *arguments]) == 2


def test_cli_rejects_template_without_frontmatter_version(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    template = tmp_path / "versionless-template.md"
    delimiter_line = f"{MODULE.FRONTMATTER_DELIMITER}\n"
    template_text = harness.build_template(harness.NEW_VERSION)
    _, after_open = template_text.split(delimiter_line, maxsplit=1)
    _, template_body = after_open.split(delimiter_line, maxsplit=1)
    template.write_text(
        MODULE.router_marker(harness.NEW_VERSION, (harness.LANG_PRIMARY,))
        + "\n"
        + template_body,
        encoding="utf-8",
    )
    repo = tmp_path / "repo"
    repo.mkdir()
    code = MODULE.main(
        ["--template", str(template), "--repo-root", str(repo), "--write"]
    )
    assert code == 2
    assert MODULE.MISSING_TEMPLATE_VERSION_ERROR in capsys.readouterr().err
    assert not (repo / harness.INSTRUCTION_CLAUDE).exists()
    assert not (repo / harness.INSTRUCTION_AGENTS).exists()


def test_cli_rejects_missing_repo_root(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code = MODULE.main(
        [
            "--template",
            str(evidence.scenario_template(tmp_path)),
            "--repo-root",
            str(tmp_path / "does-not-exist"),
            "--write",
        ]
    )
    assert code == 2
    assert "--repo-root does not exist" in capsys.readouterr().err


def test_cli_rejects_non_directory_repo_root(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    plain = tmp_path / "plain.txt"
    plain.write_text("x", encoding="utf-8")
    code = MODULE.main(
        [
            "--template",
            str(evidence.scenario_template(tmp_path)),
            "--repo-root",
            str(plain),
            "--write",
        ]
    )
    assert code == 2
    assert "is not a directory" in capsys.readouterr().err


def test_cli_rejects_missing_template(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    code = MODULE.main(
        ["--template", str(tmp_path / "gone.md"), "--repo-root", str(repo), "--write"]
    )
    assert code == 2
    assert "--template does not exist" in capsys.readouterr().err


def test_cli_rejects_directory_template(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    directory = tmp_path / "as-template"
    directory.mkdir()
    code = MODULE.main(
        ["--template", str(directory), "--repo-root", str(repo), "--write"]
    )
    assert code == 2
    assert "is not a regular file" in capsys.readouterr().err


def test_cli_rejects_root_symlink_escaping_repo(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    outside = tmp_path / "outside.md"
    outside.write_text("secret", encoding="utf-8")
    (repo / harness.INSTRUCTION_CLAUDE).symlink_to(outside)
    (repo / harness.INSTRUCTION_AGENTS).write_text(
        harness.ROOT_SHARED_BODY, encoding="utf-8"
    )
    code = MODULE.main(
        [
            "--template",
            str(evidence.scenario_template(tmp_path)),
            "--repo-root",
            str(repo),
            "--languages",
            harness.LANG_PRIMARY,
            "--write",
        ]
    )
    assert code == 2
    assert "escapes --repo-root" in capsys.readouterr().err


def test_cli_rejects_spx_symlink_during_language_detection(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    for name in (harness.INSTRUCTION_CLAUDE, harness.INSTRUCTION_AGENTS):
        (repo / name).write_text(harness.ROOT_SHARED_BODY, encoding="utf-8")
    (repo / "spx").symlink_to(tmp_path)
    # no --languages forces detection, which resolves <repo-root>/spx and rejects the symlink
    code = MODULE.main(
        [
            "--template",
            str(evidence.scenario_template(tmp_path)),
            "--repo-root",
            str(repo),
            "--write",
        ]
    )
    assert code == 2
    assert "spx directory is a symlink" in capsys.readouterr().err


def test_cli_detects_languages_from_test_extensions(tmp_path: pathlib.Path) -> None:
    spx_dir = tmp_path / "spx"
    harness.write_spx_tree_with_tests(spx_dir, ("py", "ts"))
    assert MODULE.detect_languages_from_tree(spx_dir) == ("python", "typescript")


def test_cli_write_without_repo_root_exits(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code = MODULE.main(
        ["--template", str(evidence.scenario_template(tmp_path)), "--write"]
    )
    assert code == 2
    assert "--write requires --repo-root" in capsys.readouterr().err


def test_cli_check_reports_absent_when_one_file_missing(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    template = harness.write_template(tmp_path, harness.NEW_VERSION)
    harness.run_generator_write_primary(repo, template)
    (repo / harness.INSTRUCTION_CLAUDE).unlink()
    code = MODULE.main(
        [
            "--template",
            str(template),
            "--repo-root",
            str(repo),
            "--languages",
            harness.LANG_PRIMARY,
            "--check",
        ]
    )
    assert code == 0
    # absent dominates: one missing file makes the worst-across-both status absent
    assert capsys.readouterr().out.strip() == "absent"


def test_cli_check_treats_language_order_as_set(tmp_path: pathlib.Path) -> None:
    languages = (harness.LANG_PRIMARY, harness.LANG_SECONDARY)
    block = MODULE.render(
        harness.build_template(harness.NEW_VERSION),
        languages,
        harness.NEW_VERSION,
        harness.HARNESS_CLAUDE,
    )
    repo = tmp_path / "repo"
    repo.mkdir()
    claude = repo / harness.INSTRUCTION_CLAUDE
    claude.write_text(MODULE.prepend_router_block(block, ""), encoding="utf-8")
    # the recorded language set is order-insensitive: a reversed detected order still reads current
    assert (
        MODULE.instruction_status(
            claude, harness.NEW_VERSION, tuple(reversed(languages)), repo
        )
        == "current"
    )


def test_cli_check_marks_router_not_first_as_stale(tmp_path: pathlib.Path) -> None:
    block = MODULE.render(
        harness.build_template(harness.NEW_VERSION),
        (harness.LANG_PRIMARY,),
        harness.NEW_VERSION,
        harness.HARNESS_CLAUDE,
    )
    repo = tmp_path / "repo"
    repo.mkdir()
    claude = repo / harness.INSTRUCTION_CLAUDE

    # router first -> current
    claude.write_text(MODULE.prepend_router_block(block, "PRODUCT"), encoding="utf-8")
    assert (
        MODULE.instruction_status(
            claude, harness.NEW_VERSION, (harness.LANG_PRIMARY,), repo
        )
        == "current"
    )
    # product prose before the router -> stale; the router must be the first content of the file
    claude.write_text(
        "PRODUCT PROSE FIRST\n\n" + MODULE.prepend_router_block(block, "PRODUCT"),
        encoding="utf-8",
    )
    assert (
        MODULE.instruction_status(
            claude, harness.NEW_VERSION, (harness.LANG_PRIMARY,), repo
        )
        == "stale"
    )


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


def test_quoted_router_marker_in_prose_is_preserved(tmp_path: pathlib.Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    quoted = (
        f"The router opening marker is "
        f"`{MODULE.router_marker(harness.NEW_VERSION, (harness.LANG_PRIMARY,))}` in prose.\n"
    )
    for name in (harness.INSTRUCTION_CLAUDE, harness.INSTRUCTION_AGENTS):
        (repo / name).write_text(quoted, encoding="utf-8")

    harness.run_generator_write_primary(repo, evidence.scenario_template(tmp_path))
    result = (repo / harness.INSTRUCTION_CLAUDE).read_text(encoding="utf-8")
    assert "in prose." in result
    assert result.count(MODULE.ROUTER_BLOCK_END) == 1


def test_quoted_router_closing_marker_after_block_is_preserved(
    tmp_path: pathlib.Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    block = MODULE.render(
        harness.build_template(harness.NEW_VERSION),
        (harness.LANG_PRIMARY,),
        harness.NEW_VERSION,
        harness.HARNESS_CLAUDE,
    )
    # independent content after a real router block that inline-quotes the closing marker in prose
    independent = f"Doc note: the router closes with `{MODULE.ROUTER_BLOCK_END}` on its own line.\n"
    doc = MODULE.prepend_router_block(block, independent)
    for name in (harness.INSTRUCTION_CLAUDE, harness.INSTRUCTION_AGENTS):
        (repo / name).write_text(doc, encoding="utf-8")

    harness.run_generator_write_primary(repo, evidence.scenario_template(tmp_path))
    result = (repo / harness.INSTRUCTION_CLAUDE).read_text(encoding="utf-8")
    # the real standalone closing fence bounds the block; the inline-quoted marker in independent
    # content is not mistaken for the block end, so the note survives and the block is single
    assert "Doc note: the router closes with" in result
    assert result.count(MODULE.ROUTER_MARKER_PREFIX) == 1


def test_quoted_shared_fence_in_prose_is_not_a_region() -> None:
    inline = f"Use `{MODULE.shared_open_marker('example')}` inline to open a region.\n"
    assert MODULE.parse_shared_regions(inline) == {}


def test_diverged_shared_region_reconciles_to_more_recent_side(
    tmp_path: pathlib.Path,
) -> None:
    repo = evidence.init_repo_with_committed_shared_region(
        tmp_path,
        claude_region=harness.SHARED_REGION_BODY,
        agents_region=harness.SHARED_REGION_BODY,
        timestamp=1000,
    )
    # diverge CLAUDE's region and commit only CLAUDE at a later date, making it the newer side
    evidence.diverge_region_and_commit(
        repo, harness.INSTRUCTION_CLAUDE, harness.SHARED_REGION_BODY_ALT, 2000
    )

    report = MODULE.reconcile_root_shared_regions(repo)
    assert harness.SHARED_REGION_NAME in report.reconciled
    assert (
        evidence.region_body(repo, harness.INSTRUCTION_AGENTS)
        == harness.SHARED_REGION_BODY_ALT
    )


def test_reconcile_replaces_losing_region_whole_without_blending(
    tmp_path: pathlib.Path,
) -> None:
    repo = evidence.init_repo_with_committed_shared_region(
        tmp_path,
        claude_region=harness.SHARED_REGION_BODY,
        agents_region=harness.SHARED_REGION_BODY,
        timestamp=1000,
    )
    evidence.diverge_region_and_commit(
        repo, harness.INSTRUCTION_CLAUDE, harness.SHARED_REGION_BODY_ALT, 2000
    )

    MODULE.reconcile_root_shared_regions(repo)
    agents_region = evidence.region_body(repo, harness.INSTRUCTION_AGENTS)
    # the winning body is present whole; no trace of the losing body survives
    assert agents_region == harness.SHARED_REGION_BODY_ALT
    assert harness.SHARED_REGION_BODY not in agents_region


def test_reconcile_uses_region_recency_not_whole_file_recency(
    tmp_path: pathlib.Path,
) -> None:
    # AGENTS's region is edited more recently than CLAUDE's, but CLAUDE's file then gets a later
    # commit touching only its independent content — so CLAUDE is the newer *file* while AGENTS
    # holds the newer *region*. Whole-file recency would keep CLAUDE's stale region and discard
    # AGENTS's genuine edit; region recency must keep AGENTS's more-current body.
    repo = evidence.init_repo_with_committed_shared_region(
        tmp_path,
        claude_region=harness.SHARED_REGION_BODY,
        agents_region=harness.SHARED_REGION_BODY,
        timestamp=1000,
    )
    evidence.diverge_region_and_commit(
        repo, harness.INSTRUCTION_AGENTS, harness.SHARED_REGION_BODY_ALT, 2000
    )
    claude = repo / harness.INSTRUCTION_CLAUDE
    claude.write_text(
        claude.read_text(encoding="utf-8") + "\nIndependent note appended later.\n",
        encoding="utf-8",
    )
    harness.git_commit_at(repo, 3000, harness.INSTRUCTION_CLAUDE)

    report = MODULE.reconcile_root_shared_regions(repo)
    assert harness.SHARED_REGION_NAME in report.reconciled
    assert (
        evidence.region_body(repo, harness.INSTRUCTION_CLAUDE)
        == harness.SHARED_REGION_BODY_ALT
    )


def test_region_line_range_covers_content_lines_only() -> None:
    # opening fence line 2, blank 3, body lines 4-5, blank 6, close fence line 7. The range that
    # feeds `git log -L` must be the body lines (4, 5) only — a fence or separator line inside the
    # range would let a fence-only commit read as a region-content change and flip the recency.
    name = harness.SHARED_REGION_NAME
    text = (
        "head\n"
        f"{MODULE.shared_open_marker(name)}\n"
        "\n"
        "body line four\n"
        "body line five\n"
        "\n"
        f"{MODULE.shared_close_marker(name)}\n"
    )
    assert MODULE._region_line_range(text, name) == (4, 5)


def test_recency_tie_is_reported_ambiguous(tmp_path: pathlib.Path) -> None:
    repo = evidence.init_repo_with_committed_shared_region(
        tmp_path,
        claude_region=harness.SHARED_REGION_BODY,
        agents_region=harness.SHARED_REGION_BODY_ALT,
        timestamp=1000,
    )
    report = MODULE.reconcile_root_shared_regions(repo)
    assert harness.SHARED_REGION_NAME in report.tie
    assert report.reconciled == ()


def test_one_sided_shared_region_is_reported_ambiguous(tmp_path: pathlib.Path) -> None:
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


def test_reconcile_reports_malformed_fence_as_ambiguous(tmp_path: pathlib.Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    harness.init_git_identity(repo)
    # both files carry a shared open fence with no matching close — a malformed region the
    # reconcile must surface rather than pass over, so the closing --check has a resolution path
    doc = f"# Head\n\n{MODULE.shared_open_marker('commands')}\n\nbody with no close\n"
    for name in (harness.INSTRUCTION_CLAUDE, harness.INSTRUCTION_AGENTS):
        (repo / name).write_text(doc, encoding="utf-8")
    harness.git_commit_at(
        repo, 1000, harness.INSTRUCTION_CLAUDE, harness.INSTRUCTION_AGENTS
    )

    report = MODULE.reconcile_root_shared_regions(repo)
    assert "commands" in report.malformed
    assert report.ambiguous


def test_reconcile_skips_a_malformed_duplicate_name(tmp_path: pathlib.Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    harness.init_git_identity(repo)
    open_marker = MODULE.shared_open_marker("commands")
    close_marker = MODULE.shared_close_marker("commands")
    # both files open the same name twice with different last bodies: parse collapses to the last
    # body and the collapsed bodies diverge, but the duplicate is malformed and must be reported,
    # never reconciled from its unreliable collapsed body
    (repo / harness.INSTRUCTION_CLAUDE).write_text(
        f"# H\n\n{open_marker}\n\na1\n\n{close_marker}\n\n"
        f"{open_marker}\n\nclaude-last\n\n{close_marker}\n",
        encoding="utf-8",
    )
    (repo / harness.INSTRUCTION_AGENTS).write_text(
        f"# H\n\n{open_marker}\n\nb1\n\n{close_marker}\n\n"
        f"{open_marker}\n\ncodex-last\n\n{close_marker}\n",
        encoding="utf-8",
    )
    harness.git_commit_at(
        repo, 1000, harness.INSTRUCTION_CLAUDE, harness.INSTRUCTION_AGENTS
    )

    report = MODULE.reconcile_root_shared_regions(repo)
    assert "commands" in report.malformed
    assert report.reconciled == ()


def test_cli_reconcile_requires_repo_root(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code = MODULE.main(
        ["--template", str(evidence.scenario_template(tmp_path)), "--reconcile"]
    )
    assert code == 2
    assert "--reconcile requires --repo-root" in capsys.readouterr().err


def test_cli_reconcile_from_applies_operator_tie_break(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # a diverged region committed at the same time is a recency tie; `--from claude` resolves it,
    # exercising main()'s --reconcile/--from branch end to end — the interface the skill documents
    repo = evidence.init_repo_with_committed_shared_region(
        tmp_path,
        claude_region=harness.SHARED_REGION_BODY,
        agents_region=harness.SHARED_REGION_BODY_ALT,
        timestamp=1000,
    )
    code = MODULE.main(
        [
            "--template",
            str(evidence.scenario_template(tmp_path)),
            "--repo-root",
            str(repo),
            "--reconcile",
            "--from",
            "claude",
        ]
    )
    assert code == 0
    assert f"reconciled: {harness.SHARED_REGION_NAME}" in capsys.readouterr().out
    assert (
        evidence.region_body(repo, harness.INSTRUCTION_AGENTS)
        == harness.SHARED_REGION_BODY
    )


def test_cli_reconcile_reports_no_change_when_regions_agree(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = evidence.init_repo_with_committed_shared_region(
        tmp_path,
        claude_region=harness.SHARED_REGION_BODY,
        agents_region=harness.SHARED_REGION_BODY,
        timestamp=1000,
    )
    code = MODULE.main(
        [
            "--template",
            str(evidence.scenario_template(tmp_path)),
            "--repo-root",
            str(repo),
            "--reconcile",
        ]
    )
    assert code == 0
    assert capsys.readouterr().out.strip() == ""


def test_reconcile_makes_no_change_to_a_dirty_file(tmp_path: pathlib.Path) -> None:
    repo = evidence.init_repo_with_committed_shared_region(
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
    assert (
        evidence.region_body(repo, harness.INSTRUCTION_AGENTS)
        == harness.SHARED_REGION_BODY
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


def test_the_reconcile_reports_a_pointer_body_as_an_ambiguity(
    tmp_path: pathlib.Path,
) -> None:
    repo = tmp_path / "repo"
    harness.materialize_root_instruction_topology(
        repo, harness.root_instruction_topology_delegating()
    )

    report = MODULE.reconcile_root_shared_regions(repo)

    # The reconcile is where the skill collects what it must put to the operator, so a candidate
    # reaches the operator only by arriving in this report and counting as ambiguous.
    assert report.delegating == (harness.INSTRUCTION_CLAUDE,)
    assert report.ambiguous
    assert report.reconciled == ()

    exit_code, stderr = harness.run_generator_reconcile(
        repo, harness.write_template(tmp_path, harness.NEW_VERSION)
    )

    assert exit_code != 0
    assert f"ambiguous (delegating): {harness.INSTRUCTION_CLAUDE}" in stderr


def test_an_answer_naming_a_pointer_body_is_refused(tmp_path: pathlib.Path) -> None:
    repo = tmp_path / "repo"
    seeds = harness.materialize_root_instruction_topology(
        repo, harness.root_instruction_topology_mutual_delegation()
    )
    template = harness.write_template(tmp_path, harness.NEW_VERSION)

    exit_code = harness.run_generator_write_primary(
        repo, template, adopt_harness="claude"
    )

    # Adopting either side would install a body that sends the reader to a file now carrying the
    # same pointer, and the surface would then read as current with nothing left to signal it.
    assert exit_code == 2
    for filename in (harness.INSTRUCTION_CLAUDE, harness.INSTRUCTION_AGENTS):
        assert (repo / filename).read_text(encoding="utf-8") == seeds[filename]


def test_an_answer_that_would_discard_a_content_bearing_body_is_refused(
    tmp_path: pathlib.Path,
) -> None:
    for topology in (
        harness.root_instruction_topology_separate,
        harness.root_instruction_topology_identical,
    ):
        repo = tmp_path / topology.__name__ / "repo"
        seeds = harness.materialize_root_instruction_topology(repo, topology())
        template = harness.write_template(
            tmp_path / topology.__name__, harness.NEW_VERSION
        )

        exit_code = harness.run_generator_write_primary(
            repo, template, adopt_harness="codex"
        )

        # No body here was ever reported as a pointer, so no answer authorizes replacing one.
        # Adoption discards a whole body: applying it where the discarded side states something
        # of its own destroys instructions the operator was never asked about.
        assert exit_code == 2, topology.__name__
        for filename in (harness.INSTRUCTION_CLAUDE, harness.INSTRUCTION_AGENTS):
            assert (repo / filename).read_text(encoding="utf-8") == seeds[filename], (
                topology.__name__,
                filename,
            )


def test_a_pointer_beside_a_malformed_fence_is_never_reported(
    tmp_path: pathlib.Path,
) -> None:
    repo = tmp_path / "repo"
    topology = harness.root_instruction_topology_delegating()
    # The content-bearing side also carries an unclosed fence, which refuses the bootstrap. The
    # pointer is still a pointer, so only agreement between the report and the write keeps the
    # reported remedy from being one the write would decline to apply.
    topology.files[harness.INSTRUCTION_AGENTS] += (
        f"\n{MODULE.shared_open_marker('commands')}\n\nbody with no closing fence\n"
    )
    harness.materialize_root_instruction_topology(repo, topology)
    template = harness.write_template(tmp_path, harness.NEW_VERSION)

    assert MODULE.unresolved_delegation(repo) == ()

    harness.run_generator_write_primary(repo, template, adopt_harness="codex")

    claude = (repo / harness.INSTRUCTION_CLAUDE).read_text(encoding="utf-8")
    assert topology.files[harness.INSTRUCTION_CLAUDE].strip() in claude


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
