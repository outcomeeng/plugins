"""Level 1 conformance tests for local marketplace source discovery.

The maintainer sync path reads the configured Claude and Codex marketplace
sources before refreshing Codex plugins. These tests pin the JSON contract and
the local-source gate without invoking either runtime CLI.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

import pytest

from outcomeeng.distribution.marketplace_sources import (
    CLAUDE_MARKETPLACE_ADD_COMMAND,
    CLAUDE_MARKETPLACE_REMOVE_COMMAND,
    CLAUDE_PLUGIN_DISABLE_COMMAND,
    CLAUDE_PLUGIN_ENABLE_COMMAND,
    CLAUDE_PLUGIN_INSTALL_COMMAND,
    CLAUDE_PLUGIN_LIST_COMMAND,
    CODEX_PLUGIN_MANIFEST,
    CODEX_MARKETPLACE_ADD_COMMAND,
    CODEX_MARKETPLACE_REMOVE_COMMAND,
    DEFAULT_MARKETPLACE,
    DIST_CODEX_PLUGINS_DIR,
    MarketplaceSourceError,
    available_codex_plugins,
    ensure_local_marketplace_sources,
    parse_claude_installed_plugins,
    parse_claude_marketplace_sources,
    parse_codex_marketplace_sources,
    require_matching_local_sources,
)


def test_parse_codex_marketplace_sources_accepts_local_source(
    tmp_path: Path,
) -> None:
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


def test_parse_codex_marketplace_sources_accepts_nested_local_source(
    tmp_path: Path,
) -> None:
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


def test_parse_claude_marketplace_sources_normalizes_directory_source(
    tmp_path: Path,
) -> None:
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


def test_parse_claude_installed_plugins_keeps_scope_state_and_project_path(
    tmp_path: Path,
) -> None:
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


def test_parse_codex_marketplace_sources_accepts_nested_git_source() -> None:
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


def test_parse_codex_marketplace_sources_accepts_empty_marketplace_array() -> None:
    sources = parse_codex_marketplace_sources(json.dumps({"marketplaces": []}))

    assert sources == {}


def test_require_matching_local_sources_rejects_git_backed_codex(
    tmp_path: Path,
) -> None:
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


def test_require_matching_local_sources_rejects_path_mismatch(
    tmp_path: Path,
) -> None:
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


def test_available_codex_plugins_are_read_from_dist_codex(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / "repo"
    _write_codex_manifest(repo_root, "zeta", "0.2.0")
    _write_codex_manifest(repo_root, "alpha", "0.1.0")
    (repo_root / DIST_CODEX_PLUGINS_DIR / "missing-manifest").mkdir(parents=True)

    plugins = available_codex_plugins(repo_root)

    assert [(plugin.name, plugin.version) for plugin in plugins] == [
        ("alpha", "0.1.0"),
        ("zeta", "0.2.0"),
    ]


def test_source_reconciliation_adds_absent_runtime_sources(tmp_path: Path) -> None:
    marketplace_root = tmp_path / "marketplace"
    runner = RecordingCommandRunner(
        stdout_by_command={
            ("claude", "plugin", "marketplace", "list", "--json"): "[]",
            ("codex", "plugin", "marketplace", "list", "--json"): json.dumps(
                {"marketplaces": []}
            ),
        }
    )

    result = ensure_local_marketplace_sources(
        DEFAULT_MARKETPLACE,
        source_root=marketplace_root,
        runner=runner,
    )

    assert result.root == marketplace_root.resolve(strict=False)
    assert result.changed is True
    assert runner.calls == [
        ("claude", "plugin", "marketplace", "list", "--json"),
        ("codex", "plugin", "marketplace", "list", "--json"),
        (*CLAUDE_MARKETPLACE_ADD_COMMAND, str(marketplace_root)),
        (*CODEX_MARKETPLACE_ADD_COMMAND, str(marketplace_root)),
    ]


def test_source_reconciliation_replaces_git_backed_codex_source(
    tmp_path: Path,
) -> None:
    marketplace_root = tmp_path / "marketplace"
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

    result = ensure_local_marketplace_sources(DEFAULT_MARKETPLACE, runner=runner)

    assert result.root == marketplace_root.resolve(strict=False)
    assert result.changed is True
    assert runner.calls == [
        ("claude", "plugin", "marketplace", "list", "--json"),
        ("codex", "plugin", "marketplace", "list", "--json"),
        (*CODEX_MARKETPLACE_REMOVE_COMMAND, DEFAULT_MARKETPLACE),
        (*CODEX_MARKETPLACE_ADD_COMMAND, str(result.root)),
    ]


def test_source_reconciliation_replaces_mismatched_codex_path(
    tmp_path: Path,
) -> None:
    claude_root = tmp_path / "claude-marketplace"
    codex_root = tmp_path / "codex-marketplace"
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

    result = ensure_local_marketplace_sources(DEFAULT_MARKETPLACE, runner=runner)

    assert result.root == claude_root.resolve(strict=False)
    assert result.changed is True
    assert runner.calls == [
        ("claude", "plugin", "marketplace", "list", "--json"),
        ("codex", "plugin", "marketplace", "list", "--json"),
        (*CODEX_MARKETPLACE_REMOVE_COMMAND, DEFAULT_MARKETPLACE),
        (*CODEX_MARKETPLACE_ADD_COMMAND, str(result.root)),
    ]


def test_source_reconciliation_explicit_root_replaces_stale_runtime_paths(
    tmp_path: Path,
) -> None:
    canonical_root = tmp_path / "canonical-marketplace"
    claude_root = tmp_path / "old-claude-marketplace"
    codex_root = tmp_path / "old-codex-marketplace"
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
            (*CLAUDE_PLUGIN_LIST_COMMAND,): "[]",
        }
    )

    result = ensure_local_marketplace_sources(
        DEFAULT_MARKETPLACE,
        source_root=canonical_root,
        runner=runner,
    )

    assert result.root == canonical_root.resolve(strict=False)
    assert result.changed is True
    assert runner.calls == [
        ("claude", "plugin", "marketplace", "list", "--json"),
        ("codex", "plugin", "marketplace", "list", "--json"),
        (*CLAUDE_PLUGIN_LIST_COMMAND,),
        (*CLAUDE_MARKETPLACE_REMOVE_COMMAND, DEFAULT_MARKETPLACE),
        (*CLAUDE_MARKETPLACE_ADD_COMMAND, str(result.root)),
        (*CODEX_MARKETPLACE_REMOVE_COMMAND, DEFAULT_MARKETPLACE),
        (*CODEX_MARKETPLACE_ADD_COMMAND, str(result.root)),
    ]


def test_source_reconciliation_preserves_claude_plugin_installs_when_source_changes(
    tmp_path: Path,
) -> None:
    canonical_root = tmp_path / "canonical-marketplace"
    stale_root = tmp_path / "old-marketplace"
    project_path = tmp_path / "consumer-project"
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
                        "projectPath": str(project_path),
                    },
                    {
                        "id": f"rust@{DEFAULT_MARKETPLACE}",
                        "scope": "user",
                        "enabled": False,
                    },
                ]
            ),
        }
    )

    result = ensure_local_marketplace_sources(
        DEFAULT_MARKETPLACE,
        source_root=canonical_root,
        runner=runner,
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
    assert result.changed is True
    assert runner.calls == [
        ("claude", "plugin", "marketplace", "list", "--json"),
        ("codex", "plugin", "marketplace", "list", "--json"),
        (*CLAUDE_PLUGIN_LIST_COMMAND,),
        (*CLAUDE_MARKETPLACE_REMOVE_COMMAND, DEFAULT_MARKETPLACE),
        (*CLAUDE_MARKETPLACE_ADD_COMMAND, str(result.root)),
        spec_tree_install,
        spec_tree_enable,
        rust_install,
        rust_disable,
    ]
    assert runner.cwd_by_call == [
        None,
        None,
        None,
        None,
        None,
        project_path,
        project_path,
        None,
        None,
    ]


def test_source_reconciliation_failed_codex_add_surfaces_error(
    tmp_path: Path,
) -> None:
    marketplace_root = tmp_path / "marketplace"
    codex_add = (*CODEX_MARKETPLACE_ADD_COMMAND, str(marketplace_root))
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
    manifest.write_text(json.dumps({"name": plugin, "version": version}))
