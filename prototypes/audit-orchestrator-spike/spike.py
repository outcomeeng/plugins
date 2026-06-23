#!/usr/bin/env python3
"""Spike: does a stateful cross-run audit orchestrator earn its keep?

Throwaway experiment (not shipped). Records a short sequence of per-commit
audit runs on the REAL `spx journal` (local backend), reads them back, and
folds the run set into open / resolved / reopened — then contrasts that with
what a stateless per-run audit can say at the same commit.

The question the spike answers: at commit C, does folding prior runs surface
information a stateless audit structurally cannot? If yes, an orchestrator
(and the cross-run primitive it needs) is worth designing; if no, it is not.

Run: python3 spike.py
Requires: `spx` on PATH (journal verbs), a git repo with .spx/ (any worktree).
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass

TYPE = "auditing"
NOW = "2026-06-23T00:00:00Z"

# Finding identity is content, keyed (file, line, rule, message); severity is
# excluded so a re-severitied finding still matches its prior self.
Finding = tuple[str, int, str, str]


def f(file: str, line: int, rule: str, message: str) -> Finding:
    return (file, line, rule, message)


# The scenario — one developer, three commits:
#   A: audit finds three issues
#   B: developer fixes the magic-value finding (f2 gone)
#   C: developer fixes the coupling finding (f1 gone) but a refactor
#      reintroduces the magic value (f2 is BACK)
F1 = f("orders/coupling.py", 10, "no-mocking", "test mocks the unit under test")
F2 = f("orders/price.py", 20, "magic-value", "literal 100 is a magic value")
F3 = f("orders/types.py", 5, "missing-annotation", "process_order lacks a return type")

COMMITS: list[tuple[str, list[Finding]]] = [
    ("A  initial audit", [F1, F2, F3]),
    ("B  fix the magic value", [F1, F3]),
    ("C  fix coupling; refactor reintroduces the magic value", [F3, F2]),
]


def _spx(*args: str, input_text: str | None = None) -> str:
    return subprocess.run(
        ["spx", "journal", *args],
        input=input_text,
        capture_output=True,
        text=True,
        check=True,
    ).stdout


def record_run(findings: list[Finding]) -> str:
    """Open a run, append scope/finding/run-completed events, seal. Return token."""
    token = json.loads(_spx("open", "--type", TYPE))["runToken"]
    events: list[dict] = [
        {
            "id": "scope.entered.1",
            "source": "spike",
            "type": "verification.scope.entered",
            "time": NOW,
            "attempt": 1,
            "data": {"target": "orders"},
        }
    ]
    for i, (file, line, rule, message) in enumerate(findings, start=2):
        events.append(
            {
                "id": f"finding.{i}",
                "source": "spike",
                "type": "verification.finding.reported",
                "time": NOW,
                "attempt": 1,
                "data": {"file": file, "line": line, "rule": rule, "message": message},
            }
        )
    events.append(
        {
            "id": f"run.completed.{len(findings) + 2}",
            "source": "spike",
            "type": "verification.run.completed",
            "time": NOW,
            "attempt": 1,
            "data": {"overall": "rejected" if findings else "approved"},
        }
    )
    for event in events:
        _spx("append", "--type", TYPE, "--run", token, input_text=json.dumps(event))
    _spx("seal", "--type", TYPE, "--run", token)
    return token


def read_findings(token: str) -> set[Finding]:
    """Read a sealed run back from the journal and extract its findings."""
    prefix = json.loads(_spx("read", "--type", TYPE, "--run", token, "--from", "0"))
    out: set[Finding] = set()
    for event in prefix:
        if event.get("type") == "verification.finding.reported":
            d = event["data"]
            out.add((d["file"], d["line"], d["rule"], d["message"]))
    return out


@dataclass
class Rollup:
    open: set[Finding]
    resolved: set[Finding]
    reopened: set[Finding]


def fold(run_sets: list[set[Finding]]) -> Rollup:
    """Fold the run set oldest->newest into open/resolved/reopened.

    - resolved: was open in a prior run, absent now.
    - reopened: was resolved at some point, present again in the latest run.
    """
    open_set: set[Finding] = set()
    resolved: set[Finding] = set()
    reopened: set[Finding] = set()
    for findings in run_sets:
        resolved |= open_set - findings  # were open, now gone
        reopened = findings & resolved  # were resolved, back now (latest run wins)
        resolved -= reopened
        open_set = findings
    return Rollup(open=open_set, resolved=resolved, reopened=reopened)


def short(finding: Finding) -> str:
    file, line, rule, _ = finding
    return f"{rule} @ {file}:{line}"


def main() -> None:
    print(
        "Recording 3 per-commit audit runs on the real spx journal (local backend)...\n"
    )
    tokens: list[str] = []
    for label, findings in COMMITS:
        token = record_run(findings)
        tokens.append(token)
        print(f"  commit {label}: run {token[-12:]} ({len(findings)} findings, sealed)")

    # The orchestrator must read the PRIOR runs back. The journal has no
    # read-across verb, so the spike tracks the tokens it just created. In
    # production the orchestrator cannot know prior tokens across invocations
    # — that discovery is exactly the cross-run primitive a real orchestrator
    # would need. Here we read each token to prove the fold works over real
    # journal events.
    run_sets = [read_findings(t) for t in tokens]

    latest = run_sets[-1]
    rollup = fold(run_sets)

    print("\n" + "=" * 64)
    print("At commit C — STATELESS per-run audit (what ships today):")
    print("=" * 64)
    print(f"  {len(latest)} findings:")
    for finding in sorted(latest):
        print(f"    - {short(finding)}")
    print("\n  -> a flat list. The developer cannot tell that the coupling")
    print("     finding was fixed, nor that the magic value REGRESSED.")

    print("\n" + "=" * 64)
    print("At commit C — ORCHESTRATOR (fold of the run set):")
    print("=" * 64)
    print(f"  open ({len(rollup.open)}):")
    for finding in sorted(rollup.open):
        print(f"    - {short(finding)}")
    print(f"  resolved ({len(rollup.resolved)}):")
    for finding in sorted(rollup.resolved):
        print(f"    + {short(finding)}  (fixed across commits)")
    print(f"  reopened ({len(rollup.reopened)}):")
    for finding in sorted(rollup.reopened):
        print(f"    ! {short(finding)}  (REGRESSION — was fixed, came back)")

    print("\n" + "=" * 64)
    print("Delta the orchestrator adds that the stateless audit cannot:")
    print("=" * 64)
    print("  - 'resolved' confirms the coupling fix held (positive feedback).")
    print("  - 'reopened' flags the magic value as a regression, not a new")
    print("    finding — the single most actionable signal across commits.")


if __name__ == "__main__":
    main()
