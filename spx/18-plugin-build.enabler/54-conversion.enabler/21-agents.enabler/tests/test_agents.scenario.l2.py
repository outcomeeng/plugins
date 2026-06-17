"""Level-2 sync evidence for local Codex agent installation ordering."""

from __future__ import annotations

from outcomeeng.distribution.sync import STEPS

CODEX_LOCAL_REFRESH_STEP = "codex_local_refresh"
AGENT_INSTALL_STEP = "codex_agent_install"
INSTALL_VALIDATE_STEP = "install_validate"
AGENT_INSTALL_MODULE = "outcomeeng.distribution.agents"


def test_sync_installs_codex_agents_before_installed_plugin_validation() -> None:
    step_names = tuple(step.name for step in STEPS)

    assert step_names.index(CODEX_LOCAL_REFRESH_STEP) < step_names.index(
        AGENT_INSTALL_STEP
    )
    assert step_names.index(AGENT_INSTALL_STEP) < step_names.index(
        INSTALL_VALIDATE_STEP
    )


def test_sync_agent_install_step_invokes_agent_installer_module() -> None:
    agent_step = next(step for step in STEPS if step.name == AGENT_INSTALL_STEP)

    assert AGENT_INSTALL_MODULE in agent_step.argv
    assert "install" in agent_step.argv
