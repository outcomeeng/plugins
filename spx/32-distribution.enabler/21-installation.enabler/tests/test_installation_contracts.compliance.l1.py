"""Ownership-bound placement against committed native agent artifacts."""

import hashlib
import json

from outcomeeng.distribution.installation import (
    AGENT_OWNERSHIP_DESTINATION_FIELD,
    AGENT_OWNERSHIP_DIGEST_FIELD,
    AGENT_OWNERSHIP_ENTRIES_FIELD,
    AGENT_OWNERSHIP_PLUGIN_FIELD,
    AGENT_OWNERSHIP_SCHEMA_FIELD,
    AGENT_OWNERSHIP_SCHEMA_VERSION,
)
from outcomeeng_testing.harnesses.plugin_lifecycle import (
    lifecycle_case,
    lifecycle_fixture,
)


def test_plugin_lifecycle_places_owned_definitions_and_is_idempotent() -> None:
    with lifecycle_case(lifecycle_fixture("empty.json")) as case:
        before_check = case.harness.snapshot(case.harness.home)
        check = case.run(check=True)
        assert check.exit_code == 1
        assert check.home_snapshot == before_check
        assert str(case.destination) in check.stdout

        installed = case.run()
        assert installed.exit_code == 0, installed.stdout
        for definition in case.definitions:
            assert (
                case.harness.home_agents / definition.source.name
            ).read_bytes() == definition.content
        ownership = json.loads(case.harness.ownership_path.read_text())
        assert ownership[AGENT_OWNERSHIP_SCHEMA_FIELD] == AGENT_OWNERSHIP_SCHEMA_VERSION
        assert {
            (
                entry[AGENT_OWNERSHIP_DESTINATION_FIELD],
                entry[AGENT_OWNERSHIP_PLUGIN_FIELD],
                entry[AGENT_OWNERSHIP_DIGEST_FIELD],
            )
            for entry in ownership[AGENT_OWNERSHIP_ENTRIES_FIELD]
        } == {
            (
                (case.harness.home_agents / definition.source.name)
                .relative_to(case.harness.home)
                .as_posix(),
                definition.plugin,
                hashlib.sha256(definition.content).hexdigest(),
            )
            for definition in case.definitions
        }
        identity = case.harness.file_identity(case.harness.ownership_path)
        clean_check = case.run(check=True)
        repeated = case.run()
        assert clean_check.exit_code == 0
        assert repeated.exit_code == 0
        assert repeated.home_snapshot == installed.home_snapshot
        assert case.harness.file_identity(case.harness.ownership_path) == identity


def test_plugin_lifecycle_prunes_only_matching_owned_definitions() -> None:
    with lifecycle_case(lifecycle_fixture("retired.json")) as case:
        check = case.run(check=True)
        assert check.exit_code == 1
        assert str(case.harness.home_agents / case.retired.source.name) in check.stdout
        reconciled = case.run()
        assert reconciled.exit_code == 0
        assert case.destination.read_bytes() == case.current.content
        assert not (case.harness.home_agents / case.retired.source.name).exists()
        assert case.foreign_destination.read_bytes() == case.foreign.content


def test_plugin_lifecycle_rejects_an_unrecorded_destination_without_mutation() -> None:
    with lifecycle_case(lifecycle_fixture("unrecorded.json")) as case:
        before = case.harness.snapshot(case.harness.home)
        result = case.run()
        assert result.exit_code == 2
        assert str(case.destination) in result.stdout
        assert result.home_snapshot == before


def test_plugin_lifecycle_rejects_an_uppercase_ownership_digest_without_mutation() -> (
    None
):
    with lifecycle_case(lifecycle_fixture("invalid_digest.json")) as case:
        before = case.harness.snapshot(case.harness.home)
        result = case.run()
        assert result.exit_code == 2
        assert AGENT_OWNERSHIP_DIGEST_FIELD in result.stdout
        assert "lowercase sha256 hex string" in result.stdout
        assert result.home_snapshot == before


def test_plugin_lifecycle_rejects_a_symlink_destination_without_mutation() -> None:
    with lifecycle_case(lifecycle_fixture("symlink.json")) as case:
        before = case.harness.snapshot(case.harness.home)
        result = case.run()
        assert result.exit_code == 2
        assert str(case.destination) in result.stdout
        assert result.home_snapshot == before
        assert case.external.read_bytes() == case.foreign.content


def test_plugin_lifecycle_reports_scope_splits_before_home_mutation() -> None:
    with lifecycle_case(lifecycle_fixture("scope_split.json")) as case:
        before = case.harness.snapshot(case.harness.home)
        result = case.run()
        assert result.exit_code == 2
        assert f"scope-split directed-removal: {case.scope_paths[0]}" in result.stdout
        for path in case.scope_paths[1:]:
            assert f"scope-split collision: {path}" in result.stdout
        assert result.home_snapshot == before


def test_a_lifecycle_run_adopts_an_identical_unrecorded_destination() -> None:
    with lifecycle_case(lifecycle_fixture("identical.json")) as case:
        identity = case.harness.file_identity(case.destination)
        result = case.run()
        assert result.exit_code == 0, result.stdout
        assert case.destination.read_bytes() == case.current.content
        assert case.harness.file_identity(case.destination) == identity
        assert case.harness.ownership_path.is_file()
        assert case.run(check=True).exit_code == 0


def test_a_write_destination_changed_after_preflight_stops_before_mutation() -> None:
    with lifecycle_case(lifecycle_fixture("write_race.json")) as case:
        result = case.run()
        assert result.exit_code == 2
        assert (
            f"collision: {case.destination} (changed after preflight)" in result.stdout
        )
        assert case.destination.read_bytes() == case.foreign.content
        assert not case.harness.ownership_path.exists()


def test_a_prune_destination_changed_after_preflight_stops_before_mutation() -> None:
    with lifecycle_case(lifecycle_fixture("prune_race.json")) as case:
        ownership = case.harness.ownership_path.read_bytes()
        result = case.run()
        assert result.exit_code == 2
        assert str(case.harness.home_agents / case.retired.source.name) in result.stdout
        assert (
            case.harness.home_agents / case.retired.source.name
        ).read_bytes() == case.foreign.content
        assert case.harness.ownership_path.read_bytes() == ownership


def test_a_malformed_ownership_record_still_reports_every_scope_split() -> None:
    with lifecycle_case(lifecycle_fixture("invalid_digest_and_scope.json")) as case:
        before = case.harness.snapshot(case.harness.home)
        result = case.run()
        assert result.exit_code == 2
        for path in case.scope_paths:
            assert str(path) in result.stdout
        assert "lowercase sha256 hex string" in result.stdout
        assert result.home_snapshot == before


def test_a_recorded_destination_that_is_a_directory_names_its_cause() -> None:
    with lifecycle_case(lifecycle_fixture("directory.json")) as case:
        before = case.harness.snapshot(case.harness.home)
        result = case.run()
        assert result.exit_code == 2
        assert f"collision: {case.destination} (not a regular file)" in result.stdout
        assert result.home_snapshot == before


def test_a_symlinked_agent_directory_still_reports_every_scope_split() -> None:
    with lifecycle_case(lifecycle_fixture("symlink_root_and_scope.json")) as case:
        result = case.run()
        assert result.exit_code == 2
        for path in case.scope_paths:
            assert str(path) in result.stdout
        assert str(case.harness.home_agents) in result.stdout
        assert "must not be a symlink" in result.stdout
        assert not (case.external / case.current.source.name).exists()
