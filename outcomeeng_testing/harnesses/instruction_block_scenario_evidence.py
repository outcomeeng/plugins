"""Scenario harness evidence for the instruction-block CLI edge and shared-region reconcile.

Each scenario exercises one concrete interaction: rendering both root files, preserving a shared
region and independent prose across a re-render, the router marker format, per-harness divergence,
new-section propagation, template path rejection, staleness of an unparseable version,
quoted-marker safety, and the git-recency reconcile of a diverged shared region. The harness owns
all fixture setup — templates, topologies, git commits at fixed dates.

The bootstrap-topology scenarios live in the linked scenario test, which owns their predicates
directly. The scenarios still here hold their predicates against the seam
``spec-tree:test-evidence-standards`` requires; ``ISSUES.md`` records that remaining migration.
"""

from __future__ import annotations

import pathlib
import inspect
import io
import os
from collections.abc import Callable
from contextlib import redirect_stderr, redirect_stdout
from dataclasses import dataclass
from tempfile import TemporaryDirectory
from typing import cast

from outcomeeng_testing.harnesses import instruction_block as harness

MODULE = harness.load_instruction_block_module()


@dataclass(frozen=True)
class _CapturedOutput:
    out: str
    err: str


class _OutputCapture:
    """Capture output for CLI assertions without pytest fixture binding."""

    def __init__(self) -> None:
        self.stdout = io.StringIO()
        self.stderr = io.StringIO()

    def readouterr(self) -> _CapturedOutput:
        captured = _CapturedOutput(self.stdout.getvalue(), self.stderr.getvalue())
        self.stdout.seek(0)
        self.stdout.truncate(0)
        self.stderr.seek(0)
        self.stderr.truncate(0)
        return captured


def _template(tmp_path: pathlib.Path, *, extra_section: bool = False) -> pathlib.Path:
    return harness.write_template(
        tmp_path, harness.NEW_VERSION, extra_section=extra_section
    )


def _assert_write_produces_both_files_language_and_harness_filtered(
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


def _assert_write_preserves_shared_region_and_independent_prose(
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

    template = _template(tmp_path)
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


def _assert_router_marker_format(tmp_path: pathlib.Path) -> None:
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


def _assert_both_files_identical_except_harness_spans(tmp_path: pathlib.Path) -> None:
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


def _assert_newer_template_adds_section_preserving_shared_region(
    tmp_path: pathlib.Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    harness.write_both_root_files_with_shared_region(
        MODULE, repo, languages=(harness.LANG_PRIMARY,), version=harness.OLD_VERSION
    )
    harness.run_generator_write_primary(repo, _template(tmp_path, extra_section=True))
    for name in harness.INSTRUCTION_CLAUDE, harness.INSTRUCTION_AGENTS:
        rendered = (repo / name).read_text(encoding="utf-8")
        assert f"## {harness.NEW_SECTION}" in rendered
        assert MODULE.parse_instruction_languages(rendered) == (harness.LANG_PRIMARY,)
        assert (
            MODULE.parse_shared_regions(rendered)[harness.SHARED_REGION_NAME]
            == harness.SHARED_REGION_BODY
        )


def _assert_template_symlink_is_rejected(tmp_path: pathlib.Path) -> None:
    home = tmp_path / "home"
    home.mkdir()
    real = _template(home)
    link = home / "link-template.md"
    link.symlink_to(real)
    repo = tmp_path / "repo"
    repo.mkdir()
    direct_code = MODULE.main(
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
    assert direct_code == 2
    previous_home = os.environ.get("HOME")
    os.environ["HOME"] = str(home)
    try:
        code = MODULE.main(
            [
                "--template",
                "~/link-template.md",
                "--repo-root",
                str(repo),
                "--languages",
                harness.LANG_PRIMARY,
                "--write",
            ]
        )
    finally:
        if previous_home is None:
            os.environ.pop("HOME", None)
        else:
            os.environ["HOME"] = previous_home
    assert code == 2


def _assert_cli_rejects_template_without_frontmatter_version(
    tmp_path: pathlib.Path, capsys: _OutputCapture
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


def _assert_cli_rejects_missing_repo_root(
    tmp_path: pathlib.Path, capsys: _OutputCapture
) -> None:
    code = MODULE.main(
        [
            "--template",
            str(_template(tmp_path)),
            "--repo-root",
            str(tmp_path / "does-not-exist"),
            "--write",
        ]
    )
    assert code == 2
    assert "--repo-root does not exist" in capsys.readouterr().err


def _assert_cli_rejects_non_directory_repo_root(
    tmp_path: pathlib.Path, capsys: _OutputCapture
) -> None:
    plain = tmp_path / "plain.txt"
    plain.write_text("x", encoding="utf-8")
    code = MODULE.main(
        ["--template", str(_template(tmp_path)), "--repo-root", str(plain), "--write"]
    )
    assert code == 2
    assert "is not a directory" in capsys.readouterr().err


def _assert_cli_rejects_missing_template(
    tmp_path: pathlib.Path, capsys: _OutputCapture
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    code = MODULE.main(
        ["--template", str(tmp_path / "gone.md"), "--repo-root", str(repo), "--write"]
    )
    assert code == 2
    assert "--template does not exist" in capsys.readouterr().err


def _assert_cli_rejects_directory_template(
    tmp_path: pathlib.Path, capsys: _OutputCapture
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


def _assert_cli_rejects_root_symlink_escaping_repo(
    tmp_path: pathlib.Path, capsys: _OutputCapture
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
            str(_template(tmp_path)),
            "--repo-root",
            str(repo),
            "--languages",
            harness.LANG_PRIMARY,
            "--write",
        ]
    )
    assert code == 2
    assert "escapes --repo-root" in capsys.readouterr().err


def _assert_cli_rejects_spx_symlink_during_language_detection(
    tmp_path: pathlib.Path, capsys: _OutputCapture
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    for name in (harness.INSTRUCTION_CLAUDE, harness.INSTRUCTION_AGENTS):
        (repo / name).write_text(harness.ROOT_SHARED_BODY, encoding="utf-8")
    (repo / "spx").symlink_to(tmp_path)
    # no --languages forces detection, which resolves <repo-root>/spx and rejects the symlink
    code = MODULE.main(
        ["--template", str(_template(tmp_path)), "--repo-root", str(repo), "--write"]
    )
    assert code == 2
    assert "spx directory is a symlink" in capsys.readouterr().err


def _assert_cli_detects_languages_from_test_extensions(tmp_path: pathlib.Path) -> None:
    spx_dir = tmp_path / "spx"
    harness.write_spx_tree_with_tests(spx_dir, ("py", "ts"))
    assert MODULE.detect_languages_from_tree(spx_dir) == ("python", "typescript")


def _assert_cli_write_without_repo_root_exits(
    tmp_path: pathlib.Path, capsys: _OutputCapture
) -> None:
    code = MODULE.main(["--template", str(_template(tmp_path)), "--write"])
    assert code == 2
    assert "--write requires --repo-root" in capsys.readouterr().err


def _assert_cli_check_reports_absent_when_one_file_missing(
    tmp_path: pathlib.Path, capsys: _OutputCapture
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


def _assert_cli_check_treats_language_order_as_set(tmp_path: pathlib.Path) -> None:
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


def _assert_cli_check_marks_router_not_first_as_stale(tmp_path: pathlib.Path) -> None:
    block = MODULE.render(
        harness.build_template(harness.NEW_VERSION),
        (harness.LANG_PRIMARY,),
        harness.NEW_VERSION,
        harness.HARNESS_CLAUDE,
    )
    repo = tmp_path / "repo"
    repo.mkdir()
    claude = repo / harness.INSTRUCTION_CLAUDE

    def check() -> str:
        return cast(
            str,
            MODULE.instruction_status(
                claude, harness.NEW_VERSION, (harness.LANG_PRIMARY,), repo
            ),
        )

    # router first -> current
    claude.write_text(MODULE.prepend_router_block(block, "PRODUCT"), encoding="utf-8")
    assert check() == "current"
    # product prose before the router -> stale; the router must be the first content of the file
    claude.write_text(
        "PRODUCT PROSE FIRST\n\n" + MODULE.prepend_router_block(block, "PRODUCT"),
        encoding="utf-8",
    )
    assert check() == "stale"


def _assert_unparseable_version_is_stale(tmp_path: pathlib.Path) -> None:
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


def _assert_quoted_router_marker_in_prose_is_preserved(tmp_path: pathlib.Path) -> None:
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


def _assert_quoted_router_closing_marker_after_block_is_preserved(
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

    harness.run_generator_write_primary(repo, _template(tmp_path))
    result = (repo / harness.INSTRUCTION_CLAUDE).read_text(encoding="utf-8")
    # the real standalone closing fence bounds the block; the inline-quoted marker in independent
    # content is not mistaken for the block end, so the note survives and the block is single
    assert "Doc note: the router closes with" in result
    assert result.count(MODULE.ROUTER_MARKER_PREFIX) == 1


def _assert_quoted_shared_fence_in_prose_is_not_a_region() -> None:
    inline = f"Use `{MODULE.shared_open_marker('example')}` inline to open a region.\n"
    assert MODULE.parse_shared_regions(inline) == {}


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


def _assert_diverged_shared_region_reconciles_to_more_recent_side(
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


def _assert_reconcile_replaces_losing_region_whole_without_blending(
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


def _assert_reconcile_uses_region_recency_not_whole_file_recency(
    tmp_path: pathlib.Path,
) -> None:
    # AGENTS's region is edited more recently than CLAUDE's, but CLAUDE's file then gets a later
    # commit touching only its independent content — so CLAUDE is the newer *file* while AGENTS
    # holds the newer *region*. Whole-file recency would keep CLAUDE's stale region and discard
    # AGENTS's genuine edit; region recency must keep AGENTS's more-current body.
    repo = _init_repo_with_committed_shared_region(
        tmp_path,
        claude_region=harness.SHARED_REGION_BODY,
        agents_region=harness.SHARED_REGION_BODY,
        timestamp=1000,
    )
    agents = repo / harness.INSTRUCTION_AGENTS
    agents.write_text(
        MODULE.set_shared_region(
            agents.read_text(encoding="utf-8"),
            harness.SHARED_REGION_NAME,
            harness.SHARED_REGION_BODY_ALT,
        ),
        encoding="utf-8",
    )
    harness.git_commit_at(repo, 2000, harness.INSTRUCTION_AGENTS)
    claude = repo / harness.INSTRUCTION_CLAUDE
    claude.write_text(
        claude.read_text(encoding="utf-8") + "\nIndependent note appended later.\n",
        encoding="utf-8",
    )
    harness.git_commit_at(repo, 3000, harness.INSTRUCTION_CLAUDE)

    report = MODULE.reconcile_root_shared_regions(repo)
    assert harness.SHARED_REGION_NAME in report.reconciled
    claude_region = MODULE.parse_shared_regions(claude.read_text(encoding="utf-8"))[
        harness.SHARED_REGION_NAME
    ]
    assert claude_region == harness.SHARED_REGION_BODY_ALT


def _assert_region_line_range_covers_content_lines_only() -> None:
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


def _assert_recency_tie_is_reported_ambiguous(tmp_path: pathlib.Path) -> None:
    repo = _init_repo_with_committed_shared_region(
        tmp_path,
        claude_region=harness.SHARED_REGION_BODY,
        agents_region=harness.SHARED_REGION_BODY_ALT,
        timestamp=1000,
    )
    report = MODULE.reconcile_root_shared_regions(repo)
    assert harness.SHARED_REGION_NAME in report.tie
    assert report.reconciled == ()


def _assert_one_sided_shared_region_is_reported_ambiguous(
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


def _assert_reconcile_reports_malformed_fence_as_ambiguous(
    tmp_path: pathlib.Path,
) -> None:
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


def _assert_reconcile_skips_a_malformed_duplicate_name(tmp_path: pathlib.Path) -> None:
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


def _assert_cli_reconcile_requires_repo_root(
    tmp_path: pathlib.Path, capsys: _OutputCapture
) -> None:
    code = MODULE.main(["--template", str(_template(tmp_path)), "--reconcile"])
    assert code == 2
    assert "--reconcile requires --repo-root" in capsys.readouterr().err


def _assert_cli_reconcile_from_applies_operator_tie_break(
    tmp_path: pathlib.Path, capsys: _OutputCapture
) -> None:
    # a diverged region committed at the same time is a recency tie; `--from claude` resolves it,
    # exercising main()'s --reconcile/--from branch end to end — the interface the skill documents
    repo = _init_repo_with_committed_shared_region(
        tmp_path,
        claude_region=harness.SHARED_REGION_BODY,
        agents_region=harness.SHARED_REGION_BODY_ALT,
        timestamp=1000,
    )
    code = MODULE.main(
        [
            "--template",
            str(_template(tmp_path)),
            "--repo-root",
            str(repo),
            "--reconcile",
            "--from",
            "claude",
        ]
    )
    assert code == 0
    assert f"reconciled: {harness.SHARED_REGION_NAME}" in capsys.readouterr().out
    agents_region = MODULE.parse_shared_regions(
        (repo / harness.INSTRUCTION_AGENTS).read_text(encoding="utf-8")
    )[harness.SHARED_REGION_NAME]
    assert agents_region == harness.SHARED_REGION_BODY


def _assert_cli_reconcile_reports_no_change_when_regions_agree(
    tmp_path: pathlib.Path, capsys: _OutputCapture
) -> None:
    repo = _init_repo_with_committed_shared_region(
        tmp_path,
        claude_region=harness.SHARED_REGION_BODY,
        agents_region=harness.SHARED_REGION_BODY,
        timestamp=1000,
    )
    code = MODULE.main(
        [
            "--template",
            str(_template(tmp_path)),
            "--repo-root",
            str(repo),
            "--reconcile",
        ]
    )
    assert code == 0
    assert capsys.readouterr().out.strip() == ""


def _assert_reconcile_makes_no_change_to_a_dirty_file(tmp_path: pathlib.Path) -> None:
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


def _scenario_assertions() -> list[tuple[str, Callable[..., None]]]:
    """Return every scenario assertion callable in deterministic order."""
    return sorted(
        (name, cast(Callable[..., None], assertion))
        for name, assertion in globals().items()
        if name.startswith("_assert_") and callable(assertion)
    )


def scenario_evidence_declarations() -> tuple[str, ...]:
    """Return every declared scenario case identity."""
    return harness.scenario_evidence_contract()


def scenario_evidence_run() -> harness.EvidenceRun:
    """Run every declared scenario check through harness-owned resources."""
    assertions = _scenario_assertions()
    declared = scenario_evidence_declarations()
    executed: list[str] = []
    with TemporaryDirectory() as directory:
        root = pathlib.Path(directory).resolve()
        for index, (name, assertion) in enumerate(assertions):
            parameters = inspect.signature(assertion).parameters
            arguments: dict[str, object] = {}
            if "tmp_path" in parameters:
                tmp_path = root / f"{index:02d}-{name.removeprefix('_assert_')}"
                tmp_path.mkdir()
                arguments["tmp_path"] = tmp_path
            if "capsys" in parameters:
                capture = _OutputCapture()
                arguments["capsys"] = capture
                with redirect_stdout(capture.stdout), redirect_stderr(capture.stderr):
                    assertion(**arguments)
            else:
                assertion(**arguments)
            executed.append(name.removeprefix("_assert_"))
    return harness.EvidenceRun(declared=declared, executed=tuple(executed))
