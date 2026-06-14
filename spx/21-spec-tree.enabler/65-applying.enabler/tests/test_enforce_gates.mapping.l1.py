"""Mapping: the applying gate hook maps each flow-step skill to its audit-gate reminder.

The hook is the deterministic surface of the applying node: invoked by the harness
as ``python3 scripts/enforce-gates.py`` with the PostToolUse payload on stdin, it
emits an ``additionalContext`` gate reminder for architecting/testing/coding skills
and nothing for any other skill. The test invokes the real script via subprocess —
exactly as the harness does — and derives expected reminders from the script's own
``GATE_REMINDERS`` map so no expected value is owned by the test.
"""

from __future__ import annotations

import importlib.util
import json
import pathlib
import subprocess
import sys

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
HOOK = REPO_ROOT / "src" / "plugins" / "spec-tree" / "scripts" / "enforce-gates.py"


def _load_hook_module():
    spec = importlib.util.spec_from_file_location("enforce_gates", HOOK)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


hook = _load_hook_module()

# Source-owned domain: representative step skills for each gate, expected reminder
# read from the script's own map (no test-owned constants).
GATE_SKILLS = [
    ("architecting-python", hook.GATE_REMINDERS["architecting"]),
    ("architecting-typescript", hook.GATE_REMINDERS["architecting"]),
    ("testing-python", hook.GATE_REMINDERS["testing"]),
    ("testing-typescript", hook.GATE_REMINDERS["testing"]),
    ("coding-python", hook.GATE_REMINDERS["coding"]),
    ("coding-typescript", hook.GATE_REMINDERS["coding"]),
    # Language-neutral: any <stage>-<language> step skill maps, including languages
    # the skill_map does not enumerate, and through a "plugin:" prefix.
    ("architecting-rust", hook.GATE_REMINDERS["architecting"]),
    ("testing-rust", hook.GATE_REMINDERS["testing"]),
    ("coding-rust", hook.GATE_REMINDERS["coding"]),
    ("python:coding-python", hook.GATE_REMINDERS["coding"]),
    ("typescript:testing-typescript", hook.GATE_REMINDERS["testing"]),
]

NON_GATE_SKILLS = [
    "spec-tree:understanding",
    "spec-tree:contextualizing",
    "spec-tree:auditing-tests",
    "prose:writing-prose",
    # The bare spec-tree testing/architecting skills are not <stage>-<language> step
    # skills and must not trip a gate reminder.
    "spec-tree:testing",
    "architecting",
    "",
]


def _run_hook(payload: dict) -> dict | None:
    """Invoke the hook the way the harness does: JSON on stdin, JSON or empty on stdout."""
    result = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        check=True,
    )
    out = result.stdout.strip()
    return json.loads(out) if out else None


@pytest.mark.parametrize(
    "skill, expected", GATE_SKILLS, ids=[s for s, _ in GATE_SKILLS]
)
def test_gate_step_skill_maps_to_its_reminder(skill: str, expected: str) -> None:
    out = _run_hook({"tool_input": {"skill": skill}})
    assert out is not None, f"{skill!r} should produce a gate reminder"
    assert out["hookSpecificOutput"]["hookEventName"] == "PostToolUse"
    assert out["hookSpecificOutput"]["additionalContext"] == expected


@pytest.mark.parametrize("skill", NON_GATE_SKILLS, ids=lambda s: s or "<empty>")
def test_non_gate_skill_maps_to_no_output(skill: str) -> None:
    assert _run_hook({"tool_input": {"skill": skill}}) is None


def test_missing_tool_input_maps_to_no_output() -> None:
    assert _run_hook({}) is None


def test_malformed_stdin_is_silent_noop() -> None:
    result = subprocess.run(
        [sys.executable, str(HOOK)],
        input="not json at all",
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.strip() == ""
    assert result.returncode == 0


# Parseable JSON that is not the expected {tool_input: {skill: str}} shape: a bare
# scalar, an array, a non-dict tool_input, or a non-string skill. Each must no-op
# and exit 0 — the hook fires on every Skill call, so a crash would surface to the agent.
MALFORMED_PARSEABLE = [
    "42",
    "[1, 2, 3]",
    '"a bare string"',
    "true",
    "null",
    '{"tool_input": 5}',
    '{"tool_input": {"skill": 123}}',
]


@pytest.mark.parametrize("raw", MALFORMED_PARSEABLE)
def test_parseable_but_wrong_shape_is_silent_noop(raw: str) -> None:
    result = subprocess.run(
        [sys.executable, str(HOOK)],
        input=raw,
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.strip() == "", f"{raw!r} should yield no output"
    assert result.returncode == 0
