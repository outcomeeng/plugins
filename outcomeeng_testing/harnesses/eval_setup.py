"""Setup failure raised by eval test harnesses.

Harnesses raise this when a real resource they prepare does not reach the state
the linked test needs. Behavioral verdicts stay with the linked tests.
"""

from __future__ import annotations


class EvalHarnessSetupError(RuntimeError):
    """A harness-prepared resource failed to reach its precondition state."""
