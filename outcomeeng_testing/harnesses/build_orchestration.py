"""Behavior probes for build-orchestration evidence."""

from __future__ import annotations

import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

from outcomeeng.distribution.build import (
    FORMATTER_COMMAND_NAME,
    FORMATTER_VERSION_OUTPUT,
    BuildError,
    _format_dist,
    build,
    formatter_format_command,
    formatter_version_command,
)
from outcomeeng.distribution.contracts import (
    BUILD_COMMAND_ARGV,
    DIST_DIR_NAME,
    DIST_DIFF_ARGV,
    DIST_DIFF_MODULE_NAME,
    ORCHESTRATION_VALIDATION_ARGV,
    Target,
)
from outcomeeng.distribution.dist_diff import (
    DRIFT_REBUILD_NOTE,
    EXPECTED_PRECOMMIT_NOTE,
    EXPECTED_PRECOMMIT_REMEDIATION,
    dist_drift_report,
    main,
)
from outcomeeng.distribution.orchestration import (
    CLAUDE_MARKETPLACE_PATH,
    CLAUDE_RUNTIME_ROOT,
    CODEX_MARKETPLACE_PATH,
    CODEX_RUNTIME_ROOT,
    JUSTFILE_PATH,
    LEFTHOOK_BUILD_COMMAND,
    LEFTHOOK_PATH,
    check_build_orchestration,
    claude_marketplace_plugin_root,
    claude_marketplace_plugin_sources,
    codex_marketplace_plugin_sources,
    dist_diff_surfaces_match_contract as source_dist_diff_surfaces_match_contract,
    justfile_matches_build_contract as source_justfile_matches_build_contract,
    lefthook_build_command,
    lefthook_config_matches_build_contract,
    load_json_document,
    load_lefthook_config,
    parse_lefthook_config,
    path_is_under_runtime_root,
)
from outcomeeng.validation._steps import DIST_DIFF_STEP_LABEL, VALIDATION_STEPS
from outcomeeng.validation.build_orchestration import (
    main as validate_build_orchestration,
)
from outcomeeng_testing.harnesses.dist_drift import dist_drift_repo
from outcomeeng_testing.generators.source_and_templating import source_scenarios
from outcomeeng_testing.harnesses.dist_tree import DistTreeReader
from outcomeeng_testing.harnesses.src_tree import SrcTreeBuilder

REPOSITORY_ROOT = Path(".")
FORMATTER_FAILURE_DIAGNOSTIC = "formatter failed"
FORMATTER_VERSION_FAILURE_DIAGNOSTIC = "formatter version failed"
FORMATTER_TEST_PATH = f"/usr/local/bin/{FORMATTER_COMMAND_NAME}"
RAW_DIFF_HUNK_MARKER = "@@"
RAW_DIFF_LINE_PREFIXES = ("+", "-")
INVALID_PATH_SEGMENT = "develop"
INVALID_PATH_SUFFIX = "-extra"


def dist_drift_with_source_edit_matches_contract() -> bool:
    with dist_drift_repo() as repo:
        repo.drift_dist()
        repo.edit_src()
        report = dist_drift_report(cwd=repo.root)
        return (
            report is not None
            and repo.dist_path.as_posix() in report
            and EXPECTED_PRECOMMIT_NOTE in report
            and EXPECTED_PRECOMMIT_REMEDIATION in report
            and DRIFT_REBUILD_NOTE not in report
            and not _carries_unified_diff(report)
            and main(cwd=repo.root) == 1
        )


def dist_drift_without_source_edit_matches_contract() -> bool:
    with dist_drift_repo() as repo:
        repo.drift_dist()
        report = dist_drift_report(cwd=repo.root)
        return (
            report is not None
            and repo.dist_path.as_posix() in report
            and DRIFT_REBUILD_NOTE in report
            and EXPECTED_PRECOMMIT_NOTE not in report
            and not _carries_unified_diff(report)
            and main(cwd=repo.root) == 1
        )


def clean_dist_matches_contract() -> bool:
    with dist_drift_repo() as repo:
        return dist_drift_report(cwd=repo.root) is None and main(cwd=repo.root) == 0


def missing_formatter_matches_contract() -> bool:
    runner_calls: list[tuple[tuple[str, ...], Path]] = []

    def unavailable_formatter(command_name: str) -> str | None:
        if command_name != FORMATTER_COMMAND_NAME:
            raise AssertionError(command_name)
        return None

    def recording_runner(
        command: tuple[str, ...], cwd: Path
    ) -> subprocess.CompletedProcess[str]:
        runner_calls.append((command, cwd))
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    try:
        _format_dist(
            REPOSITORY_ROOT,
            formatter_probe=unavailable_formatter,
            runner=recording_runner,
        )
    except BuildError as error:
        return FORMATTER_COMMAND_NAME in str(error) and not runner_calls
    return False


def failing_formatter_matches_contract() -> bool:
    runner_calls: list[tuple[tuple[str, ...], Path]] = []

    def formatter_probe(command_name: str) -> str | None:
        if command_name != FORMATTER_COMMAND_NAME:
            raise AssertionError(command_name)
        return FORMATTER_TEST_PATH

    def failing_runner(
        command: tuple[str, ...], cwd: Path
    ) -> subprocess.CompletedProcess[str]:
        runner_calls.append((command, cwd))
        if command == formatter_version_command(FORMATTER_TEST_PATH):
            return subprocess.CompletedProcess(
                command,
                0,
                stdout=FORMATTER_VERSION_OUTPUT,
                stderr="",
            )
        return subprocess.CompletedProcess(
            command,
            1,
            stdout="",
            stderr=FORMATTER_FAILURE_DIAGNOSTIC,
        )

    try:
        _format_dist(
            REPOSITORY_ROOT,
            formatter_probe=formatter_probe,
            runner=failing_runner,
        )
    except BuildError as error:
        return FORMATTER_FAILURE_DIAGNOSTIC in str(error) and runner_calls == [
            (formatter_version_command(FORMATTER_TEST_PATH), REPOSITORY_ROOT),
            (formatter_format_command(FORMATTER_TEST_PATH), REPOSITORY_ROOT),
        ]
    return False


def failing_formatter_version_probe_matches_contract() -> bool:
    """Return whether a version-probe failure reaches the build diagnostic."""
    runner_calls: list[tuple[tuple[str, ...], Path]] = []

    def formatter_probe(command_name: str) -> str | None:
        if command_name != FORMATTER_COMMAND_NAME:
            raise AssertionError(command_name)
        return FORMATTER_TEST_PATH

    def failing_version_runner(
        command: tuple[str, ...], cwd: Path
    ) -> subprocess.CompletedProcess[str]:
        runner_calls.append((command, cwd))
        return subprocess.CompletedProcess(
            command,
            1,
            stdout="",
            stderr=FORMATTER_VERSION_FAILURE_DIAGNOSTIC,
        )

    try:
        _format_dist(
            REPOSITORY_ROOT,
            formatter_probe=formatter_probe,
            runner=failing_version_runner,
        )
    except BuildError as error:
        return FORMATTER_VERSION_FAILURE_DIAGNOSTIC in str(error) and runner_calls == [
            (formatter_version_command(FORMATTER_TEST_PATH), REPOSITORY_ROOT)
        ]
    return False


def repository_build_orchestration_matches_contract() -> bool:
    return not check_build_orchestration(REPOSITORY_ROOT)


def quality_gate_matches_build_orchestration_contract() -> bool:
    return (
        ORCHESTRATION_VALIDATION_ARGV in {step.argv for step in VALIDATION_STEPS}
        and validate_build_orchestration([str(REPOSITORY_ROOT)]) == 0
    )


def dist_diff_surfaces_match_contract() -> bool:
    dist_diff_argvs: set[tuple[str, ...]] = {
        step.argv for step in VALIDATION_STEPS if step.label == DIST_DIFF_STEP_LABEL
    }
    command = lefthook_build_command(load_lefthook_config(LEFTHOOK_PATH))
    return source_dist_diff_surfaces_match_contract(dist_diff_argvs, command)


def dist_diff_surface_violations_are_rejected() -> bool:
    command = lefthook_build_command(load_lefthook_config(LEFTHOOK_PATH))
    gate_without_reporter: set[tuple[str, ...]] = {DIST_DIFF_ARGV[:-1]}
    hook_without_reporter = command.replace(
        DIST_DIFF_MODULE_NAME,
        DIST_DIR_NAME,
        1,
    )
    return not source_dist_diff_surfaces_match_contract(
        gate_without_reporter,
        command,
    ) and not source_dist_diff_surfaces_match_contract(
        {DIST_DIFF_ARGV},
        hook_without_reporter,
    )


def justfile_matches_build_contract() -> bool:
    justfile = JUSTFILE_PATH.read_text(encoding="utf-8")
    return source_justfile_matches_build_contract(justfile) and (
        _build_emits_every_source_scenario_to_each_target()
    )


def justfile_recipe_violation_is_rejected() -> bool:
    justfile = JUSTFILE_PATH.read_text(encoding="utf-8")
    violating_command = " ".join(BUILD_COMMAND_ARGV[:-1])
    violating_justfile = justfile.replace(
        " ".join(BUILD_COMMAND_ARGV),
        violating_command,
        1,
    )
    return not source_justfile_matches_build_contract(violating_justfile)


def lefthook_matches_build_contract() -> bool:
    config = load_lefthook_config(LEFTHOOK_PATH)
    if not lefthook_config_matches_build_contract(config):
        return False
    violating_text = LEFTHOOK_PATH.read_text(encoding="utf-8").replace(
        LEFTHOOK_BUILD_COMMAND,
        " ".join(BUILD_COMMAND_ARGV),
        1,
    )
    if lefthook_config_matches_build_contract(parse_lefthook_config(violating_text)):
        return False
    with dist_drift_repo() as repo:
        repo.drift_dist()
        return main(cwd=repo.root) != 0


def claude_marketplace_matches_runtime_contract() -> bool:
    data = load_json_document(CLAUDE_MARKETPLACE_PATH)
    sources = claude_marketplace_plugin_sources(data)
    return (
        claude_marketplace_plugin_root(data) == CLAUDE_RUNTIME_ROOT
        and bool(sources)
        and all(
            path_is_under_runtime_root(source, CLAUDE_RUNTIME_ROOT)
            for source in sources
        )
        and _rejects_runtime_prefix_collision(CLAUDE_RUNTIME_ROOT)
        and _rejects_runtime_parent_escape(
            runtime_root=CLAUDE_RUNTIME_ROOT,
            sibling_root=CODEX_RUNTIME_ROOT,
        )
    )


def codex_marketplace_matches_runtime_contract() -> bool:
    data = load_json_document(CODEX_MARKETPLACE_PATH)
    sources = codex_marketplace_plugin_sources(data)
    return (
        bool(sources)
        and all(
            path_is_under_runtime_root(source, CODEX_RUNTIME_ROOT) for source in sources
        )
        and _rejects_runtime_prefix_collision(CODEX_RUNTIME_ROOT)
        and _rejects_runtime_parent_escape(
            runtime_root=CODEX_RUNTIME_ROOT,
            sibling_root=CLAUDE_RUNTIME_ROOT,
        )
    )


def _carries_unified_diff(report: str) -> bool:
    return RAW_DIFF_HUNK_MARKER in report or any(
        line.startswith(RAW_DIFF_LINE_PREFIXES) for line in report.splitlines()
    )


def _rejects_runtime_prefix_collision(runtime_root: str) -> bool:
    candidate = f"{runtime_root}{INVALID_PATH_SUFFIX}/{INVALID_PATH_SEGMENT}"
    return not path_is_under_runtime_root(candidate, runtime_root)


def _rejects_runtime_parent_escape(*, runtime_root: str, sibling_root: str) -> bool:
    candidate = f"{runtime_root}/../{sibling_root}/{INVALID_PATH_SEGMENT}"
    return not path_is_under_runtime_root(candidate, runtime_root)


def _build_emits_every_source_scenario_to_each_target() -> bool:
    scenarios = source_scenarios()
    with TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        builder = SrcTreeBuilder(root)
        for scenario in scenarios:
            builder.add_plugin(
                scenario.plugin,
                skills={scenario.skill: scenario.fragment_body},
            )
        build(builder.src_root, root / DIST_DIR_NAME)
        reader = DistTreeReader(root)
        return all(
            reader.is_skill_present(
                scenario.plugin,
                scenario.skill,
                target=target,
            )
            for scenario in scenarios
            for target in Target
        )
