"""Compliance evidence for the root managed-section guide generator.

Rules in ``update-spx.md`` with deterministic test evidence:

- NEVER: the render substitutes a product-specific string — a brace-delimited illustration
  token in the template passes through to the managed section unchanged.
- NEVER: an update keeps an unmodeled hand-prose edit inside the managed section — a
  tampered section re-renders to the same output as a clean render from the same languages.
- ALWAYS: generation writes managed sections into both root guide files.
- ALWAYS: product guides render from harness-specific templates under ``dist/``.
- NEVER: guide generation writes output from a template with unresolved build macros.
"""

import os
import pathlib
import subprocess

import pytest

from outcomeeng.distribution import guide_diff
from outcomeeng.distribution.contracts import DIST_DIR_NAME
from outcomeeng_testing.harnesses.update_spx import (
    GUIDE_AGENTS,
    GUIDE_CLAUDE,
    ILLUSTRATION_TOKEN,
    LANG_PRIMARY,
    HARNESS_CLAUDE,
    HARNESS_CODEX,
    ROOT_GUIDE_SHARED_BODY,
    SESSION_ARCHIVE_RESULT_INSTRUCTION,
    SESSION_MANAGEMENT_HEADING,
    SESSION_RESULT_FRONTMATTER_FIELD,
    build_template,
    extract_markdown_section,
    load_update_spx_module,
    read_canonical_spx_template,
    render_build_macro,
    write_template,
)

VERSION = "0.18.0"
JUNK_EDIT = "HAND-EDITED JUNK THAT MUST NOT SURVIVE A RE-RENDER"


def _git(repo_root: pathlib.Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo_root,
        capture_output=True,
        check=True,
        text=True,
    )


def _workflow_run_block(step_name: str) -> str:
    workflow = guide_diff.REPO_ROOT.joinpath(
        ".github", "workflows", "refresh-root-guides.yml"
    ).read_text(encoding="utf-8")
    lines = workflow.splitlines()
    step_line = f"      - name: {step_name}"
    start = lines.index(step_line)
    run_line = lines.index("        run: |", start)
    block: list[str] = []
    for line in lines[run_line + 1 :]:
        if line.startswith("      - name: "):
            break
        if line.startswith("          "):
            block.append(line[10:])
        elif line:
            break
        else:
            block.append("")
    return "\n".join(block) + "\n"


def _write_gh_stub(bin_dir: pathlib.Path, log_path: pathlib.Path) -> None:
    stub = bin_dir / "gh"
    stub.write_text(
        "\n".join(
            [
                "#!/usr/bin/env bash",
                "set -euo pipefail",
                f'printf "%s\\n" "$*" >> {str(log_path)!r}',
                'if [ "${1:-}" = "pr" ] && [ "${2:-}" = "list" ]; then',
                "  exit 0",
                "fi",
                'if [ "${1:-}" = "pr" ] && [ "${2:-}" = "create" ]; then',
                "  exit 0",
                "fi",
                'echo "unexpected gh invocation: $*" >&2',
                "exit 64",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    stub.chmod(0o755)


def _run_refresh_pr_step(repo_root: pathlib.Path, gh_log: pathlib.Path) -> str:
    bin_dir = repo_root.parent / f"{repo_root.name}-stub-bin"
    bin_dir.mkdir()
    _write_gh_stub(bin_dir, gh_log)
    env = os.environ.copy()
    env["GH_TOKEN"] = "test-token"
    env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"
    result = subprocess.run(
        ["/bin/bash", "-c", _workflow_run_block("Open guide refresh pull request")],
        cwd=repo_root,
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout


def test_render_passes_brace_token_through_unchanged() -> None:
    module = load_update_spx_module()
    rendered = module.render(
        build_template(VERSION), (LANG_PRIMARY,), VERSION, HARNESS_CLAUDE
    )
    assert ILLUSTRATION_TOKEN in rendered


def test_re_render_ignores_unmodeled_managed_section_edits() -> None:
    module = load_update_spx_module()
    template = build_template(VERSION)
    section = module.render(template, (LANG_PRIMARY,), VERSION, HARNESS_CLAUDE)

    tampered = section + f"\n\n## Hand Section\n\n{JUNK_EDIT}\n"
    updated = module.render(
        template, module.parse_languages(tampered), VERSION, HARNESS_CLAUDE
    )

    assert JUNK_EDIT not in updated
    assert updated == module.render(template, (LANG_PRIMARY,), VERSION, HARNESS_CLAUDE)


def test_generation_writes_both_root_guide_files(tmp_path: pathlib.Path) -> None:
    module = load_update_spx_module()
    template = write_template(tmp_path, VERSION)

    exit_code = module.main(
        [
            "--template",
            str(template),
            "--repo-root",
            str(tmp_path),
            "--languages",
            LANG_PRIMARY,
            "--write",
        ]
    )
    assert exit_code == 0

    written = {
        name
        for name in module.AGENT_HARNESS_GUIDE_FILENAMES.values()
        if (tmp_path / name).is_file()
    }
    assert written == set(module.AGENT_HARNESS_GUIDE_FILENAMES.values())


def test_root_content_outside_managed_section_is_preserved(
    tmp_path: pathlib.Path,
) -> None:
    module = load_update_spx_module()
    template = write_template(tmp_path, VERSION)
    for filename in (GUIDE_CLAUDE, GUIDE_AGENTS):
        (tmp_path / filename).write_text(ROOT_GUIDE_SHARED_BODY, encoding="utf-8")

    assert (
        module.main(
            [
                "--template",
                str(template),
                "--repo-root",
                str(tmp_path),
                "--languages",
                LANG_PRIMARY,
                "--write",
            ]
        )
        == 0
    )

    for filename in (GUIDE_CLAUDE, GUIDE_AGENTS):
        content = (tmp_path / filename).read_text(encoding="utf-8")
        assert ROOT_GUIDE_SHARED_BODY.rstrip("\n") in content
        assert content.count(module.MANAGED_SECTION_START) == 1
        assert content.count(module.MANAGED_SECTION_END) == 1


def test_guide_templates_are_loaded_from_harness_specific_dist_outputs(
    tmp_path: pathlib.Path,
) -> None:
    module = load_update_spx_module()
    expected: dict[str, str] = {}
    for harness in module.AGENT_HARNESS_GUIDE_FILENAMES:
        path = guide_diff.dist_template_path(harness)
        assert (
            path
            == guide_diff.REPO_ROOT
            / DIST_DIR_NAME
            / harness
            / guide_diff.DIST_TEMPLATE_RELATIVE_PATH
        )
        template = build_template(f"{VERSION}.{harness}")
        expected[harness] = template
        dist_path = guide_diff.dist_template_path(harness, repo_root=tmp_path)
        dist_path.parent.mkdir(parents=True, exist_ok=True)
        dist_path.write_text(template, encoding="utf-8")

    assert guide_diff.load_harness_templates(module, repo_root=tmp_path) == expected


def test_guide_render_rejects_unresolved_build_macro() -> None:
    module = load_update_spx_module()
    harness_templates = {
        harness: build_template(VERSION)
        for harness in module.AGENT_HARNESS_GUIDE_FILENAMES
    }
    harness_templates[HARNESS_CODEX] += render_build_macro()

    with pytest.raises(guide_diff.UnresolvedGuideTemplateError):
        guide_diff.render_guides_from_harness_templates(
            module, harness_templates, (LANG_PRIMARY,)
        )


def test_justfile_exposes_guide_writer_and_gate() -> None:
    justfile = guide_diff.REPO_ROOT.joinpath(guide_diff.JUSTFILE_NAME).read_text(
        encoding="utf-8"
    )

    assert f"\n{guide_diff.BUILD_GUIDES_RECIPE}:" in justfile
    assert f"\n{guide_diff.GUIDE_CHECK_RECIPE}:" in justfile
    assert f"outcomeeng.distribution.guide_diff {guide_diff.WRITE_FLAG}" in justfile
    assert "outcomeeng.distribution.guide_diff\n" in justfile


def test_lefthook_guide_refresh_uses_repo_root_argument() -> None:
    lefthook = guide_diff.REPO_ROOT.joinpath("lefthook.yml").read_text(encoding="utf-8")

    assert "--repo-root ." in lefthook
    assert "--spx-dir" not in lefthook


def test_guide_drift_probe_marks_untracked_root_guides_intent_to_add(
    tmp_path: pathlib.Path,
) -> None:
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.name", "Test User")
    _git(tmp_path, "config", "user.email", "test@example.com")
    (tmp_path / ".gitignore").write_text("\n", encoding="utf-8")
    _git(tmp_path, "add", ".gitignore")
    _git(tmp_path, "commit", "-m", "seed repository")
    (tmp_path / GUIDE_CLAUDE).write_text("generated claude\n", encoding="utf-8")
    (tmp_path / GUIDE_AGENTS).write_text("generated agents\n", encoding="utf-8")

    assert guide_diff.drifting_guides(repo_root=tmp_path) == [
        GUIDE_AGENTS,
        GUIDE_CLAUDE,
    ]


def test_guide_drift_probe_reports_missing_root_guides(
    tmp_path: pathlib.Path,
) -> None:
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.name", "Test User")
    _git(tmp_path, "config", "user.email", "test@example.com")
    (tmp_path / ".gitignore").write_text("\n", encoding="utf-8")
    _git(tmp_path, "add", ".gitignore")
    _git(tmp_path, "commit", "-m", "seed repository")

    assert guide_diff.drifting_guides(repo_root=tmp_path) == [
        GUIDE_AGENTS,
        GUIDE_CLAUDE,
    ]


def test_guide_drift_probe_skips_missing_obsolete_spx_guides(
    tmp_path: pathlib.Path,
) -> None:
    spx_dir = tmp_path / "spx"
    spx_dir.mkdir()
    for path in (
        tmp_path / GUIDE_CLAUDE,
        tmp_path / GUIDE_AGENTS,
        spx_dir / GUIDE_CLAUDE,
        spx_dir / GUIDE_AGENTS,
    ):
        path.write_text(f"{path.name}\n", encoding="utf-8")

    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.name", "Test User")
    _git(tmp_path, "config", "user.email", "test@example.com")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-m", "seed guides")

    (spx_dir / GUIDE_CLAUDE).unlink()
    (spx_dir / GUIDE_AGENTS).unlink()

    assert guide_diff.drifting_guides(repo_root=tmp_path) == [
        f"spx/{GUIDE_AGENTS}",
        f"spx/{GUIDE_CLAUDE}",
    ]


def test_root_guide_refresh_workflow_regenerates_and_opens_pr() -> None:
    workflow = guide_diff.REPO_ROOT.joinpath(
        ".github", "workflows", "refresh-root-guides.yml"
    ).read_text(encoding="utf-8")

    assert "workflow_dispatch:" in workflow
    assert "schedule:" in workflow
    assert "contents: write" in workflow
    assert "pull-requests: write" in workflow
    regenerate_commands = _workflow_run_block("Regenerate guide sections").splitlines()
    build_skills = regenerate_commands.index("just build-skills")
    build_guides = regenerate_commands.index("just build-guides")
    guide_check = regenerate_commands.index("just guide-check")
    assert build_skills < build_guides < guide_check


def test_root_guide_refresh_pr_step_exits_cleanly_without_drift(
    tmp_path: pathlib.Path,
) -> None:
    gh_log = tmp_path / "gh.log"
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.name", "Test User")
    _git(tmp_path, "config", "user.email", "test@example.com")
    (tmp_path / GUIDE_CLAUDE).write_text("current\n", encoding="utf-8")
    (tmp_path / GUIDE_AGENTS).write_text("current\n", encoding="utf-8")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-m", "seed guides")

    output = _run_refresh_pr_step(tmp_path, gh_log)

    assert output == "Root guide sections are current.\n"
    assert not gh_log.exists()


def test_root_guide_refresh_pr_step_stages_obsolete_guide_deletions(
    tmp_path: pathlib.Path,
) -> None:
    remote = tmp_path / "remote.git"
    repo = tmp_path / "repo"
    gh_log = tmp_path / "gh.log"
    _git(tmp_path, "init", "--bare", str(remote))
    _git(tmp_path, "clone", str(remote), str(repo))
    _git(repo, "config", "user.name", "Test User")
    _git(repo, "config", "user.email", "test@example.com")
    spx_dir = repo / "spx"
    spx_dir.mkdir()
    for path in (
        repo / GUIDE_CLAUDE,
        repo / GUIDE_AGENTS,
        spx_dir / GUIDE_CLAUDE,
        spx_dir / GUIDE_AGENTS,
    ):
        path.write_text(f"{path.name}\n", encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "seed guides")
    _git(repo, "branch", "-M", "main")
    _git(repo, "push", "-u", "origin", "main")

    (repo / GUIDE_CLAUDE).write_text("updated\n", encoding="utf-8")
    (repo / GUIDE_AGENTS).write_text("updated\n", encoding="utf-8")
    (spx_dir / GUIDE_CLAUDE).unlink()
    (spx_dir / GUIDE_AGENTS).unlink()

    _run_refresh_pr_step(repo, gh_log)

    committed = _git(
        repo,
        "show",
        "--name-status",
        "--format=%s",
        "automation/refresh-root-guides",
    ).stdout
    assert "Refresh root guide sections" in committed
    assert f"M\t{GUIDE_CLAUDE}" in committed
    assert f"M\t{GUIDE_AGENTS}" in committed
    assert f"D\tspx/{GUIDE_CLAUDE}" in committed
    assert f"D\tspx/{GUIDE_AGENTS}" in committed
    gh_calls = gh_log.read_text(encoding="utf-8")
    assert "pr list" in gh_calls
    assert "pr create" in gh_calls


def test_write_regenerates_a_drifted_guide(tmp_path: pathlib.Path) -> None:
    module = load_update_spx_module()
    template = write_template(tmp_path, VERSION)
    args = [
        "--template",
        str(template),
        "--repo-root",
        str(tmp_path),
        "--languages",
        LANG_PRIMARY,
    ]
    assert module.main([*args, "--write"]) == 0

    # Drift both managed sections by hand, then regenerate. Product-owned root content
    # outside the managed markers remains; drift inside the managed section is removed.
    guides = [tmp_path / name for name in module.AGENT_HARNESS_GUIDE_FILENAMES.values()]
    for guide in guides:
        guide.write_text(
            guide.read_text().replace(
                module.MANAGED_SECTION_END,
                f"\nHAND DRIFT\n{module.MANAGED_SECTION_END}",
            ),
            encoding="utf-8",
        )
    assert module.main([*args, "--write"]) == 0
    for guide in guides:
        assert "HAND DRIFT" not in guide.read_text(encoding="utf-8")


def test_no_rendered_guide_teaches_result_session_frontmatter() -> None:
    module = load_update_spx_module()
    template = read_canonical_spx_template()
    # Render the canonical template for each agent harness and assert the rendered
    # Session Management section carries no result-frontmatter instruction —
    # exercising the generator's output, not just the authored template text.
    for harness in (HARNESS_CLAUDE, HARNESS_CODEX):
        rendered = module.render(template, (LANG_PRIMARY,), VERSION, harness)
        section = extract_markdown_section(rendered, SESSION_MANAGEMENT_HEADING)
        assert SESSION_ARCHIVE_RESULT_INSTRUCTION not in section
        assert SESSION_RESULT_FRONTMATTER_FIELD not in section


def test_write_removes_obsolete_spx_guides(tmp_path: pathlib.Path) -> None:
    module = load_update_spx_module()
    template = write_template(tmp_path, VERSION)
    spx_dir = tmp_path / "spx"
    spx_dir.mkdir()
    for filename in (GUIDE_CLAUDE, GUIDE_AGENTS):
        (spx_dir / filename).write_text("obsolete\n", encoding="utf-8")

    assert (
        module.main(
            [
                "--template",
                str(template),
                "--repo-root",
                str(tmp_path),
                "--languages",
                LANG_PRIMARY,
                "--write",
            ]
        )
        == 0
    )

    assert not (spx_dir / GUIDE_CLAUDE).exists()
    assert not (spx_dir / GUIDE_AGENTS).exists()
