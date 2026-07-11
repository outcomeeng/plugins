"""Compliance evidence for build orchestration wiring."""

from __future__ import annotations

from pathlib import Path

from outcomeeng.distribution.contracts import (
    BUILD_COMMAND_ARGV,
    DIST_DIFF_ARGV,
    DIST_DIFF_MODULE_NAME,
    ORCHESTRATION_VALIDATION_ARGV,
)
from outcomeeng.distribution.codex_project import (
    CODEX_LOCAL_BUILD_ARGV,
    CODEX_LOCAL_LAUNCH_ARGV,
    CODEX_LOCAL_RECIPE_NAME,
    PROJECT_RUNTIME_BUILD_ARGV,
)
from outcomeeng.distribution.orchestration import (
    BUILD_RECIPE_NAME,
    CLAUDE_MARKETPLACE_PATH,
    CLAUDE_RUNTIME_ROOT,
    CODEX_MARKETPLACE_PATH,
    CODEX_RUNTIME_ROOT,
    JUSTFILE_PATH,
    LEFTHOOK_BUILD_COMMAND,
    LEFTHOOK_PATH,
    claude_marketplace_plugin_root,
    claude_marketplace_plugin_sources,
    check_build_orchestration,
    codex_marketplace_plugin_sources,
    just_recipe_commands,
    just_recipe_names,
    lefthook_build_command,
    load_json_document,
    load_lefthook_config,
    path_is_under_runtime_root,
)
from outcomeeng.validation._steps import VALIDATION_STEPS
from outcomeeng.validation.build_orchestration import (
    main as validate_build_orchestration,
)


def test_repository_passes_the_build_orchestration_contract() -> None:
    assert check_build_orchestration(Path(".")) == []


def test_quality_gate_runs_the_build_orchestration_contract() -> None:
    assert ORCHESTRATION_VALIDATION_ARGV in {step.argv for step in VALIDATION_STEPS}
    assert validate_build_orchestration(["."]) == 0


def test_dist_diff_surfaces_invoke_the_actionable_reporter() -> None:
    dist_diff_argvs = {
        step.argv for step in VALIDATION_STEPS if step.label == "dist-diff"
    }
    assert dist_diff_argvs == {DIST_DIFF_ARGV}
    assert DIST_DIFF_MODULE_NAME in DIST_DIFF_ARGV
    assert "diff" not in DIST_DIFF_ARGV

    command = lefthook_build_command(load_lefthook_config(LEFTHOOK_PATH))
    assert DIST_DIFF_MODULE_NAME in command
    assert "git diff --exit-code" not in command


def test_justfile_declares_build_skills_recipe() -> None:
    justfile = JUSTFILE_PATH.read_text(encoding="utf-8")
    commands = just_recipe_commands(justfile)

    assert just_recipe_names(justfile).count(BUILD_RECIPE_NAME) == 1
    assert BUILD_COMMAND_ARGV in commands


def test_justfile_declares_checkout_local_codex_recipe() -> None:
    justfile = JUSTFILE_PATH.read_text(encoding="utf-8")
    commands = just_recipe_commands(justfile, CODEX_LOCAL_RECIPE_NAME)

    assert just_recipe_names(justfile).count(CODEX_LOCAL_RECIPE_NAME) == 1
    assert CODEX_LOCAL_BUILD_ARGV in commands
    assert PROJECT_RUNTIME_BUILD_ARGV in commands
    assert CODEX_LOCAL_LAUNCH_ARGV in commands


def test_lefthook_runs_build_and_checks_dist_drift() -> None:
    config = load_lefthook_config(LEFTHOOK_PATH)

    assert lefthook_build_command(config) == LEFTHOOK_BUILD_COMMAND


def test_claude_marketplace_points_at_dist_claude() -> None:
    data = load_json_document(CLAUDE_MARKETPLACE_PATH)
    sources = claude_marketplace_plugin_sources(data)

    assert claude_marketplace_plugin_root(data) == CLAUDE_RUNTIME_ROOT
    assert sources
    assert all(
        path_is_under_runtime_root(source, CLAUDE_RUNTIME_ROOT) for source in sources
    )
    assert not path_is_under_runtime_root(
        f"{CLAUDE_RUNTIME_ROOT}-extra/develop", CLAUDE_RUNTIME_ROOT
    )
    assert not path_is_under_runtime_root(
        f"{CLAUDE_RUNTIME_ROOT}/../codex/develop", CLAUDE_RUNTIME_ROOT
    )


def test_codex_marketplace_points_at_dist_codex() -> None:
    data = load_json_document(CODEX_MARKETPLACE_PATH)
    sources = codex_marketplace_plugin_sources(data)

    assert sources
    assert all(
        path_is_under_runtime_root(source, CODEX_RUNTIME_ROOT) for source in sources
    )
    assert not path_is_under_runtime_root(
        f"{CODEX_RUNTIME_ROOT}-extra/develop", CODEX_RUNTIME_ROOT
    )
    assert not path_is_under_runtime_root(
        f"{CODEX_RUNTIME_ROOT}/../claude/develop", CODEX_RUNTIME_ROOT
    )
