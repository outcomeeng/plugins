"""Per-agent disable switches declaring a run's real-process rows optional."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Final

DISABLE_CODEX_ENV: Final = "OE_AGENTIC_DISABLE_CODEX"
"""The switch declaring rows that start a real Codex process optional for this run."""
DISABLE_CLAUDE_ENV: Final = "OE_AGENTIC_DISABLE_CLAUDE"
"""The switch declaring rows that start a real Claude process optional for this run."""
DISABLE_VALUE: Final = "1"
"""The one value that declares an agent's rows optional; every other value runs them."""
DISABLED_REASON: Final = "{switch}={value} declares this row optional for this run"
"""The reason a declared skip reports; it names the switch that declared the skip."""
SWITCH_STATE_LINE: Final = "{switch} is {state}"
"""One plan-explanation line per agent, naming that switch's state before the run."""
SWITCH_SET: Final = (
    "set: rows starting a real process for this agent skip by declaration"
)
"""The state wording for a switch holding the disable value."""
SWITCH_UNSET: Final = "unset: rows starting a real process for this agent run"
"""The state wording for a switch holding anything else."""
AGENT_SWITCHES: Final = (DISABLE_CLAUDE_ENV, DISABLE_CODEX_ENV)
"""Every switch that can declare a row optional, in reporting order."""


def codex_disabled_reason(environment: Mapping[str, str]) -> str | None:
    """Return the Codex skip reason, or `None` when this run's Codex rows run."""
    return _disabled_reason(environment, DISABLE_CODEX_ENV)


def claude_disabled_reason(environment: Mapping[str, str]) -> str | None:
    """Return the Claude skip reason, or `None` when this run's Claude rows run."""
    return _disabled_reason(environment, DISABLE_CLAUDE_ENV)


def _disabled_reason(environment: Mapping[str, str], switch: str) -> str | None:
    if environment.get(switch) != DISABLE_VALUE:
        return None
    return DISABLED_REASON.format(switch=switch, value=DISABLE_VALUE)


@dataclass(frozen=True)
class AgentDisableStates:
    """Both switches' readings for one run, resolved once at the command edge.

    Every field is required: a reading of process state has no default, because
    a default would render as a state the run never observed.
    """

    codex: str | None
    claude: str | None

    @property
    def explanation_lines(self) -> tuple[str, ...]:
        """Return one line per agent naming that switch's state before the run."""
        return tuple(
            SWITCH_STATE_LINE.format(
                switch=switch,
                state=SWITCH_SET if reason is not None else SWITCH_UNSET,
            )
            for switch, reason in (
                (DISABLE_CLAUDE_ENV, self.claude),
                (DISABLE_CODEX_ENV, self.codex),
            )
        )


def read_agent_disable_states(environment: Mapping[str, str]) -> AgentDisableStates:
    """Read both switches once, each through its own predicate."""
    return AgentDisableStates(
        codex=codex_disabled_reason(environment),
        claude=claude_disabled_reason(environment),
    )


def declared_switch(reason: str) -> str | None:
    """Return the switch whose own declared reason this text carries, or `None`.

    The match is against the reason this module produces for that switch, so a
    skip declared for an unrelated cause never attributes itself to a switch
    merely by mentioning its name.
    """
    for switch in AGENT_SWITCHES:
        declared = _disabled_reason({switch: DISABLE_VALUE}, switch)
        if declared is not None and declared in reason:
            return switch
    return None
