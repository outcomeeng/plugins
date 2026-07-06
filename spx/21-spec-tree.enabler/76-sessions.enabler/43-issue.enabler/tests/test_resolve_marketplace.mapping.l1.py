"""Mapping evidence for the `/issue` marketplace resolver."""

from outcomeeng_testing.harnesses.marketplace_sources import (
    issue_resolver_claude_directory_marketplace_json_maps_to_path,
    issue_resolver_codex_local_marketplace_json_maps_to_path,
    issue_resolver_creates_no_temporary_files,
    issue_resolver_malformed_marketplace_json_maps_to_invalid_json_error,
    issue_resolver_missing_local_marketplace_maps_to_resolution_error,
)


def test_claude_directory_marketplace_json_maps_to_path() -> None:
    assert issue_resolver_claude_directory_marketplace_json_maps_to_path()


def test_codex_local_marketplace_json_maps_to_path() -> None:
    assert issue_resolver_codex_local_marketplace_json_maps_to_path()


def test_malformed_marketplace_json_maps_to_invalid_json_error() -> None:
    assert issue_resolver_malformed_marketplace_json_maps_to_invalid_json_error()


def test_missing_local_marketplace_maps_to_resolution_error() -> None:
    assert issue_resolver_missing_local_marketplace_maps_to_resolution_error()


def test_resolver_creates_no_temporary_files() -> None:
    assert issue_resolver_creates_no_temporary_files()
