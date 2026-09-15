"""Ambient-state and repository-config evidence for installation."""

import hashlib
import json
import subprocess
from pathlib import Path

import pytest

from outcomeeng.distribution.installation import (
    Agent,
    CLAUDE_LOCAL_SCOPE,
    CODEX_CONFIG_PATH,
    SPEC_TREE_PLUGIN,
    Operation,
    SourceAction,
)
from outcomeeng.validation.ci_gate import CODEX_API_KEY_ENVIRONMENT
from outcomeeng_testing.harnesses.discovery_auth import (
    API_LOGIN_FLAG,
    WORKSPACE_LOGIN_FLAG,
    AUTH_FILENAME,
    CREDENTIAL_ENVIRONMENTS,
    REDACTED_CREDENTIAL,
    SAVED_LOGIN_ACCOUNT_FIELD,
    SAVED_LOGIN_TOKENS_FIELD,
    AuthenticationMode,
    DiscoveryAuthentication,
    DiscoveryAuthenticationError,
    select_authentication,
)
from outcomeeng_testing.harnesses.discovery_auth_cases import (
    NativeFault,
    SavedLoginFault,
    SESSION_COMMAND,
    authentication_case,
    ci_without_authentication_mode,
    dispose_authenticated_home,
    invalid_saved_login,
    lock_contention_case,
    missing_credential_environment,
)
from outcomeeng_testing.harnesses.installation import (
    CONCURRENT_EDIT_CONTENT,
    EXTERNAL_DEFINITION_CONTENT,
    FOREIGN_DEFINITION_CONTENT,
    MALFORMED_OWNERSHIP_DIGEST,
    NONCANONICAL_MARKETPLACE_SOURCE,
    UNOWNED_AGENT_CONTENT,
    UNOWNED_AGENT_FILENAME,
    observe_designated_failure,
    observe_interrupted_reconciliation,
    observe_local_record_bootstrap_plan,
    observe_persistent_execution,
    observe_persistent_plan,
    ScopeSplitClassification,
    racing_digest_reader,
    RENAMED_CHECKOUT_AGENT_NAME,
    PluginLifecycleHarness,
    observe_agent_home_collision,
    observe_agent_home_reconciliation,
    observe_codex_config_independence,
    observe_codex_subagent_discovery,
    observe_failed_run_restore,
    observe_noncanonical_reconciliation,
    observe_scope_split,
    skill_enabling_definition,
)


def test_plugin_lifecycle_places_owned_definitions_and_is_idempotent(
    tmp_path: Path,
) -> None:
    lifecycle = PluginLifecycleHarness.create(tmp_path, plugin_name="fixture")
    module = lifecycle.load_module()
    shipped = lifecycle.ship("auditor")

    before_check = lifecycle.snapshot(lifecycle.home)
    check = lifecycle.run(check=True)
    assert check.exit_code == 1
    assert f"{module.WRITE_PREFIX}{lifecycle.home_agents / shipped.name}" in (
        check.stdout
    )
    assert check.home_snapshot == before_check

    installed = lifecycle.run()
    assert installed.exit_code == 0
    destination = lifecycle.home_agents / shipped.name
    assert destination.read_bytes() == shipped.read_bytes()
    ownership = json.loads(lifecycle.ownership_path.read_text(encoding="utf-8"))
    assert ownership == lifecycle.ownership_document(
        lifecycle.ownership_entry(
            shipped.name, hashlib.sha256(destination.read_bytes()).hexdigest()
        )
    )

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
    module = lifecycle.load_module()
    current = lifecycle.ship("current")
    retired = lifecycle.ship("retired")
    foreign = lifecycle.write_home(
        UNOWNED_AGENT_FILENAME, UNOWNED_AGENT_CONTENT.encode()
    )
    assert lifecycle.run().exit_code == 0

    retired.unlink()
    check = lifecycle.run(check=True)
    assert check.exit_code == 1
    assert f"{module.PRUNE_PREFIX}{lifecycle.home_agents / retired.name}" in (
        check.stdout
    )

    reconciled = lifecycle.run()
    assert reconciled.exit_code == 0
    assert (lifecycle.home_agents / current.name).read_bytes() == current.read_bytes()
    assert not (lifecycle.home_agents / retired.name).exists()
    assert foreign.read_bytes() == UNOWNED_AGENT_CONTENT.encode()


def test_plugin_lifecycle_rejects_an_unrecorded_destination_without_mutation(
    tmp_path: Path,
) -> None:
    lifecycle = PluginLifecycleHarness.create(tmp_path, plugin_name="fixture")
    module = lifecycle.load_module()
    shipped = lifecycle.ship("auditor")
    lifecycle.write_home(shipped.name, FOREIGN_DEFINITION_CONTENT)
    before = lifecycle.snapshot(lifecycle.home)

    result = lifecycle.run()
    assert result.exit_code == 2
    assert f"{module.COLLISION_PREFIX}{lifecycle.home_agents / shipped.name}" in (
        result.stdout
    )
    assert result.home_snapshot == before


def test_plugin_lifecycle_rejects_a_non_hex_ownership_digest_without_mutation(
    tmp_path: Path,
) -> None:
    lifecycle = PluginLifecycleHarness.create(tmp_path, plugin_name="fixture")
    module = lifecycle.load_module()
    shipped = lifecycle.ship("auditor")
    lifecycle.write_ownership(
        lifecycle.ownership_document(
            lifecycle.ownership_entry(shipped.name, MALFORMED_OWNERSHIP_DIGEST)
        )
    )
    before = lifecycle.snapshot(lifecycle.home)

    result = lifecycle.run()
    assert result.exit_code == 2
    assert module.NON_HEX_DIGEST in result.stdout
    assert result.home_snapshot == before


def test_plugin_lifecycle_rejects_a_symlink_destination_without_mutation(
    tmp_path: Path,
) -> None:
    lifecycle = PluginLifecycleHarness.create(tmp_path / "case", plugin_name="fixture")
    module = lifecycle.load_module()
    shipped = lifecycle.ship("auditor")
    external = tmp_path / "external.toml"
    external.write_bytes(EXTERNAL_DEFINITION_CONTENT)
    lifecycle.home_agents.mkdir(parents=True, exist_ok=True)
    (lifecycle.home_agents / shipped.name).symlink_to(external)
    before = lifecycle.snapshot(lifecycle.home)

    result = lifecycle.run()
    assert result.exit_code == 2
    assert f"{module.COLLISION_PREFIX}{lifecycle.home_agents / shipped.name}" in (
        result.stdout
    )
    assert result.home_snapshot == before
    assert external.read_bytes() == EXTERNAL_DEFINITION_CONTENT


def test_plugin_lifecycle_reports_scope_splits_before_home_mutation(
    tmp_path: Path,
) -> None:
    lifecycle = PluginLifecycleHarness.create(tmp_path, plugin_name="fixture")
    module = lifecycle.load_module()
    exact = lifecycle.ship("exact")
    changed = lifecycle.ship("changed")
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
        f"{module.SCOPE_SPLIT_REMOVAL_PREFIX}{lifecycle.checkout_agents / exact.name}"
        in result.stdout
    )
    assert (
        f"{module.SCOPE_SPLIT_COLLISION_PREFIX}"
        f"{lifecycle.checkout_agents / changed.name}" in result.stdout
    )
    assert f"{module.SCOPE_SPLIT_COLLISION_PREFIX}{renamed}" in result.stdout
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
    module = lifecycle.load_module()
    content = lifecycle.definition_content("auditor")
    shipped = lifecycle.ship("auditor")
    lifecycle.write_home(shipped.name, content)

    run = lifecycle.run()

    assert run.exit_code == 0, run.stdout + run.stderr
    assert module.COLLISION_PREFIX not in run.stdout
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
    observation = observe_failed_run_restore(Operation.PLUGIN_UPDATE)

    assert observation.failure is not None
    assert observation.settings_after == observation.settings_before
    assert observation.attempted[-1].operation is observation.failed_operation


def test_a_write_destination_changed_after_preflight_stops_before_mutation(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    lifecycle = PluginLifecycleHarness.create(tmp_path, plugin_name="fixture")
    shipped = lifecycle.ship("auditor")
    module = lifecycle.load_module()
    destination = lifecycle.home_agents / shipped.name

    def inject() -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(CONCURRENT_EDIT_CONTENT)

    exit_code = module.main(
        ["--home", str(lifecycle.home), "--checkout", str(lifecycle.checkout)],
        current_digest=racing_digest_reader(
            destination, inject, module._current_digest
        ),
    )

    assert exit_code == 2
    assert (
        f"{module.COLLISION_PREFIX}{destination} "
        f"({module.CAUSE_CHANGED_AFTER_PREFLIGHT})" in capsys.readouterr().out
    )
    assert destination.read_bytes() == CONCURRENT_EDIT_CONTENT
    assert not lifecycle.ownership_path.exists()


def test_a_prune_destination_changed_after_preflight_stops_before_mutation(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    lifecycle = PluginLifecycleHarness.create(tmp_path, plugin_name="fixture")
    retired = lifecycle.definition_content("retired")
    stale = lifecycle.write_home(lifecycle.definition_name("retired"), retired)
    lifecycle.write_ownership(
        lifecycle.ownership_document(
            lifecycle.ownership_entry(stale.name, hashlib.sha256(retired).hexdigest())
        )
    )
    module = lifecycle.load_module()

    def inject() -> None:
        stale.write_bytes(CONCURRENT_EDIT_CONTENT)

    exit_code = module.main(
        ["--home", str(lifecycle.home), "--checkout", str(lifecycle.checkout)],
        current_digest=racing_digest_reader(stale, inject, module._current_digest),
    )

    assert exit_code == 2
    assert (
        f"{module.COLLISION_PREFIX}{stale} ({module.CAUSE_CHANGED_AFTER_PREFLIGHT})"
        in capsys.readouterr().out
    )
    assert stale.read_bytes() == CONCURRENT_EDIT_CONTENT


def test_a_missing_probe_credential_fails_before_any_agent_process() -> None:
    with pytest.raises(DiscoveryAuthenticationError, match=CODEX_API_KEY_ENVIRONMENT):
        observe_codex_subagent_discovery(
            environment=missing_credential_environment(AuthenticationMode.API)
        )


def test_subscription_refresh_writes_through_only_the_saved_login_link() -> None:
    with authentication_case() as case:
        with case.auth.authenticated_home(
            case.home, cwd=case.home, env=case.environment
        ):
            assert (case.home / AUTH_FILENAME).is_symlink()
            assert (case.home / AUTH_FILENAME).resolve() == case.saved
            result = case.auth.run(SESSION_COMMAND, cwd=case.home, env=case.environment)
        assert case.saved.read_text() == case.refreshed
        assert case.initial != case.refreshed
        assert all(
            call.home != case.home or "login" not in call.argv
            for call in case.runner.calls
        )
        assert all("logout" not in call.argv for call in case.runner.calls)
        assert all(
            not (set(call.environment) & CREDENTIAL_ENVIRONMENTS)
            for call in case.runner.calls
        )
        assert all(
            token not in result.stdout + result.stderr
            for token in json.loads(case.refreshed)[SAVED_LOGIN_TOKENS_FIELD].values()
        )
        assert REDACTED_CREDENTIAL in result.stdout


def test_incompatible_native_writer_never_receives_the_saved_login() -> None:
    with authentication_case(fault=NativeFault.INCOMPATIBLE_WRITER) as case:
        with pytest.raises(DiscoveryAuthenticationError):
            with case.auth.authenticated_home(
                case.home, cwd=case.home, env=case.environment
            ):
                pytest.fail("incompatible writer reached saved-login use")
        assert case.saved.read_text() == case.initial
        assert not (case.home / AUTH_FILENAME).exists()
        assert all(call.home != case.home for call in case.runner.calls)


def test_replacing_the_saved_file_fails_without_restoring_old_credentials() -> None:
    with authentication_case(fault=NativeFault.REPLACE_FILE) as case:
        with pytest.raises(DiscoveryAuthenticationError):
            with case.auth.authenticated_home(
                case.home, cwd=case.home, env=case.environment
            ):
                case.auth.run(SESSION_COMMAND, cwd=case.home, env=case.environment)
        assert case.saved.read_text() == case.refreshed


def test_replacing_the_link_fails_without_overwriting_the_saved_file() -> None:
    with authentication_case(fault=NativeFault.REPLACE_LINK) as case:
        with pytest.raises(DiscoveryAuthenticationError):
            with case.auth.authenticated_home(
                case.home, cwd=case.home, env=case.environment
            ):
                case.auth.run(SESSION_COMMAND, cwd=case.home, env=case.environment)
        assert (case.home / AUTH_FILENAME).read_text() == case.refreshed
        assert case.saved.read_text() == case.initial


def test_switching_account_fails_without_restoring_the_previous_account() -> None:
    with authentication_case(fault=NativeFault.SWITCH_ACCOUNT) as case:
        with pytest.raises(DiscoveryAuthenticationError):
            with case.auth.authenticated_home(
                case.home, cwd=case.home, env=case.environment
            ):
                case.auth.run(SESSION_COMMAND, cwd=case.home, env=case.environment)
        assert (
            json.loads(case.saved.read_text())[SAVED_LOGIN_TOKENS_FIELD][
                SAVED_LOGIN_ACCOUNT_FIELD
            ]
            != json.loads(case.initial)[SAVED_LOGIN_TOKENS_FIELD][
                SAVED_LOGIN_ACCOUNT_FIELD
            ]
        )


def test_timeout_capture_scrubs_credentials_after_native_rotation() -> None:
    with authentication_case(fault=NativeFault.TIMEOUT) as case:
        with pytest.raises(subprocess.TimeoutExpired) as raised:
            with case.auth.authenticated_home(
                case.home, cwd=case.home, env=case.environment
            ):
                case.auth.run(SESSION_COMMAND, cwd=case.home, env=case.environment)
        assert all(
            token.encode()
            not in (raised.value.output or b"") + (raised.value.stderr or b"")
            for token in json.loads(case.refreshed)[SAVED_LOGIN_TOKENS_FIELD].values()
        )
        assert REDACTED_CREDENTIAL.encode() in (raised.value.output or b"")
        assert case.saved.read_text() == case.refreshed


def test_api_mode_uses_only_stdin_and_the_disposable_home() -> None:
    with authentication_case(AuthenticationMode.API) as case:
        with case.auth.authenticated_home(
            case.home, cwd=case.home, env=case.environment
        ):
            assert case.runner.calls[-1].input_text == case.auth.selection.credential
            assert case.runner.calls[-1].home == case.home
            assert case.auth.selection.credential not in case.runner.calls[-1].argv
            assert not (
                set(case.runner.calls[-1].environment) & CREDENTIAL_ENVIRONMENTS
            )
        assert case.saved.read_text() == case.initial


def test_workspace_mode_requires_its_own_credential_without_api_fallback() -> None:
    with pytest.raises(DiscoveryAuthenticationError):
        select_authentication(
            missing_credential_environment(AuthenticationMode.WORKSPACE_TOKEN)
        )


def test_local_default_reuses_subscription_despite_other_available_credentials() -> (
    None
):
    with authentication_case(explicit_mode=False) as case:
        assert case.auth.selection.mode is AuthenticationMode.SUBSCRIPTION
        assert case.auth.selection.saved_login == case.saved
        assert case.auth.selection.credential is None


def test_ci_requires_an_explicit_authentication_mode() -> None:
    with pytest.raises(DiscoveryAuthenticationError):
        select_authentication(ci_without_authentication_mode())


def test_workspace_login_uses_its_native_stdin_mechanism() -> None:
    with authentication_case(AuthenticationMode.WORKSPACE_TOKEN) as case:
        with case.auth.authenticated_home(
            case.home, cwd=case.home, env=case.environment
        ):
            assert WORKSPACE_LOGIN_FLAG in case.runner.calls[-1].argv
            assert API_LOGIN_FLAG not in case.runner.calls[-1].argv
            assert case.runner.calls[-1].input_text == case.auth.selection.credential
            assert not (
                set(case.runner.calls[-1].environment) & CREDENTIAL_ENVIRONMENTS
            )
        assert case.saved.read_text() == case.initial


def test_failed_login_stops_before_session_execution_and_scrubs_the_error() -> None:
    with authentication_case(
        AuthenticationMode.API, fault=NativeFault.LOGIN_FAILURE
    ) as case:
        with pytest.raises(DiscoveryAuthenticationError) as raised:
            with case.auth.authenticated_home(
                case.home, cwd=case.home, env=case.environment
            ):
                pytest.fail("failed login reached session execution")
        assert all("exec" not in call.argv for call in case.runner.calls)
        assert case.auth.selection.credential not in str(raised.value)
        assert REDACTED_CREDENTIAL in str(raised.value)


def test_failed_installation_stops_before_credentials_are_attached() -> None:
    with authentication_case(fault=NativeFault.INSTALL_FAILURE) as case:
        with pytest.raises(DiscoveryAuthenticationError):
            observe_codex_subagent_discovery(
                environment=case.original_environment, runner=case.runner
            )
        assert all(call.argv[0] == "just" for call in case.runner.calls)
        assert case.saved.read_text() == case.initial


def test_saved_login_contention_times_out_before_linking_credentials() -> None:
    with lock_contention_case() as case:
        with pytest.raises(DiscoveryAuthenticationError):
            with case.auth.authenticated_home(
                case.home, cwd=case.home, env=case.environment
            ):
                pytest.fail(
                    "credential use started while another verifier held the file"
                )
        assert not (case.home / AUTH_FILENAME).is_symlink()
        assert case.saved.read_text() == case.initial
        assert all("exec" not in call.argv for call in case.runner.calls)


@pytest.mark.parametrize("fault", list(SavedLoginFault), ids=str)
def test_invalid_saved_login_fails_before_any_native_command(
    fault: SavedLoginFault,
) -> None:
    with invalid_saved_login(fault) as case:
        with pytest.raises(DiscoveryAuthenticationError):
            DiscoveryAuthentication(
                select_authentication(case.original_environment), case.runner
            )
        assert case.runner.calls == []


def test_disposable_cleanup_preserves_native_refresh_in_the_saved_file() -> None:
    with authentication_case() as case:
        with case.auth.authenticated_home(
            case.home, cwd=case.home, env=case.environment
        ):
            case.auth.run(SESSION_COMMAND, cwd=case.home, env=case.environment)
        dispose_authenticated_home(case)
        assert not case.home.exists()
        assert case.saved.read_text() == case.refreshed


def test_a_malformed_ownership_record_still_reports_every_scope_split(
    tmp_path: Path,
) -> None:
    lifecycle = PluginLifecycleHarness.create(tmp_path, plugin_name="fixture")
    module = lifecycle.load_module()
    exact = lifecycle.ship("exact")
    lifecycle.write_checkout(exact.name, exact.read_bytes())
    lifecycle.write_ownership(
        lifecycle.ownership_document(
            lifecycle.ownership_entry(exact.name, MALFORMED_OWNERSHIP_DIGEST)
        )
    )
    before = lifecycle.snapshot(lifecycle.home)

    result = lifecycle.run()

    assert result.exit_code == 2
    assert (
        f"{module.SCOPE_SPLIT_REMOVAL_PREFIX}{lifecycle.checkout_agents / exact.name}"
        in result.stdout
    )
    assert module.NON_HEX_DIGEST in result.stdout
    assert result.home_snapshot == before


def test_a_recorded_destination_that_is_a_directory_names_its_cause(
    tmp_path: Path,
) -> None:
    lifecycle = PluginLifecycleHarness.create(tmp_path, plugin_name="fixture")
    module = lifecycle.load_module()
    content = lifecycle.definition_content("auditor")
    shipped = lifecycle.ship("auditor")
    destination = lifecycle.home_agents / shipped.name
    destination.mkdir(parents=True)
    lifecycle.write_ownership(
        lifecycle.ownership_document(
            lifecycle.ownership_entry(shipped.name, hashlib.sha256(content).hexdigest())
        )
    )
    before = lifecycle.snapshot(lifecycle.home)

    result = lifecycle.run()

    assert result.exit_code == 2
    assert (
        f"{module.COLLISION_PREFIX}{destination} ({module.CAUSE_NOT_REGULAR_FILE})"
        in result.stdout
    )
    assert result.home_snapshot == before


def test_a_symlinked_agent_directory_still_reports_every_scope_split(
    tmp_path: Path,
) -> None:
    lifecycle = PluginLifecycleHarness.create(tmp_path / "case", plugin_name="fixture")
    module = lifecycle.load_module()
    exact = lifecycle.ship("exact")
    lifecycle.write_checkout(exact.name, exact.read_bytes())
    real_agents = tmp_path / "real-agents"
    real_agents.mkdir()
    lifecycle.home.mkdir(parents=True, exist_ok=True)
    lifecycle.home_agents.symlink_to(real_agents)

    result = lifecycle.run()

    assert result.exit_code == 2
    assert (
        f"{module.SCOPE_SPLIT_REMOVAL_PREFIX}{lifecycle.checkout_agents / exact.name}"
        in result.stdout
    )
    assert (
        f"{module.COLLISION_PREFIX}"
        f"{module.SYMLINKED_AGENT_DIRECTORY.format(path=lifecycle.home_agents)}"
        in result.stdout
    )
    assert not (real_agents / exact.name).exists()


def test_a_recorded_plugin_is_refreshed_by_the_native_update_never_a_reinstall() -> (
    None
):
    execution = observe_persistent_execution()
    claude_commands = [
        command
        for command in execution.report.plan.commands
        if command.agent is Agent.CLAUDE
    ]
    updated = [
        command.plugin
        for command in claude_commands
        if command.operation is Operation.PLUGIN_UPDATE
    ]
    failure = observe_designated_failure(
        isolated=False,
        operation=Operation.PLUGIN_UPDATE,
        stderr="update failed for a reason the marketplace did not name",
    )

    assert execution.report.plan.claude_plugins
    assert not any(
        command.operation in {Operation.PLUGIN_INSTALL, Operation.PLUGIN_ENABLE}
        for command in claude_commands
    )
    assert tuple(updated) == execution.report.plan.claude_plugins
    assert all(
        command.cwd == execution.report.plan.roots.checkout
        for command in claude_commands
        if command.operation is Operation.PLUGIN_UPDATE
    )
    replacing = observe_persistent_plan(
        claude_repository=NONCANONICAL_MARKETPLACE_SOURCE,
        codex_source=NONCANONICAL_MARKETPLACE_SOURCE,
    )
    replacing_claude = [
        command for command in replacing.plan.commands if command.agent is Agent.CLAUDE
    ]
    replacing_operations = [command.operation for command in replacing_claude]
    assert replacing.plan.claude_plugins
    assert not any(
        operation in {Operation.PLUGIN_INSTALL, Operation.PLUGIN_ENABLE}
        for operation in replacing_operations
    )
    assert (
        tuple(
            command.plugin
            for command in replacing_claude
            if command.operation is Operation.PLUGIN_UPDATE
        )
        == replacing.plan.claude_plugins
    )
    assert replacing_operations.index(Operation.MARKETPLACE_ADD) < (
        replacing_operations.index(Operation.PLUGIN_UPDATE)
    )
    assert failure.report is None
    assert failure.failure is not None
    assert failure.failure.command.operation is Operation.PLUGIN_UPDATE
    assert not any(
        command.operation is Operation.PLUGIN_LIST and command.agent is Agent.CLAUDE
        for command in failure.calls
    )


def test_a_local_scope_record_for_the_checkout_suppresses_the_bootstrap_install() -> (
    None
):
    observation = observe_local_record_bootstrap_plan()
    claude_commands = [
        command
        for command in observation.plan.commands
        if command.agent is Agent.CLAUDE
    ]
    updates = [
        command
        for command in claude_commands
        if command.operation is Operation.PLUGIN_UPDATE
    ]

    assert not any(
        command.operation in {Operation.PLUGIN_INSTALL, Operation.PLUGIN_ENABLE}
        for command in claude_commands
    )
    assert [(command.plugin, command.argv[-1], command.cwd) for command in updates] == [
        (SPEC_TREE_PLUGIN, CLAUDE_LOCAL_SCOPE, observation.plan.roots.checkout)
    ]
