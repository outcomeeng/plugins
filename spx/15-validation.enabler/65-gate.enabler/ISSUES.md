# Known Issues

## Compliance assertion does not lock the `fmt-check` (dprint) step (FOLLOW-UP)

`gate.md`'s Compliance assertion enumerates the `ruff format --check`, `ruff check`, and `spx validation markdown` steps that `STEPS` must include, verified by `test_gate.compliance.l1.py`. It does not name the `fmt-check` (`dprint check`) step, which is also in `STEPS`. A change that accidentally dropped `dprint check` from the gate would not be caught by any compliance test.

The assertion was originally scoped to the steps that had drifted out of `just check` (lint and Markdown link checking); `fmt-check` has no such history, so its omission is deliberate rather than an oversight. Whether to extend the assertion and the compliance test to also lock the `fmt-check` step is a coverage decision, not a defect in the current gate.

Surfaced by the local `review-changes` gate on `build/python-ruff-formatting`.

## `test_gate.scenario.l2.py` grace window flakes under the gate's own load

`test_signal_terminates_process_group_within_grace[1]` (the 1-second grace case in `test_gate.scenario.l2.py`) intermittently fails its `assert not _process_is_alive(child_pid)` when run inside a full `just check`: the gate forks dozens of subprocesses, and on a busy host the signalled process group does not finish exiting within the 1-second window. On a quiet machine the same case passes (verified: all three grace cases green when re-run in isolation at loadavg ~2.3 on 12 cores). The behavior under test — signal terminates the process group within grace — is correct; the 1-second case's window is too tight to be reliable under the load the gate itself generates.

**Resolution shape**: make the shortest grace case load-aware (skip or widen the window when loadavg exceeds the core count), or raise the smallest grace bound so the assertion is not starved by the gate's own concurrency. Keep the longer-grace cases as the behavioral evidence.

Surfaced during PR #205's post-rebase `just check` (2026-06-14); confirmed starvation, not a defect.
