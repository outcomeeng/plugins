"""Level 1 property tests for the gate orchestrator.

Verifies invariants that must hold across arbitrary step lists:
- Spawn invocation order matches the declared step-list order.
- The elapsed-time value recorded in the timing summary is non-negative
  for any step that completes.
"""

from __future__ import annotations

import io
import re
from typing import Final

from hypothesis import given, settings
from hypothesis import strategies as st

from outcomeeng.validation import Step, run
from outcomeeng_testing.harnesses.gate import RecordingSpawner

LABEL_ALPHABET: Final = (
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-"
)
ARGV_ALPHABET: Final = (
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_."
)
MAX_LABEL_LEN: Final = 16
MAX_ARGV_TOKEN_LEN: Final = 12
MAX_ARGV_TOKENS: Final = 4
MAX_STEP_COUNT: Final = 6
MAX_EXAMPLES: Final = 50
PASS: Final = 0

label_strategy = st.text(alphabet=LABEL_ALPHABET, min_size=1, max_size=MAX_LABEL_LEN)
argv_token_strategy = st.text(
    alphabet=ARGV_ALPHABET,
    min_size=1,
    max_size=MAX_ARGV_TOKEN_LEN,
)
argv_strategy = st.lists(
    argv_token_strategy,
    min_size=1,
    max_size=MAX_ARGV_TOKENS,
).map(tuple)


@st.composite
def step_strategy(draw: st.DrawFn) -> Step:
    return Step(label=draw(label_strategy), argv=draw(argv_strategy))


step_list_strategy = st.lists(
    step_strategy(),
    min_size=1,
    max_size=MAX_STEP_COUNT,
    unique_by=lambda step: step.label,
).map(tuple)


@given(steps=step_list_strategy)
@settings(max_examples=MAX_EXAMPLES)
def test_spawn_order_matches_step_list_order(steps: tuple[Step, ...]) -> None:
    """The order in which subprocesses are started equals the step-list order."""
    spawner = RecordingSpawner(exit_codes=[PASS] * len(steps))
    sink = io.StringIO()

    run(spawner=spawner, sink=sink, steps=steps)

    invoked_argvs = spawner.spawn_calls
    expected_argvs = [step.argv for step in steps]
    assert invoked_argvs == expected_argvs


# Row pattern: a label followed by whitespace, optional digits, then "s".
_TIMING_ROW = re.compile(r"^\s*(\S+)\s+(-?\d+)s\s*$", re.MULTILINE)


@given(steps=step_list_strategy)
@settings(max_examples=MAX_EXAMPLES)
def test_elapsed_time_is_non_negative_for_completed_steps(
    steps: tuple[Step, ...],
) -> None:
    """Every per-step timing row in the summary records a non-negative integer."""
    spawner = RecordingSpawner(exit_codes=[PASS] * len(steps))
    sink = io.StringIO()

    run(spawner=spawner, sink=sink, steps=steps)

    output = sink.getvalue()
    summary_start = output.index("━━━ Timing Summary ━━━")
    summary = output[summary_start:]
    rows = _TIMING_ROW.findall(summary)
    assert rows, "timing summary must contain at least one parseable row"
    for _, seconds in rows:
        assert int(seconds) >= 0
