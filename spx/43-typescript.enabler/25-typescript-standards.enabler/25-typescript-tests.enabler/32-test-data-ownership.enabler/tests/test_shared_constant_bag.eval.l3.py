"""End-to-end eval for the shared-test-owned-constant-bag rule.

l3: spawns the `claude` binary using the user's OAuth subscription, replays
the cases JSONL, parses each XML verdict, and gates on the suite pass rate.

Skipped by default. Set ``OUTCOMEENG_RUN_L3_EVALS=1`` to enable.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from outcomeeng_evals.case import Case
from outcomeeng_evals.report import write_html_report
from outcomeeng_evals.runner import ClaudeCliRunner
from outcomeeng_evals.suite import format_report, run_suite


HERE = Path(__file__).parent
CASES = HERE / "shared_constant_bag.eval.cases.jsonl"
PROMPT_TEMPLATE = HERE / "shared_constant_bag.prompt.md"
# parents[6] reaches the project root from this test file's depth.
PROJECT_ROOT = Path(__file__).resolve().parents[6]
PLUGIN_DIR = PROJECT_ROOT / "plugins" / "typescript"
REPORT_PATH = (
    PROJECT_ROOT / ".spx" / "evals" / "transcripts" / "shared_constant_bag.html"
)


@pytest.mark.skipif(
    os.environ.get("OUTCOMEENG_RUN_L3_EVALS") != "1",
    reason="l3 eval; set OUTCOMEENG_RUN_L3_EVALS=1 to enable",
)
def test_shared_constant_bag_rule_recognized_in_typescript_test_files() -> None:
    template = PROMPT_TEMPLATE.read_text(encoding="utf-8")
    runner = ClaudeCliRunner(plugin_dir=PLUGIN_DIR)
    result = run_suite(
        cases_path=CASES,
        runner=runner,
        build_prompt=lambda case: _render(template, case),
        trials_per_case=int(os.environ.get("OUTCOMEENG_EVAL_TRIALS", "1")),
        suite_threshold=float(os.environ.get("OUTCOMEENG_EVAL_THRESHOLD", "0.85")),
    )
    report_path = write_html_report(
        result,
        REPORT_PATH,
        title="Eval: shared-test-owned-constant-bag",
    )
    print(f"\nHTML report: {report_path}")
    assert result.passed, "\n" + format_report(result)


def _render(template: str, case: Case) -> str:
    return template.replace("{case_id}", case.id).replace(
        "{input_json}", json.dumps(case.input, indent=2)
    )
