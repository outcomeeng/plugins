"""Compliance evidence for the breach report on an over-ceiling root instruction file."""

from __future__ import annotations

import pathlib

from outcomeeng_testing.harnesses import instruction_block as harness

MODULE = harness.load_instruction_block_module()


def test_check_reports_breach_with_exact_counts_and_no_false_positive(
    tmp_path: pathlib.Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    template = harness.write_template(tmp_path, harness.NEW_VERSION)
    harness.run_generator_write_primary(repo, template)

    # The violating input is the whole rendered root file grown past the ceiling: the
    # smallest breaching size derives from the declared ceiling and the current size.
    budget = MODULE.PROJECT_DOC_BUDGET_BYTES
    agents = repo / harness.INSTRUCTION_AGENTS
    base = agents.read_text(encoding="utf-8")
    padding = max(budget + 1 - len(base.encode("utf-8")), 1)
    agents.write_text(base + "x" * padding, encoding="utf-8")
    breach_size = len(agents.read_text(encoding="utf-8").encode("utf-8"))
    claude_size = len(
        (repo / harness.INSTRUCTION_CLAUDE).read_text(encoding="utf-8").encode("utf-8")
    )
    assert breach_size > budget
    assert claude_size <= budget

    code, _verdict, diagnostics = harness.run_generator_check_with_diagnostics(
        repo, template
    )

    assert code == 0
    lines = [line for line in diagnostics.splitlines() if line.startswith("budget:")]
    agents_lines = [line for line in lines if harness.INSTRUCTION_AGENTS in line]
    claude_lines = [line for line in lines if harness.INSTRUCTION_CLAUDE in line]
    assert len(agents_lines) == 1
    assert len(claude_lines) == 1
    assert f"{breach_size}/{budget}" in agents_lines[0]
    assert str(MODULE.BudgetState.BREACH) in agents_lines[0]
    assert f"{breach_size - budget} over" in agents_lines[0]
    # The fitting file proves no false positive.
    assert f"{claude_size}/{budget}" in claude_lines[0]
    assert str(MODULE.BudgetState.FIT) in claude_lines[0]
    assert str(MODULE.BudgetState.BREACH) not in claude_lines[0]
