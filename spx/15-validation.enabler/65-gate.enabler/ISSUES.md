# Known Issues

## mypy: `int` assigned to a `Signals`-typed variable in the signal-restore loop

`uv run mypy outcomeeng/validation/_engine.py` reports:

```text
outcomeeng/validation/_engine.py:113: error: Incompatible types in assignment (expression has type "int", variable has type "Signals")  [assignment]
```

Line 113 is the `for sig, old in old_handlers.items():` loop in the `run` function's `finally` block, which restores the original signal handlers. The loop variable's inferred type disagrees with the `Signals` annotation carried by the handler mapping.

mypy is not part of the committed quality gate: `just check` runs ruff, the manifest and skill validators, markdown link-checking, and pytest — not mypy or pyright. The error therefore does not fail CI and surfaces only on an explicit mypy run. Resolve by aligning the key type of the `old_handlers` mapping with the value `signal.signal` returns and `.items()` yields.
