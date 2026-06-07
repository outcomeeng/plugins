# Known Issues

## mypy: `int` assigned to a `Signals`-typed variable in the signal-restore loop

`uv run mypy outcomeeng/validation/_engine.py` reports:

```text
outcomeeng/validation/_engine.py:113: error: Incompatible types in assignment (expression has type "int", variable has type "Signals")  [assignment]
```

Line 113 is the `for sig, old in old_handlers.items():` loop in the `run` function's `finally` block, which restores the original signal handlers. The loop variable's inferred type disagrees with the `Signals` annotation carried by the handler mapping.

mypy is not part of the committed quality gate: `just check` runs ruff, the manifest and skill validators, markdown link-checking, and pytest — not mypy or pyright. The error therefore does not fail CI and surfaces only on an explicit mypy run. Resolve by aligning the key type of the `old_handlers` mapping with the value `signal.signal` returns and `.items()` yields.

## Compliance assertion does not lock the `fmt-check` (dprint) step (FOLLOW-UP)

`gate.md`'s Compliance assertion enumerates the `ruff format --check`, `ruff check`, and `spx validation markdown` steps that `STEPS` must include, verified by `test_gate.compliance.l1.py`. It does not name the `fmt-check` (`dprint check`) step, which is also in `STEPS`. A change that accidentally dropped `dprint check` from the gate would not be caught by any compliance test.

The assertion was originally scoped to the steps that had drifted out of `just check` (lint and Markdown link checking); `fmt-check` has no such history, so its omission is deliberate rather than an oversight. Whether to extend the assertion and the compliance test to also lock the `fmt-check` step is a coverage decision, not a defect in the current gate.

Surfaced by the local `reviewing-changes` gate on `build/python-ruff-formatting`.
