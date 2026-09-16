"""Saved-login rejection across the declared unsupported states."""

import pytest

from outcomeeng_testing.generators.discovery_auth import (
    SavedLoginInput,
    generated_saved_login_inputs,
)
from outcomeeng_testing.harnesses.discovery_auth import (
    DiscoveryAuthentication,
    SavedLoginError,
    select_authentication,
)
from outcomeeng_testing.harnesses.discovery_auth_cases import (
    saved_login_document,
)


@pytest.mark.parametrize("row", generated_saved_login_inputs())
def test_invalid_saved_login_fails_before_any_native_command(
    row: SavedLoginInput,
) -> None:
    with saved_login_document(row.document) as case:
        with pytest.raises(SavedLoginError) as captured:
            DiscoveryAuthentication(
                select_authentication(case.original_environment), case.runner
            )
        assert captured.value.condition is row.condition
        assert case.runner.calls == []
