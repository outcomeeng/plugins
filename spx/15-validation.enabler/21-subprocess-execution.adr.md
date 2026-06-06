# Subprocess Execution in the Validation Package

The validation package exposes one subprocess seam per pattern, both passed through dependency injection. The gate orchestrator accepts a `ProcessSpawner` Protocol for subprocess creation and a `TextIO`-like sink for output; its production entry point binds them to `subprocess.Popen` (with `start_new_session=True`) and `sys.stdout`, while `l1` tests bind in-process doubles that record invocations and emit deterministic exit codes. A capturing validator CLI runs each external process through a dependency-injected runner whose default bounds the wait with an explicit timeout, isolates the child's standard input, captures output without depending on a descendant closing an inherited stream, starts the child in its own process group, and `SIGKILL`s the group on expiry. No validation-package code performs an unbounded capture that blocks while a surviving descendant holds the stream, and the gate's step list is a module-level `tuple[Step, ...]` of `Step(label, argv)`.

## Rationale

A `ProcessSpawner` Protocol whose method returns a handle implementing `pid`, `poll`, `wait`, and a process-group signalling contract gives the orchestrator one observable seam; production binds it to a thin `subprocess.Popen` adapter and tests bind a recording double, so the signal-handling, step-iteration, and timing-summary paths all run without launching real validators. An output sink as a second injected dependency lets tests capture header and timing lines as strings. The step list stays a module-level tuple because steps are inert data and a constant keeps the gate's composition falsifiable by reading it rather than running the orchestrator. A capturing runner that writes the child's output to a file rather than reading an inherited pipe makes the wait depend only on the invoked process exiting, and the timeout plus process-group `SIGKILL` bound the wait even when the child hangs or ignores `SIGTERM`. Framework replacement of `subprocess`, a full `Runner` Protocol owning the step loop, a TOML-driven step list, an unbounded `capture_output=True`, and a capture bounded only by `subprocess.run(timeout=...)` are each rejected — they violate the dependency-injection standard, move the logic-under-test behind an interface, add needless configurability, or fail to bound the wait when a descendant holds the stream.

## Verification

### Testing

- ALWAYS: on timeout, the capturing runner returns a non-zero result identifying the timed-out command — preserving the package's exit-code contract when a child fails to exit ([compliance])
- NEVER: a capturing validator CLI performs an unbounded capture that waits on pipe EOF — a surviving descendant holding the stream blocks the read without bound ([compliance])
- NEVER: a capturing CLI relies on `SIGTERM` alone to stop a child — a child that ignores the signal leaves the wait unbounded ([compliance])

### Audit

- ALWAYS: the orchestrator's step-execution function accepts the `ProcessSpawner` and the output sink as parameters — enabling `l1` verification of step ordering, header emission, timing summary, and exit-code propagation without launching real validators ([audit])
- ALWAYS: the `ProcessSpawner` Protocol method returns a handle exposing `pid: int`, `poll() -> int | None`, `wait() -> int`, and `send_signal_to_group(sig: int) -> None` — naming every observable the signal-handling path needs ([audit])
- ALWAYS: the production `ProcessSpawner` adapter passes `start_new_session=True` so `send_signal_to_group` can target the child's process group via `os.killpg` ([audit])
- ALWAYS: the step list is exposed as a module-level `tuple[Step, ...]` constant (`STEPS`) importable by tests ([audit])
- ALWAYS: a capturing validator CLI runs each external-process invocation through a dependency-injected runner whose default bounds the wait with an explicit, overridable timeout, isolates stdin, captures output without depending on a descendant closing an inherited stream, and `SIGKILL`s the child's process group on expiry ([audit])
- ALWAYS: the capturing runner's wait-bound is a source-owned constant on the owning module, imported by tests rather than restated ([audit])
- NEVER: a gate orchestrator module (`_engine.py`, `_model.py`, `_spawner.py`, `_steps.py`, `__init__.py`, `__main__.py`) imports `subprocess` outside the production `_spawner.py` adapter ([audit])
- NEVER: tests for the orchestrator use `unittest.mock.patch`, `monkeypatch.setattr`, or `MagicMock` to replace `subprocess`, `os.killpg`, `time.monotonic`, or any module the orchestrator imports ([audit])
- NEVER: the step list is loaded from a config file, environment variable, or plugin discovery mechanism — the fixed tuple is the safeguard against gate-composition drift ([audit])
