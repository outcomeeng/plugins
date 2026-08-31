"""Ambient-state and repository-config evidence for installation."""

import hashlib
import json
from pathlib import Path

import pytest

from outcomeeng.distribution.installation import (
    AGENT_OWNERSHIP_DESTINATION_FIELD,
    AGENT_OWNERSHIP_DIGEST_FIELD,
    AGENT_OWNERSHIP_ENTRIES_FIELD,
    AGENT_OWNERSHIP_PLUGIN_FIELD,
    AGENT_OWNERSHIP_SCHEMA_FIELD,
    AGENT_OWNERSHIP_SCHEMA_VERSION,
    CODEX_CONFIG_PATH,
    Operation,
    SourceAction,
)
from outcomeeng_testing.generators.installation import (
    generated_codex_login_payload,
    generated_codex_login_payload_with_metadata,
    generated_unknown_codex_login_payload,
)
from outcomeeng_testing.harnesses.installation import (
    CODEX_CREDENTIAL_TOKEN_FIELDS,
    CODEX_TOKEN_METADATA_FIELDS,
    CodexRoleDiscoveryHarness,
    RoleDiscoveryCredentialSurface,
    observe_interrupted_reconciliation,
    ScopeSplitClassification,
    racing_digest_reader,
    RENAMED_CHECKOUT_AGENT_NAME,
    PluginLifecycleHarness,
    observe_agent_home_collision,
    observe_agent_home_reconciliation,
    observe_codex_config_independence,
    observe_failed_run_restore,
    observe_noncanonical_reconciliation,
    observe_scope_split,
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
        AGENT_OWNERSHIP_ENTRIES_FIELD: [
            {
                AGENT_OWNERSHIP_DESTINATION_FIELD: f"agents/{shipped.name}",
                AGENT_OWNERSHIP_DIGEST_FIELD: hashlib.sha256(
                    destination.read_bytes()
                ).hexdigest(),
                AGENT_OWNERSHIP_PLUGIN_FIELD: "fixture",
            }
        ],
        AGENT_OWNERSHIP_SCHEMA_FIELD: AGENT_OWNERSHIP_SCHEMA_VERSION,
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
            AGENT_OWNERSHIP_SCHEMA_FIELD: AGENT_OWNERSHIP_SCHEMA_VERSION,
            AGENT_OWNERSHIP_ENTRIES_FIELD: [
                {
                    AGENT_OWNERSHIP_DESTINATION_FIELD: "agents/fixture_auditor.toml",
                    AGENT_OWNERSHIP_PLUGIN_FIELD: "fixture",
                    AGENT_OWNERSHIP_DIGEST_FIELD: "z" * 64,
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


def test_an_interrupted_run_is_adopted_cleanly_on_rerun() -> None:
    observation = observe_interrupted_reconciliation()

    assert observation.first_result.collisions == ()
    assert observation.second_result.collisions == ()
    assert observation.second_result.written == ()
    assert observation.second_result.pruned == ()
    assert observation.home_second == observation.home_first
    assert observation.record_present_after


def test_a_lifecycle_run_adopts_an_identical_unrecorded_destination(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    lifecycle = PluginLifecycleHarness.create(tmp_path, plugin_name="fixture")
    content = b'name = "auditor"\n'
    shipped = lifecycle.write_shipped("fixture_auditor.toml", content)
    lifecycle.write_home(shipped.name, content)

    run = lifecycle.run()

    assert run.exit_code == 0, run.stdout + run.stderr
    assert "collision" not in run.stdout
    assert (lifecycle.home_agents / shipped.name).read_bytes() == content
    assert lifecycle.ownership_path.is_file()
    check = lifecycle.run(check=True)
    assert check.exit_code == 0, check.stdout + check.stderr


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
        ScopeSplitClassification.DIRECTED_REMOVAL,
        ScopeSplitClassification.SHADOWING_COLLISION,
    }
    assert len(observation.entries) == 4
    assert {
        entry.classification
        for entry in observation.entries
        if entry.path.name == RENAMED_CHECKOUT_AGENT_NAME
    } == {ScopeSplitClassification.SHADOWING_COLLISION}
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

    def inject() -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(b"foreign concurrent content\n")

    exit_code = module.main(
        ["--home", str(lifecycle.home), "--checkout", str(lifecycle.checkout)],
        current_digest=racing_digest_reader(
            destination, inject, module._current_digest
        ),
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
            AGENT_OWNERSHIP_SCHEMA_FIELD: AGENT_OWNERSHIP_SCHEMA_VERSION,
            AGENT_OWNERSHIP_ENTRIES_FIELD: [
                {
                    AGENT_OWNERSHIP_DESTINATION_FIELD: "agents/fixture_retired.toml",
                    AGENT_OWNERSHIP_PLUGIN_FIELD: "fixture",
                    AGENT_OWNERSHIP_DIGEST_FIELD: hashlib.sha256(retired).hexdigest(),
                }
            ],
        }
    )
    module = lifecycle.load_module()

    def inject() -> None:
        stale.write_bytes(b"edited while the run was planning\n")

    exit_code = module.main(
        ["--home", str(lifecycle.home), "--checkout", str(lifecycle.checkout)],
        current_digest=racing_digest_reader(stale, inject, module._current_digest),
    )

    assert exit_code == 2
    assert f"collision: {stale} (changed after preflight)" in capsys.readouterr().out
    assert stale.read_bytes() == b"edited while the run was planning\n"


def test_missing_selected_codex_login_state_fails_before_any_agent_process(
    tmp_path: Path,
) -> None:
    harness = CodexRoleDiscoveryHarness.without_login(tmp_path)

    with pytest.raises(RuntimeError, match="required Codex login state"):
        harness.observe()

    assert harness.commands == ()


@pytest.mark.parametrize("credential_field", sorted(CODEX_CREDENTIAL_TOKEN_FIELDS))
def test_role_discovery_rejects_each_known_credential_in_a_captured_stream(
    tmp_path: Path,
    credential_field: str,
) -> None:
    login = generated_codex_login_payload(credential_field)
    harness = CodexRoleDiscoveryHarness.with_captured_stream(
        tmp_path,
        login_payload=login.text,
        stream_text=login.credential,
    )

    with pytest.raises(RuntimeError, match="login material appeared"):
        harness.observe()

    assert len(harness.commands) == 1


@pytest.mark.parametrize("credential_field", sorted(CODEX_CREDENTIAL_TOKEN_FIELDS))
def test_role_discovery_rejects_each_known_credential_in_timeout_output(
    tmp_path: Path,
    credential_field: str,
) -> None:
    login = generated_codex_login_payload(credential_field)
    harness = CodexRoleDiscoveryHarness.with_timeout_stream(
        tmp_path,
        login_payload=login.text,
        stream_text=login.credential,
    )

    with pytest.raises(RuntimeError, match="login material appeared"):
        harness.observe()

    assert len(harness.commands) == 2


@pytest.mark.parametrize(
    "surface",
    tuple(RoleDiscoveryCredentialSurface),
)
@pytest.mark.parametrize("credential_field", sorted(CODEX_CREDENTIAL_TOKEN_FIELDS))
def test_role_discovery_rejects_credentials_across_session_process_surfaces(
    tmp_path: Path,
    credential_field: str,
    surface: RoleDiscoveryCredentialSurface,
) -> None:
    login = generated_codex_login_payload(credential_field)
    harness = CodexRoleDiscoveryHarness.with_session_credential_surface(
        tmp_path,
        login_payload=login.text,
        credential=login.credential,
        surface=surface,
    )

    with pytest.raises(RuntimeError, match="login material appeared"):
        harness.observe()

    assert len(harness.commands) == 3


def test_role_discovery_rejects_an_unknown_token_field_as_a_credential(
    tmp_path: Path,
) -> None:
    login = generated_unknown_codex_login_payload()
    harness = CodexRoleDiscoveryHarness.with_captured_stream(
        tmp_path,
        login_payload=login.text,
        stream_text=login.credential,
    )

    with pytest.raises(RuntimeError, match="login material appeared"):
        harness.observe()

    assert len(harness.commands) == 1


def test_role_discovery_rejects_a_nested_unknown_token_credential(
    tmp_path: Path,
) -> None:
    login = generated_unknown_codex_login_payload(nested=True)
    harness = CodexRoleDiscoveryHarness.with_captured_stream(
        tmp_path,
        login_payload=login.text,
        stream_text=login.credential,
    )

    with pytest.raises(RuntimeError, match="login material appeared"):
        harness.observe()

    assert len(harness.commands) == 1


@pytest.mark.parametrize("metadata_field", sorted(CODEX_TOKEN_METADATA_FIELDS))
def test_role_discovery_allows_each_token_metadata_field_in_captured_output(
    tmp_path: Path,
    metadata_field: str,
) -> None:
    login = generated_codex_login_payload_with_metadata(
        CODEX_CREDENTIAL_TOKEN_FIELDS,
        metadata_field,
    )
    harness = CodexRoleDiscoveryHarness.with_captured_stream(
        tmp_path,
        login_payload=login.text,
        stream_text=login.metadata_value,
    )

    observation = harness.observe()

    assert login.metadata_value in observation.install_stdout
    assert len(harness.commands) == 3


def test_a_malformed_ownership_record_still_reports_every_scope_split(
    tmp_path: Path,
) -> None:
    lifecycle = PluginLifecycleHarness.create(tmp_path, plugin_name="fixture")
    exact = lifecycle.write_shipped("fixture_exact.toml", b'name = "fixture-exact"\n')
    lifecycle.write_checkout(exact.name, exact.read_bytes())
    lifecycle.write_ownership(
        {
            AGENT_OWNERSHIP_SCHEMA_FIELD: AGENT_OWNERSHIP_SCHEMA_VERSION,
            AGENT_OWNERSHIP_ENTRIES_FIELD: [
                {
                    AGENT_OWNERSHIP_DESTINATION_FIELD: "agents/fixture_exact.toml",
                    AGENT_OWNERSHIP_PLUGIN_FIELD: "fixture",
                    AGENT_OWNERSHIP_DIGEST_FIELD: "z" * 64,
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
            AGENT_OWNERSHIP_SCHEMA_FIELD: AGENT_OWNERSHIP_SCHEMA_VERSION,
            AGENT_OWNERSHIP_ENTRIES_FIELD: [
                {
                    AGENT_OWNERSHIP_DESTINATION_FIELD: f"agents/{shipped.name}",
                    AGENT_OWNERSHIP_PLUGIN_FIELD: "fixture",
                    AGENT_OWNERSHIP_DIGEST_FIELD: hashlib.sha256(content).hexdigest(),
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
