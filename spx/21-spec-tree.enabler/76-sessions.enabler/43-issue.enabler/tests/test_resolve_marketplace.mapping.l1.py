"""Mapping tests for the /issue marketplace resolver script."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

REPO_ROOT = Path(__file__).resolve().parents[5]
SCRIPT_PATH = (
    REPO_ROOT
    / "src"
    / "plugins"
    / "spec-tree"
    / "skills"
    / "issue"
    / "scripts"
    / "resolve_marketplace.py"
)


def _load_resolver() -> ModuleType:
    spec = importlib.util.spec_from_file_location("resolve_marketplace", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


RESOLVER = _load_resolver()


def _run_resolver(
    payload: object | str,
    *,
    runtime: str,
    cwd: Path | None = None,
    name: str | None = RESOLVER.DEFAULT_MARKETPLACE_NAME,
) -> subprocess.CompletedProcess[str]:
    """Drive the resolver; `name=None` omits `--name` to take the CLI default."""
    stdin = payload if isinstance(payload, str) else json.dumps(payload)
    name_argv = [] if name is None else ["--name", name]
    return subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--runtime",
            runtime,
            *name_argv,
        ],
        input=stdin,
        capture_output=True,
        text=True,
        check=False,
        cwd=cwd,
    )


def test_claude_directory_marketplace_json_maps_to_path(tmp_path: Path) -> None:
    registered_path = tmp_path / "claude-marketplace"
    payload = [
        {
            RESOLVER.NAME_FIELD: RESOLVER.DEFAULT_MARKETPLACE_NAME,
            RESOLVER.SOURCE_FIELD: RESOLVER.CLAUDE_DIRECTORY_SOURCE.title(),
            RESOLVER.PATH_FIELD: str(registered_path),
        }
    ]

    result = _run_resolver(payload, runtime=RESOLVER.RUNTIME_CLAUDE)

    assert result.returncode == 0
    assert result.stdout == f"{registered_path}\n"
    assert result.stderr == ""


def test_codex_local_marketplace_json_maps_to_path(tmp_path: Path) -> None:
    registered_path = tmp_path / "codex-marketplace"
    payload = {
        RESOLVER.MARKETPLACES_FIELD: [
            {
                RESOLVER.NAME_FIELD: RESOLVER.DEFAULT_MARKETPLACE_NAME,
                RESOLVER.MARKETPLACE_SOURCE_FIELD: {
                    RESOLVER.SOURCE_TYPE_FIELD: RESOLVER.CODEX_LOCAL_SOURCE_TYPE,
                    RESOLVER.SOURCE_FIELD: str(registered_path),
                },
            }
        ]
    }

    result = _run_resolver(payload, runtime=RESOLVER.RUNTIME_CODEX)

    assert result.returncode == 0
    assert result.stdout == f"{registered_path}\n"
    assert result.stderr == ""


def test_codex_local_marketplace_root_only_maps_to_root(tmp_path: Path) -> None:
    materialized_root = tmp_path / "codex-root"
    payload = {
        RESOLVER.MARKETPLACES_FIELD: [
            {
                RESOLVER.NAME_FIELD: RESOLVER.DEFAULT_MARKETPLACE_NAME,
                RESOLVER.ROOT_FIELD: str(materialized_root),
                RESOLVER.MARKETPLACE_SOURCE_FIELD: {
                    RESOLVER.SOURCE_TYPE_FIELD: RESOLVER.CODEX_LOCAL_SOURCE_TYPE,
                },
            }
        ]
    }

    result = _run_resolver(payload, runtime=RESOLVER.RUNTIME_CODEX)

    assert result.returncode == 0
    assert result.stdout == f"{materialized_root}\n"
    assert result.stderr == ""


def test_codex_local_marketplace_maps_both_fields_to_source(tmp_path: Path) -> None:
    registered_source = tmp_path / "codex-source"
    materialized_root = tmp_path / "codex-root"
    payload = {
        RESOLVER.MARKETPLACES_FIELD: [
            {
                RESOLVER.NAME_FIELD: RESOLVER.DEFAULT_MARKETPLACE_NAME,
                RESOLVER.ROOT_FIELD: str(materialized_root),
                RESOLVER.MARKETPLACE_SOURCE_FIELD: {
                    RESOLVER.SOURCE_TYPE_FIELD: RESOLVER.CODEX_LOCAL_SOURCE_TYPE,
                    RESOLVER.SOURCE_FIELD: str(registered_source),
                },
            }
        ]
    }

    result = _run_resolver(payload, runtime=RESOLVER.RUNTIME_CODEX)

    assert result.returncode == 0
    assert result.stdout == f"{registered_source}\n"


def test_no_local_codex_marketplace_maps_to_none_available(tmp_path: Path) -> None:
    payload = {
        RESOLVER.MARKETPLACES_FIELD: [
            {
                RESOLVER.NAME_FIELD: "git-marketplace",
                RESOLVER.ROOT_FIELD: str(tmp_path / "git-cache"),
                RESOLVER.MARKETPLACE_SOURCE_FIELD: {
                    RESOLVER.SOURCE_TYPE_FIELD: "git",
                    RESOLVER.SOURCE_FIELD: "https://example.invalid/plugins.git",
                },
            }
        ]
    }

    result = _run_resolver(payload, runtime=RESOLVER.RUNTIME_CODEX)

    assert result.returncode == RESOLVER.EXIT_MARKETPLACE_NOT_FOUND
    assert result.stdout == ""
    assert (
        f"available local marketplaces: {RESOLVER.NO_LOCAL_MARKETPLACES}"
    ) in result.stderr


def test_claude_non_directory_source_maps_to_none_available(tmp_path: Path) -> None:
    payload = [
        {
            RESOLVER.NAME_FIELD: RESOLVER.DEFAULT_MARKETPLACE_NAME,
            RESOLVER.SOURCE_FIELD: "github",
            RESOLVER.PATH_FIELD: str(tmp_path / "github-cache"),
        }
    ]

    result = _run_resolver(payload, runtime=RESOLVER.RUNTIME_CLAUDE)

    assert result.returncode == RESOLVER.EXIT_MARKETPLACE_NOT_FOUND
    assert result.stdout == ""
    assert (
        f"available local marketplaces: {RESOLVER.NO_LOCAL_MARKETPLACES}"
    ) in result.stderr


def _unresolvable_payloads() -> list[tuple[str, str, object]]:
    """Registration payloads whose shape resolves no local checkout path."""
    return [
        # A str payload reaches _run_resolver as raw stdin, so this is the JSON
        # text encoding a scalar rather than a registration object or array.
        ("bare-scalar-payload", RESOLVER.RUNTIME_CLAUDE, '"not-a-registration"'),
        (
            "marketplaces-field-not-a-list",
            RESOLVER.RUNTIME_CLAUDE,
            # Non-iterable, so dropping the list guard raises rather than
            # silently yielding nothing.
            {RESOLVER.MARKETPLACES_FIELD: 17},
        ),
        (
            "non-dict-entry-in-list-payload",
            RESOLVER.RUNTIME_CLAUDE,
            [["not", "a", "mapping"]],
        ),
        (
            "non-dict-entry-in-marketplaces-field",
            RESOLVER.RUNTIME_CLAUDE,
            {RESOLVER.MARKETPLACES_FIELD: [17]},
        ),
        (
            "entry-name-not-a-string",
            RESOLVER.RUNTIME_CLAUDE,
            [
                {
                    RESOLVER.NAME_FIELD: 17,
                    RESOLVER.SOURCE_FIELD: RESOLVER.CLAUDE_DIRECTORY_SOURCE,
                    RESOLVER.PATH_FIELD: "/somewhere",
                }
            ],
        ),
        (
            "claude-directory-without-path",
            RESOLVER.RUNTIME_CLAUDE,
            [
                {
                    RESOLVER.NAME_FIELD: RESOLVER.DEFAULT_MARKETPLACE_NAME,
                    RESOLVER.SOURCE_FIELD: RESOLVER.CLAUDE_DIRECTORY_SOURCE,
                }
            ],
        ),
        (
            "codex-local-without-source-or-root",
            RESOLVER.RUNTIME_CODEX,
            {
                RESOLVER.MARKETPLACES_FIELD: [
                    {
                        RESOLVER.NAME_FIELD: RESOLVER.DEFAULT_MARKETPLACE_NAME,
                        RESOLVER.MARKETPLACE_SOURCE_FIELD: {
                            RESOLVER.SOURCE_TYPE_FIELD: (
                                RESOLVER.CODEX_LOCAL_SOURCE_TYPE
                            ),
                        },
                    }
                ]
            },
        ),
        (
            "marketplaces-field-absent",
            RESOLVER.RUNTIME_CLAUDE,
            {"version": 1},
        ),
        (
            "claude-entry-without-source",
            RESOLVER.RUNTIME_CLAUDE,
            [
                {
                    RESOLVER.NAME_FIELD: RESOLVER.DEFAULT_MARKETPLACE_NAME,
                    RESOLVER.PATH_FIELD: "/somewhere",
                }
            ],
        ),
        (
            # The shape Codex emits for a marketplace it materialized without
            # a recorded source: a top-level root and no marketplaceSource.
            "codex-entry-without-marketplace-source",
            RESOLVER.RUNTIME_CODEX,
            {
                RESOLVER.MARKETPLACES_FIELD: [
                    {
                        RESOLVER.NAME_FIELD: RESOLVER.DEFAULT_MARKETPLACE_NAME,
                        RESOLVER.ROOT_FIELD: "/somewhere",
                    }
                ]
            },
        ),
        (
            "codex-marketplace-source-not-a-mapping",
            RESOLVER.RUNTIME_CODEX,
            {
                RESOLVER.MARKETPLACES_FIELD: [
                    {
                        RESOLVER.NAME_FIELD: RESOLVER.DEFAULT_MARKETPLACE_NAME,
                        RESOLVER.MARKETPLACE_SOURCE_FIELD: "local",
                        RESOLVER.ROOT_FIELD: "/somewhere",
                    }
                ]
            },
        ),
    ]


UNRESOLVABLE_PAYLOADS = _unresolvable_payloads()


@pytest.mark.parametrize(
    ("shape", "runtime", "payload"),
    UNRESOLVABLE_PAYLOADS,
    ids=[case[0] for case in UNRESOLVABLE_PAYLOADS],
)
def test_unresolvable_payload_shape_maps_to_none_available(
    shape: str, runtime: str, payload: object
) -> None:
    result = _run_resolver(payload, runtime=runtime)

    assert result.returncode == RESOLVER.EXIT_MARKETPLACE_NOT_FOUND
    assert result.stdout == ""
    assert (
        f"available local marketplaces: {RESOLVER.NO_LOCAL_MARKETPLACES}"
    ) in result.stderr


def test_codex_empty_source_maps_to_root(tmp_path: Path) -> None:
    materialized_root = tmp_path / "codex-root"
    payload = {
        RESOLVER.MARKETPLACES_FIELD: [
            {
                RESOLVER.NAME_FIELD: RESOLVER.DEFAULT_MARKETPLACE_NAME,
                RESOLVER.ROOT_FIELD: str(materialized_root),
                RESOLVER.MARKETPLACE_SOURCE_FIELD: {
                    RESOLVER.SOURCE_TYPE_FIELD: RESOLVER.CODEX_LOCAL_SOURCE_TYPE,
                    RESOLVER.SOURCE_FIELD: "",
                },
            }
        ]
    }

    result = _run_resolver(payload, runtime=RESOLVER.RUNTIME_CODEX)

    assert result.returncode == 0
    assert result.stdout == f"{materialized_root}\n"


def test_same_name_entries_map_to_the_first_resolvable_one(tmp_path: Path) -> None:
    resolvable_path = tmp_path / "second-registration"
    payload = [
        {
            RESOLVER.NAME_FIELD: RESOLVER.DEFAULT_MARKETPLACE_NAME,
            RESOLVER.SOURCE_FIELD: RESOLVER.CLAUDE_DIRECTORY_SOURCE,
        },
        {
            RESOLVER.NAME_FIELD: RESOLVER.DEFAULT_MARKETPLACE_NAME,
            RESOLVER.SOURCE_FIELD: RESOLVER.CLAUDE_DIRECTORY_SOURCE,
            RESOLVER.PATH_FIELD: str(resolvable_path),
        },
    ]

    result = _run_resolver(payload, runtime=RESOLVER.RUNTIME_CLAUDE)

    assert result.returncode == 0
    assert result.stdout == f"{resolvable_path}\n"


def test_omitted_name_maps_to_the_default_marketplace(tmp_path: Path) -> None:
    registered_path = tmp_path / "default-name-marketplace"
    payload = [
        {
            RESOLVER.NAME_FIELD: RESOLVER.DEFAULT_MARKETPLACE_NAME,
            RESOLVER.SOURCE_FIELD: RESOLVER.CLAUDE_DIRECTORY_SOURCE,
            RESOLVER.PATH_FIELD: str(registered_path),
        }
    ]

    result = _run_resolver(payload, runtime=RESOLVER.RUNTIME_CLAUDE, name=None)

    assert result.returncode == 0
    assert result.stdout == f"{registered_path}\n"


def test_malformed_marketplace_json_maps_to_invalid_json_error() -> None:
    result = _run_resolver("{", runtime=RESOLVER.RUNTIME_CLAUDE)

    assert result.returncode == RESOLVER.EXIT_INVALID_JSON
    assert result.stdout == ""
    assert "invalid marketplace JSON:" in result.stderr


def test_missing_local_marketplace_maps_to_resolution_error(tmp_path: Path) -> None:
    other_path = tmp_path / "other-marketplace"
    payload = {
        RESOLVER.MARKETPLACES_FIELD: [
            {
                RESOLVER.NAME_FIELD: "other-marketplace",
                RESOLVER.SOURCE_FIELD: RESOLVER.CLAUDE_DIRECTORY_SOURCE,
                RESOLVER.PATH_FIELD: str(other_path),
            }
        ]
    }

    result = _run_resolver(payload, runtime=RESOLVER.RUNTIME_CLAUDE)

    assert result.returncode == RESOLVER.EXIT_MARKETPLACE_NOT_FOUND
    assert result.stdout == ""
    assert (
        f"marketplace {RESOLVER.DEFAULT_MARKETPLACE_NAME!r} is not registered as a "
        f"local {RESOLVER.RUNTIME_CLAUDE} marketplace"
    ) in result.stderr
    assert "available local marketplaces: other-marketplace" in result.stderr


def test_resolver_creates_no_temporary_files(tmp_path: Path) -> None:
    workdir = tmp_path / "empty-working-directory"
    workdir.mkdir()
    registered_path = tmp_path / "registered-marketplace"
    payload = [
        {
            RESOLVER.NAME_FIELD: RESOLVER.DEFAULT_MARKETPLACE_NAME,
            RESOLVER.SOURCE_FIELD: RESOLVER.CLAUDE_DIRECTORY_SOURCE,
            RESOLVER.PATH_FIELD: str(registered_path),
        }
    ]

    result = _run_resolver(payload, runtime=RESOLVER.RUNTIME_CLAUDE, cwd=workdir)

    assert result.returncode == 0
    assert list(workdir.iterdir()) == []
