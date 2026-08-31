"""Compliance evidence for the drift gate's budget-regression boundary."""

from __future__ import annotations

import pytest

from outcomeeng.distribution import instruction_block as gate
from outcomeeng_testing.harnesses import instruction_block as harness

MODULE = harness.load_instruction_block_module()


def test_gate_fails_only_a_regression_above_the_ceiling() -> None:
    # Every case derives from the declared ceiling and the decision's boundary law:
    # the largest fitting size and the smallest breaching sizes are the partition
    # representatives on each side of the committed/rendered pair.
    budget = MODULE.PROJECT_DOC_BUDGET_BYTES
    fitting = budget
    breaching = budget + 1

    # The violating case: a surface that previously fit regresses above the ceiling.
    assert gate.budget_regression(fitting, breaching, budget) is True
    # A breach the checked change did not introduce is reported, never failed.
    assert gate.budget_regression(breaching, breaching + 1, budget) is False
    # A fitting surface stays clean.
    assert gate.budget_regression(fitting, fitting, budget) is False
    # A file with no committed form cannot regress.
    assert gate.budget_regression(None, breaching, budget) is False


def _breach_line(path: str) -> str:
    # The report line for the smallest breaching size derives from the ceiling and the
    # generator's own report contract.
    budget = MODULE.PROJECT_DOC_BUDGET_BYTES
    return str(
        MODULE.budget_report_line(MODULE.measure_budget(path, "x" * (budget + 1)))
    )


def test_gate_run_fails_a_regression_and_reports_it(
    capsys: pytest.CaptureFixture[str],
) -> None:
    # The real collaborators regenerate the checkout's root files and mutate its git
    # index, so the run is driven through injected controlled collaborators — the
    # /test Stage 5 safety exception (case 4) — preserving main()'s real branching,
    # reporting, and exit-code wiring as the behavior under test.
    regressed = gate.root_instruction_paths()[0]

    code = gate.main(
        [],
        regenerate=lambda: None,
        budget=lambda: ((_breach_line(regressed),), (regressed,)),
        drift_files=lambda: [],
        shared_regions=lambda: (),
    )

    captured = capsys.readouterr()
    assert code == 1
    assert gate.BUDGET_REGRESSION_HEADER in captured.out
    assert regressed in captured.out
    assert gate.BUDGET_REGRESSION_REMEDIATION in captured.out


def test_gate_run_reports_a_preexisting_breach_without_failing(
    capsys: pytest.CaptureFixture[str],
) -> None:
    # A breach with no regression — the committed file already exceeded the ceiling —
    # is reported on stderr while the gate stays green.
    reported = gate.root_instruction_paths()[0]

    code = gate.main(
        [],
        regenerate=lambda: None,
        budget=lambda: ((_breach_line(reported),), ()),
        drift_files=lambda: [],
        shared_regions=lambda: (),
    )

    captured = capsys.readouterr()
    assert code == 0
    assert reported in captured.err
    assert gate.BUDGET_REGRESSION_HEADER not in captured.out
