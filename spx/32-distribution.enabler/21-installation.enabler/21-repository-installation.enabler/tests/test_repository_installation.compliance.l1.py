"""Ambient-state and repository-config evidence for installation."""

import hashlib
import json
from pathlib import Path

import pytest

from outcomeeng.distribution.installation import (
    CODEX_CONFIG_PATH,
    Operation,
    SourceAction,
)
from outcomeeng.validation.ci_gate import CODEX_API_KEY_ENVIRONMENT
from outcomeeng_testing.harnesses.installation import (
    RENAMED_CHECKOUT_AGENT_NAME,
    PluginLifecycleHarness,
    observe_agent_home_collision,
    observe_agent_home_reconciliation,
    observe_codex_config_independence,
    observe_codex_role_discovery,
    observe_failed_run_restore,
    observe_noncanonical_reconciliation,
    observe_scope_split,
    scrub_credential,
    skill_enabling_definition,
)


def test_plugin_lifecycle_places_owned_definitions_and_is_idempotent(
    tmp_path: Path,
) -> None:
    lifecycle = PluginLifecycleHarness.create(tmp_path, plugin_name="fixture")
    shipped = lifecycle.write_shipped(
        "fixture_auditor.toml", b'name = "fixture-auditor"\n'
    )

    before_check = lifecycle.snapshot(lifecycle.home)
    check = lifecycle.run(check=True)
    assert check.exit_code == 1
    assert f"write: {lifecycle.home_agents / shipped.name}" in check.stdout
    assert check.home_snapshot == before_check

    installed = lifecycle.run()
    assert installed.exit_code == 0
    destination = lifecycle.home_agents / shipped.name
    assert destination.read_bytes() == shipped.read_bytes()
    ownership = json.loads(lifecycle.ownership_path.read_text(encoding="utf-8"))
    assert ownership == {
        "entries": [
            {
                "destination": f"agents/{shipped.name}",
                "digest": hashlib.sha256(destination.read_bytes()).hexdigest(),
                "plugin": "fixture",
            }
        ],
        "schema_version": 1,
    }

    ownership_identity = lifecycle.file_identity(lifecycle.ownership_path)
    clean_check = lifecycle.run(check=True)
    repeated = lifecycle.run()
    assert clean_check.exit_code == 0
    assert repeated.exit_code == 0
    assert repeated.home_snapshot == installed.home_snapshot
    assert lifecycle.file_identity(lifecycle.ownership_path) == ownership_identity


def test_plugin_lifecycle_prunes_only_matching_owned_definitions(
    tmp_path: Path,
) -> None:
    lifecycle = PluginLifecycleHarness.create(tmp_path, plugin_name="fixture")
    current = lifecycle.write_shipped(
        "fixture_current.toml", b'name = "fixture-current"\n'
    )
    retired = lifecycle.write_shipped(
        "fixture_retired.toml", b'name = "fixture-retired"\n'
    )
    foreign = lifecycle.write_home(
        "developer-owned.toml", b'name = "developer-owned"\n'
    )
    assert lifecycle.run().exit_code == 0

    retired.unlink()
    check = lifecycle.run(check=True)
    assert check.exit_code == 1
    assert f"prune: {lifecycle.home_agents / retired.name}" in check.stdout

    reconciled = lifecycle.run()
    assert reconciled.exit_code == 0
    assert (lifecycle.home_agents / current.name).read_bytes() == current.read_bytes()
    assert not (lifecycle.home_agents / retired.name).exists()
    assert foreign.read_bytes() == b'name = "developer-owned"\n'


def test_plugin_lifecycle_rejects_an_unrecorded_destination_without_mutation(
    tmp_path: Path,
) -> None:
    lifecycle = PluginLifecycleHarness.create(tmp_path, plugin_name="fixture")
    shipped = lifecycle.write_shipped(
        "fixture_auditor.toml", b'name = "fixture-auditor"\n'
    )
    lifecycle.write_home(shipped.name, b'name = "foreign-definition"\n')
    before = lifecycle.snapshot(lifecycle.home)

    result = lifecycle.run()
    assert result.exit_code == 2
    assert f"collision: {lifecycle.home_agents / shipped.name}" in result.stdout
    assert result.home_snapshot == before


def test_plugin_lifecycle_rejects_a_non_hex_ownership_digest_without_mutation(
    tmp_path: Path,
) -> None:
    lifecycle = PluginLifecycleHarness.create(tmp_path, plugin_name="fixture")
    lifecycle.write_shipped("fixture_auditor.toml", b'name = "fixture-auditor"\n')
    lifecycle.write_ownership(
        {
            "schema_version": 1,
            "entries": [
                {
                    "destination": "agents/fixture_auditor.toml",
                    "plugin": "fixture",
                    "digest": "z" * 64,
                }
            ],
        }
    )
    before = lifecycle.snapshot(lifecycle.home)

    result = lifecycle.run()
    assert result.exit_code == 2
    assert "entry 0 digest" in result.stdout
    assert "is not a lowercase sha256 hex string" in result.stdout
    assert result.home_snapshot == before


def test_plugin_lifecycle_rejects_a_symlink_destination_without_mutation(
    tmp_path: Path,
) -> None:
    lifecycle = PluginLifecycleHarness.create(tmp_path / "case", plugin_name="fixture")
    shipped = lifecycle.write_shipped(
        "fixture_auditor.toml", b'name = "fixture-auditor"\n'
    )
    external = tmp_path / "external.toml"
    external.write_bytes(b'name = "external"\n')
    lifecycle.home_agents.mkdir(parents=True, exist_ok=True)
    (lifecycle.home_agents / shipped.name).symlink_to(external)
    before = lifecycle.snapshot(lifecycle.home)

    result = lifecycle.run()
    assert result.exit_code == 2
    assert f"collision: {lifecycle.home_agents / shipped.name}" in result.stdout
    assert result.home_snapshot == before
    assert external.read_bytes() == b'name = "external"\n'


def test_plugin_lifecycle_reports_scope_splits_before_home_mutation(
    tmp_path: Path,
) -> None:
    lifecycle = PluginLifecycleHarness.create(tmp_path, plugin_name="fixture")
    exact = lifecycle.write_shipped("fixture_exact.toml", b'name = "fixture-exact"\n')
    changed = lifecycle.write_shipped(
        "fixture_changed.toml", b'name = "fixture-changed"\n'
    )
    lifecycle.write_checkout(exact.name, exact.read_bytes())
    lifecycle.write_checkout(changed.name, changed.read_bytes() + b"# changed\n")
    renamed = lifecycle.write_checkout(
        RENAMED_CHECKOUT_AGENT_NAME,
        skill_enabling_definition(lifecycle.plugin_name),
    )
    before = lifecycle.snapshot(lifecycle.home)

    result = lifecycle.run()
    assert result.exit_code == 2
    assert (
        f"scope-split directed-removal: {lifecycle.checkout_agents / exact.name}"
        in result.stdout
    )
    assert (
        f"scope-split collision: {lifecycle.checkout_agents / changed.name}"
        in result.stdout
    )
    assert f"scope-split collision: {renamed}" in result.stdout
    assert result.home_snapshot == before


def test_persistent_installation_places_agents_in_the_selected_home() -> None:
    observation = observe_agent_home_reconciliation()

    assert set(observation.home_first) == (
        set(observation.home_initial) | set(observation.desired_first)
    )
    assert len(observation.home_first) == len(
        {name for name, _ in observation.home_first}
    )
    assert observation.ownership_record_present
    assert observation.foreign_first == observation.foreign_initial
    assert {path.name for path in observation.first_result.written} == {
        name for name, _ in observation.desired_first
    }


def test_catalog_reconciliation_prunes_only_stale_owned_agents() -> None:
    observation = observe_agent_home_reconciliation()
    retired = set(observation.desired_first) - set(observation.desired_second)

    assert len(retired) == 1
    assert set(observation.home_second) == (
        set(observation.home_initial) | set(observation.desired_second)
    )
    assert {path.name for path in observation.second_result.pruned} == {
        name for name, _ in retired
    }
    assert observation.foreign_second == observation.foreign_initial


def test_foreign_agent_collision_stops_before_any_mutation() -> None:
    observation = observe_agent_home_collision()

    assert observation.collisions
    assert observation.attempted
    assert all(
        command.operation in {Operation.MARKETPLACE_INSPECT, Operation.PLUGIN_INSPECT}
        for command in observation.attempted
    )
    assert observation.home_after == observation.home_before


def test_scope_split_reports_exact_and_changed_copies_before_mutation() -> None:
    observation = observe_scope_split()

    assert {entry.classification for entry in observation.entries} == {
        "directed-removal",
        "shadowing-collision",
    }
    assert len(observation.entries) == 4
    assert {
        entry.classification
        for entry in observation.entries
        if entry.path.name == RENAMED_CHECKOUT_AGENT_NAME
    } == {"shadowing-collision"}
    assert observation.attempted == ()
    assert observation.home_after == observation.home_before


def test_repository_codex_config_has_no_installation_semantics() -> None:
    observation = observe_codex_config_independence()

    assert observation.before.commands == observation.after.commands
    assert observation.before.claude_plugins == observation.after.claude_plugins
    assert observation.before.codex_plugins == observation.after.codex_plugins
    assert (
        observation.persistent_before.commands == observation.persistent_after.commands
    )
    assert (
        observation.persistent_before.codex_plugins
        == observation.persistent_after.codex_plugins
    )
    assert observation.config_observed == observation.config_written
    assert all(
        str(CODEX_CONFIG_PATH) not in argument
        for plan in (observation.after, observation.persistent_after)
        for command in plan.commands
        for argument in command.argv
    )


def test_restoring_the_selection_keeps_the_reconciled_marketplace_source() -> None:
    observation = observe_noncanonical_reconciliation()

    assert observation.source_action is SourceAction.REPLACE
    assert observation.selection_after == observation.selection_before
    assert observation.marketplace_before != observation.canonical_marketplace
    assert observation.marketplace_after == observation.canonical_marketplace


def test_failed_persistent_run_restores_the_committed_selection() -> None:
    observation = observe_failed_run_restore(Operation.PLUGIN_ENABLE)

    assert observation.failure is not None
    assert observation.settings_after == observation.settings_before
    assert observation.attempted[-1].operation is observation.failed_operation


def test_a_write_destination_changed_after_preflight_stops_before_mutation(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    lifecycle = PluginLifecycleHarness.create(tmp_path, plugin_name="fixture")
    shipped = lifecycle.write_shipped("fixture_auditor.toml", b'name = "auditor"\n')
    module = lifecycle.load_module()
    destination = lifecycle.home_agents / shipped.name
    observed = module._current_digest
    calls: dict[Path, int] = {}

    def concurrent_writer(path: Path) -> str | None:
        calls[path] = calls.get(path, 0) + 1
        if path == destination and calls[path] == 2:
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(b"foreign concurrent content\n")
        return observed(path)

    # Controlled digest reader under `/test` Stage 5 exception 3 (Time and
    # concurrency): a writer racing the run between preflight and mutation
    # cannot be scheduled deterministically against the real filesystem.
    exit_code = module.main(
        ["--home", str(lifecycle.home), "--checkout", str(lifecycle.checkout)],
        current_digest=concurrent_writer,
    )

    assert exit_code == 2
    assert (
        f"collision: {destination} (changed after preflight)" in capsys.readouterr().out
    )
    assert destination.read_bytes() == b"foreign concurrent content\n"
    assert not lifecycle.ownership_path.exists()


def test_a_prune_destination_changed_after_preflight_stops_before_mutation(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    lifecycle = PluginLifecycleHarness.create(tmp_path, plugin_name="fixture")
    retired = b'name = "retired"\n'
    stale = lifecycle.write_home("fixture_retired.toml", retired)
    lifecycle.write_ownership(
        {
            "schema_version": 1,
            "entries": [
                {
                    "destination": "agents/fixture_retired.toml",
                    "plugin": "fixture",
                    "digest": hashlib.sha256(retired).hexdigest(),
                }
            ],
        }
    )
    module = lifecycle.load_module()
    observed = module._current_digest
    calls: dict[Path, int] = {}

    def concurrent_writer(path: Path) -> str | None:
        calls[path] = calls.get(path, 0) + 1
        if path == stale and calls[path] == 2:
            stale.write_bytes(b"edited while the run was planning\n")
        return observed(path)

    # Controlled digest reader under `/test` Stage 5 exception 3 (Time and
    # concurrency): a writer racing the run between preflight and mutation
    # cannot be scheduled deterministically against the real filesystem.
    exit_code = module.main(
        ["--home", str(lifecycle.home), "--checkout", str(lifecycle.checkout)],
        current_digest=concurrent_writer,
    )

    assert exit_code == 2
    assert f"collision: {stale} (changed after preflight)" in capsys.readouterr().out
    assert stale.read_bytes() == b"edited while the run was planning\n"


def test_a_missing_probe_credential_fails_loudly_before_any_agent_process(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(CODEX_API_KEY_ENVIRONMENT, raising=False)

    with pytest.raises(RuntimeError, match="required credential"):
        observe_codex_role_discovery()


def test_scrubbing_replaces_every_credential_occurrence() -> None:
    credential = "sk-fake-credential-0123456789"
    text = f"login failed: key {credential} rejected\ntail {credential}"

    scrubbed = scrub_credential(text, credential)

    assert credential not in scrubbed
    assert scrubbed.count("[REDACTED-CREDENTIAL]") == 2
    assert scrub_credential("no secret here", credential) == "no secret here"


def test_a_malformed_ownership_record_still_reports_every_scope_split(
    tmp_path: Path,
) -> None:
    lifecycle = PluginLifecycleHarness.create(tmp_path, plugin_name="fixture")
    exact = lifecycle.write_shipped("fixture_exact.toml", b'name = "fixture-exact"\n')
    lifecycle.write_checkout(exact.name, exact.read_bytes())
    lifecycle.write_ownership(
        {
            "schema_version": 1,
            "entries": [
                {
                    "destination": "agents/fixture_exact.toml",
                    "plugin": "fixture",
                    "digest": "z" * 64,
                }
            ],
        }
    )
    before = lifecycle.snapshot(lifecycle.home)

    result = lifecycle.run()

    assert result.exit_code == 2
    assert (
        f"scope-split directed-removal: {lifecycle.checkout_agents / exact.name}"
        in result.stdout
    )
    assert "is not a lowercase sha256 hex string" in result.stdout
    assert result.home_snapshot == before


def test_a_recorded_destination_that_is_a_directory_names_its_cause(
    tmp_path: Path,
) -> None:
    lifecycle = PluginLifecycleHarness.create(tmp_path, plugin_name="fixture")
    content = b'name = "fixture-auditor"\n'
    shipped = lifecycle.write_shipped("fixture_auditor.toml", content)
    destination = lifecycle.home_agents / shipped.name
    destination.mkdir(parents=True)
    lifecycle.write_ownership(
        {
            "schema_version": 1,
            "entries": [
                {
                    "destination": f"agents/{shipped.name}",
                    "plugin": "fixture",
                    "digest": hashlib.sha256(content).hexdigest(),
                }
            ],
        }
    )
    before = lifecycle.snapshot(lifecycle.home)

    result = lifecycle.run()

    assert result.exit_code == 2
    assert f"collision: {destination} (not a regular file)" in result.stdout
    assert result.home_snapshot == before


def test_a_symlinked_agent_directory_still_reports_every_scope_split(
    tmp_path: Path,
) -> None:
    lifecycle = PluginLifecycleHarness.create(tmp_path / "case", plugin_name="fixture")
    exact = lifecycle.write_shipped("fixture_exact.toml", b'name = "fixture-exact"\n')
    lifecycle.write_checkout(exact.name, exact.read_bytes())
    real_agents = tmp_path / "real-agents"
    real_agents.mkdir()
    lifecycle.home.mkdir(parents=True, exist_ok=True)
    lifecycle.home_agents.symlink_to(real_agents)

    result = lifecycle.run()

    assert result.exit_code == 2
    assert (
        f"scope-split directed-removal: {lifecycle.checkout_agents / exact.name}"
        in result.stdout
    )
    assert (
        f"collision: selected agent directory {lifecycle.home_agents} "
        "must not be a symlink" in result.stdout
    )
    assert not (real_agents / exact.name).exists()
