"""Level 1 conformance for the Codex installed-set query and its parser.

The cache-preservation step scopes its work to the plugins Codex reports as
installed for the marketplace, read from `codex plugin list --json
--marketplace <mkt>`. These tests pin the parser to the Codex CLI's JSON
contract: the `installed` array's `name` and `version` entries scoped to the
queried marketplace, and a loud failure on any payload that does not match — so a
changed CLI contract is detected rather than silently read as an empty installed
set or stale target.

The provider scenarios inject a runner stub (Stage 5 exception 1 — failure
simulation, and exception 7 — contract probe) so the CLI boundary is exercised
without the real `codex` binary, which is absent in CI.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass

import pytest

from outcomeeng.distribution import codex_cache
from outcomeeng.distribution.marketplace_sources import DEFAULT_MARKETPLACE

OTHER_MARKETPLACE = "elsewhere"


@dataclass(frozen=True)
class StubRunner:
    """Returns a predetermined CompletedProcess for the installed-set query.

    Stands in for the real `codex plugin list` subprocess so the provider's
    return-code handling and stdout parsing are observable at l1.
    """

    result: subprocess.CompletedProcess[str]

    def __call__(self, command: list[str]) -> subprocess.CompletedProcess[str]:
        return self.result


def _payload(installed: list[dict[str, object]]) -> str:
    return json.dumps({"installed": installed, "available": []})


def test_parse_extracts_installed_versions_for_marketplace() -> None:
    """A well-formed payload yields name to version for every in-scope entry."""
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


def test_parse_filters_out_other_marketplace_entries() -> None:
    """An entry whose marketplaceName names a different marketplace is excluded."""
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


def test_parse_empty_installed_array_is_a_valid_empty_map() -> None:
    """A successful query with no installed plugins is a valid empty map."""
    versions = codex_cache.parse_installed_plugin_versions(
        _payload([]), DEFAULT_MARKETPLACE
    )

    assert versions == {}


def test_parse_raises_on_missing_installed_key() -> None:
    """A payload without an `installed` array is an unrecognized shape."""
    with pytest.raises(codex_cache.InstalledSetError):
        codex_cache.parse_installed_plugin_versions(
            json.dumps({"available": []}), DEFAULT_MARKETPLACE
        )


def test_parse_raises_on_non_object_payload() -> None:
    """A top-level JSON array does not match the contract and raises."""
    with pytest.raises(codex_cache.InstalledSetError):
        codex_cache.parse_installed_plugin_versions(json.dumps([]), DEFAULT_MARKETPLACE)


def test_parse_raises_on_invalid_json() -> None:
    """Unparseable output raises instead of becoming an empty map."""
    with pytest.raises(codex_cache.InstalledSetError):
        codex_cache.parse_installed_plugin_versions("{not json", DEFAULT_MARKETPLACE)


def test_parse_raises_on_installed_entry_without_name() -> None:
    """An installed entry lacking a string `name` is malformed and raises."""
    payload = _payload([{"version": "0.4.0", "marketplaceName": DEFAULT_MARKETPLACE}])

    with pytest.raises(codex_cache.InstalledSetError):
        codex_cache.parse_installed_plugin_versions(payload, DEFAULT_MARKETPLACE)


def test_parse_raises_on_installed_entry_with_non_string_name() -> None:
    """An installed entry whose `name` is present but not a string raises."""
    payload = _payload(
        [{"name": 42, "version": "0.4.0", "marketplaceName": DEFAULT_MARKETPLACE}]
    )

    with pytest.raises(codex_cache.InstalledSetError):
        codex_cache.parse_installed_plugin_versions(payload, DEFAULT_MARKETPLACE)


def test_parse_raises_on_installed_entry_without_version() -> None:
    """An installed entry lacking a string `version` is malformed and raises."""
    payload = _payload([{"name": "prose", "marketplaceName": DEFAULT_MARKETPLACE}])

    with pytest.raises(codex_cache.InstalledSetError):
        codex_cache.parse_installed_plugin_versions(payload, DEFAULT_MARKETPLACE)


def test_parse_raises_on_installed_entry_with_non_string_version() -> None:
    """An installed entry whose `version` is present but not a string raises."""
    payload = _payload(
        [{"name": "prose", "version": 4, "marketplaceName": DEFAULT_MARKETPLACE}]
    )

    with pytest.raises(codex_cache.InstalledSetError):
        codex_cache.parse_installed_plugin_versions(payload, DEFAULT_MARKETPLACE)


def test_parse_raises_on_non_object_installed_entry() -> None:
    """An `installed` array element that is not an object raises."""
    payload = json.dumps({"installed": ["not-an-object"], "available": []})

    with pytest.raises(codex_cache.InstalledSetError):
        codex_cache.parse_installed_plugin_versions(payload, DEFAULT_MARKETPLACE)


def test_parse_includes_entry_without_marketplace_name() -> None:
    """Absent marketplaceName is treated as in-scope for the scoped query."""
    versions = codex_cache.parse_installed_plugin_versions(
        _payload([{"name": "prose", "version": "0.4.0"}]), DEFAULT_MARKETPLACE
    )

    assert versions == {"prose": "0.4.0"}


def test_provider_returns_versions_on_successful_query() -> None:
    """The provider runs the CLI and returns the parsed installed versions."""
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


def test_provider_raises_when_query_exits_nonzero() -> None:
    """A non-zero exit from `codex plugin list` is a failed query."""
    runner = StubRunner(
        subprocess.CompletedProcess([], 1, stdout="", stderr="marketplace not found")
    )

    provider = codex_cache.CodexCliInstalled(runner=runner)

    with pytest.raises(codex_cache.InstalledSetError) as exc_info:
        provider.installed_plugin_versions(DEFAULT_MARKETPLACE)

    assert "marketplace not found" in str(exc_info.value)


def test_provider_invokes_the_codex_plugin_list_command() -> None:
    """The provider invokes `codex plugin list --json --marketplace <mkt>`."""
    captured: list[list[str]] = []

    def recording_runner(command: list[str]) -> subprocess.CompletedProcess[str]:
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
