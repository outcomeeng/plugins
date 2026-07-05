"""Harnesses for local marketplace source conformance evidence.

The maintainer sync path reads the configured Claude and Codex marketplace
sources before refreshing Codex plugins. These tests pin the JSON contract and
the local-source gate without invoking either runtime CLI.
"""

from __future__ import annotations

import json
import subprocess
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from outcomeeng.distribution.marketplace_sources import (
    CLAUDE_MARKETPLACE_ADD_COMMAND,
    CLAUDE_MARKETPLACE_LIST_COMMAND,
    CLAUDE_MARKETPLACE_REMOVE_COMMAND,
    CLAUDE_SCOPE_LOCAL,
    CLAUDE_SCOPE_PROJECT,
    CLAUDE_PLUGIN_ALREADY_DISABLED_FRAGMENT,
    CLAUDE_PLUGIN_ALREADY_ENABLED_FRAGMENT,
    CLAUDE_PLUGIN_ALREADY_INSTALLED_FRAGMENT,
    CLAUDE_PLUGIN_DISABLE_COMMAND,
    CLAUDE_PLUGIN_ENABLE_COMMAND,
    CLAUDE_PLUGIN_INSTALL_COMMAND,
    CLAUDE_PLUGIN_LIST_COMMAND,
    ClaudeSettingsPaths,
    CODEX_PLUGIN_MANIFEST,
    CODEX_MARKETPLACE_ADD_COMMAND,
    CODEX_MARKETPLACE_LIST_COMMAND,
    CODEX_MARKETPLACE_REMOVE_COMMAND,
    DEFAULT_MARKETPLACE,
    DIST_CODEX_PLUGINS_DIR,
    ClaudeInstalledPlugin,
    ClaudeMarketplaceRepairTarget,
    MarketplaceConfigRepairResult,
    MarketplaceSourceError,
    CLAUDE_SCOPE_USER,
    _claude_plugin_belongs_to_repair_targets,
    available_codex_plugins,
    ensure_local_marketplace_sources,
    parse_claude_installed_plugins,
    parse_claude_marketplace_sources,
    parse_codex_marketplace_sources,
    require_matching_local_sources,
)

CLAUDE_MARKETPLACE_LIST_CALL = (*CLAUDE_MARKETPLACE_LIST_COMMAND,)
CODEX_MARKETPLACE_LIST_CALL = (*CODEX_MARKETPLACE_LIST_COMMAND,)
CLAUDE_PLUGIN_LIST_CALL = (*CLAUDE_PLUGIN_LIST_COMMAND,)


def with_temporary_marketplace_path(
    assertion: Callable[[Path], bool],
) -> bool:
    with TemporaryDirectory() as directory:
        return assertion(Path(directory))


def _claude_directory_marketplace_payload(path: Path) -> str:
    return json.dumps(
        [
            {
                "name": DEFAULT_MARKETPLACE,
                "source": "Directory",
                "path": str(path),
            }
        ]
    )


def _scoped_claude_directory_marketplace_payload(
    path: Path,
    *,
    scope: str,
    project_path: Path | None = None,
) -> str:
    payload: dict[str, object] = {
        "name": DEFAULT_MARKETPLACE,
        "source": "Directory",
        "path": str(path),
        "scope": scope,
    }
    if project_path is not None:
        payload["projectPath"] = str(project_path)
    return json.dumps([payload])


def _codex_local_marketplace_payload(path: Path) -> str:
    return json.dumps(
        [
            {
                "name": DEFAULT_MARKETPLACE,
                "sourceType": "local",
                "path": str(path),
            }
        ]
    )


def _claude_plugin_payload(
    plugin: str,
    *,
    scope: str,
    enabled: bool,
    project_path: Path | None = None,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "id": f"{plugin}@{DEFAULT_MARKETPLACE}",
        "scope": scope,
        "enabled": enabled,
    }
    if project_path is not None:
        payload["projectPath"] = str(project_path)
    return payload


def _assert_repair_result(
    result: MarketplaceConfigRepairResult,
    runner: RecordingCommandRunner,
    *,
    expected_root: Path,
    expected_calls: list[tuple[str, ...]],
    expected_cwd: list[Path | None],
) -> None:
    assert result.root == expected_root.resolve(strict=False)
    assert result.changed is True
    assert runner.calls == expected_calls, runner.calls
    assert runner.cwd_by_call == expected_cwd, runner.cwd_by_call


def _source_repair_runner(
    *,
    claude_payload: str,
    codex_root: Path,
    plugin_payload: str = "[]",
    returncode_by_command: dict[tuple[str, ...], int] | None = None,
    stderr_by_command: dict[tuple[str, ...], str] | None = None,
) -> RecordingCommandRunner:
    return RecordingCommandRunner(
        stdout_by_command={
            CLAUDE_MARKETPLACE_LIST_CALL: claude_payload,
            CODEX_MARKETPLACE_LIST_CALL: _codex_local_marketplace_payload(codex_root),
            CLAUDE_PLUGIN_LIST_CALL: plugin_payload,
        },
        returncode_by_command=returncode_by_command or {},
        stderr_by_command=stderr_by_command or {},
    )


def _expected_discovery_calls() -> list[tuple[str, ...]]:
    return [
        CLAUDE_MARKETPLACE_LIST_CALL,
        CODEX_MARKETPLACE_LIST_CALL,
        CLAUDE_PLUGIN_LIST_CALL,
    ]


def _scoped_claude_repair_calls(
    scope: str,
    result: MarketplaceConfigRepairResult,
) -> list[tuple[str, ...]]:
    return [
        (*CLAUDE_MARKETPLACE_REMOVE_COMMAND, "--scope", scope, DEFAULT_MARKETPLACE),
        (*CLAUDE_MARKETPLACE_ADD_COMMAND, "--scope", scope, str(result.root)),
    ]


def _assert_project_scope_repair(
    tmp_path: Path,
    *,
    claude_payload: str,
    claude_project_root: Path | None = None,
) -> bool:
    canonical_root = tmp_path / "canonical-marketplace"
    settings_paths = _settings_paths(tmp_path)
    runner = _source_repair_runner(
        claude_payload=claude_payload,
        codex_root=canonical_root,
    )

    result = ensure_local_marketplace_sources(
        DEFAULT_MARKETPLACE,
        source_root=canonical_root,
        claude_project_root=claude_project_root,
        claude_settings_paths=settings_paths,
        runner=runner,
    )

    repair_cwd = (claude_project_root or canonical_root).resolve(strict=False)
    _assert_repair_result(
        result,
        runner,
        expected_root=canonical_root,
        expected_calls=[
            *_expected_discovery_calls(),
            *_scoped_claude_repair_calls("project", result),
        ],
        expected_cwd=[None, None, repair_cwd, repair_cwd, repair_cwd],
    )
    return True


def parse_codex_marketplace_sources_accepts_local_source(
    tmp_path: Path,
) -> bool:
    marketplace_root = tmp_path / "marketplace"
    payload = json.dumps(
        [
            {
                "name": DEFAULT_MARKETPLACE,
                "sourceType": "local",
                "path": str(marketplace_root),
            }
        ]
    )

    sources = parse_codex_marketplace_sources(payload)

    assert sources[DEFAULT_MARKETPLACE].source_type == "local"
    assert sources[DEFAULT_MARKETPLACE].path == marketplace_root
    return True


def parse_codex_marketplace_sources_accepts_nested_local_source(
    tmp_path: Path,
) -> bool:
    marketplace_root = tmp_path / "marketplace"
    installed_root = tmp_path / "installed"
    payload = json.dumps(
        {
            "marketplaces": [
                {
                    "name": DEFAULT_MARKETPLACE,
                    "root": str(installed_root),
                    "marketplaceSource": {
                        "sourceType": "local",
                        "source": str(marketplace_root),
                    },
                }
            ]
        }
    )

    sources = parse_codex_marketplace_sources(payload)

    assert sources[DEFAULT_MARKETPLACE].source_type == "local"
    assert sources[DEFAULT_MARKETPLACE].path == marketplace_root
    return True


def parse_claude_marketplace_sources_normalizes_directory_source(
    tmp_path: Path,
) -> bool:
    marketplace_root = tmp_path / "marketplace"
    payload = json.dumps(
        [
            {
                "name": DEFAULT_MARKETPLACE,
                "source": "Directory",
                "path": str(marketplace_root),
            }
        ]
    )

    sources = parse_claude_marketplace_sources(payload)

    assert sources[DEFAULT_MARKETPLACE].source_type == "local"
    assert sources[DEFAULT_MARKETPLACE].path == marketplace_root
    return True


def parse_claude_installed_plugins_keeps_scope_state_and_project_path(
    tmp_path: Path,
) -> bool:
    project_path = tmp_path / "project"
    payload = json.dumps(
        [
            {
                "id": f"spec-tree@{DEFAULT_MARKETPLACE}",
                "scope": "project",
                "enabled": True,
                "projectPath": str(project_path),
            },
            {
                "id": f"rust@{DEFAULT_MARKETPLACE}",
                "scope": "user",
                "enabled": False,
            },
            {
                "id": "github@claude-plugins-official",
                "scope": "user",
                "enabled": True,
            },
        ]
    )

    plugins = parse_claude_installed_plugins(payload, DEFAULT_MARKETPLACE)

    assert [(plugin.name, plugin.scope, plugin.enabled) for plugin in plugins] == [
        ("spec-tree", "project", True),
        ("rust", "user", False),
    ]
    assert plugins[0].project_path == project_path
    assert plugins[1].project_path is None
    return True


def parse_codex_marketplace_sources_accepts_nested_git_source() -> bool:
    payload = json.dumps(
        {
            "marketplaces": [
                {
                    "name": DEFAULT_MARKETPLACE,
                    "root": "/Users/example/.codex/.tmp/marketplaces/outcomeeng",
                    "marketplaceSource": {
                        "sourceType": "git",
                        "source": "https://github.com/outcomeeng/plugins.git",
                    },
                }
            ]
        }
    )

    sources = parse_codex_marketplace_sources(payload)

    assert sources[DEFAULT_MARKETPLACE].source_type == "git"
    assert (
        sources[DEFAULT_MARKETPLACE].url == "https://github.com/outcomeeng/plugins.git"
    )
    return True


def parse_codex_marketplace_sources_accepts_empty_marketplace_array() -> bool:
    sources = parse_codex_marketplace_sources(json.dumps({"marketplaces": []}))

    assert sources == {}
    return True


def require_matching_local_sources_rejects_git_backed_codex(
    tmp_path: Path,
) -> bool:
    marketplace_root = tmp_path / "marketplace"
    claude_sources = parse_claude_marketplace_sources(
        json.dumps(
            [
                {
                    "name": DEFAULT_MARKETPLACE,
                    "source": "Directory",
                    "path": str(marketplace_root),
                }
            ]
        )
    )
    codex_sources = parse_codex_marketplace_sources(
        json.dumps(
            [
                {
                    "name": DEFAULT_MARKETPLACE,
                    "sourceType": "git",
                    "url": "https://github.com/outcomeeng/plugins.git",
                }
            ]
        )
    )

    with pytest.raises(MarketplaceSourceError) as exc_info:
        require_matching_local_sources(
            DEFAULT_MARKETPLACE,
            claude_sources=claude_sources,
            codex_sources=codex_sources,
        )

    message = str(exc_info.value)
    assert DEFAULT_MARKETPLACE in message
    assert "local" in message
    assert "git" in message
    return True


def require_matching_local_sources_rejects_path_mismatch(
    tmp_path: Path,
) -> bool:
    claude_root = tmp_path / "claude-marketplace"
    codex_root = tmp_path / "codex-marketplace"
    claude_sources = parse_claude_marketplace_sources(
        json.dumps(
            [
                {
                    "name": DEFAULT_MARKETPLACE,
                    "source": "Directory",
                    "path": str(claude_root),
                }
            ]
        )
    )
    codex_sources = parse_codex_marketplace_sources(
        json.dumps(
            [
                {
                    "name": DEFAULT_MARKETPLACE,
                    "sourceType": "local",
                    "path": str(codex_root),
                }
            ]
        )
    )

    with pytest.raises(MarketplaceSourceError) as exc_info:
        require_matching_local_sources(
            DEFAULT_MARKETPLACE,
            claude_sources=claude_sources,
            codex_sources=codex_sources,
        )

    message = str(exc_info.value)
    assert str(claude_root) in message
    assert str(codex_root) in message
    return True


def available_codex_plugins_are_read_from_dist_codex(
    tmp_path: Path,
) -> bool:
    repo_root = tmp_path / "repo"
    _write_codex_manifest(repo_root, "zeta", "0.2.0")
    _write_codex_manifest(repo_root, "alpha", "0.1.0")
    (repo_root / DIST_CODEX_PLUGINS_DIR / "missing-manifest").mkdir(parents=True)

    initial_plugins = available_codex_plugins(repo_root)
    _write_codex_manifest(repo_root, "beta", "0.3.0")
    refreshed_plugins = available_codex_plugins(repo_root)

    assert [(plugin.name, plugin.version) for plugin in initial_plugins] == [
        ("alpha", "0.1.0"),
        ("zeta", "0.2.0"),
    ]
    assert [(plugin.name, plugin.version) for plugin in refreshed_plugins] == [
        ("alpha", "0.1.0"),
        ("beta", "0.3.0"),
        ("zeta", "0.2.0"),
    ]
    return True


def source_reconciliation_adds_absent_runtime_sources(tmp_path: Path) -> bool:
    marketplace_root = tmp_path / "marketplace"
    settings_paths = _settings_paths(tmp_path)
    runner = RecordingCommandRunner(
        stdout_by_command={
            ("claude", "plugin", "marketplace", "list", "--json"): "[]",
            ("codex", "plugin", "marketplace", "list", "--json"): json.dumps(
                {"marketplaces": []}
            ),
            (*CLAUDE_PLUGIN_LIST_COMMAND,): "[]",
        }
    )

    result = ensure_local_marketplace_sources(
        DEFAULT_MARKETPLACE,
        source_root=marketplace_root,
        claude_settings_paths=settings_paths,
        runner=runner,
    )

    resolved_root = marketplace_root.resolve(strict=False)
    assert result.root == resolved_root
    assert result.changed is True
    expected_calls = [
        ("claude", "plugin", "marketplace", "list", "--json"),
        ("codex", "plugin", "marketplace", "list", "--json"),
        (*CLAUDE_PLUGIN_LIST_COMMAND,),
        (*CLAUDE_MARKETPLACE_ADD_COMMAND, str(resolved_root)),
        (*CODEX_MARKETPLACE_ADD_COMMAND, str(resolved_root)),
    ]
    assert runner.calls == expected_calls, runner.calls
    assert runner.cwd_by_call == [None, None, None, None, None]
    return True


def source_reconciliation_adds_absent_runtime_source_at_matching_project_scope(
    tmp_path: Path,
) -> bool:
    marketplace_root = tmp_path / "marketplace"
    project_path = tmp_path / "consumer-project"
    settings_paths = _settings_paths(project_path)
    _write_claude_marketplace_settings(settings_paths.project, marketplace_root)
    runner = RecordingCommandRunner(
        stdout_by_command={
            CLAUDE_MARKETPLACE_LIST_CALL: "[]",
            CODEX_MARKETPLACE_LIST_CALL: _codex_local_marketplace_payload(
                marketplace_root
            ),
            CLAUDE_PLUGIN_LIST_CALL: "[]",
        }
    )

    result = ensure_local_marketplace_sources(
        DEFAULT_MARKETPLACE,
        source_root=marketplace_root,
        claude_project_root=project_path,
        claude_settings_paths=settings_paths,
        runner=runner,
    )

    resolved_project_path = project_path.resolve(strict=False)
    _assert_repair_result(
        result,
        runner,
        expected_root=marketplace_root,
        expected_calls=[
            *_expected_discovery_calls(),
            (*CLAUDE_MARKETPLACE_ADD_COMMAND, "--scope", "project", str(result.root)),
        ],
        expected_cwd=[
            None,
            None,
            resolved_project_path,
            resolved_project_path,
        ],
    )
    return True


def source_reconciliation_unscoped_default_restores_only_user_plugins(
    tmp_path: Path,
) -> bool:
    marketplace_root = tmp_path / "marketplace"
    project_path = tmp_path / "consumer-project"
    user_install = (
        *CLAUDE_PLUGIN_INSTALL_COMMAND,
        "--scope",
        "user",
        f"rust@{DEFAULT_MARKETPLACE}",
    )
    user_disable = (
        *CLAUDE_PLUGIN_DISABLE_COMMAND,
        "--scope",
        "user",
        f"rust@{DEFAULT_MARKETPLACE}",
    )
    project_install = (
        *CLAUDE_PLUGIN_INSTALL_COMMAND,
        "--scope",
        "project",
        f"spec-tree@{DEFAULT_MARKETPLACE}",
    )
    settings_paths = _settings_paths(tmp_path)
    runner = RecordingCommandRunner(
        stdout_by_command={
            CLAUDE_MARKETPLACE_LIST_CALL: "[]",
            CODEX_MARKETPLACE_LIST_CALL: _codex_local_marketplace_payload(
                marketplace_root
            ),
            CLAUDE_PLUGIN_LIST_CALL: json.dumps(
                [
                    _claude_plugin_payload("rust", scope="user", enabled=False),
                    _claude_plugin_payload(
                        "spec-tree",
                        scope="project",
                        enabled=True,
                        project_path=project_path,
                    ),
                ]
            ),
        }
    )

    result = ensure_local_marketplace_sources(
        DEFAULT_MARKETPLACE,
        source_root=marketplace_root,
        claude_settings_paths=settings_paths,
        runner=runner,
    )

    _assert_repair_result(
        result,
        runner,
        expected_root=marketplace_root,
        expected_calls=[
            *_expected_discovery_calls(),
            (*CLAUDE_MARKETPLACE_ADD_COMMAND, str(result.root)),
            user_install,
            user_disable,
        ],
        expected_cwd=[None, None, None, None, None, None],
    )
    assert project_install not in runner.calls
    return True


def source_reconciliation_accepts_matching_runtime_sources(
    tmp_path: Path,
) -> bool:
    marketplace_root = tmp_path / "marketplace"
    settings_paths = _settings_paths(tmp_path)
    _write_claude_marketplace_settings(settings_paths.project, marketplace_root)
    runner = RecordingCommandRunner(
        stdout_by_command={
            ("claude", "plugin", "marketplace", "list", "--json"): json.dumps(
                [
                    {
                        "name": DEFAULT_MARKETPLACE,
                        "source": "Directory",
                        "path": str(marketplace_root),
                    }
                ]
            ),
            ("codex", "plugin", "marketplace", "list", "--json"): json.dumps(
                [
                    {
                        "name": DEFAULT_MARKETPLACE,
                        "sourceType": "local",
                        "path": str(marketplace_root),
                    }
                ]
            ),
        }
    )

    result = ensure_local_marketplace_sources(
        DEFAULT_MARKETPLACE,
        claude_settings_paths=settings_paths,
        runner=runner,
    )

    assert result.root == marketplace_root.resolve(strict=False)
    assert result.changed is False
    assert result.commands == ()
    assert runner.calls == [
        ("claude", "plugin", "marketplace", "list", "--json"),
        ("codex", "plugin", "marketplace", "list", "--json"),
    ]
    return True


def source_reconciliation_accepts_relative_project_settings_source(
    tmp_path: Path,
) -> bool:
    marketplace_root = tmp_path / "consumer-project"
    settings_paths = ClaudeSettingsPaths(
        user=tmp_path / "user-settings.json",
        project=Path(".claude") / "settings.json",
        local=Path(".claude") / "settings.local.json",
    )
    _write_claude_marketplace_settings(marketplace_root / settings_paths.project, ".")
    runner = RecordingCommandRunner(
        stdout_by_command={
            ("claude", "plugin", "marketplace", "list", "--json"): (
                _claude_directory_marketplace_payload(marketplace_root)
            ),
            ("codex", "plugin", "marketplace", "list", "--json"): (
                _codex_local_marketplace_payload(marketplace_root)
            ),
        }
    )

    result = ensure_local_marketplace_sources(
        DEFAULT_MARKETPLACE,
        source_root=marketplace_root,
        claude_project_root=marketplace_root,
        claude_settings_paths=settings_paths,
        runner=runner,
    )

    assert result.root == marketplace_root.resolve(strict=False)
    assert result.changed is False
    assert result.commands == ()
    assert runner.calls == [
        ("claude", "plugin", "marketplace", "list", "--json"),
        ("codex", "plugin", "marketplace", "list", "--json"),
    ]
    return True


def source_reconciliation_replaces_git_backed_codex_source(
    tmp_path: Path,
) -> bool:
    marketplace_root = tmp_path / "marketplace"
    settings_paths = _settings_paths(tmp_path)
    _write_claude_marketplace_settings(settings_paths.project, marketplace_root)
    runner = RecordingCommandRunner(
        stdout_by_command={
            ("claude", "plugin", "marketplace", "list", "--json"): json.dumps(
                [
                    {
                        "name": DEFAULT_MARKETPLACE,
                        "source": "Directory",
                        "path": str(marketplace_root),
                    }
                ]
            ),
            ("codex", "plugin", "marketplace", "list", "--json"): json.dumps(
                [
                    {
                        "name": DEFAULT_MARKETPLACE,
                        "sourceType": "git",
                        "url": "https://github.com/outcomeeng/plugins.git",
                    }
                ]
            ),
        }
    )

    result = ensure_local_marketplace_sources(
        DEFAULT_MARKETPLACE,
        claude_settings_paths=settings_paths,
        runner=runner,
    )

    assert result.root == marketplace_root.resolve(strict=False)
    assert result.changed is True
    assert runner.calls == [
        ("claude", "plugin", "marketplace", "list", "--json"),
        ("codex", "plugin", "marketplace", "list", "--json"),
        (*CODEX_MARKETPLACE_REMOVE_COMMAND, DEFAULT_MARKETPLACE),
        (*CODEX_MARKETPLACE_ADD_COMMAND, str(result.root)),
    ]
    return True


def source_reconciliation_replaces_mismatched_codex_path(
    tmp_path: Path,
) -> bool:
    claude_root = tmp_path / "claude-marketplace"
    codex_root = tmp_path / "codex-marketplace"
    settings_paths = _settings_paths(tmp_path)
    _write_claude_marketplace_settings(settings_paths.project, claude_root)
    runner = RecordingCommandRunner(
        stdout_by_command={
            ("claude", "plugin", "marketplace", "list", "--json"): json.dumps(
                [
                    {
                        "name": DEFAULT_MARKETPLACE,
                        "source": "Directory",
                        "path": str(claude_root),
                    }
                ]
            ),
            ("codex", "plugin", "marketplace", "list", "--json"): json.dumps(
                [
                    {
                        "name": DEFAULT_MARKETPLACE,
                        "sourceType": "local",
                        "path": str(codex_root),
                    }
                ]
            ),
        }
    )

    result = ensure_local_marketplace_sources(
        DEFAULT_MARKETPLACE,
        claude_settings_paths=settings_paths,
        runner=runner,
    )

    assert result.root == claude_root.resolve(strict=False)
    assert result.changed is True
    assert runner.calls == [
        ("claude", "plugin", "marketplace", "list", "--json"),
        ("codex", "plugin", "marketplace", "list", "--json"),
        (*CODEX_MARKETPLACE_REMOVE_COMMAND, DEFAULT_MARKETPLACE),
        (*CODEX_MARKETPLACE_ADD_COMMAND, str(result.root)),
    ]
    return True


def source_reconciliation_explicit_root_replaces_stale_runtime_paths(
    tmp_path: Path,
) -> bool:
    canonical_root = tmp_path / "canonical-marketplace"
    claude_root = tmp_path / "old-claude-marketplace"
    codex_root = tmp_path / "old-codex-marketplace"
    settings_paths = _settings_paths(tmp_path)
    _write_claude_marketplace_settings(settings_paths.project, claude_root)
    runner = _source_repair_runner(
        claude_payload=_claude_directory_marketplace_payload(claude_root),
        codex_root=codex_root,
    )

    result = ensure_local_marketplace_sources(
        DEFAULT_MARKETPLACE,
        source_root=canonical_root,
        claude_settings_paths=settings_paths,
        runner=runner,
    )

    _assert_repair_result(
        result,
        runner,
        expected_root=canonical_root,
        expected_calls=[
            *_expected_discovery_calls(),
            (*CLAUDE_MARKETPLACE_REMOVE_COMMAND, DEFAULT_MARKETPLACE),
            (*CLAUDE_MARKETPLACE_ADD_COMMAND, str(result.root)),
            *_scoped_claude_repair_calls("project", result),
            (*CODEX_MARKETPLACE_REMOVE_COMMAND, DEFAULT_MARKETPLACE),
            (*CODEX_MARKETPLACE_ADD_COMMAND, str(result.root)),
        ],
        expected_cwd=[
            None,
            None,
            result.root,
            None,
            None,
            result.root,
            result.root,
            None,
            None,
        ],
    )
    return True


def source_reconciliation_repairs_stale_project_declaration_when_runtime_matches(
    tmp_path: Path,
) -> bool:
    canonical_root = tmp_path / "canonical-marketplace"
    stale_root = tmp_path / "old-marketplace"
    settings_paths = _settings_paths(tmp_path)
    _write_claude_marketplace_settings(settings_paths.project, stale_root)
    spec_tree_install = (
        *CLAUDE_PLUGIN_INSTALL_COMMAND,
        "--scope",
        "project",
        f"spec-tree@{DEFAULT_MARKETPLACE}",
    )
    spec_tree_enable = (
        *CLAUDE_PLUGIN_ENABLE_COMMAND,
        "--scope",
        "project",
        f"spec-tree@{DEFAULT_MARKETPLACE}",
    )
    runner = RecordingCommandRunner(
        stdout_by_command={
            ("claude", "plugin", "marketplace", "list", "--json"): (
                _claude_directory_marketplace_payload(canonical_root)
            ),
            ("codex", "plugin", "marketplace", "list", "--json"): (
                _codex_local_marketplace_payload(canonical_root)
            ),
            (*CLAUDE_PLUGIN_LIST_COMMAND,): json.dumps(
                [
                    _claude_plugin_payload(
                        "spec-tree",
                        scope="project",
                        enabled=True,
                        project_path=canonical_root,
                    )
                ]
            ),
        }
    )

    result = ensure_local_marketplace_sources(
        DEFAULT_MARKETPLACE,
        source_root=canonical_root,
        claude_settings_paths=settings_paths,
        runner=runner,
    )

    _assert_repair_result(
        result,
        runner,
        expected_root=canonical_root,
        expected_calls=[
            ("claude", "plugin", "marketplace", "list", "--json"),
            ("codex", "plugin", "marketplace", "list", "--json"),
            (*CLAUDE_PLUGIN_LIST_COMMAND,),
            (
                *CLAUDE_MARKETPLACE_REMOVE_COMMAND,
                "--scope",
                "project",
                DEFAULT_MARKETPLACE,
            ),
            (*CLAUDE_MARKETPLACE_ADD_COMMAND, "--scope", "project", str(result.root)),
            spec_tree_install,
            spec_tree_enable,
        ],
        expected_cwd=[
            None,
            None,
            result.root,
            result.root,
            result.root,
            canonical_root,
            canonical_root,
        ],
    )
    return True


def source_reconciliation_repairs_stale_project_declaration_for_scoped_runtime(
    tmp_path: Path,
) -> bool:
    canonical_root = tmp_path / "canonical-marketplace"
    stale_root = tmp_path / "old-marketplace"
    project_path = tmp_path / "consumer-project"
    settings_paths = _settings_paths(tmp_path)
    _write_claude_marketplace_settings(settings_paths.project, stale_root)
    spec_tree_install = (
        *CLAUDE_PLUGIN_INSTALL_COMMAND,
        "--scope",
        "project",
        f"spec-tree@{DEFAULT_MARKETPLACE}",
    )
    spec_tree_enable = (
        *CLAUDE_PLUGIN_ENABLE_COMMAND,
        "--scope",
        "project",
        f"spec-tree@{DEFAULT_MARKETPLACE}",
    )
    for scope in (CLAUDE_SCOPE_USER, CLAUDE_SCOPE_PROJECT, CLAUDE_SCOPE_LOCAL):
        runner = RecordingCommandRunner(
            stdout_by_command={
                CLAUDE_MARKETPLACE_LIST_CALL: (
                    _scoped_claude_directory_marketplace_payload(
                        canonical_root,
                        scope=scope,
                        project_path=(
                            project_path
                            if scope in {CLAUDE_SCOPE_PROJECT, CLAUDE_SCOPE_LOCAL}
                            else None
                        ),
                    )
                ),
                CODEX_MARKETPLACE_LIST_CALL: _codex_local_marketplace_payload(
                    canonical_root
                ),
                CLAUDE_PLUGIN_LIST_CALL: json.dumps(
                    [
                        _claude_plugin_payload(
                            "spec-tree",
                            scope="project",
                            enabled=True,
                            project_path=project_path,
                        )
                    ]
                ),
            }
        )

        result = ensure_local_marketplace_sources(
            DEFAULT_MARKETPLACE,
            source_root=canonical_root,
            claude_project_root=project_path,
            claude_settings_paths=settings_paths,
            runner=runner,
        )

        _assert_repair_result(
            result,
            runner,
            expected_root=canonical_root,
            expected_calls=[
                *_expected_discovery_calls(),
                *_scoped_claude_repair_calls("project", result),
                spec_tree_install,
                spec_tree_enable,
            ],
            expected_cwd=[
                None,
                None,
                project_path.resolve(strict=False),
                project_path.resolve(strict=False),
                project_path.resolve(strict=False),
                project_path,
                project_path,
            ],
        )
    return True


def source_reconciliation_preserves_claude_plugin_installs_when_source_changes(
    tmp_path: Path,
) -> bool:
    canonical_root = tmp_path / "canonical-marketplace"
    stale_root = tmp_path / "old-marketplace"
    project_path = tmp_path / "consumer-project"
    other_project_path = tmp_path / "other-project"
    settings_paths = _settings_paths(tmp_path)
    _write_claude_marketplace_settings(settings_paths.project, stale_root)
    spec_tree_install = (
        *CLAUDE_PLUGIN_INSTALL_COMMAND,
        "--scope",
        "project",
        f"spec-tree@{DEFAULT_MARKETPLACE}",
    )
    spec_tree_enable = (
        *CLAUDE_PLUGIN_ENABLE_COMMAND,
        "--scope",
        "project",
        f"spec-tree@{DEFAULT_MARKETPLACE}",
    )
    rust_install = (
        *CLAUDE_PLUGIN_INSTALL_COMMAND,
        "--scope",
        "user",
        f"rust@{DEFAULT_MARKETPLACE}",
    )
    rust_disable = (
        *CLAUDE_PLUGIN_DISABLE_COMMAND,
        "--scope",
        "user",
        f"rust@{DEFAULT_MARKETPLACE}",
    )
    prose_install = (
        *CLAUDE_PLUGIN_INSTALL_COMMAND,
        "--scope",
        "project",
        f"prose@{DEFAULT_MARKETPLACE}",
    )
    prose_enable = (
        *CLAUDE_PLUGIN_ENABLE_COMMAND,
        "--scope",
        "project",
        f"prose@{DEFAULT_MARKETPLACE}",
    )
    typescript_install = (
        *CLAUDE_PLUGIN_INSTALL_COMMAND,
        "--scope",
        "project",
        f"typescript@{DEFAULT_MARKETPLACE}",
    )
    typescript_disable = (
        *CLAUDE_PLUGIN_DISABLE_COMMAND,
        "--scope",
        "project",
        f"typescript@{DEFAULT_MARKETPLACE}",
    )
    hdl_install = (
        *CLAUDE_PLUGIN_INSTALL_COMMAND,
        "--scope",
        "local",
        f"hdl@{DEFAULT_MARKETPLACE}",
    )
    hdl_enable = (
        *CLAUDE_PLUGIN_ENABLE_COMMAND,
        "--scope",
        "local",
        f"hdl@{DEFAULT_MARKETPLACE}",
    )
    stdout_by_command = {
        ("claude", "plugin", "marketplace", "list", "--json"): (
            _claude_directory_marketplace_payload(stale_root)
        ),
        ("codex", "plugin", "marketplace", "list", "--json"): (
            _codex_local_marketplace_payload(canonical_root)
        ),
        (*CLAUDE_PLUGIN_LIST_COMMAND,): json.dumps(
            [
                _claude_plugin_payload(
                    "spec-tree",
                    scope="project",
                    enabled=True,
                    project_path=project_path,
                ),
                _claude_plugin_payload(
                    "rust",
                    scope="user",
                    enabled=False,
                ),
                _claude_plugin_payload(
                    "prose",
                    scope="project",
                    enabled=True,
                    project_path=other_project_path,
                ),
                _claude_plugin_payload(
                    "typescript",
                    scope="project",
                    enabled=False,
                    project_path=project_path,
                ),
                _claude_plugin_payload(
                    "hdl",
                    scope="local",
                    enabled=True,
                    project_path=project_path,
                ),
            ]
        ),
    }
    runner = RecordingCommandRunner(
        stdout_by_command=stdout_by_command,
        returncode_by_command={
            spec_tree_install: 1,
            spec_tree_enable: 1,
            rust_disable: 1,
            typescript_disable: 1,
        },
        stderr_by_command={
            # Message body matches Claude Code CLI stderr observed from:
            # claude plugin install --scope project spec-tree@outcomeeng
            spec_tree_install: (
                f'Failed to install plugin "spec-tree@{DEFAULT_MARKETPLACE}": '
                f'Plugin "spec-tree@{DEFAULT_MARKETPLACE}" is '
                f"{CLAUDE_PLUGIN_ALREADY_INSTALLED_FRAGMENT} at project scope"
            ),
            # Message body matches Claude Code CLI stderr observed from:
            # claude plugin enable --scope project spec-tree@outcomeeng
            spec_tree_enable: (
                f'\u2718 Failed to enable plugin "spec-tree@{DEFAULT_MARKETPLACE}": '
                f'Plugin "spec-tree@{DEFAULT_MARKETPLACE}" is '
                f"{CLAUDE_PLUGIN_ALREADY_ENABLED_FRAGMENT} at project scope"
            ),
            # Message body matches Claude Code CLI stderr observed from:
            # claude plugin disable --scope project typescript@outcomeeng
            typescript_disable: (
                f'\u2718 Failed to disable plugin "typescript@{DEFAULT_MARKETPLACE}": '
                f'Plugin "typescript@{DEFAULT_MARKETPLACE}" is '
                f"{CLAUDE_PLUGIN_ALREADY_DISABLED_FRAGMENT} at project scope"
            ),
            # Message body matches Claude Code CLI stderr observed from:
            # claude plugin disable --scope user rust@outcomeeng
            rust_disable: (
                f'\u2718 Failed to disable plugin "rust@{DEFAULT_MARKETPLACE}": '
                f'Plugin "rust@{DEFAULT_MARKETPLACE}" is '
                f"{CLAUDE_PLUGIN_ALREADY_DISABLED_FRAGMENT} at user scope"
            ),
        },
    )

    result = ensure_local_marketplace_sources(
        DEFAULT_MARKETPLACE,
        source_root=canonical_root,
        claude_project_root=project_path,
        claude_settings_paths=settings_paths,
        runner=runner,
    )

    assert result.changed is True
    resolved_project_path = project_path.resolve(strict=False)
    assert runner.calls == [
        ("claude", "plugin", "marketplace", "list", "--json"),
        ("codex", "plugin", "marketplace", "list", "--json"),
        (*CLAUDE_PLUGIN_LIST_COMMAND,),
        (*CLAUDE_MARKETPLACE_REMOVE_COMMAND, DEFAULT_MARKETPLACE),
        (*CLAUDE_MARKETPLACE_ADD_COMMAND, str(result.root)),
        (*CLAUDE_MARKETPLACE_REMOVE_COMMAND, "--scope", "project", DEFAULT_MARKETPLACE),
        (*CLAUDE_MARKETPLACE_ADD_COMMAND, "--scope", "project", str(result.root)),
        spec_tree_install,
        spec_tree_enable,
        rust_install,
        rust_disable,
        typescript_install,
        typescript_disable,
        hdl_install,
        hdl_enable,
    ]
    expected_cwd = [
        None,
        None,
        resolved_project_path,
        None,
        None,
        resolved_project_path,
        resolved_project_path,
        project_path,
        project_path,
        None,
        None,
        project_path,
        project_path,
        project_path,
        project_path,
    ]
    assert runner.cwd_by_call == expected_cwd, runner.cwd_by_call
    assert prose_install not in runner.calls
    assert prose_enable not in runner.calls

    def assert_restore_failure_surfaces(
        command: tuple[str, ...],
        stderr: str,
        command_fragment: str,
    ) -> None:
        rejecting_runner = RecordingCommandRunner(
            stdout_by_command=stdout_by_command,
            returncode_by_command={command: 1},
            stderr_by_command={command: stderr},
        )

        with pytest.raises(MarketplaceSourceError) as exc_info:
            ensure_local_marketplace_sources(
                DEFAULT_MARKETPLACE,
                source_root=canonical_root,
                claude_project_root=project_path,
                claude_settings_paths=settings_paths,
                runner=rejecting_runner,
            )

        message = str(exc_info.value)
        assert command_fragment in message
        assert stderr in message

    for command, stderr, command_fragment in (
        (
            spec_tree_install,
            (
                f'Failed to install plugin "spec-tree@{DEFAULT_MARKETPLACE}": '
                f'Plugin "spec-tree@{DEFAULT_MARKETPLACE}" is '
                f"{CLAUDE_PLUGIN_ALREADY_INSTALLED_FRAGMENT} at project scope; "
                "permission update failed"
            ),
            "claude plugin install --scope project",
        ),
        (
            spec_tree_enable,
            (
                f'Failed to enable plugin "spec-tree@{DEFAULT_MARKETPLACE}": '
                f'Plugin "spec-tree@{DEFAULT_MARKETPLACE}" is '
                f"{CLAUDE_PLUGIN_ALREADY_ENABLED_FRAGMENT} at project scope; "
                "permission update failed"
            ),
            "claude plugin enable --scope project",
        ),
        (
            typescript_disable,
            (
                f'Failed to disable plugin "typescript@{DEFAULT_MARKETPLACE}": '
                f'Plugin "typescript@{DEFAULT_MARKETPLACE}" is '
                f"{CLAUDE_PLUGIN_ALREADY_DISABLED_FRAGMENT} at project scope; "
                "permission update failed"
            ),
            "claude plugin disable --scope project",
        ),
    ):
        assert_restore_failure_surfaces(command, stderr, command_fragment)

    return True


def source_reconciliation_preserves_user_scope_claude_plugin_installs(
    tmp_path: Path,
) -> bool:
    canonical_root = tmp_path / "canonical-marketplace"
    stale_root = tmp_path / "old-marketplace"
    settings_paths = _settings_paths(tmp_path)
    _write_claude_marketplace_settings(settings_paths.user, stale_root)
    rust_install = (
        *CLAUDE_PLUGIN_INSTALL_COMMAND,
        "--scope",
        "user",
        f"rust@{DEFAULT_MARKETPLACE}",
    )
    rust_disable = (
        *CLAUDE_PLUGIN_DISABLE_COMMAND,
        "--scope",
        "user",
        f"rust@{DEFAULT_MARKETPLACE}",
    )
    spec_tree_install = (
        *CLAUDE_PLUGIN_INSTALL_COMMAND,
        "--scope",
        "project",
        f"spec-tree@{DEFAULT_MARKETPLACE}",
    )
    spec_tree_enable = (
        *CLAUDE_PLUGIN_ENABLE_COMMAND,
        "--scope",
        "project",
        f"spec-tree@{DEFAULT_MARKETPLACE}",
    )
    runner = RecordingCommandRunner(
        stdout_by_command={
            ("claude", "plugin", "marketplace", "list", "--json"): (
                _scoped_claude_directory_marketplace_payload(
                    stale_root,
                    scope="user",
                )
            ),
            ("codex", "plugin", "marketplace", "list", "--json"): (
                _codex_local_marketplace_payload(canonical_root)
            ),
            (*CLAUDE_PLUGIN_LIST_COMMAND,): json.dumps(
                [
                    _claude_plugin_payload(
                        "rust",
                        scope="user",
                        enabled=False,
                    ),
                    _claude_plugin_payload(
                        "spec-tree",
                        scope="project",
                        enabled=True,
                        project_path=canonical_root,
                    ),
                ]
            ),
        }
    )

    result = ensure_local_marketplace_sources(
        DEFAULT_MARKETPLACE,
        source_root=canonical_root,
        claude_settings_paths=settings_paths,
        runner=runner,
    )

    assert result.root == canonical_root.resolve(strict=False)
    assert result.changed is True
    assert runner.calls == [
        ("claude", "plugin", "marketplace", "list", "--json"),
        ("codex", "plugin", "marketplace", "list", "--json"),
        (*CLAUDE_PLUGIN_LIST_COMMAND,),
        (*CLAUDE_MARKETPLACE_REMOVE_COMMAND, "--scope", "user", DEFAULT_MARKETPLACE),
        (*CLAUDE_MARKETPLACE_ADD_COMMAND, "--scope", "user", str(result.root)),
        rust_install,
        rust_disable,
        spec_tree_install,
        spec_tree_enable,
    ]
    assert runner.cwd_by_call == [
        None,
        None,
        result.root,
        None,
        None,
        None,
        None,
        canonical_root,
        canonical_root,
    ]
    return True


def source_reconciliation_restores_user_plugin_from_scoped_repair_context(
    tmp_path: Path,
) -> bool:
    canonical_root = tmp_path / "canonical-marketplace"
    stale_project_root = tmp_path / "old-project-marketplace"
    project_path = tmp_path / "consumer-project"
    settings_paths = _settings_paths(tmp_path)
    _write_claude_marketplace_settings(settings_paths.project, stale_project_root)
    rust_install = (
        *CLAUDE_PLUGIN_INSTALL_COMMAND,
        "--scope",
        "user",
        f"rust@{DEFAULT_MARKETPLACE}",
    )
    rust_disable = (
        *CLAUDE_PLUGIN_DISABLE_COMMAND,
        "--scope",
        "user",
        f"rust@{DEFAULT_MARKETPLACE}",
    )
    runner = _source_repair_runner(
        claude_payload=_claude_directory_marketplace_payload(canonical_root),
        codex_root=canonical_root,
        plugin_payload=json.dumps(
            [
                _claude_plugin_payload(
                    "rust",
                    scope="user",
                    enabled=False,
                )
            ]
        ),
    )

    result = ensure_local_marketplace_sources(
        DEFAULT_MARKETPLACE,
        source_root=canonical_root,
        claude_project_root=project_path,
        claude_settings_paths=settings_paths,
        runner=runner,
    )

    _assert_repair_result(
        result,
        runner,
        expected_root=canonical_root,
        expected_calls=[
            *_expected_discovery_calls(),
            *_scoped_claude_repair_calls("project", result),
            rust_install,
            rust_disable,
        ],
        expected_cwd=[
            None,
            None,
            project_path.resolve(strict=False),
            project_path.resolve(strict=False),
            project_path.resolve(strict=False),
            project_path.resolve(strict=False),
            project_path.resolve(strict=False),
        ],
    )
    return True


def source_reconciliation_repairs_local_scope_claude_source(
    tmp_path: Path,
) -> bool:
    canonical_root = tmp_path / "canonical-marketplace"
    stale_root = tmp_path / "old-marketplace"
    project_path = tmp_path / "consumer-project"
    settings_paths = _settings_paths(tmp_path)
    _write_claude_marketplace_settings(settings_paths.local, stale_root)
    prose_install = (
        *CLAUDE_PLUGIN_INSTALL_COMMAND,
        "--scope",
        "local",
        f"prose@{DEFAULT_MARKETPLACE}",
    )
    prose_enable = (
        *CLAUDE_PLUGIN_ENABLE_COMMAND,
        "--scope",
        "local",
        f"prose@{DEFAULT_MARKETPLACE}",
    )
    runner = RecordingCommandRunner(
        stdout_by_command={
            ("claude", "plugin", "marketplace", "list", "--json"): (
                _scoped_claude_directory_marketplace_payload(
                    stale_root,
                    scope="local",
                    project_path=project_path,
                )
            ),
            ("codex", "plugin", "marketplace", "list", "--json"): (
                _codex_local_marketplace_payload(canonical_root)
            ),
            (*CLAUDE_PLUGIN_LIST_COMMAND,): json.dumps(
                [
                    _claude_plugin_payload(
                        "prose",
                        scope="local",
                        enabled=True,
                        project_path=project_path,
                    )
                ]
            ),
        }
    )

    result = ensure_local_marketplace_sources(
        DEFAULT_MARKETPLACE,
        source_root=canonical_root,
        claude_project_root=project_path,
        claude_settings_paths=settings_paths,
        runner=runner,
    )

    assert result.root == canonical_root.resolve(strict=False)
    assert result.changed is True
    assert runner.calls == [
        ("claude", "plugin", "marketplace", "list", "--json"),
        ("codex", "plugin", "marketplace", "list", "--json"),
        (*CLAUDE_PLUGIN_LIST_COMMAND,),
        (*CLAUDE_MARKETPLACE_REMOVE_COMMAND, "--scope", "local", DEFAULT_MARKETPLACE),
        (*CLAUDE_MARKETPLACE_ADD_COMMAND, "--scope", "local", str(result.root)),
        prose_install,
        prose_enable,
    ]
    assert runner.cwd_by_call == [
        None,
        None,
        project_path.resolve(strict=False),
        project_path.resolve(strict=False),
        project_path.resolve(strict=False),
        project_path,
        project_path,
    ]
    return True


def source_reconciliation_repairs_runtime_source_with_stale_scoped_settings(
    tmp_path: Path,
) -> bool:
    canonical_root = tmp_path / "canonical-marketplace"
    stale_user_root = tmp_path / "old-user-marketplace"
    stale_project_root = tmp_path / "old-project-marketplace"
    project_path = tmp_path / "consumer-project"
    settings_paths = _settings_paths(tmp_path)
    _write_claude_marketplace_settings(settings_paths.project, stale_project_root)
    runner = _source_repair_runner(
        claude_payload=_scoped_claude_directory_marketplace_payload(
            stale_user_root,
            scope="user",
        ),
        codex_root=canonical_root,
        plugin_payload=json.dumps(
            [
                _claude_plugin_payload(
                    "rust",
                    scope="user",
                    enabled=True,
                )
            ]
        ),
    )
    rust_install = (
        *CLAUDE_PLUGIN_INSTALL_COMMAND,
        "--scope",
        "user",
        f"rust@{DEFAULT_MARKETPLACE}",
    )
    rust_enable = (
        *CLAUDE_PLUGIN_ENABLE_COMMAND,
        "--scope",
        "user",
        f"rust@{DEFAULT_MARKETPLACE}",
    )

    result = ensure_local_marketplace_sources(
        DEFAULT_MARKETPLACE,
        source_root=canonical_root,
        claude_project_root=project_path,
        claude_settings_paths=settings_paths,
        runner=runner,
    )

    _assert_repair_result(
        result,
        runner,
        expected_root=canonical_root,
        expected_calls=[
            *_expected_discovery_calls(),
            *_scoped_claude_repair_calls("project", result),
            *_scoped_claude_repair_calls("user", result),
            rust_install,
            rust_enable,
        ],
        expected_cwd=[
            None,
            None,
            project_path.resolve(strict=False),
            project_path.resolve(strict=False),
            project_path.resolve(strict=False),
            None,
            None,
            None,
            None,
        ],
    )
    return True


def source_reconciliation_preserves_second_matching_scoped_plugin(
    tmp_path: Path,
) -> bool:
    canonical_root = tmp_path / "canonical-marketplace"
    stale_project_root = tmp_path / "old-project-marketplace"
    stale_local_root = tmp_path / "old-local-marketplace"
    project_path = tmp_path / "consumer-project"
    settings_paths = _settings_paths(tmp_path)
    _write_claude_marketplace_settings(settings_paths.project, stale_project_root)
    spec_tree_install = (
        *CLAUDE_PLUGIN_INSTALL_COMMAND,
        "--scope",
        "project",
        f"spec-tree@{DEFAULT_MARKETPLACE}",
    )
    spec_tree_enable = (
        *CLAUDE_PLUGIN_ENABLE_COMMAND,
        "--scope",
        "project",
        f"spec-tree@{DEFAULT_MARKETPLACE}",
    )
    runner = _source_repair_runner(
        claude_payload=_scoped_claude_directory_marketplace_payload(
            stale_local_root,
            scope="local",
            project_path=project_path,
        ),
        codex_root=canonical_root,
        plugin_payload=json.dumps(
            [
                _claude_plugin_payload(
                    "spec-tree",
                    scope="project",
                    enabled=True,
                    project_path=project_path,
                )
            ]
        ),
    )

    result = ensure_local_marketplace_sources(
        DEFAULT_MARKETPLACE,
        source_root=canonical_root,
        claude_project_root=project_path,
        claude_settings_paths=settings_paths,
        runner=runner,
    )

    _assert_repair_result(
        result,
        runner,
        expected_root=canonical_root,
        expected_calls=[
            *_expected_discovery_calls(),
            *_scoped_claude_repair_calls("project", result),
            *_scoped_claude_repair_calls("local", result),
            spec_tree_install,
            spec_tree_enable,
        ],
        expected_cwd=[
            None,
            None,
            project_path.resolve(strict=False),
            project_path.resolve(strict=False),
            project_path.resolve(strict=False),
            project_path.resolve(strict=False),
            project_path.resolve(strict=False),
            project_path,
            project_path,
        ],
    )
    return True


def source_reconciliation_filter_checks_later_repair_targets(tmp_path: Path) -> bool:
    first_project_path = tmp_path / "first-project"
    second_project_path = tmp_path / "second-project"
    plugin = ClaudeInstalledPlugin(
        name="spec-tree",
        marketplace=DEFAULT_MARKETPLACE,
        scope=CLAUDE_SCOPE_PROJECT,
        enabled=True,
        project_path=second_project_path,
    )
    targets = (
        ClaudeMarketplaceRepairTarget(
            scope=CLAUDE_SCOPE_PROJECT,
            source=None,
            project_path=first_project_path,
        ),
        ClaudeMarketplaceRepairTarget(
            scope=CLAUDE_SCOPE_LOCAL,
            source=None,
            project_path=second_project_path,
        ),
    )

    assert _claude_plugin_belongs_to_repair_targets(plugin, targets) is True
    return True


def source_reconciliation_filter_skips_unscoped_before_later_scoped_target(
    tmp_path: Path,
) -> bool:
    project_path = tmp_path / "consumer-project"
    plugin = ClaudeInstalledPlugin(
        name="spec-tree",
        marketplace=DEFAULT_MARKETPLACE,
        scope=CLAUDE_SCOPE_PROJECT,
        enabled=True,
        project_path=project_path,
    )
    targets = (
        ClaudeMarketplaceRepairTarget(
            scope=None,
            source=None,
            project_path=None,
        ),
        ClaudeMarketplaceRepairTarget(
            scope=CLAUDE_SCOPE_PROJECT,
            source=None,
            project_path=project_path,
        ),
    )

    assert _claude_plugin_belongs_to_repair_targets(plugin, targets) is True
    return True


def source_reconciliation_repairs_matching_source_with_stale_project_path(
    tmp_path: Path,
) -> bool:
    canonical_root = tmp_path / "canonical-marketplace"
    project_path = tmp_path / "consumer-project"
    stale_project_path = tmp_path / "old-consumer-project"
    return _assert_project_scope_repair(
        tmp_path,
        claude_payload=_scoped_claude_directory_marketplace_payload(
            canonical_root,
            scope="project",
            project_path=stale_project_path,
        ),
        claude_project_root=project_path,
    )


def source_reconciliation_repairs_scoped_runtime_source_without_project_path(
    tmp_path: Path,
) -> bool:
    canonical_root = tmp_path / "canonical-marketplace"
    project_path = tmp_path / "consumer-project"
    return _assert_project_scope_repair(
        tmp_path,
        claude_payload=_scoped_claude_directory_marketplace_payload(
            canonical_root,
            scope="project",
        ),
        claude_project_root=project_path,
    )


def source_reconciliation_rejects_malformed_claude_settings(
    tmp_path: Path,
) -> bool:
    canonical_root = tmp_path / "canonical-marketplace"
    settings_paths = _settings_paths(tmp_path)
    settings_paths.project.write_text("{not json", encoding="utf-8")
    runner = RecordingCommandRunner(
        stdout_by_command={
            ("claude", "plugin", "marketplace", "list", "--json"): (
                _claude_directory_marketplace_payload(canonical_root)
            ),
            ("codex", "plugin", "marketplace", "list", "--json"): (
                _codex_local_marketplace_payload(canonical_root)
            ),
        }
    )

    with pytest.raises(MarketplaceSourceError) as exc_info:
        ensure_local_marketplace_sources(
            DEFAULT_MARKETPLACE,
            source_root=canonical_root,
            claude_settings_paths=settings_paths,
            runner=runner,
        )

    message = str(exc_info.value)
    assert "not valid JSON" in message
    assert str(settings_paths.project) in message
    return True


def source_reconciliation_rejects_non_object_claude_settings(
    tmp_path: Path,
) -> bool:
    canonical_root = tmp_path / "canonical-marketplace"
    settings_paths = _settings_paths(tmp_path)
    settings_paths.project.write_text("[]", encoding="utf-8")
    runner = RecordingCommandRunner(
        stdout_by_command={
            ("claude", "plugin", "marketplace", "list", "--json"): (
                _claude_directory_marketplace_payload(canonical_root)
            ),
            ("codex", "plugin", "marketplace", "list", "--json"): (
                _codex_local_marketplace_payload(canonical_root)
            ),
        }
    )

    with pytest.raises(MarketplaceSourceError) as exc_info:
        ensure_local_marketplace_sources(
            DEFAULT_MARKETPLACE,
            source_root=canonical_root,
            claude_settings_paths=settings_paths,
            runner=runner,
        )

    message = str(exc_info.value)
    assert "not an object" in message
    assert str(settings_paths.project) in message
    return True


def source_reconciliation_rejects_scoped_claude_plugin_without_project_path(
    tmp_path: Path,
) -> bool:
    canonical_root = tmp_path / "canonical-marketplace"
    stale_root = tmp_path / "old-marketplace"
    settings_paths = _settings_paths(tmp_path)
    _write_claude_marketplace_settings(settings_paths.project, stale_root)
    runner = RecordingCommandRunner(
        stdout_by_command={
            ("claude", "plugin", "marketplace", "list", "--json"): json.dumps(
                [
                    {
                        "name": DEFAULT_MARKETPLACE,
                        "source": "Directory",
                        "path": str(stale_root),
                    }
                ]
            ),
            ("codex", "plugin", "marketplace", "list", "--json"): json.dumps(
                [
                    {
                        "name": DEFAULT_MARKETPLACE,
                        "sourceType": "local",
                        "path": str(canonical_root),
                    }
                ]
            ),
            (*CLAUDE_PLUGIN_LIST_COMMAND,): json.dumps(
                [
                    {
                        "id": f"spec-tree@{DEFAULT_MARKETPLACE}",
                        "scope": "project",
                        "enabled": True,
                    }
                ]
            ),
        }
    )

    with pytest.raises(MarketplaceSourceError) as exc_info:
        ensure_local_marketplace_sources(
            DEFAULT_MARKETPLACE,
            source_root=canonical_root,
            claude_project_root=tmp_path,
            claude_settings_paths=settings_paths,
            runner=runner,
        )

    message = str(exc_info.value)
    assert f"spec-tree@{DEFAULT_MARKETPLACE}" in message
    assert "projectPath" in message
    assert runner.calls == [
        ("claude", "plugin", "marketplace", "list", "--json"),
        ("codex", "plugin", "marketplace", "list", "--json"),
        (*CLAUDE_PLUGIN_LIST_COMMAND,),
    ]
    return True


def source_reconciliation_repairs_unscoped_stale_claude_runtime_source(
    tmp_path: Path,
) -> bool:
    canonical_root = tmp_path / "canonical-marketplace"
    stale_root = tmp_path / "old-marketplace"
    runner = _source_repair_runner(
        claude_payload=_claude_directory_marketplace_payload(stale_root),
        codex_root=canonical_root,
    )

    result = ensure_local_marketplace_sources(
        DEFAULT_MARKETPLACE,
        source_root=canonical_root,
        claude_settings_paths=_settings_paths(tmp_path),
        runner=runner,
    )

    _assert_repair_result(
        result,
        runner,
        expected_root=canonical_root,
        expected_calls=[
            *_expected_discovery_calls(),
            (*CLAUDE_MARKETPLACE_REMOVE_COMMAND, DEFAULT_MARKETPLACE),
            (*CLAUDE_MARKETPLACE_ADD_COMMAND, str(result.root)),
        ],
        expected_cwd=[None, None, None, None, None],
    )
    return True


def source_reconciliation_repairs_unscoped_runtime_with_stale_scoped_settings(
    tmp_path: Path,
) -> bool:
    canonical_root = tmp_path / "canonical-marketplace"
    stale_runtime_root = tmp_path / "old-runtime-marketplace"
    stale_project_root = tmp_path / "old-project-marketplace"
    settings_paths = _settings_paths(tmp_path)
    _write_claude_marketplace_settings(settings_paths.project, stale_project_root)
    runner = _source_repair_runner(
        claude_payload=_claude_directory_marketplace_payload(stale_runtime_root),
        codex_root=canonical_root,
    )

    result = ensure_local_marketplace_sources(
        DEFAULT_MARKETPLACE,
        source_root=canonical_root,
        claude_settings_paths=settings_paths,
        runner=runner,
    )

    _assert_repair_result(
        result,
        runner,
        expected_root=canonical_root,
        expected_calls=[
            *_expected_discovery_calls(),
            (*CLAUDE_MARKETPLACE_REMOVE_COMMAND, DEFAULT_MARKETPLACE),
            (*CLAUDE_MARKETPLACE_ADD_COMMAND, str(result.root)),
            *_scoped_claude_repair_calls("project", result),
        ],
        expected_cwd=[
            None,
            None,
            result.root,
            None,
            None,
            result.root,
            result.root,
        ],
    )
    return True


def source_reconciliation_readds_matching_scoped_settings_after_unscoped_repair(
    tmp_path: Path,
) -> bool:
    canonical_root = tmp_path / "canonical-marketplace"
    stale_runtime_root = tmp_path / "old-runtime-marketplace"
    settings_paths = _settings_paths(tmp_path)
    _write_claude_marketplace_settings(settings_paths.project, canonical_root)
    runner = _source_repair_runner(
        claude_payload=_claude_directory_marketplace_payload(stale_runtime_root),
        codex_root=canonical_root,
    )

    result = ensure_local_marketplace_sources(
        DEFAULT_MARKETPLACE,
        source_root=canonical_root,
        claude_settings_paths=settings_paths,
        runner=runner,
    )

    _assert_repair_result(
        result,
        runner,
        expected_root=canonical_root,
        expected_calls=[
            *_expected_discovery_calls(),
            (*CLAUDE_MARKETPLACE_REMOVE_COMMAND, DEFAULT_MARKETPLACE),
            (*CLAUDE_MARKETPLACE_ADD_COMMAND, str(result.root)),
            (*CLAUDE_MARKETPLACE_ADD_COMMAND, "--scope", "project", str(result.root)),
        ],
        expected_cwd=[
            None,
            None,
            result.root,
            None,
            None,
            result.root,
        ],
    )
    return True


def source_reconciliation_failed_codex_add_surfaces_error(
    tmp_path: Path,
) -> bool:
    marketplace_root = tmp_path / "marketplace"
    resolved_root = marketplace_root.resolve(strict=False)
    settings_paths = _settings_paths(tmp_path)
    _write_claude_marketplace_settings(settings_paths.project, marketplace_root)
    codex_add = (*CODEX_MARKETPLACE_ADD_COMMAND, str(resolved_root))
    runner = RecordingCommandRunner(
        stdout_by_command={
            ("claude", "plugin", "marketplace", "list", "--json"): json.dumps(
                [
                    {
                        "name": DEFAULT_MARKETPLACE,
                        "source": "Directory",
                        "path": str(marketplace_root),
                    }
                ]
            ),
            ("codex", "plugin", "marketplace", "list", "--json"): json.dumps(
                [
                    {
                        "name": DEFAULT_MARKETPLACE,
                        "sourceType": "git",
                        "url": "https://github.com/outcomeeng/plugins.git",
                    }
                ]
            ),
        },
        returncode_by_command={codex_add: 17},
        stderr_by_command={codex_add: "add failed"},
    )

    with pytest.raises(MarketplaceSourceError) as exc_info:
        ensure_local_marketplace_sources(
            DEFAULT_MARKETPLACE,
            source_root=marketplace_root,
            claude_settings_paths=settings_paths,
            runner=runner,
        )

    message = str(exc_info.value)
    assert "codex plugin marketplace add" in message
    assert "add failed" in message
    assert runner.calls == [
        ("claude", "plugin", "marketplace", "list", "--json"),
        ("codex", "plugin", "marketplace", "list", "--json"),
        (*CODEX_MARKETPLACE_REMOVE_COMMAND, DEFAULT_MARKETPLACE),
        codex_add,
    ]
    return True


@dataclass
class RecordingCommandRunner:
    """Command runner spy for marketplace source reconciliation.

    Stage 5 exception 2 (interaction-protocol DI): correctness depends on the
    sequence of runtime CLI calls, while the real commands mutate user config.
    """

    stdout_by_command: dict[tuple[str, ...], str]
    returncode_by_command: dict[tuple[str, ...], int] = field(default_factory=dict)
    stderr_by_command: dict[tuple[str, ...], str] = field(default_factory=dict)
    calls: list[tuple[str, ...]] = field(default_factory=list)
    cwd_by_call: list[Path | None] = field(default_factory=list)

    def __call__(
        self, command: list[str], *, cwd: Path | None = None
    ) -> subprocess.CompletedProcess[str]:
        command_tuple = tuple(command)
        self.calls.append(command_tuple)
        self.cwd_by_call.append(cwd)
        return subprocess.CompletedProcess(
            command,
            self.returncode_by_command.get(command_tuple, 0),
            stdout=self.stdout_by_command.get(command_tuple, ""),
            stderr=self.stderr_by_command.get(command_tuple, ""),
        )


def _write_codex_manifest(repo_root: Path, plugin: str, version: str) -> None:
    manifest = repo_root / DIST_CODEX_PLUGINS_DIR / plugin / CODEX_PLUGIN_MANIFEST
    manifest.parent.mkdir(parents=True)
    manifest.write_text(
        json.dumps({"name": plugin, "version": version}), encoding="utf-8"
    )


def _settings_paths(tmp_path: Path) -> ClaudeSettingsPaths:
    return ClaudeSettingsPaths(
        user=tmp_path / "user-settings.json",
        project=tmp_path / "project-settings.json",
        local=tmp_path / "local-settings.json",
    )


def _write_claude_marketplace_settings(path: Path, source_path: Path | str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "extraKnownMarketplaces": {
                    DEFAULT_MARKETPLACE: {
                        "source": {
                            "source": "directory",
                            "path": str(source_path),
                        }
                    }
                }
            }
        ),
        encoding="utf-8",
    )
