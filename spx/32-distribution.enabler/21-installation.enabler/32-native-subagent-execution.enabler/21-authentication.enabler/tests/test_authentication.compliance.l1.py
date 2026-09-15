"""Installation evidence grouped by its governing contract."""

from outcomeeng.distribution.installation import CODEX_EXECUTABLE
from outcomeeng.validation.ci_gate import CODEX_API_KEY_ENVIRONMENT
from outcomeeng_testing.harnesses.discovery_auth import (
    AuthField,
    NativeCommand,
    API_LOGIN_FLAG,
    WORKSPACE_LOGIN_FLAG,
    AUTH_FILENAME,
    CREDENTIAL_ENVIRONMENTS,
    REDACTED_CREDENTIAL,
    AuthenticationMode,
    DiscoveryAuthenticationError,
    select_authentication,
)
from outcomeeng_testing.harnesses.discovery_auth_cases import (
    NativeFault,
    SESSION_COMMAND,
    authentication_case,
    ci_without_authentication_mode,
    dispose_authenticated_home,
    lock_contention_case,
    missing_credential_environment,
)
from outcomeeng_testing.harnesses.installation import observe_codex_subagent_discovery
import json
import pytest
import subprocess


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
            call.home != case.home or NativeCommand.LOGIN not in call.argv
            for call in case.runner.calls
        )
        assert all(NativeCommand.LOGOUT not in call.argv for call in case.runner.calls)
        assert all(
            not (set(call.environment) & CREDENTIAL_ENVIRONMENTS)
            for call in case.runner.calls
        )
        assert all(
            token not in result.stdout + result.stderr
            for token in json.loads(case.refreshed)[AuthField.TOKENS].values()
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
            json.loads(case.saved.read_text())[AuthField.TOKENS][AuthField.ACCOUNT_ID]
            != json.loads(case.initial)[AuthField.TOKENS][AuthField.ACCOUNT_ID]
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
            for token in json.loads(case.refreshed)[AuthField.TOKENS].values()
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
        assert all(NativeCommand.EXEC not in call.argv for call in case.runner.calls)
        assert case.auth.selection.credential not in str(raised.value)
        assert REDACTED_CREDENTIAL in str(raised.value)


def test_failed_installation_stops_before_credentials_are_attached() -> None:
    with authentication_case(fault=NativeFault.INSTALL_FAILURE) as case:
        with pytest.raises(DiscoveryAuthenticationError):
            observe_codex_subagent_discovery(
                environment=case.original_environment, runner=case.runner
            )
        assert all(call.argv[0] != CODEX_EXECUTABLE for call in case.runner.calls)
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
        assert all(NativeCommand.EXEC not in call.argv for call in case.runner.calls)


def test_disposable_cleanup_preserves_native_refresh_in_the_saved_file() -> None:
    with authentication_case() as case:
        with case.auth.authenticated_home(
            case.home, cwd=case.home, env=case.environment
        ):
            case.auth.run(SESSION_COMMAND, cwd=case.home, env=case.environment)
        dispose_authenticated_home(case)
        assert not case.home.exists()
        assert case.saved.read_text() == case.refreshed
