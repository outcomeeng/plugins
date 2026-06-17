"""CLI scenario tests for ``audit_orchestrator.py verdict-diff``.

Covers the cross-process determinism contract on ``compute_verdict_diff``:
the resolved/reopened arrays must be byte-equal across Python processes
regardless of ``PYTHONHASHSEED``. The set differences and intersections
underlying the diff have hash-randomized iteration order between
processes; the production code sorts by content identity to make the
output stable, and this test proves the property at the CLI boundary
(stdin → stdout) the way the ``pr-review-orchestrator`` agent invokes it.

Single-process tests cannot observe the bug — Python's hash seed is fixed
within a process — so this evidence lives at the subprocess level.
"""

from __future__ import annotations

import json
import os
import pathlib

from outcomeeng_testing.harnesses.verdict_toolchain import (
    AUDIT_ORCHESTRATOR_SCRIPT,
    load_verdict_module,
    run_script,
)

_verdict_module = load_verdict_module()
_Finding = _verdict_module.Finding
_finding_to_json_dict = _verdict_module.finding_to_json_dict
_Severity = _verdict_module.Severity

# Two PYTHONHASHSEED values chosen to maximize the probability that
# unsorted set iteration produces different orders across the two runs.
# The stable-sort fix in compute_verdict_diff makes both runs produce
# identical output regardless of seed; without the fix, the assertion
# would fail at least on one of these seed pairs in a typical CPython.
HASH_SEED_LO = "0"
HASH_SEED_HI = "999983"

# The verdict-diff CLI exit codes documented on _cmd_verdict_diff.
EXIT_SUCCESS = 0


def _finding_dict(
    *, finding_id: str, file: str, line: int | None, rule: str, message: str
) -> dict[str, object]:
    return _finding_to_json_dict(
        _Finding(
            id=finding_id,
            file=file,
            line=line,
            rule=rule,
            severity=_Severity.REJECT,
            message=message,
        )
    )


def _verdict_dict(open_findings: list[dict[str, object]]) -> dict[str, object]:
    return {
        "schema_version": 1,
        "skill": "audit",
        "target": "scope",
        "overall": "REJECTED" if open_findings else "APPROVED",
        "rows": [{"name": "row-1", "status": "FAIL", "findings": open_findings}],
        "children": [],
        "metadata": {},
    }


def _diff_with_hash_seed(
    *, prior_path: pathlib.Path, current: dict[str, object], hash_seed: str
) -> dict[str, object]:
    env = {**os.environ, "PYTHONHASHSEED": hash_seed}
    result = run_script(
        AUDIT_ORCHESTRATOR_SCRIPT,
        "verdict-diff",
        "--prior",
        str(prior_path),
        stdin=json.dumps(current),
        env=env,
    )
    assert result.returncode == EXIT_SUCCESS, (
        f"verdict-diff failed (seed={hash_seed}): "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    return json.loads(result.stdout)


def test_verdict_diff_output_is_byte_equal_across_hash_seeds(
    tmp_path: pathlib.Path,
) -> None:
    """Same input → same JSON bytes regardless of PYTHONHASHSEED.

    Builds a prior verdict with several findings whose identity tuples
    do not coincide with any single hash order, then runs
    ``audit_orchestrator.py verdict-diff`` twice in subprocesses with
    different hash seeds. The resolved/reopened arrays must be byte-equal
    across runs — that is what makes PR-thread comment comparison a
    meaningful drift signal rather than noise.
    """
    findings = [
        _finding_dict(
            finding_id="f-001",
            file="src/a.ts",
            line=1,
            rule="no-shared-bag",
            message="shared bag in a",
        ),
        _finding_dict(
            finding_id="f-002",
            file="src/a.ts",
            line=None,
            rule="no-shared-bag",
            message="whole-file finding in a",
        ),
        _finding_dict(
            finding_id="f-003",
            file="src/b.ts",
            line=2,
            rule="no-shared-bag",
            message="shared bag in b",
        ),
        _finding_dict(
            finding_id="f-004",
            file="src/c.ts",
            line=42,
            rule="rule-c",
            message="finding in c",
        ),
        _finding_dict(
            finding_id="f-005",
            file="src/z.ts",
            line=9,
            rule="rule-z",
            message="finding in z",
        ),
        _finding_dict(
            finding_id="f-006",
            file="src/d.ts",
            line=7,
            rule="rule-d",
            message="finding in d",
        ),
    ]
    prior = _verdict_dict(findings)
    current = _verdict_dict([])  # all prior findings become resolved

    prior_path = tmp_path / "prior.json"
    prior_path.write_text(json.dumps(prior), encoding="utf-8")

    out_lo = _diff_with_hash_seed(
        prior_path=prior_path, current=current, hash_seed=HASH_SEED_LO
    )
    out_hi = _diff_with_hash_seed(
        prior_path=prior_path, current=current, hash_seed=HASH_SEED_HI
    )

    # Both runs must produce identical resolved-array ordering. JSON
    # serialization with the same key order makes the comparison byte-equal
    # at the wire level, which is what the PR-thread audit comment carries.
    assert out_lo["resolved"] == out_hi["resolved"]
    assert out_hi["reopened"] == []
    assert out_lo["reopened"] == []
    assert len(out_lo["resolved"]) == len(findings)


def test_verdict_diff_first_run_with_no_prior_argument_is_empty(
    tmp_path: pathlib.Path,
) -> None:
    """``--prior`` omitted → first-run case, resolved/reopened empty.

    The CLI's first-run branch is exercised directly: omit ``--prior``,
    pass a non-empty current verdict on stdin, and assert resolved and
    reopened are both empty. This pairs with the first-run case the
    ``pr-review-orchestrator`` agent hits on a fresh PR.
    """
    current = _verdict_dict(
        [
            _finding_dict(
                finding_id="f-001",
                file="src/a.ts",
                line=1,
                rule="r",
                message="m",
            ),
        ]
    )
    result = run_script(
        AUDIT_ORCHESTRATOR_SCRIPT,
        "verdict-diff",
        stdin=json.dumps(current),
    )
    assert result.returncode == EXIT_SUCCESS, (
        f"verdict-diff failed: stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    out = json.loads(result.stdout)
    assert out["resolved"] == []
    assert out["reopened"] == []
