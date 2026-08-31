"""Compliance evidence for the drift gate's budget-regression boundary."""

from __future__ import annotations

import pathlib

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


def test_budget_findings_derive_a_regression_from_the_baseline_commit(
    tmp_path: pathlib.Path,
) -> None:
    # The real prior-state comparison: a root file that fit at the baseline commit is
    # committed breaching by the changeset, while a file already breaching at the
    # baseline only grows — the first is the violating case the gate fails, the
    # second the pre-existing breach it reports. The baseline is the parent commit,
    # so the tip commit carrying the changeset's own regenerated files is never its
    # own baseline. Sizes derive from the ceiling and the boundary law; both states
    # come from real commits in a real git repository.
    budget = MODULE.PROJECT_DOC_BUDGET_BYTES
    repo = tmp_path / "repo"
    repo.mkdir()
    harness.init_git_identity(repo)
    regressed, preexisting = gate.root_instruction_paths()[:2]

    (repo / regressed).write_text("x" * budget, encoding="utf-8")
    (repo / preexisting).write_text("x" * (budget + 1), encoding="utf-8")
    harness.git_commit_at(repo, 1, regressed, preexisting)
    (repo / regressed).write_text("x" * (budget + 1), encoding="utf-8")
    (repo / preexisting).write_text("x" * (budget + 2), encoding="utf-8")
    harness.git_commit_at(repo, 2, regressed, preexisting)

    lines, regressions = gate.budget_findings(repo_root=repo)

    assert regressions == (regressed,)
    assert len(lines) == len(gate.root_instruction_paths())
    breach_state = str(MODULE.BudgetState.BREACH)
    assert all(breach_state in line for line in lines)


def test_budget_baseline_prefers_the_default_branch_merge_base(
    tmp_path: pathlib.Path,
) -> None:
    # On a branch whose own parent commit already breaches, the baseline is the
    # merge-base with the default branch — the changeset's true prior state — so a
    # first-time crossing by a multi-commit branch is still a regression. A
    # parent-commit baseline would read the branch's own breaching commit and
    # misclassify it as pre-existing.
    budget = MODULE.PROJECT_DOC_BUDGET_BYTES
    repo = tmp_path / "repo"
    repo.mkdir()
    harness.init_git_identity(repo)
    regressed = gate.root_instruction_paths()[0]

    (repo / regressed).write_text("x" * budget, encoding="utf-8")
    harness.git_commit_at(repo, 1, regressed)
    default_branch = harness.git_command(
        repo, "branch", "--show-current"
    ).stdout.strip()
    harness.git_command(repo, "remote", "add", "origin", str(repo))
    harness.git_command(repo, "fetch", "origin")
    harness.git_command(repo, "remote", "set-head", "origin", default_branch)
    harness.git_command(repo, "checkout", "-b", "work")
    (repo / regressed).write_text("x" * (budget + 1), encoding="utf-8")
    harness.git_commit_at(repo, 2, regressed)
    (repo / regressed).write_text("x" * (budget + 2), encoding="utf-8")
    harness.git_commit_at(repo, 3, regressed)

    _lines, regressions = gate.budget_findings(repo_root=repo)

    assert regressions == (regressed,)


def test_budget_findings_report_without_failing_when_no_baseline_exists(
    tmp_path: pathlib.Path,
) -> None:
    # A repository whose only commit already carries the breach has no prior state
    # to regress from: the breach is reported, never failed.
    budget = MODULE.PROJECT_DOC_BUDGET_BYTES
    repo = tmp_path / "repo"
    repo.mkdir()
    harness.init_git_identity(repo)
    reported = gate.root_instruction_paths()[0]

    (repo / reported).write_text("x" * (budget + 1), encoding="utf-8")
    harness.git_commit_at(repo, 1, reported)

    lines, regressions = gate.budget_findings(repo_root=repo)

    assert regressions == ()
    assert any(str(MODULE.BudgetState.BREACH) in line for line in lines)


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
