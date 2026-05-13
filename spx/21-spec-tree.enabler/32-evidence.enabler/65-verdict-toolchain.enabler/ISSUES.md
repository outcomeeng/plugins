# Issues: Verdict Toolchain Enabler

## 1. `verdict_toolchain.py` resolves `SCRIPTS_DIR` at import time without an early guard

`outcomeeng_testing/harnesses/verdict_toolchain.py` walks `pathlib.Path(__file__).resolve().parents[2]` to compute `SCRIPTS_DIR`. If the file is moved (or the marketplace layout shifts) the hop count silently becomes wrong: the path stays a `Path`, no exception fires at import, and the first test subprocess call surfaces a confusing `FileNotFoundError` on the script path instead of a clear configuration error.

A cheap module-level guard catches the problem at the import that loads `verdict_toolchain` rather than at the first subprocess invocation:

```python
if not SCRIPTS_DIR.is_dir():
    raise RuntimeError(
        f"SCRIPTS_DIR not found at {SCRIPTS_DIR}; "
        "verify the parents[] hop count in verdict_toolchain.py "
        "matches the file's location relative to the repo root."
    )
```

Surfaced by `claude-review` on PR 14 round 3 (2026-05-13).
