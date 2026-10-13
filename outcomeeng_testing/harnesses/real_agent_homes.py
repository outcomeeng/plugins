"""Codex home provisioning observed at the first command of every real-agent observation.

Each entry runs one real-agent observation as far as the moment it would spawn
its first agent command and returns the `config.toml` the selected `CODEX_HOME`
held then, or `None` when it held none. The observations route every command
through one process boundary, so an observation that spawns a command against
a home it never provisioned shows up here as a missing configuration; no entry
launches an agent CLI.

Exception case: Stage 5, Observability — the signal is hidden by the real
spawn, which needs credentials and network.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping

from outcomeeng_testing.harnesses.discovery_auth import DiscoveryAuthenticationError
from outcomeeng_testing.harnesses.discovery_auth_cases import (
    NativeFault,
    authentication_case,
)
from outcomeeng_testing.harnesses.installation import (
    home_config_at_first_agent_process,
    observe_codex_subagent_discovery,
    observe_real_first_install,
    observe_real_installation,
    observe_real_record_refresh,
)


def _discovery_home_config_at_first_command() -> bytes | None:
    with authentication_case(fault=NativeFault.INSTALL_FAILURE) as case:
        try:
            observe_codex_subagent_discovery(
                environment=case.original_environment, runner=case.runner
            )
        except DiscoveryAuthenticationError:
            pass
        return case.runner.calls[0].home_config


REAL_AGENT_CODEX_HOME_PROVISIONERS: Mapping[str, Callable[[], bytes | None]] = {
    "first-install": lambda: home_config_at_first_agent_process(
        observe_real_first_install.__wrapped__
    ),
    "record-refresh": lambda: home_config_at_first_agent_process(
        observe_real_record_refresh.__wrapped__
    ),
    "installation": lambda: home_config_at_first_agent_process(
        observe_real_installation.__wrapped__
    ),
    "subagent-discovery": _discovery_home_config_at_first_command,
}
"""Every real-agent observation, keyed by name, observed at its first agent command."""

__all__ = ["REAL_AGENT_CODEX_HOME_PROVISIONERS"]
