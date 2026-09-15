"""Saved-login rejection across the declared unsupported states."""

import pytest

from outcomeeng_testing.harnesses.discovery_auth import (
    DiscoveryAuthentication,
    SavedLoginCondition,
    SavedLoginError,
    select_authentication,
)
from outcomeeng_testing.harnesses.discovery_auth_cases import (
    invalid_saved_login,
)


@pytest.mark.parametrize("fault", list(SavedLoginCondition), ids=str)
def test_invalid_saved_login_fails_before_any_native_command(
    fault: SavedLoginCondition,
) -> None:
    with invalid_saved_login(fault) as case:
        with pytest.raises(SavedLoginError) as captured:
            DiscoveryAuthentication(
                select_authentication(case.original_environment), case.runner
            )
        assert captured.value.condition is fault
        assert case.runner.calls == []
