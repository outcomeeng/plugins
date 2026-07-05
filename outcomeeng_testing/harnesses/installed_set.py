"""Harnesses for Codex installed-set parser conformance."""

from __future__ import annotations

import json
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import pytest

from outcomeeng.distribution import codex_cache
from outcomeeng.distribution.marketplace_sources import DEFAULT_MARKETPLACE

OTHER_MARKETPLACE = "elsewhere"


@dataclass(frozen=True)
class StubRunner:
    """Returns a predetermined CompletedProcess for the installed-set query."""

    result: subprocess.CompletedProcess[str]

    def __call__(
        self, command: list[str], *, cwd: Path | None = None
    ) -> subprocess.CompletedProcess[str]:
        return self.result


def installed_set_conformance_passes() -> bool:
    for assertion in (
        parse_extracts_installed_versions_for_marketplace,
        parse_filters_out_other_marketplace_entries,
        parse_empty_installed_array_is_a_valid_empty_map,
        parse_raises_on_missing_installed_key,
        parse_raises_on_non_object_payload,
        parse_raises_on_invalid_json,
        parse_raises_on_installed_entry_without_name,
        parse_raises_on_installed_entry_with_non_string_name,
        parse_raises_on_installed_entry_without_version,
        parse_raises_on_installed_entry_with_non_string_version,
        parse_raises_on_non_object_installed_entry,
        parse_includes_entry_without_marketplace_name,
        provider_returns_versions_on_successful_query,
        provider_raises_when_query_exits_nonzero,
        provider_invokes_the_codex_plugin_list_command,
    ):
        assertion()
    return True


def parse_extracts_installed_versions_for_marketplace() -> None:
    payload = _payload(
        [
            {
                "name": "prose",
                "version": "0.4.0",
                "marketplaceName": DEFAULT_MARKETPLACE,
            },
            {
                "name": "rust",
                "version": "0.2.11",
                "marketplaceName": DEFAULT_MARKETPLACE,
            },
            {
                "name": "spec-tree",
                "version": "0.57.32",
                "marketplaceName": DEFAULT_MARKETPLACE,
            },
        ]
    )

    versions = codex_cache.parse_installed_plugin_versions(payload, DEFAULT_MARKETPLACE)

    assert versions == {
        "prose": "0.4.0",
        "rust": "0.2.11",
        "spec-tree": "0.57.32",
    }


def parse_filters_out_other_marketplace_entries() -> None:
    payload = _payload(
        [
            {
                "name": "prose",
                "version": "0.4.0",
                "marketplaceName": DEFAULT_MARKETPLACE,
            },
            {
                "name": "foreign",
                "version": "9.9.9",
                "marketplaceName": OTHER_MARKETPLACE,
            },
        ]
    )

    versions = codex_cache.parse_installed_plugin_versions(payload, DEFAULT_MARKETPLACE)

    assert versions == {"prose": "0.4.0"}


def parse_empty_installed_array_is_a_valid_empty_map() -> None:
    versions = codex_cache.parse_installed_plugin_versions(
        _payload([]), DEFAULT_MARKETPLACE
    )

    assert versions == {}


def parse_raises_on_missing_installed_key() -> None:
    with pytest.raises(codex_cache.InstalledSetError):
        codex_cache.parse_installed_plugin_versions(
            json.dumps({"available": []}), DEFAULT_MARKETPLACE
        )


def parse_raises_on_non_object_payload() -> None:
    with pytest.raises(codex_cache.InstalledSetError):
        codex_cache.parse_installed_plugin_versions(json.dumps([]), DEFAULT_MARKETPLACE)


def parse_raises_on_invalid_json() -> None:
    with pytest.raises(codex_cache.InstalledSetError):
        codex_cache.parse_installed_plugin_versions("{not json", DEFAULT_MARKETPLACE)


def parse_raises_on_installed_entry_without_name() -> None:
    payload = _payload([{"version": "0.4.0", "marketplaceName": DEFAULT_MARKETPLACE}])

    with pytest.raises(codex_cache.InstalledSetError):
        codex_cache.parse_installed_plugin_versions(payload, DEFAULT_MARKETPLACE)


def parse_raises_on_installed_entry_with_non_string_name() -> None:
    payload = _payload(
        [{"name": 42, "version": "0.4.0", "marketplaceName": DEFAULT_MARKETPLACE}]
    )

    with pytest.raises(codex_cache.InstalledSetError):
        codex_cache.parse_installed_plugin_versions(payload, DEFAULT_MARKETPLACE)


def parse_raises_on_installed_entry_without_version() -> None:
    payload = _payload([{"name": "prose", "marketplaceName": DEFAULT_MARKETPLACE}])

    with pytest.raises(codex_cache.InstalledSetError):
        codex_cache.parse_installed_plugin_versions(payload, DEFAULT_MARKETPLACE)


def parse_raises_on_installed_entry_with_non_string_version() -> None:
    payload = _payload(
        [{"name": "prose", "version": 4, "marketplaceName": DEFAULT_MARKETPLACE}]
    )

    with pytest.raises(codex_cache.InstalledSetError):
        codex_cache.parse_installed_plugin_versions(payload, DEFAULT_MARKETPLACE)


def parse_raises_on_non_object_installed_entry() -> None:
    payload = json.dumps({"installed": ["not-an-object"], "available": []})

    with pytest.raises(codex_cache.InstalledSetError):
        codex_cache.parse_installed_plugin_versions(payload, DEFAULT_MARKETPLACE)


def parse_includes_entry_without_marketplace_name() -> None:
    versions = codex_cache.parse_installed_plugin_versions(
        _payload([{"name": "prose", "version": "0.4.0"}]), DEFAULT_MARKETPLACE
    )

    assert versions == {"prose": "0.4.0"}


def provider_returns_versions_on_successful_query() -> None:
    payload = _payload(
        [
            {
                "name": "prose",
                "version": "0.4.0",
                "marketplaceName": DEFAULT_MARKETPLACE,
            }
        ]
    )
    runner = StubRunner(subprocess.CompletedProcess([], 0, stdout=payload))

    provider = codex_cache.CodexCliInstalled(runner=runner)

    assert provider.installed_plugin_versions(DEFAULT_MARKETPLACE) == {"prose": "0.4.0"}


def provider_raises_when_query_exits_nonzero() -> None:
    runner = StubRunner(
        subprocess.CompletedProcess([], 1, stdout="", stderr="marketplace not found")
    )

    provider = codex_cache.CodexCliInstalled(runner=runner)

    with pytest.raises(codex_cache.InstalledSetError) as exc_info:
        provider.installed_plugin_versions(DEFAULT_MARKETPLACE)

    assert "marketplace not found" in str(exc_info.value)


def provider_invokes_the_codex_plugin_list_command() -> None:
    captured: list[list[str]] = []

    def recording_runner(
        command: list[str], *, cwd: Path | None = None
    ) -> subprocess.CompletedProcess[str]:
        captured.append(command)
        return subprocess.CompletedProcess(
            command,
            0,
            stdout=_payload(
                [
                    {
                        "name": "prose",
                        "version": "0.4.0",
                        "marketplaceName": DEFAULT_MARKETPLACE,
                    }
                ]
            ),
        )

    provider = codex_cache.CodexCliInstalled(runner=recording_runner)

    provider.installed_plugin_versions(DEFAULT_MARKETPLACE)

    assert captured == [[*codex_cache.CODEX_LIST_COMMAND, DEFAULT_MARKETPLACE]], (
        f"expected the codex plugin list command, got {captured}"
    )


def _payload(installed: list[dict[str, object]]) -> str:
    return json.dumps({"installed": installed, "available": []})


_: tuple[Callable[[], None], ...] = (
    parse_extracts_installed_versions_for_marketplace,
    parse_filters_out_other_marketplace_entries,
    parse_empty_installed_array_is_a_valid_empty_map,
    parse_raises_on_missing_installed_key,
    parse_raises_on_non_object_payload,
    parse_raises_on_invalid_json,
    parse_raises_on_installed_entry_without_name,
    parse_raises_on_installed_entry_with_non_string_name,
    parse_raises_on_installed_entry_without_version,
    parse_raises_on_installed_entry_with_non_string_version,
    parse_raises_on_non_object_installed_entry,
    parse_includes_entry_without_marketplace_name,
    provider_returns_versions_on_successful_query,
    provider_raises_when_query_exits_nonzero,
    provider_invokes_the_codex_plugin_list_command,
)
