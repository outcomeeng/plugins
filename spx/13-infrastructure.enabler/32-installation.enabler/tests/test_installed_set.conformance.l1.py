"""Level 1 conformance for the Codex installed-set query and its parser.

The cache-preservation step scopes its work to the plugins Codex reports as
installed for the marketplace, read from `codex plugin list --json
--marketplace <mkt>`. These tests pin the parser to the Codex CLI's JSON
contract: the `installed` array's `name` entries scoped to the queried
marketplace, and a loud failure on any payload that does not match — so a
changed CLI contract is detected rather than silently read as an empty
installed set.

The provider scenarios inject a runner stub (Stage 5 exception 1 -- failure
simulation, and exception 7 -- contract probe) so the CLI boundary is exercised
without the real `codex` binary, which is absent in CI.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass

import pytest

from outcomeeng.distribution import codex_cache
from outcomeeng.distribution.codex_cache import DEFAULT_MARKETPLACE

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


def _payload(installed: list[dict[str, str]]) -> str:
    return json.dumps({"installed": installed, "available": []})


def test_parse_extracts_installed_names_for_marketplace() -> None:
    """A well-formed payload yields the `name` of every `installed` entry whose
    marketplaceName matches the queried marketplace."""
    payload = _payload(
        [
            {"name": "prose", "marketplaceName": DEFAULT_MARKETPLACE},
            {"name": "rust", "marketplaceName": DEFAULT_MARKETPLACE},
            {"name": "spec-tree", "marketplaceName": DEFAULT_MARKETPLACE},
        ]
    )

    names = codex_cache.parse_installed_plugins(payload, DEFAULT_MARKETPLACE)

    assert names == frozenset({"prose", "rust", "spec-tree"})


def test_parse_filters_out_other_marketplace_entries() -> None:
    """An entry whose marketplaceName names a different marketplace is excluded,
    so the installed set is scoped even if the caller's filter is absent."""
    payload = _payload(
        [
            {"name": "prose", "marketplaceName": DEFAULT_MARKETPLACE},
            {"name": "foreign", "marketplaceName": OTHER_MARKETPLACE},
        ]
    )

    names = codex_cache.parse_installed_plugins(payload, DEFAULT_MARKETPLACE)

    assert names == frozenset({"prose"})


def test_parse_empty_installed_array_is_a_valid_empty_set() -> None:
    """A successful query with no installed plugins is a valid empty set, distinct
    from a failed query -- it must not raise."""
    names = codex_cache.parse_installed_plugins(_payload([]), DEFAULT_MARKETPLACE)

    assert names == frozenset()


def test_parse_raises_on_missing_installed_key() -> None:
    """A payload without an `installed` array is an unrecognized shape and raises,
    rather than yielding a silent empty set that would prune every cache directory."""
    with pytest.raises(codex_cache.InstalledSetError):
        codex_cache.parse_installed_plugins(
            json.dumps({"available": []}), DEFAULT_MARKETPLACE
        )


def test_parse_raises_on_non_object_payload() -> None:
    """A top-level JSON array (not an object) does not match the contract and raises."""
    with pytest.raises(codex_cache.InstalledSetError):
        codex_cache.parse_installed_plugins(json.dumps([]), DEFAULT_MARKETPLACE)


def test_parse_raises_on_invalid_json() -> None:
    """Unparseable output raises rather than being swallowed into an empty set."""
    with pytest.raises(codex_cache.InstalledSetError):
        codex_cache.parse_installed_plugins("{not json", DEFAULT_MARKETPLACE)


def test_parse_raises_on_installed_entry_without_name() -> None:
    """An installed entry lacking a string `name` is malformed and raises."""
    payload = _payload([{"marketplaceName": DEFAULT_MARKETPLACE}])

    with pytest.raises(codex_cache.InstalledSetError):
        codex_cache.parse_installed_plugins(payload, DEFAULT_MARKETPLACE)


def test_parse_raises_on_installed_entry_with_non_string_name() -> None:
    """An installed entry whose `name` is present but not a string is malformed and
    raises — the present-but-wrong-type path, distinct from the absent-key path."""
    payload = json.dumps(
        {
            "installed": [{"name": 42, "marketplaceName": DEFAULT_MARKETPLACE}],
            "available": [],
        }
    )

    with pytest.raises(codex_cache.InstalledSetError):
        codex_cache.parse_installed_plugins(payload, DEFAULT_MARKETPLACE)


def test_parse_raises_on_non_object_installed_entry() -> None:
    """An `installed` array element that is not an object does not match the contract
    and raises rather than being skipped."""
    payload = json.dumps({"installed": ["not-an-object"], "available": []})

    with pytest.raises(codex_cache.InstalledSetError):
        codex_cache.parse_installed_plugins(payload, DEFAULT_MARKETPLACE)


def test_parse_includes_entry_without_marketplace_name() -> None:
    """An installed entry that omits `marketplaceName` is treated as in-scope and
    included — absent attribution does not exclude an entry the `--marketplace` query
    already scoped."""
    names = codex_cache.parse_installed_plugins(
        _payload([{"name": "prose"}]), DEFAULT_MARKETPLACE
    )

    assert names == frozenset({"prose"})


def test_provider_returns_names_on_successful_query() -> None:
    """The provider runs the CLI through its injected runner and returns the parsed
    installed names when the query exits zero."""
    payload = _payload([{"name": "prose", "marketplaceName": DEFAULT_MARKETPLACE}])
    runner = StubRunner(subprocess.CompletedProcess([], 0, stdout=payload))

    provider = codex_cache.CodexCliInstalled(runner=runner)

    assert provider.installed_plugins(DEFAULT_MARKETPLACE) == frozenset({"prose"})


def test_provider_raises_when_query_exits_nonzero() -> None:
    """A non-zero exit from `codex plugin list` is a failed query: the provider
    raises so preservation aborts rather than pruning against a degraded signal."""
    runner = StubRunner(subprocess.CompletedProcess([], 1, stdout=""))

    provider = codex_cache.CodexCliInstalled(runner=runner)

    with pytest.raises(codex_cache.InstalledSetError):
        provider.installed_plugins(DEFAULT_MARKETPLACE)
