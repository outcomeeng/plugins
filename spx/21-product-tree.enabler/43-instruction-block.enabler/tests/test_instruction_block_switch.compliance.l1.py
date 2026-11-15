"""Compliance evidence for the switch that turns the root instruction blocks off.

The module's command-line entry reads the switch variable from an injected
environment and runs the generator through an injected callable that records
each call, so the test observes whether the generator ran and with which
arguments for each value of the variable.
"""

from __future__ import annotations

from collections.abc import Sequence

import pytest

from outcomeeng.distribution import instruction_block as gate

GENERATOR_CODE = 7


def run(argv: list[str], environ: dict[str, str]) -> tuple[int, list[list[str] | None]]:
    calls: list[list[str] | None] = []

    def generator(args: Sequence[str] | None) -> int:
        calls.append(None if args is None else list(args))
        return GENERATOR_CODE

    code = gate.entry(argv, environ=environ, run=generator)
    return code, calls


@pytest.mark.parametrize("argv", [[], ["--write"]], ids=["check", "write"])
def test_switch_off_writes_and_checks_nothing(
    argv: list[str], capsys: pytest.CaptureFixture[str]
) -> None:
    code, calls = run(argv, {gate.SWITCH_VARIABLE: gate.SWITCH_OFF})
    assert code == 0
    assert calls == []
    assert f"{gate.SWITCH_VARIABLE}={gate.SWITCH_OFF}" in capsys.readouterr().err


@pytest.mark.parametrize(
    "environ",
    [
        {},
        {gate.SWITCH_VARIABLE: "on"},
        {gate.SWITCH_VARIABLE: ""},
        {gate.SWITCH_VARIABLE: "OFF"},
        {gate.SWITCH_VARIABLE: " off"},
    ],
    ids=["unset", "on", "empty", "uppercase", "padded"],
)
@pytest.mark.parametrize("argv", [[], ["--write"]], ids=["check", "write"])
def test_switch_other_values_run_the_generator(
    argv: list[str], environ: dict[str, str], capsys: pytest.CaptureFixture[str]
) -> None:
    code, calls = run(argv, environ)
    assert code == GENERATOR_CODE
    assert calls == [argv]
    assert gate.SWITCH_VARIABLE not in capsys.readouterr().err
