"""Rendered document observations for instruction-block compliance evidence."""

from __future__ import annotations

import pathlib
from dataclasses import dataclass
from typing import cast

from outcomeeng.distribution import instruction_block as dist
from outcomeeng.distribution.contracts import DIST_DIR_NAME
from outcomeeng_testing.harnesses import instruction_block as harness

MODULE = harness.load_instruction_block_module()
WORKFLOW = dist.REFRESH_WORKFLOW


def _distribution_module() -> dist.InstructionBlockModule:
    """Narrow the dynamic script module at distribution-helper boundaries."""
    return cast(dist.InstructionBlockModule, MODULE)


def _template(tmp_path: pathlib.Path) -> pathlib.Path:
    return harness.write_template(tmp_path, harness.NEW_VERSION)


def _render_shipped_instruction_blocks(
    enabled_languages: tuple[str, ...] = harness.TEMPLATE_LANGUAGES,
) -> dict[str, str]:
    """Render shipped harness templates for one source-declared language subset."""
    templates = dist.load_harness_templates(_distribution_module())
    return dist.render_instruction_blocks_from_harness_templates(
        _distribution_module(), templates, enabled_languages
    )


def rendered_instruction_blocks(
    enabled_languages: tuple[str, ...] = harness.TEMPLATE_LANGUAGES,
) -> dict[str, str]:
    """Expose the rendered harness routers keyed by agent harness.

    An observation for a linked test that owns its own predicates; this returns
    rendered content and never judges it.
    """
    return _render_shipped_instruction_blocks(enabled_languages)


def generated_root_paths(tmp_path: pathlib.Path) -> tuple[pathlib.Path, ...]:
    repo = tmp_path / "repo"
    repo.mkdir()
    harness.run_generator_write_primary(repo, _template(tmp_path))
    return tuple(
        repo / name for name in MODULE.AGENT_HARNESS_INSTRUCTION_FILENAMES.values()
    )


def missing_root_drift(tmp_path: pathlib.Path) -> list[str]:
    repo = tmp_path / "repo"
    repo.mkdir()
    harness.init_git_identity(repo)
    harness.write_both_root_files_with_shared_region(
        MODULE, repo, languages=(harness.LANG_PRIMARY,), version=harness.NEW_VERSION
    )
    harness.git_commit_at(
        repo, 1000, harness.INSTRUCTION_CLAUDE, harness.INSTRUCTION_AGENTS
    )
    (repo / harness.INSTRUCTION_CLAUDE).unlink()
    return dist.drifting_instruction_files(
        repo_root=repo, module=_distribution_module()
    )


def untracked_root_drift(tmp_path: pathlib.Path) -> list[str]:
    repo = tmp_path / "repo"
    repo.mkdir()
    harness.init_git_identity(repo)
    harness.write_both_root_files_with_shared_region(
        MODULE, repo, languages=(harness.LANG_PRIMARY,), version=harness.NEW_VERSION
    )
    return dist.drifting_instruction_files(
        repo_root=repo, module=_distribution_module()
    )


def absent_obsolete_drift(tmp_path: pathlib.Path) -> list[str]:
    repo = tmp_path / "repo"
    repo.mkdir()
    harness.init_git_identity(repo)
    harness.write_both_root_files_with_shared_region(
        MODULE, repo, languages=(harness.LANG_PRIMARY,), version=harness.NEW_VERSION
    )
    harness.git_commit_at(
        repo, 1000, harness.INSTRUCTION_CLAUDE, harness.INSTRUCTION_AGENTS
    )
    return dist.drifting_instruction_files(
        repo_root=repo, module=_distribution_module()
    )


@dataclass(frozen=True)
class RouterDriftObservation:
    drifted: str
    regenerated: str
    canonical_body: str
    hand_edited_body: str


def overwritten_router_drift(tmp_path: pathlib.Path) -> RouterDriftObservation:
    repo = tmp_path / "repo"
    repo.mkdir()
    template = _template(tmp_path)
    harness.run_generator_write_primary(repo, template)
    claude = repo / harness.INSTRUCTION_CLAUDE
    canonical_body = harness.harness_line(harness.HARNESS_CLAUDE)
    hand_edited_body = f"{canonical_body} {harness.SHARED_REGION_BODY_ALT}"
    claude.write_text(
        claude.read_text(encoding="utf-8")
        .replace(f"v{harness.NEW_VERSION}", f"v{harness.OLD_VERSION}", 1)
        .replace(canonical_body, hand_edited_body, 1),
        encoding="utf-8",
    )
    drifted = claude.read_text(encoding="utf-8")
    harness.run_generator_write_primary(repo, template)
    return RouterDriftObservation(
        drifted, claude.read_text(encoding="utf-8"), canonical_body, hand_edited_body
    )


def former_command_slot_render(tmp_path: pathlib.Path) -> tuple[str, str]:
    repo = tmp_path / "repo"
    repo.mkdir()
    slot_fence = (
        "<!-- SPEC-TREE:author -->\n\nproduct author command\n\n"
        "<!-- /SPEC-TREE:author -->\n"
    )
    for name in (harness.INSTRUCTION_CLAUDE, harness.INSTRUCTION_AGENTS):
        (repo / name).write_text(slot_fence, encoding="utf-8")
    harness.run_generator_write_primary(repo, _template(tmp_path))
    return (repo / harness.INSTRUCTION_CLAUDE).read_text(encoding="utf-8"), slot_fence


def removed_obsolete_paths(tmp_path: pathlib.Path) -> tuple[pathlib.Path, ...]:
    repo = tmp_path / "repo"
    repo.mkdir()
    spx_dir = repo / "spx"
    spx_dir.mkdir()
    paths = tuple(
        spx_dir / name
        for name in (harness.INSTRUCTION_CLAUDE, harness.INSTRUCTION_AGENTS)
    )
    for path in paths:
        path.write_text("retired spx instruction file\n", encoding="utf-8")
    harness.run_generator_write_primary(repo, _template(tmp_path))
    return paths


@dataclass(frozen=True)
class TemplateLoadObservation:
    paths: dict[str, pathlib.Path]
    expected: dict[str, str]
    loaded: dict[str, str]
    rendered: dict[str, str]
    markers: dict[str, str]


def dist_template_load(tmp_path: pathlib.Path) -> TemplateLoadObservation:
    expected: dict[str, str] = {}
    paths: dict[str, pathlib.Path] = {}
    markers: dict[str, str] = {}
    for agent_harness in MODULE.AGENT_HARNESS_INSTRUCTION_FILENAMES:
        paths[agent_harness] = dist.dist_template_path(agent_harness)
        markers[agent_harness] = f"DIST TEMPLATE SOURCE: {agent_harness}"
        template = (
            harness.build_template(harness.NEW_VERSION)
            + f"\n{markers[agent_harness]}\n"
        )
        expected[agent_harness] = template
        dist_path = dist.dist_template_path(agent_harness, repo_root=tmp_path)
        dist_path.parent.mkdir(parents=True, exist_ok=True)
        dist_path.write_text(template, encoding="utf-8")
    loaded = dist.load_harness_templates(_distribution_module(), repo_root=tmp_path)
    rendered = dist.render_instruction_blocks_from_harness_templates(
        _distribution_module(), loaded, harness.TEMPLATE_LANGUAGES
    )
    return TemplateLoadObservation(paths, expected, loaded, rendered, markers)


@dataclass(frozen=True)
class RefreshWorkflowObservation:
    initial_gh_log_exists: bool
    advanced_version: str
    template_versions: tuple[str | None, ...]
    root_versions: tuple[str | None, ...]
    obsolete_present: tuple[bool, ...]
    committed: str
    template_paths: tuple[pathlib.Path, ...]
    gh_calls: str
    existing_pr_number: str
    update_output: str
    update_calls: str
    updated_agents: str
    update_version: str


def refresh_workflow_observation(
    tmp_path: pathlib.Path,
) -> RefreshWorkflowObservation:
    gh_log = tmp_path / "gh.log"
    repo = harness.materialize_refresh_repository(tmp_path)

    harness.run_refresh_regeneration_step(repo)
    harness.git_command(
        repo,
        "add",
        harness.INSTRUCTION_CLAUDE,
        harness.INSTRUCTION_AGENTS,
        DIST_DIR_NAME,
    )
    harness.git_command(repo, "commit", "-m", "seed generated workflow output")
    harness.git_command(repo, "push", "origin", WORKFLOW.default_branch)
    harness.run_refresh_regeneration_step(repo)
    harness.run_refresh_pr_step(repo, gh_log)
    initial_gh_log_exists = gh_log.exists()

    spx_dir = repo / "spx"
    for name in harness.INSTRUCTION_CLAUDE, harness.INSTRUCTION_AGENTS:
        (spx_dir / name).write_text(
            (repo / name).read_text(encoding="utf-8"), encoding="utf-8"
        )
    harness.git_command(repo, "add", ".")
    harness.git_command(repo, "commit", "-m", "seed obsolete instruction files")
    harness.git_command(repo, "push", "origin", WORKFLOW.default_branch)

    _, advanced_version = harness.advance_authored_template_version(repo)
    harness.run_refresh_regeneration_step(repo)
    template_versions: list[str | None] = []
    for agent_harness in MODULE.AGENT_HARNESS_INSTRUCTION_FILENAMES:
        rendered_template = dist.dist_template_path(
            agent_harness, repo_root=repo
        ).read_text(encoding="utf-8")
        template_versions.append(MODULE.parse_template_version(rendered_template))
    root_versions: list[str | None] = []
    for name in harness.INSTRUCTION_CLAUDE, harness.INSTRUCTION_AGENTS:
        rendered_root = (repo / name).read_text(encoding="utf-8")
        root_versions.append(MODULE.parse_instruction_version(rendered_root))
    obsolete_present = tuple(
        (spx_dir / name).exists()
        for name in (harness.INSTRUCTION_CLAUDE, harness.INSTRUCTION_AGENTS)
    )
    harness.run_refresh_pr_step(repo, gh_log)

    committed = harness.git_command(
        repo,
        "show",
        "--name-status",
        "--format=%s",
        WORKFLOW.automation_branch,
    ).stdout
    template_paths: list[pathlib.Path] = []
    for agent_harness in MODULE.AGENT_HARNESS_INSTRUCTION_FILENAMES:
        rendered_template_path = dist.dist_template_path(
            agent_harness, repo_root=repo
        ).relative_to(repo)
        template_paths.append(rendered_template_path)
    gh_calls = gh_log.read_text(encoding="utf-8")

    harness.git_command(repo, "switch", WORKFLOW.default_branch)
    _, update_version = harness.advance_authored_template_version(repo)
    harness.run_refresh_regeneration_step(repo)
    update_log = tmp_path / "gh-update.log"
    existing_pr_number = harness.git_command(
        repo, "rev-list", "--count", WORKFLOW.default_branch
    ).stdout.strip()
    update_output = harness.run_refresh_pr_step(
        repo, update_log, existing_pr_number=existing_pr_number
    )
    update_calls = update_log.read_text(encoding="utf-8")
    updated_agents = harness.git_command(
        repo,
        "show",
        f"{WORKFLOW.automation_branch}:{harness.INSTRUCTION_AGENTS}",
    ).stdout

    return RefreshWorkflowObservation(
        initial_gh_log_exists,
        advanced_version,
        tuple(template_versions),
        tuple(root_versions),
        obsolete_present,
        committed,
        tuple(template_paths),
        gh_calls,
        existing_pr_number,
        update_output,
        update_calls,
        updated_agents,
        update_version,
    )
