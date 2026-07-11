"""Harnesses for local marketplace source conformance evidence."""

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
    CLAUDE_PLUGIN_ALREADY_DISABLED_FRAGMENT,
    CLAUDE_PLUGIN_ALREADY_ENABLED_FRAGMENT,
    CLAUDE_PLUGIN_ALREADY_INSTALLED_FRAGMENT,
    CLAUDE_PLUGIN_DISABLE_COMMAND,
    CLAUDE_PLUGIN_ENABLE_COMMAND,
    CLAUDE_PLUGIN_INSTALL_COMMAND,
    CLAUDE_PLUGIN_LIST_COMMAND,
    CLAUDE_SCOPE_LOCAL,
    CLAUDE_SCOPE_MANAGED,
    CLAUDE_SCOPE_PROJECT,
    CLAUDE_SCOPE_USER,
    CODEX_MARKETPLACE_ADD_COMMAND,
    CODEX_MARKETPLACE_LIST_COMMAND,
    CODEX_MARKETPLACE_REMOVE_COMMAND,
    DEFAULT_MARKETPLACE,
    MARKETPLACE_FIELD_MARKETPLACE_SOURCE,
    MARKETPLACE_FIELD_MARKETPLACES,
    MARKETPLACE_FIELD_NAME,
    MARKETPLACE_FIELD_PATH,
    MARKETPLACE_FIELD_PROJECT_PATH,
    MARKETPLACE_FIELD_ROOT,
    MARKETPLACE_FIELD_SCOPE,
    MARKETPLACE_FIELD_SOURCE,
    MARKETPLACE_FIELD_SOURCE_TYPE,
    MARKETPLACE_FIELD_URL,
    MarketplaceConfigRepairResult,
    MarketplaceSourceError,
    PLUGIN_FIELD_ENABLED,
    PLUGIN_FIELD_ID,
    SOURCE_TYPE_GIT,
    SOURCE_TYPE_LOCAL,
    configured_claude_directory_marketplace_root,
    configured_local_marketplace_root,
    ensure_local_marketplace_sources,
    parse_claude_installed_plugins,
    parse_claude_marketplace_sources,
    parse_codex_marketplace_sources,
    require_matching_local_sources,
)

CLAUDE_MARKETPLACE_LIST_CALL = (*CLAUDE_MARKETPLACE_LIST_COMMAND,)
CODEX_MARKETPLACE_LIST_CALL = (*CODEX_MARKETPLACE_LIST_COMMAND,)
CLAUDE_PLUGIN_LIST_CALL = (*CLAUDE_PLUGIN_LIST_COMMAND,)


@dataclass
class RecordingCommandRunner:
    """Command runner fixture recording calls without invoking runtime CLIs."""

    stdout_by_command: dict[tuple[str, ...], str] = field(default_factory=dict)
    returncode_by_command: dict[tuple[str, ...], int] = field(default_factory=dict)
    stderr_by_command: dict[tuple[str, ...], str] = field(default_factory=dict)
    calls: list[tuple[str, ...]] = field(default_factory=list)
    cwd_by_call: list[Path | None] = field(default_factory=list)

    def __call__(
        self,
        command: list[str],
        *,
        cwd: Path | None = None,
    ) -> subprocess.CompletedProcess[str]:
        key = tuple(command)
        self.calls.append(key)
        self.cwd_by_call.append(cwd)
        return subprocess.CompletedProcess(
            args=command,
            returncode=self.returncode_by_command.get(key, 0),
            stdout=self.stdout_by_command.get(key, ""),
            stderr=self.stderr_by_command.get(key, ""),
        )


def with_temporary_marketplace_path(
    assertion: Callable[[Path], bool],
) -> bool:
    with TemporaryDirectory() as directory:
        return assertion(Path(directory))


def _claude_directory_marketplace_payload(path: Path) -> str:
    return json.dumps(
        [
            {
                MARKETPLACE_FIELD_NAME: DEFAULT_MARKETPLACE,
                MARKETPLACE_FIELD_SOURCE: "Directory",
                MARKETPLACE_FIELD_PATH: str(path),
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
        MARKETPLACE_FIELD_NAME: DEFAULT_MARKETPLACE,
        MARKETPLACE_FIELD_SOURCE: "Directory",
        MARKETPLACE_FIELD_PATH: str(path),
        MARKETPLACE_FIELD_SCOPE: scope,
    }
    if project_path is not None:
        payload[MARKETPLACE_FIELD_PROJECT_PATH] = str(project_path)
    return json.dumps([payload])


def _codex_local_marketplace_payload(path: Path) -> str:
    return json.dumps(
        [
            {
                MARKETPLACE_FIELD_NAME: DEFAULT_MARKETPLACE,
                MARKETPLACE_FIELD_SOURCE_TYPE: SOURCE_TYPE_LOCAL,
                MARKETPLACE_FIELD_PATH: str(path),
            }
        ]
    )


def _scoped_codex_local_marketplace_payload(path: Path, *, scope: str) -> str:
    return json.dumps(
        [
            {
                MARKETPLACE_FIELD_NAME: DEFAULT_MARKETPLACE,
                MARKETPLACE_FIELD_SOURCE_TYPE: SOURCE_TYPE_LOCAL,
                MARKETPLACE_FIELD_PATH: str(path),
                MARKETPLACE_FIELD_SCOPE: scope,
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
        PLUGIN_FIELD_ID: f"{plugin}@{DEFAULT_MARKETPLACE}",
        MARKETPLACE_FIELD_SCOPE: scope,
        PLUGIN_FIELD_ENABLED: enabled,
    }
    if project_path is not None:
        payload[MARKETPLACE_FIELD_PROJECT_PATH] = str(project_path)
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


def _expected_discovery_and_user_plugin_snapshot_calls() -> list[tuple[str, ...]]:
    return [
        CLAUDE_MARKETPLACE_LIST_CALL,
        CODEX_MARKETPLACE_LIST_CALL,
        CLAUDE_PLUGIN_LIST_CALL,
    ]


def _expected_source_discovery_calls() -> list[tuple[str, ...]]:
    return [
        CLAUDE_MARKETPLACE_LIST_CALL,
        CODEX_MARKETPLACE_LIST_CALL,
    ]


def _user_scope_rust_restore_calls() -> list[tuple[str, ...]]:
    return [
        (
            *CLAUDE_PLUGIN_INSTALL_COMMAND,
            "--scope",
            CLAUDE_SCOPE_USER,
            f"rust@{DEFAULT_MARKETPLACE}",
        ),
        (
            *CLAUDE_PLUGIN_DISABLE_COMMAND,
            "--scope",
            CLAUDE_SCOPE_USER,
            f"rust@{DEFAULT_MARKETPLACE}",
        ),
    ]


def _user_scope_python_enable_calls() -> list[tuple[str, ...]]:
    return [
        (
            *CLAUDE_PLUGIN_INSTALL_COMMAND,
            "--scope",
            CLAUDE_SCOPE_USER,
            f"python@{DEFAULT_MARKETPLACE}",
        ),
        (
            *CLAUDE_PLUGIN_ENABLE_COMMAND,
            "--scope",
            CLAUDE_SCOPE_USER,
            f"python@{DEFAULT_MARKETPLACE}",
        ),
    ]


def parse_codex_marketplace_sources_accepts_local_source(
    tmp_path: Path,
) -> bool:
    marketplace_root = tmp_path / "marketplace"
    payload = json.dumps(
        [
            {
                MARKETPLACE_FIELD_NAME: DEFAULT_MARKETPLACE,
                MARKETPLACE_FIELD_SOURCE_TYPE: SOURCE_TYPE_LOCAL,
                MARKETPLACE_FIELD_PATH: str(marketplace_root),
            }
        ]
    )

    sources = parse_codex_marketplace_sources(payload)

    assert sources[DEFAULT_MARKETPLACE].source_type == SOURCE_TYPE_LOCAL
    assert sources[DEFAULT_MARKETPLACE].path == marketplace_root
    return True


def parse_codex_marketplace_sources_accepts_nested_local_source(
    tmp_path: Path,
) -> bool:
    marketplace_root = tmp_path / "marketplace"
    installed_root = tmp_path / "installed"
    payload = json.dumps(
        {
            MARKETPLACE_FIELD_MARKETPLACES: [
                {
                    MARKETPLACE_FIELD_NAME: DEFAULT_MARKETPLACE,
                    MARKETPLACE_FIELD_ROOT: str(installed_root),
                    MARKETPLACE_FIELD_MARKETPLACE_SOURCE: {
                        MARKETPLACE_FIELD_SOURCE_TYPE: SOURCE_TYPE_LOCAL,
                        MARKETPLACE_FIELD_SOURCE: str(marketplace_root),
                    },
                }
            ]
        }
    )

    sources = parse_codex_marketplace_sources(payload)

    assert sources[DEFAULT_MARKETPLACE].source_type == SOURCE_TYPE_LOCAL
    assert sources[DEFAULT_MARKETPLACE].path == marketplace_root
    return True


def parse_claude_marketplace_sources_normalizes_directory_source(
    tmp_path: Path,
) -> bool:
    marketplace_root = tmp_path / "marketplace"

    sources = parse_claude_marketplace_sources(
        _claude_directory_marketplace_payload(marketplace_root)
    )

    assert sources[DEFAULT_MARKETPLACE].source_type == SOURCE_TYPE_LOCAL
    assert sources[DEFAULT_MARKETPLACE].path == marketplace_root
    return True


def parse_marketplace_sources_reject_local_sources_without_paths() -> bool:
    claude_payload = json.dumps(
        [
            {
                MARKETPLACE_FIELD_NAME: DEFAULT_MARKETPLACE,
                MARKETPLACE_FIELD_SOURCE: "Directory",
            }
        ]
    )
    codex_payload = json.dumps(
        [
            {
                MARKETPLACE_FIELD_NAME: DEFAULT_MARKETPLACE,
                MARKETPLACE_FIELD_SOURCE_TYPE: SOURCE_TYPE_LOCAL,
            }
        ]
    )

    with pytest.raises(MarketplaceSourceError) as claude_exc_info:
        parse_claude_marketplace_sources(claude_payload)
    with pytest.raises(MarketplaceSourceError) as codex_exc_info:
        parse_codex_marketplace_sources(codex_payload)

    assert "Claude Code marketplace" in str(claude_exc_info.value)
    assert "Codex marketplace" in str(codex_exc_info.value)
    assert "local source has no usable path" in str(claude_exc_info.value)
    assert "local source has no usable path" in str(codex_exc_info.value)
    return True


def parse_claude_marketplace_sources_prefers_user_directory_source(
    tmp_path: Path,
) -> bool:
    user_root = tmp_path / "user-marketplace"
    managed_root = tmp_path / "managed-marketplace"
    payload = json.dumps(
        [
            {
                MARKETPLACE_FIELD_NAME: DEFAULT_MARKETPLACE,
                MARKETPLACE_FIELD_SOURCE: "Directory",
                MARKETPLACE_FIELD_PATH: str(managed_root),
                MARKETPLACE_FIELD_SCOPE: CLAUDE_SCOPE_MANAGED,
            },
            {
                MARKETPLACE_FIELD_NAME: DEFAULT_MARKETPLACE,
                MARKETPLACE_FIELD_SOURCE: "Git",
                MARKETPLACE_FIELD_URL: "https://github.com/outcomeeng/plugins.git",
            },
            {
                MARKETPLACE_FIELD_NAME: DEFAULT_MARKETPLACE,
                MARKETPLACE_FIELD_SOURCE: "Directory",
                MARKETPLACE_FIELD_PATH: str(user_root),
                MARKETPLACE_FIELD_SCOPE: CLAUDE_SCOPE_USER,
            },
        ]
    )

    sources = parse_claude_marketplace_sources(payload)

    assert sources[DEFAULT_MARKETPLACE].source_type == SOURCE_TYPE_LOCAL
    assert sources[DEFAULT_MARKETPLACE].path == user_root
    assert sources[DEFAULT_MARKETPLACE].scope == CLAUDE_SCOPE_USER
    return True


def parse_codex_marketplace_sources_prefers_local_source(
    tmp_path: Path,
) -> bool:
    local_root = tmp_path / "local-marketplace"
    payload = json.dumps(
        [
            {
                MARKETPLACE_FIELD_NAME: DEFAULT_MARKETPLACE,
                MARKETPLACE_FIELD_SOURCE_TYPE: SOURCE_TYPE_GIT,
                MARKETPLACE_FIELD_URL: "https://github.com/outcomeeng/plugins.git",
            },
            {
                MARKETPLACE_FIELD_NAME: DEFAULT_MARKETPLACE,
                MARKETPLACE_FIELD_SOURCE_TYPE: SOURCE_TYPE_LOCAL,
                MARKETPLACE_FIELD_PATH: str(local_root),
            },
        ]
    )

    sources = parse_codex_marketplace_sources(payload)

    assert sources[DEFAULT_MARKETPLACE].source_type == SOURCE_TYPE_LOCAL
    assert sources[DEFAULT_MARKETPLACE].path == local_root
    return True


def source_reconciliation_rejects_ambiguous_shared_roots(tmp_path: Path) -> bool:
    first_root = tmp_path / "first-marketplace"
    second_root = tmp_path / "second-marketplace"
    claude_payload = json.dumps(
        [
            {
                MARKETPLACE_FIELD_NAME: DEFAULT_MARKETPLACE,
                MARKETPLACE_FIELD_SOURCE: "Directory",
                MARKETPLACE_FIELD_PATH: str(first_root),
            },
            {
                MARKETPLACE_FIELD_NAME: DEFAULT_MARKETPLACE,
                MARKETPLACE_FIELD_SOURCE: "Directory",
                MARKETPLACE_FIELD_PATH: str(second_root),
            },
        ]
    )
    codex_payload = json.dumps(
        [
            {
                MARKETPLACE_FIELD_NAME: DEFAULT_MARKETPLACE,
                MARKETPLACE_FIELD_SOURCE_TYPE: SOURCE_TYPE_LOCAL,
                MARKETPLACE_FIELD_PATH: str(first_root),
            },
            {
                MARKETPLACE_FIELD_NAME: DEFAULT_MARKETPLACE,
                MARKETPLACE_FIELD_SOURCE_TYPE: SOURCE_TYPE_LOCAL,
                MARKETPLACE_FIELD_PATH: str(second_root),
            },
        ]
    )
    runner = RecordingCommandRunner(
        stdout_by_command={
            CLAUDE_MARKETPLACE_LIST_CALL: claude_payload,
            CODEX_MARKETPLACE_LIST_CALL: codex_payload,
        }
    )

    with pytest.raises(MarketplaceSourceError) as exc_info:
        ensure_local_marketplace_sources(DEFAULT_MARKETPLACE, runner=runner)

    message = str(exc_info.value)
    assert "multiple shared local marketplace roots" in message
    assert str(first_root.resolve(strict=False)) in message
    assert str(second_root.resolve(strict=False)) in message
    return True


def source_reconciliation_rejects_ambiguous_claude_roots(tmp_path: Path) -> bool:
    stale_root = tmp_path / "old-marketplace"
    managed_root = tmp_path / "managed-marketplace"
    runner = RecordingCommandRunner(
        stdout_by_command={
            CLAUDE_MARKETPLACE_LIST_CALL: json.dumps(
                [
                    {
                        MARKETPLACE_FIELD_NAME: DEFAULT_MARKETPLACE,
                        MARKETPLACE_FIELD_SOURCE: "Directory",
                        MARKETPLACE_FIELD_PATH: str(stale_root),
                        MARKETPLACE_FIELD_SCOPE: CLAUDE_SCOPE_PROJECT,
                        MARKETPLACE_FIELD_PROJECT_PATH: str(tmp_path / "project"),
                    },
                    {
                        MARKETPLACE_FIELD_NAME: DEFAULT_MARKETPLACE,
                        MARKETPLACE_FIELD_SOURCE: "Directory",
                        MARKETPLACE_FIELD_PATH: str(managed_root),
                        MARKETPLACE_FIELD_SCOPE: CLAUDE_SCOPE_MANAGED,
                    },
                ]
            ),
            CODEX_MARKETPLACE_LIST_CALL: json.dumps(
                [
                    {
                        MARKETPLACE_FIELD_NAME: DEFAULT_MARKETPLACE,
                        MARKETPLACE_FIELD_SOURCE_TYPE: SOURCE_TYPE_GIT,
                        MARKETPLACE_FIELD_URL: "https://github.com/outcomeeng/plugins.git",
                    }
                ]
            ),
        }
    )

    with pytest.raises(MarketplaceSourceError) as exc_info:
        ensure_local_marketplace_sources(DEFAULT_MARKETPLACE, runner=runner)

    message = str(exc_info.value)
    assert "Claude Code reported multiple local marketplace roots" in message
    assert str(stale_root.resolve(strict=False)) in message
    assert str(managed_root.resolve(strict=False)) in message
    return True


def parse_claude_installed_plugins_keeps_scope_state_and_project_path(
    tmp_path: Path,
) -> bool:
    project_path = tmp_path / "project"
    payload = json.dumps(
        [
            _claude_plugin_payload(
                "spec-tree",
                scope=CLAUDE_SCOPE_PROJECT,
                enabled=True,
                project_path=project_path,
            ),
            _claude_plugin_payload("rust", scope=CLAUDE_SCOPE_USER, enabled=False),
            {
                PLUGIN_FIELD_ID: "github@claude-plugins-official",
                MARKETPLACE_FIELD_SCOPE: CLAUDE_SCOPE_USER,
                PLUGIN_FIELD_ENABLED: True,
            },
        ]
    )

    plugins = parse_claude_installed_plugins(payload, DEFAULT_MARKETPLACE)

    assert [(plugin.name, plugin.scope, plugin.enabled) for plugin in plugins] == [
        ("spec-tree", CLAUDE_SCOPE_PROJECT, True),
        ("rust", CLAUDE_SCOPE_USER, False),
    ]
    assert plugins[0].project_path == project_path
    assert plugins[1].project_path is None
    return True


def parse_codex_marketplace_sources_accepts_nested_git_source() -> bool:
    payload = json.dumps(
        {
            MARKETPLACE_FIELD_MARKETPLACES: [
                {
                    MARKETPLACE_FIELD_NAME: DEFAULT_MARKETPLACE,
                    MARKETPLACE_FIELD_ROOT: "/Users/example/.codex/.tmp/marketplaces/outcomeeng",
                    MARKETPLACE_FIELD_MARKETPLACE_SOURCE: {
                        MARKETPLACE_FIELD_SOURCE_TYPE: SOURCE_TYPE_GIT,
                        MARKETPLACE_FIELD_SOURCE: "https://github.com/outcomeeng/plugins.git",
                    },
                }
            ]
        }
    )

    sources = parse_codex_marketplace_sources(payload)

    assert sources[DEFAULT_MARKETPLACE].source_type == SOURCE_TYPE_GIT
    assert (
        sources[DEFAULT_MARKETPLACE].url == "https://github.com/outcomeeng/plugins.git"
    )
    return True


def parse_codex_marketplace_sources_accepts_empty_marketplace_array() -> bool:
    sources = parse_codex_marketplace_sources(
        json.dumps({MARKETPLACE_FIELD_MARKETPLACES: []})
    )

    assert sources == {}
    return True


def require_matching_local_sources_rejects_git_backed_codex(
    tmp_path: Path,
) -> bool:
    marketplace_root = tmp_path / "marketplace"
    claude_sources = parse_claude_marketplace_sources(
        _claude_directory_marketplace_payload(marketplace_root)
    )
    codex_sources = parse_codex_marketplace_sources(
        json.dumps(
            [
                {
                    MARKETPLACE_FIELD_NAME: DEFAULT_MARKETPLACE,
                    MARKETPLACE_FIELD_SOURCE_TYPE: SOURCE_TYPE_GIT,
                    MARKETPLACE_FIELD_URL: "https://github.com/outcomeeng/plugins.git",
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
    assert SOURCE_TYPE_LOCAL in message
    assert SOURCE_TYPE_GIT in message
    return True


def require_matching_local_sources_rejects_path_mismatch(
    tmp_path: Path,
) -> bool:
    claude_root = tmp_path / "claude-marketplace"
    codex_root = tmp_path / "codex-marketplace"
    claude_sources = parse_claude_marketplace_sources(
        _claude_directory_marketplace_payload(claude_root)
    )
    codex_sources = parse_codex_marketplace_sources(
        _codex_local_marketplace_payload(codex_root)
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


def source_reconciliation_adds_absent_runtime_sources(tmp_path: Path) -> bool:
    marketplace_root = tmp_path / "marketplace"
    runner = RecordingCommandRunner(
        stdout_by_command={
            CLAUDE_MARKETPLACE_LIST_CALL: "[]",
            CODEX_MARKETPLACE_LIST_CALL: json.dumps(
                {MARKETPLACE_FIELD_MARKETPLACES: []}
            ),
            CLAUDE_PLUGIN_LIST_CALL: "[]",
        }
    )

    result = ensure_local_marketplace_sources(
        DEFAULT_MARKETPLACE,
        source_root=marketplace_root,
        runner=runner,
    )

    _assert_repair_result(
        result,
        runner,
        expected_root=marketplace_root,
        expected_calls=[
            *_expected_discovery_and_user_plugin_snapshot_calls(),
            (
                *CLAUDE_MARKETPLACE_ADD_COMMAND,
                str(result.root),
                "--scope",
                CLAUDE_SCOPE_USER,
            ),
            (*CODEX_MARKETPLACE_ADD_COMMAND, str(result.root)),
        ],
        expected_cwd=[None, None, None, None, None],
    )
    return True


def source_reconciliation_unscoped_default_adds_user_registration_and_restores_user_plugins(
    tmp_path: Path,
) -> bool:
    marketplace_root = tmp_path / "marketplace"
    project_path = tmp_path / "consumer-project"
    project_install = (
        *CLAUDE_PLUGIN_INSTALL_COMMAND,
        "--scope",
        CLAUDE_SCOPE_PROJECT,
        f"spec-tree@{DEFAULT_MARKETPLACE}",
    )
    runner = RecordingCommandRunner(
        stdout_by_command={
            CLAUDE_MARKETPLACE_LIST_CALL: "[]",
            CODEX_MARKETPLACE_LIST_CALL: _codex_local_marketplace_payload(
                marketplace_root
            ),
            CLAUDE_PLUGIN_LIST_CALL: json.dumps(
                [
                    _claude_plugin_payload(
                        "rust",
                        scope=CLAUDE_SCOPE_USER,
                        enabled=False,
                    ),
                    _claude_plugin_payload(
                        "spec-tree",
                        scope=CLAUDE_SCOPE_PROJECT,
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
        runner=runner,
    )

    _assert_repair_result(
        result,
        runner,
        expected_root=marketplace_root,
        expected_calls=[
            *_expected_discovery_and_user_plugin_snapshot_calls(),
            (
                *CLAUDE_MARKETPLACE_ADD_COMMAND,
                str(result.root),
                "--scope",
                CLAUDE_SCOPE_USER,
            ),
            *_user_scope_rust_restore_calls(),
        ],
        expected_cwd=[None, None, None, None, None, None],
    )
    assert project_install not in runner.calls
    return True


def source_reconciliation_accepts_matching_runtime_sources(
    tmp_path: Path,
) -> bool:
    marketplace_root = tmp_path / "marketplace"
    runner = RecordingCommandRunner(
        stdout_by_command={
            CLAUDE_MARKETPLACE_LIST_CALL: _scoped_claude_directory_marketplace_payload(
                marketplace_root,
                scope=CLAUDE_SCOPE_USER,
            ),
            CODEX_MARKETPLACE_LIST_CALL: _codex_local_marketplace_payload(
                marketplace_root
            ),
        }
    )

    result = ensure_local_marketplace_sources(DEFAULT_MARKETPLACE, runner=runner)

    assert result.root == marketplace_root.resolve(strict=False)
    assert result.changed is False
    assert result.commands == ()
    assert runner.calls == [
        CLAUDE_MARKETPLACE_LIST_CALL,
        CODEX_MARKETPLACE_LIST_CALL,
    ]
    return True


def source_reconciliation_accepts_duplicate_lower_priority_matching_sources(
    tmp_path: Path,
) -> bool:
    marketplace_root = tmp_path / "marketplace"
    project_path = tmp_path / "consumer-project"
    runner = RecordingCommandRunner(
        stdout_by_command={
            CLAUDE_MARKETPLACE_LIST_CALL: json.dumps(
                [
                    {
                        MARKETPLACE_FIELD_NAME: DEFAULT_MARKETPLACE,
                        MARKETPLACE_FIELD_SOURCE: "Directory",
                        MARKETPLACE_FIELD_PATH: str(marketplace_root),
                        MARKETPLACE_FIELD_SCOPE: CLAUDE_SCOPE_USER,
                    },
                    {
                        MARKETPLACE_FIELD_NAME: DEFAULT_MARKETPLACE,
                        MARKETPLACE_FIELD_SOURCE: "Directory",
                        MARKETPLACE_FIELD_PATH: str(marketplace_root),
                        MARKETPLACE_FIELD_SCOPE: CLAUDE_SCOPE_MANAGED,
                    },
                ]
            ),
            CODEX_MARKETPLACE_LIST_CALL: json.dumps(
                [
                    {
                        MARKETPLACE_FIELD_NAME: DEFAULT_MARKETPLACE,
                        MARKETPLACE_FIELD_SOURCE_TYPE: SOURCE_TYPE_LOCAL,
                        MARKETPLACE_FIELD_PATH: str(marketplace_root),
                    },
                    {
                        MARKETPLACE_FIELD_NAME: DEFAULT_MARKETPLACE,
                        MARKETPLACE_FIELD_SOURCE_TYPE: SOURCE_TYPE_LOCAL,
                        MARKETPLACE_FIELD_PATH: str(marketplace_root),
                        MARKETPLACE_FIELD_SCOPE: CLAUDE_SCOPE_PROJECT,
                        MARKETPLACE_FIELD_PROJECT_PATH: str(project_path),
                    },
                ]
            ),
        }
    )

    result = ensure_local_marketplace_sources(DEFAULT_MARKETPLACE, runner=runner)

    assert result.root == marketplace_root.resolve(strict=False)
    assert result.changed is False
    assert result.commands == ()
    assert runner.calls == [
        CLAUDE_MARKETPLACE_LIST_CALL,
        CODEX_MARKETPLACE_LIST_CALL,
    ]
    return True


def source_validation_prefers_user_source_over_stale_project_or_local_duplicate(
    tmp_path: Path,
) -> bool:
    canonical_root = tmp_path / "canonical-marketplace"
    stale_root = tmp_path / "old-marketplace"
    runner = RecordingCommandRunner(
        stdout_by_command={
            CLAUDE_MARKETPLACE_LIST_CALL: json.dumps(
                [
                    {
                        MARKETPLACE_FIELD_NAME: DEFAULT_MARKETPLACE,
                        MARKETPLACE_FIELD_SOURCE: "Directory",
                        MARKETPLACE_FIELD_PATH: str(canonical_root),
                        MARKETPLACE_FIELD_SCOPE: CLAUDE_SCOPE_USER,
                    },
                    {
                        MARKETPLACE_FIELD_NAME: DEFAULT_MARKETPLACE,
                        MARKETPLACE_FIELD_SOURCE: "Directory",
                        MARKETPLACE_FIELD_PATH: str(stale_root),
                        MARKETPLACE_FIELD_SCOPE: CLAUDE_SCOPE_LOCAL,
                        MARKETPLACE_FIELD_PROJECT_PATH: str(tmp_path),
                    },
                ]
            ),
            CODEX_MARKETPLACE_LIST_CALL: _codex_local_marketplace_payload(
                canonical_root
            ),
        }
    )

    root = configured_local_marketplace_root(DEFAULT_MARKETPLACE, runner=runner)

    assert root == canonical_root.resolve(strict=False)
    assert root != stale_root.resolve(strict=False)
    assert runner.calls == [
        CLAUDE_MARKETPLACE_LIST_CALL,
        CODEX_MARKETPLACE_LIST_CALL,
    ]
    return True


def source_validation_accepts_shared_root_with_stale_user_duplicate(
    tmp_path: Path,
) -> bool:
    canonical_root = tmp_path / "canonical-marketplace"
    stale_root = tmp_path / "old-marketplace"
    runner = RecordingCommandRunner(
        stdout_by_command={
            CLAUDE_MARKETPLACE_LIST_CALL: json.dumps(
                [
                    {
                        MARKETPLACE_FIELD_NAME: DEFAULT_MARKETPLACE,
                        MARKETPLACE_FIELD_SOURCE: "Directory",
                        MARKETPLACE_FIELD_PATH: str(stale_root),
                        MARKETPLACE_FIELD_SCOPE: CLAUDE_SCOPE_USER,
                    },
                    {
                        MARKETPLACE_FIELD_NAME: DEFAULT_MARKETPLACE,
                        MARKETPLACE_FIELD_SOURCE: "Directory",
                        MARKETPLACE_FIELD_PATH: str(canonical_root),
                        MARKETPLACE_FIELD_SCOPE: CLAUDE_SCOPE_MANAGED,
                    },
                ]
            ),
            CODEX_MARKETPLACE_LIST_CALL: _codex_local_marketplace_payload(
                canonical_root
            ),
        }
    )

    root = configured_local_marketplace_root(DEFAULT_MARKETPLACE, runner=runner)

    assert root == canonical_root.resolve(strict=False)
    assert root != stale_root.resolve(strict=False)
    assert runner.calls == [
        CLAUDE_MARKETPLACE_LIST_CALL,
        CODEX_MARKETPLACE_LIST_CALL,
    ]
    return True


def claude_directory_root_does_not_require_codex_configuration(
    tmp_path: Path,
) -> bool:
    marketplace_root = tmp_path / "marketplace"
    runner = RecordingCommandRunner(
        stdout_by_command={
            CLAUDE_MARKETPLACE_LIST_CALL: _scoped_claude_directory_marketplace_payload(
                marketplace_root,
                scope=CLAUDE_SCOPE_USER,
            ),
            CODEX_MARKETPLACE_LIST_CALL: json.dumps(
                [
                    {
                        MARKETPLACE_FIELD_NAME: DEFAULT_MARKETPLACE,
                        MARKETPLACE_FIELD_SOURCE_TYPE: SOURCE_TYPE_GIT,
                        MARKETPLACE_FIELD_URL: "https://github.com/outcomeeng/plugins.git",
                    }
                ]
            ),
        }
    )

    root = configured_claude_directory_marketplace_root(
        DEFAULT_MARKETPLACE,
        runner=runner,
    )

    assert root == marketplace_root.resolve(strict=False)
    assert runner.calls == [CLAUDE_MARKETPLACE_LIST_CALL]
    return True


def claude_directory_root_rejects_duplicate_local_roots(
    tmp_path: Path,
) -> bool:
    canonical_root = tmp_path / "canonical-marketplace"
    stale_root = tmp_path / "old-marketplace"
    runner = RecordingCommandRunner(
        stdout_by_command={
            CLAUDE_MARKETPLACE_LIST_CALL: json.dumps(
                [
                    {
                        MARKETPLACE_FIELD_NAME: DEFAULT_MARKETPLACE,
                        MARKETPLACE_FIELD_SOURCE: "Directory",
                        MARKETPLACE_FIELD_PATH: str(stale_root),
                        MARKETPLACE_FIELD_SCOPE: CLAUDE_SCOPE_USER,
                    },
                    {
                        MARKETPLACE_FIELD_NAME: DEFAULT_MARKETPLACE,
                        MARKETPLACE_FIELD_SOURCE: "Directory",
                        MARKETPLACE_FIELD_PATH: str(canonical_root),
                        MARKETPLACE_FIELD_SCOPE: CLAUDE_SCOPE_MANAGED,
                    },
                ]
            )
        }
    )

    with pytest.raises(MarketplaceSourceError) as exc_info:
        configured_claude_directory_marketplace_root(
            DEFAULT_MARKETPLACE,
            runner=runner,
        )

    message = str(exc_info.value)
    assert "Claude Code reported multiple local marketplace roots" in message
    assert str(canonical_root.resolve(strict=False)) in message
    assert str(stale_root.resolve(strict=False)) in message
    assert runner.calls == [CLAUDE_MARKETPLACE_LIST_CALL]
    return True


def source_reconciliation_replaces_git_backed_codex_source(
    tmp_path: Path,
) -> bool:
    marketplace_root = tmp_path / "marketplace"
    runner = RecordingCommandRunner(
        stdout_by_command={
            CLAUDE_MARKETPLACE_LIST_CALL: _scoped_claude_directory_marketplace_payload(
                marketplace_root,
                scope=CLAUDE_SCOPE_USER,
            ),
            CODEX_MARKETPLACE_LIST_CALL: json.dumps(
                [
                    {
                        MARKETPLACE_FIELD_NAME: DEFAULT_MARKETPLACE,
                        MARKETPLACE_FIELD_SOURCE_TYPE: SOURCE_TYPE_GIT,
                        MARKETPLACE_FIELD_URL: "https://github.com/outcomeeng/plugins.git",
                    }
                ]
            ),
        }
    )

    result = ensure_local_marketplace_sources(DEFAULT_MARKETPLACE, runner=runner)

    assert result.root == marketplace_root.resolve(strict=False)
    assert result.changed is True
    assert runner.calls == [
        CLAUDE_MARKETPLACE_LIST_CALL,
        CODEX_MARKETPLACE_LIST_CALL,
        (*CODEX_MARKETPLACE_REMOVE_COMMAND, DEFAULT_MARKETPLACE),
        (*CODEX_MARKETPLACE_ADD_COMMAND, str(result.root)),
    ]
    return True


def source_reconciliation_replaces_mismatched_codex_path(
    tmp_path: Path,
) -> bool:
    claude_root = tmp_path / "claude-marketplace"
    codex_root = tmp_path / "codex-marketplace"
    runner = RecordingCommandRunner(
        stdout_by_command={
            CLAUDE_MARKETPLACE_LIST_CALL: _scoped_claude_directory_marketplace_payload(
                claude_root,
                scope=CLAUDE_SCOPE_USER,
            ),
            CODEX_MARKETPLACE_LIST_CALL: _codex_local_marketplace_payload(codex_root),
        }
    )

    result = ensure_local_marketplace_sources(DEFAULT_MARKETPLACE, runner=runner)

    assert result.root == claude_root.resolve(strict=False)
    assert result.changed is True
    assert runner.calls == [
        CLAUDE_MARKETPLACE_LIST_CALL,
        CODEX_MARKETPLACE_LIST_CALL,
        (*CODEX_MARKETPLACE_REMOVE_COMMAND, DEFAULT_MARKETPLACE),
        (*CODEX_MARKETPLACE_ADD_COMMAND, str(result.root)),
    ]
    return True


def source_reconciliation_repairs_scoped_matching_codex_source(
    tmp_path: Path,
) -> bool:
    marketplace_root = tmp_path / "marketplace"
    runner = RecordingCommandRunner(
        stdout_by_command={
            CLAUDE_MARKETPLACE_LIST_CALL: _scoped_claude_directory_marketplace_payload(
                marketplace_root,
                scope=CLAUDE_SCOPE_USER,
            ),
            CODEX_MARKETPLACE_LIST_CALL: _scoped_codex_local_marketplace_payload(
                marketplace_root,
                scope=CLAUDE_SCOPE_PROJECT,
            ),
        }
    )

    result = ensure_local_marketplace_sources(DEFAULT_MARKETPLACE, runner=runner)

    assert result.root == marketplace_root.resolve(strict=False)
    assert result.changed is True
    assert runner.calls == [
        CLAUDE_MARKETPLACE_LIST_CALL,
        CODEX_MARKETPLACE_LIST_CALL,
        (*CODEX_MARKETPLACE_REMOVE_COMMAND, DEFAULT_MARKETPLACE),
        (*CODEX_MARKETPLACE_ADD_COMMAND, str(result.root)),
    ]
    return True


def source_reconciliation_repairs_stale_codex_duplicate(
    tmp_path: Path,
) -> bool:
    canonical_root = tmp_path / "canonical-marketplace"
    stale_root = tmp_path / "old-codex-marketplace"
    runner = RecordingCommandRunner(
        stdout_by_command={
            CLAUDE_MARKETPLACE_LIST_CALL: _scoped_claude_directory_marketplace_payload(
                canonical_root,
                scope=CLAUDE_SCOPE_USER,
            ),
            CODEX_MARKETPLACE_LIST_CALL: json.dumps(
                [
                    {
                        MARKETPLACE_FIELD_NAME: DEFAULT_MARKETPLACE,
                        MARKETPLACE_FIELD_SOURCE_TYPE: SOURCE_TYPE_LOCAL,
                        MARKETPLACE_FIELD_PATH: str(canonical_root),
                    },
                    {
                        MARKETPLACE_FIELD_NAME: DEFAULT_MARKETPLACE,
                        MARKETPLACE_FIELD_SOURCE_TYPE: SOURCE_TYPE_LOCAL,
                        MARKETPLACE_FIELD_PATH: str(stale_root),
                    },
                ]
            ),
        }
    )

    result = ensure_local_marketplace_sources(DEFAULT_MARKETPLACE, runner=runner)

    assert result.root == canonical_root.resolve(strict=False)
    assert result.changed is True
    assert runner.calls == [
        CLAUDE_MARKETPLACE_LIST_CALL,
        CODEX_MARKETPLACE_LIST_CALL,
        (*CODEX_MARKETPLACE_REMOVE_COMMAND, DEFAULT_MARKETPLACE),
        (*CODEX_MARKETPLACE_ADD_COMMAND, str(result.root)),
    ]
    return True


def source_reconciliation_repairs_scoped_stale_codex_duplicate(
    tmp_path: Path,
) -> bool:
    canonical_root = tmp_path / "canonical-marketplace"
    stale_root = tmp_path / "old-codex-marketplace"
    runner = RecordingCommandRunner(
        stdout_by_command={
            CLAUDE_MARKETPLACE_LIST_CALL: _scoped_claude_directory_marketplace_payload(
                canonical_root,
                scope=CLAUDE_SCOPE_USER,
            ),
            CODEX_MARKETPLACE_LIST_CALL: json.dumps(
                [
                    {
                        MARKETPLACE_FIELD_NAME: DEFAULT_MARKETPLACE,
                        MARKETPLACE_FIELD_SOURCE_TYPE: SOURCE_TYPE_LOCAL,
                        MARKETPLACE_FIELD_PATH: str(canonical_root),
                    },
                    {
                        MARKETPLACE_FIELD_NAME: DEFAULT_MARKETPLACE,
                        MARKETPLACE_FIELD_SOURCE_TYPE: SOURCE_TYPE_LOCAL,
                        MARKETPLACE_FIELD_PATH: str(stale_root),
                        MARKETPLACE_FIELD_SCOPE: CLAUDE_SCOPE_PROJECT,
                    },
                ]
            ),
        }
    )

    result = ensure_local_marketplace_sources(DEFAULT_MARKETPLACE, runner=runner)

    assert result.root == canonical_root.resolve(strict=False)
    assert result.changed is True
    assert runner.calls == [
        CLAUDE_MARKETPLACE_LIST_CALL,
        CODEX_MARKETPLACE_LIST_CALL,
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
    runner = _source_repair_runner(
        claude_payload=_claude_directory_marketplace_payload(claude_root),
        codex_root=codex_root,
    )

    result = ensure_local_marketplace_sources(
        DEFAULT_MARKETPLACE,
        source_root=canonical_root,
        runner=runner,
    )

    _assert_repair_result(
        result,
        runner,
        expected_root=canonical_root,
        expected_calls=[
            *_expected_discovery_and_user_plugin_snapshot_calls(),
            (
                *CLAUDE_MARKETPLACE_REMOVE_COMMAND,
                DEFAULT_MARKETPLACE,
                "--scope",
                CLAUDE_SCOPE_USER,
            ),
            (
                *CLAUDE_MARKETPLACE_ADD_COMMAND,
                str(result.root),
                "--scope",
                CLAUDE_SCOPE_USER,
            ),
            (*CODEX_MARKETPLACE_REMOVE_COMMAND, DEFAULT_MARKETPLACE),
            (*CODEX_MARKETPLACE_ADD_COMMAND, str(result.root)),
        ],
        expected_cwd=[None, None, None, None, None, None, None],
    )
    return True


def source_reconciliation_preserves_user_scope_claude_plugin_installs(
    tmp_path: Path,
) -> bool:
    canonical_root = tmp_path / "canonical-marketplace"
    stale_root = tmp_path / "old-marketplace"
    project_path = tmp_path / "consumer-project"
    project_install = (
        *CLAUDE_PLUGIN_INSTALL_COMMAND,
        "--scope",
        CLAUDE_SCOPE_PROJECT,
        f"spec-tree@{DEFAULT_MARKETPLACE}",
    )
    runner = _source_repair_runner(
        claude_payload=_scoped_claude_directory_marketplace_payload(
            stale_root,
            scope=CLAUDE_SCOPE_USER,
        ),
        codex_root=canonical_root,
        plugin_payload=json.dumps(
            [
                _claude_plugin_payload(
                    "rust",
                    scope=CLAUDE_SCOPE_USER,
                    enabled=False,
                ),
                _claude_plugin_payload(
                    "spec-tree",
                    scope=CLAUDE_SCOPE_PROJECT,
                    enabled=True,
                    project_path=project_path,
                ),
            ]
        ),
    )

    result = ensure_local_marketplace_sources(
        DEFAULT_MARKETPLACE,
        source_root=canonical_root,
        runner=runner,
    )

    _assert_repair_result(
        result,
        runner,
        expected_root=canonical_root,
        expected_calls=[
            *_expected_discovery_and_user_plugin_snapshot_calls(),
            (
                *CLAUDE_MARKETPLACE_REMOVE_COMMAND,
                DEFAULT_MARKETPLACE,
                "--scope",
                CLAUDE_SCOPE_USER,
            ),
            (
                *CLAUDE_MARKETPLACE_ADD_COMMAND,
                str(result.root),
                "--scope",
                CLAUDE_SCOPE_USER,
            ),
            *_user_scope_rust_restore_calls(),
        ],
        expected_cwd=[None, None, None, None, None, None, None],
    )
    assert project_install not in runner.calls
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
        runner=runner,
    )

    _assert_repair_result(
        result,
        runner,
        expected_root=canonical_root,
        expected_calls=[
            *_expected_discovery_and_user_plugin_snapshot_calls(),
            (
                *CLAUDE_MARKETPLACE_REMOVE_COMMAND,
                DEFAULT_MARKETPLACE,
                "--scope",
                CLAUDE_SCOPE_USER,
            ),
            (
                *CLAUDE_MARKETPLACE_ADD_COMMAND,
                str(result.root),
                "--scope",
                CLAUDE_SCOPE_USER,
            ),
        ],
        expected_cwd=[None, None, None, None, None],
    )
    return True


def source_reconciliation_accepts_unscoped_matching_claude_runtime_source(
    tmp_path: Path,
) -> bool:
    marketplace_root = tmp_path / "marketplace"
    runner = _source_repair_runner(
        claude_payload=_claude_directory_marketplace_payload(marketplace_root),
        codex_root=marketplace_root,
    )

    result = ensure_local_marketplace_sources(DEFAULT_MARKETPLACE, runner=runner)

    assert result.changed is False
    assert result.commands == ()
    assert runner.calls == _expected_source_discovery_calls()
    return True


def source_reconciliation_adds_user_registration_for_managed_claude_source(
    tmp_path: Path,
) -> bool:
    marketplace_root = tmp_path / "marketplace"
    project_path = tmp_path / "consumer-project"
    project_install = (
        *CLAUDE_PLUGIN_INSTALL_COMMAND,
        "--scope",
        CLAUDE_SCOPE_PROJECT,
        f"spec-tree@{DEFAULT_MARKETPLACE}",
    )
    runner = _source_repair_runner(
        claude_payload=_scoped_claude_directory_marketplace_payload(
            marketplace_root,
            scope=CLAUDE_SCOPE_MANAGED,
        ),
        codex_root=marketplace_root,
        plugin_payload=json.dumps(
            [
                _claude_plugin_payload(
                    "rust",
                    scope=CLAUDE_SCOPE_USER,
                    enabled=False,
                ),
                _claude_plugin_payload(
                    "spec-tree",
                    scope=CLAUDE_SCOPE_PROJECT,
                    enabled=True,
                    project_path=project_path,
                ),
            ]
        ),
    )

    result = ensure_local_marketplace_sources(DEFAULT_MARKETPLACE, runner=runner)

    _assert_repair_result(
        result,
        runner,
        expected_root=marketplace_root,
        expected_calls=[
            *_expected_discovery_and_user_plugin_snapshot_calls(),
            (
                *CLAUDE_MARKETPLACE_ADD_COMMAND,
                str(result.root),
                "--scope",
                CLAUDE_SCOPE_USER,
            ),
            *_user_scope_rust_restore_calls(),
        ],
        expected_cwd=[None, None, None, None, None, None],
    )
    assert project_install not in runner.calls
    return True


def source_reconciliation_prefers_shared_root_over_stale_user_duplicate(
    tmp_path: Path,
) -> bool:
    canonical_root = tmp_path / "canonical-marketplace"
    stale_root = tmp_path / "old-marketplace"
    runner = _source_repair_runner(
        claude_payload=json.dumps(
            [
                {
                    MARKETPLACE_FIELD_NAME: DEFAULT_MARKETPLACE,
                    MARKETPLACE_FIELD_SOURCE: "Directory",
                    MARKETPLACE_FIELD_PATH: str(stale_root),
                    MARKETPLACE_FIELD_SCOPE: CLAUDE_SCOPE_USER,
                },
                {
                    MARKETPLACE_FIELD_NAME: DEFAULT_MARKETPLACE,
                    MARKETPLACE_FIELD_SOURCE: "Directory",
                    MARKETPLACE_FIELD_PATH: str(canonical_root),
                    MARKETPLACE_FIELD_SCOPE: CLAUDE_SCOPE_MANAGED,
                },
            ]
        ),
        codex_root=canonical_root,
    )

    result = ensure_local_marketplace_sources(DEFAULT_MARKETPLACE, runner=runner)

    _assert_repair_result(
        result,
        runner,
        expected_root=canonical_root,
        expected_calls=[
            *_expected_discovery_and_user_plugin_snapshot_calls(),
            (
                *CLAUDE_MARKETPLACE_REMOVE_COMMAND,
                DEFAULT_MARKETPLACE,
                "--scope",
                CLAUDE_SCOPE_USER,
            ),
            (
                *CLAUDE_MARKETPLACE_ADD_COMMAND,
                str(result.root),
                "--scope",
                CLAUDE_SCOPE_USER,
            ),
        ],
        expected_cwd=[None, None, None, None, None],
    )
    return True


def source_reconciliation_ignores_project_duplicate_when_user_source_canonical(
    tmp_path: Path,
) -> bool:
    canonical_root = tmp_path / "canonical-marketplace"
    stale_root = tmp_path / "old-marketplace"
    project_path = tmp_path / "consumer-project"
    runner = _source_repair_runner(
        claude_payload=json.dumps(
            [
                {
                    MARKETPLACE_FIELD_NAME: DEFAULT_MARKETPLACE,
                    MARKETPLACE_FIELD_SOURCE: "Directory",
                    MARKETPLACE_FIELD_PATH: str(canonical_root),
                    MARKETPLACE_FIELD_SCOPE: CLAUDE_SCOPE_USER,
                },
                {
                    MARKETPLACE_FIELD_NAME: DEFAULT_MARKETPLACE,
                    MARKETPLACE_FIELD_SOURCE: "Directory",
                    MARKETPLACE_FIELD_PATH: str(stale_root),
                    MARKETPLACE_FIELD_SCOPE: CLAUDE_SCOPE_PROJECT,
                    MARKETPLACE_FIELD_PROJECT_PATH: str(project_path),
                },
            ]
        ),
        codex_root=canonical_root,
    )

    result = ensure_local_marketplace_sources(DEFAULT_MARKETPLACE, runner=runner)

    project_remove = (
        *CLAUDE_MARKETPLACE_REMOVE_COMMAND,
        DEFAULT_MARKETPLACE,
        "--scope",
        CLAUDE_SCOPE_PROJECT,
    )
    assert result.changed is False
    assert result.commands == ()
    assert runner.calls == _expected_source_discovery_calls()
    assert project_remove not in runner.calls
    return True


def source_reconciliation_ignores_unscoped_duplicate_when_user_source_canonical(
    tmp_path: Path,
) -> bool:
    canonical_root = tmp_path / "canonical-marketplace"
    stale_root = tmp_path / "old-marketplace"
    runner = _source_repair_runner(
        claude_payload=json.dumps(
            [
                {
                    MARKETPLACE_FIELD_NAME: DEFAULT_MARKETPLACE,
                    MARKETPLACE_FIELD_SOURCE: "Directory",
                    MARKETPLACE_FIELD_PATH: str(canonical_root),
                    MARKETPLACE_FIELD_SCOPE: CLAUDE_SCOPE_USER,
                },
                {
                    MARKETPLACE_FIELD_NAME: DEFAULT_MARKETPLACE,
                    MARKETPLACE_FIELD_SOURCE: "Directory",
                    MARKETPLACE_FIELD_PATH: str(stale_root),
                },
            ]
        ),
        codex_root=canonical_root,
    )

    result = ensure_local_marketplace_sources(DEFAULT_MARKETPLACE, runner=runner)

    assert result.changed is False
    assert result.commands == ()
    assert runner.calls == _expected_source_discovery_calls()
    return True


def source_reconciliation_rejects_project_source_without_project_path(
    tmp_path: Path,
) -> bool:
    canonical_root = tmp_path / "canonical-marketplace"
    stale_root = tmp_path / "old-marketplace"
    runner = _source_repair_runner(
        claude_payload=_scoped_claude_directory_marketplace_payload(
            stale_root,
            scope=CLAUDE_SCOPE_PROJECT,
        ),
        codex_root=canonical_root,
    )

    with pytest.raises(MarketplaceSourceError) as exc_info:
        ensure_local_marketplace_sources(
            DEFAULT_MARKETPLACE,
            source_root=canonical_root,
            runner=runner,
        )

    message = str(exc_info.value)
    assert f"marketplace `{DEFAULT_MARKETPLACE}` with project scope" in message
    assert MARKETPLACE_FIELD_PROJECT_PATH in message
    assert runner.calls == _expected_source_discovery_calls()
    return True


def source_reconciliation_ignores_project_source_and_adds_user_registration(
    tmp_path: Path,
) -> bool:
    canonical_root = tmp_path / "canonical-marketplace"
    stale_root = tmp_path / "old-marketplace"
    project_path = tmp_path / "consumer-project"
    project_install = (
        *CLAUDE_PLUGIN_INSTALL_COMMAND,
        "--scope",
        CLAUDE_SCOPE_PROJECT,
        f"spec-tree@{DEFAULT_MARKETPLACE}",
    )
    project_remove = (
        *CLAUDE_MARKETPLACE_REMOVE_COMMAND,
        DEFAULT_MARKETPLACE,
        "--scope",
        CLAUDE_SCOPE_PROJECT,
    )
    runner = _source_repair_runner(
        claude_payload=_scoped_claude_directory_marketplace_payload(
            stale_root,
            scope=CLAUDE_SCOPE_PROJECT,
            project_path=project_path,
        ),
        codex_root=canonical_root,
        plugin_payload=json.dumps(
            [
                _claude_plugin_payload(
                    "rust",
                    scope=CLAUDE_SCOPE_USER,
                    enabled=False,
                ),
                _claude_plugin_payload(
                    "spec-tree",
                    scope=CLAUDE_SCOPE_PROJECT,
                    enabled=True,
                    project_path=project_path,
                ),
            ]
        ),
    )

    result = ensure_local_marketplace_sources(
        DEFAULT_MARKETPLACE,
        source_root=canonical_root,
        runner=runner,
    )

    _assert_repair_result(
        result,
        runner,
        expected_root=canonical_root,
        expected_calls=[
            *_expected_discovery_and_user_plugin_snapshot_calls(),
            (
                *CLAUDE_MARKETPLACE_ADD_COMMAND,
                str(result.root),
                "--scope",
                CLAUDE_SCOPE_USER,
            ),
            *_user_scope_rust_restore_calls(),
        ],
        expected_cwd=[None, None, None, None, None, None],
    )
    assert project_install not in runner.calls
    assert project_remove not in runner.calls
    return True


def source_reconciliation_failed_codex_add_surfaces_error(
    tmp_path: Path,
) -> bool:
    claude_root = tmp_path / "marketplace"
    codex_root = tmp_path / "old-codex-marketplace"
    codex_add = (*CODEX_MARKETPLACE_ADD_COMMAND, str(claude_root.resolve(strict=False)))
    runner = RecordingCommandRunner(
        stdout_by_command={
            CLAUDE_MARKETPLACE_LIST_CALL: _scoped_claude_directory_marketplace_payload(
                claude_root,
                scope=CLAUDE_SCOPE_USER,
            ),
            CODEX_MARKETPLACE_LIST_CALL: _codex_local_marketplace_payload(codex_root),
        },
        returncode_by_command={codex_add: 1},
        stderr_by_command={codex_add: "permission denied"},
    )

    with pytest.raises(MarketplaceSourceError) as exc_info:
        ensure_local_marketplace_sources(DEFAULT_MARKETPLACE, runner=runner)

    message = str(exc_info.value)
    assert "codex plugin marketplace add" in message
    assert "permission denied" in message
    return True


def source_reconciliation_user_restore_idempotent_errors_are_accepted(
    tmp_path: Path,
) -> bool:
    canonical_root = tmp_path / "canonical-marketplace"
    stale_root = tmp_path / "old-marketplace"
    rust_install, rust_disable = _user_scope_rust_restore_calls()
    runner = _source_repair_runner(
        claude_payload=_claude_directory_marketplace_payload(stale_root),
        codex_root=canonical_root,
        plugin_payload=json.dumps(
            [
                _claude_plugin_payload(
                    "rust",
                    scope=CLAUDE_SCOPE_USER,
                    enabled=False,
                )
            ]
        ),
        returncode_by_command={
            rust_install: 1,
            rust_disable: 1,
        },
        stderr_by_command={
            rust_install: (
                f'Failed to install plugin "rust@{DEFAULT_MARKETPLACE}": '
                f'Plugin "rust@{DEFAULT_MARKETPLACE}" is '
                f"{CLAUDE_PLUGIN_ALREADY_INSTALLED_FRAGMENT} at user scope"
            ),
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
        runner=runner,
    )

    assert result.changed is True
    assert rust_install in runner.calls
    assert rust_disable in runner.calls
    return True


def source_reconciliation_user_restore_already_enabled_response_is_accepted(
    tmp_path: Path,
) -> bool:
    canonical_root = tmp_path / "canonical-marketplace"
    stale_root = tmp_path / "old-marketplace"
    _python_install, python_enable = _user_scope_python_enable_calls()
    runner = _source_repair_runner(
        claude_payload=_claude_directory_marketplace_payload(stale_root),
        codex_root=canonical_root,
        plugin_payload=json.dumps(
            [
                _claude_plugin_payload(
                    "python",
                    scope=CLAUDE_SCOPE_USER,
                    enabled=True,
                )
            ]
        ),
        returncode_by_command={python_enable: 1},
        stderr_by_command={
            python_enable: (
                f'\u2718 Failed to enable plugin "python@{DEFAULT_MARKETPLACE}": '
                f'Plugin "python@{DEFAULT_MARKETPLACE}" is '
                f"{CLAUDE_PLUGIN_ALREADY_ENABLED_FRAGMENT} at user scope"
            ),
        },
    )

    result = ensure_local_marketplace_sources(
        DEFAULT_MARKETPLACE,
        source_root=canonical_root,
        runner=runner,
    )

    assert result.changed is True
    assert python_enable in runner.calls
    return True


def source_reconciliation_ignores_managed_scope_claude_plugins_without_project_path(
    tmp_path: Path,
) -> bool:
    canonical_root = tmp_path / "canonical-marketplace"
    stale_root = tmp_path / "old-marketplace"
    runner = _source_repair_runner(
        claude_payload=_claude_directory_marketplace_payload(stale_root),
        codex_root=canonical_root,
        plugin_payload=json.dumps(
            [
                _claude_plugin_payload(
                    "spec-tree",
                    scope=CLAUDE_SCOPE_MANAGED,
                    enabled=True,
                ),
                _claude_plugin_payload(
                    "rust",
                    scope=CLAUDE_SCOPE_USER,
                    enabled=False,
                ),
            ]
        ),
    )

    result = ensure_local_marketplace_sources(
        DEFAULT_MARKETPLACE,
        source_root=canonical_root,
        runner=runner,
    )

    _assert_repair_result(
        result,
        runner,
        expected_root=canonical_root,
        expected_calls=[
            *_expected_discovery_and_user_plugin_snapshot_calls(),
            (
                *CLAUDE_MARKETPLACE_REMOVE_COMMAND,
                DEFAULT_MARKETPLACE,
                "--scope",
                CLAUDE_SCOPE_USER,
            ),
            (
                *CLAUDE_MARKETPLACE_ADD_COMMAND,
                str(result.root),
                "--scope",
                CLAUDE_SCOPE_USER,
            ),
            *_user_scope_rust_restore_calls(),
        ],
        expected_cwd=[None, None, None, None, None, None, None],
    )
    return True


def source_reconciliation_restores_enabled_user_scope_claude_plugins(
    tmp_path: Path,
) -> bool:
    canonical_root = tmp_path / "canonical-marketplace"
    stale_root = tmp_path / "old-marketplace"
    python_install, python_enable = _user_scope_python_enable_calls()
    runner = _source_repair_runner(
        claude_payload=_claude_directory_marketplace_payload(stale_root),
        codex_root=canonical_root,
        plugin_payload=json.dumps(
            [
                _claude_plugin_payload(
                    "python",
                    scope=CLAUDE_SCOPE_USER,
                    enabled=True,
                )
            ]
        ),
    )

    result = ensure_local_marketplace_sources(
        DEFAULT_MARKETPLACE,
        source_root=canonical_root,
        runner=runner,
    )

    _assert_repair_result(
        result,
        runner,
        expected_root=canonical_root,
        expected_calls=[
            *_expected_discovery_and_user_plugin_snapshot_calls(),
            (
                *CLAUDE_MARKETPLACE_REMOVE_COMMAND,
                DEFAULT_MARKETPLACE,
                "--scope",
                CLAUDE_SCOPE_USER,
            ),
            (
                *CLAUDE_MARKETPLACE_ADD_COMMAND,
                str(result.root),
                "--scope",
                CLAUDE_SCOPE_USER,
            ),
            python_install,
            python_enable,
        ],
        expected_cwd=[None, None, None, None, None, None, None],
    )
    return True


def source_reconciliation_user_restore_non_idempotent_errors_surface(
    tmp_path: Path,
) -> bool:
    canonical_root = tmp_path / "canonical-marketplace"
    stale_root = tmp_path / "old-marketplace"
    python_install, _python_enable = _user_scope_python_enable_calls()
    runner = _source_repair_runner(
        claude_payload=_claude_directory_marketplace_payload(stale_root),
        codex_root=canonical_root,
        plugin_payload=json.dumps(
            [
                _claude_plugin_payload(
                    "python",
                    scope=CLAUDE_SCOPE_USER,
                    enabled=True,
                )
            ]
        ),
        returncode_by_command={python_install: 1},
        stderr_by_command={
            python_install: (
                f'Failed to install plugin "python@{DEFAULT_MARKETPLACE}": '
                "permission update failed"
            )
        },
    )

    with pytest.raises(MarketplaceSourceError) as exc_info:
        ensure_local_marketplace_sources(
            DEFAULT_MARKETPLACE,
            source_root=canonical_root,
            runner=runner,
        )

    message = str(exc_info.value)
    assert "claude plugin install --scope user" in message
    assert "permission update failed" in message
    return True
