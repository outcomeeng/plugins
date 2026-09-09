"""Network-backed real isolated-state boundary evidence."""

import pytest

from outcomeeng_testing.harnesses.installation import (
    observe_real_codex_role_discovery,
    observe_real_installation,
    selected_codex_login_state_available,
)


def test_isolated_installation_preserves_persistent_agent_state() -> None:
    observation = observe_real_installation()

    assert observation.first_exit_code == 0, observation.first_stderr
    assert observation.second_exit_code == 0, observation.second_stderr
    assert observation.persistent_mode_first & 0o777 == 0
    assert observation.persistent_mode_second & 0o777 == 0
    assert observation.persistent_initial == observation.persistent_first
    assert observation.persistent_initial == observation.persistent_second


def test_role_discovery_preserves_login_without_exposing_credentials() -> None:
    if not selected_codex_login_state_available():
        pytest.skip("selected Codex login state is unavailable")
    observation = observe_real_codex_role_discovery()

    assert observation.selected_login_digest_before == (
        observation.selected_login_digest_after
    )
    assert (
        observation.disposable_login_digest == observation.selected_login_digest_before
    )

    assert observation.credential_scalar_count > 0
    assert observation.credential_surface_match_count == 0
