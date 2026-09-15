"""Saved-login rejection across the declared unsupported states."""

import pytest

from outcomeeng_testing.harnesses.discovery_auth import (
    DiscoveryAuthentication,
    DiscoveryAuthenticationError,
    select_authentication,
)
from outcomeeng_testing.harnesses.discovery_auth_cases import (
    SavedLoginFault,
    invalid_saved_login,
)


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
