# Known Issues

## Compliance assertion does not lock the `fmt-check` (dprint) step (FOLLOW-UP)

`gate.md`'s Compliance assertion enumerates the `ruff format --check`, `ruff check`, and `spx validation markdown` steps that `STEPS` must include, verified by `test_gate.compliance.l1.py`. It does not name the `fmt-check` (`dprint check`) step, which is also in `STEPS`. A change that accidentally dropped `dprint check` from the gate would not be caught by any compliance test.

The assertion was originally scoped to the steps that had drifted out of `just check` (lint and Markdown link checking); `fmt-check` has no such history, so its omission is deliberate rather than an oversight. Whether to extend the assertion and the compliance test to also lock the `fmt-check` step is a coverage decision, not a defect in the current gate.

Surfaced by the local `reviewing-changes` gate on `build/python-ruff-formatting`.
