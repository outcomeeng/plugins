# Subprocess Execution in the Validation Package

## Purpose

This decision governs how the validation package (`outcomeeng/validation/`) creates and supervises subprocesses across its two patterns of use: the gate orchestrator, which streams each step's output and forwards OS signals to the child's process group, and the capturing validator CLIs (`plugins.py` and peers), which collect each child's output to report results. The gate orchestrator's behavior — step ordering, header printing, timing summary, exit-code propagation, signal forwarding — is verifiable at `l1` without invoking the real validators it wraps; a capturing CLI bounds every external-process wait so that a child which fails to exit, or a descendant which holds an inherited output stream open, can never hang the toolchain.

## Context

**Business impact:** The validation package runs the marketplace's quality gate and its standalone validators (manifest validation, skill-frontmatter checks, install verification). A regression in the gate orchestrator's sequencing, signal handling, or exit-code propagation silently weakens the gate. A capturing validator that blocks forever on a misbehaving child stalls `just check`, the pre-commit hook, and CI with no diagnostic, forcing a manual kill.

**Technical constraints:**

- The gate orchestrator delegates each step to a subprocess and must survive `SIGTERM`, `SIGINT`, and `SIGHUP` cleanly, forwarding to the child's process group. Real validator steps invoke `uv run python -m ...`, `dprint`, and `spx validation markdown`; each costs seconds, requires the marketplace's `uv` environment, and produces output a unit test cannot meaningfully assert on.
- A capturing CLI reads each child's stdout and stderr to report which target failed. Capturing through inherited pipes ties the read to pipe EOF, which arrives only once every write-end closes; a short-lived descendant in the child's process group holds that write-end open after the invoked process has exited, blocking the read without bound. A timeout on the capture call alone does not bound this — the standard library kills the direct child on expiry and resumes a read that a surviving descendant still blocks. Some children — the Claude Code CLI among them — ignore `SIGTERM`, so only `SIGKILL` to the whole process group reliably stops them.
- `spx/15-test-infrastructure.pdr.md` mandates harnesses for subprocess access, prohibits framework mocks for the behavior under test, and requires source-owned protocol values.
- `spx/13-plugin-and-runtime-conventions.adr.md` forbids unbounded polling and long-lived subprocesses, leaving signal-driven termination as the only acceptable interruption path.

## Decision

The validation package exposes one subprocess seam per pattern, both passed through dependency injection. The gate orchestrator accepts a `ProcessSpawner` Protocol for subprocess creation and a `TextIO`-like sink for output; its production entry point binds them to `subprocess.Popen` (with `start_new_session=True`) and `sys.stdout`, and `l1` tests bind them to in-process doubles that record invocations and emit deterministic exit codes. A capturing validator CLI runs each external process through a dependency-injected runner whose default implementation bounds the wait with an explicit timeout, isolates the child's standard input, captures output without depending on a descendant closing an inherited stream, starts the child in its own process group, and signals the whole group with `SIGKILL` on expiry. No validation-package code performs an unbounded capture that blocks while a surviving descendant holds the stream.

## Rationale

A `ProcessSpawner` Protocol whose single method returns an object implementing `pid`, `poll`, `wait`, and a process-group-aware signalling contract gives the orchestrator one observable seam. Production binds it to a thin adapter over `subprocess.Popen`; tests bind it to a recording double that returns scripted exit codes. The orchestrator never imports `subprocess` directly, so the signal-handling path, step-iteration path, and timing-summary path all run under test without launching real validators.

An output sink as a second injected dependency lets tests capture the header lines (`━━━ {label} ━━━`) and timing summary (`━━━ Timing Summary ━━━` followed by rows) as strings rather than scraping stdout. Production binds it to `sys.stdout`; tests bind it to `io.StringIO`. The sink boundary keeps the orchestrator's prose stable while letting tests assert on what gets emitted.

The step list stays as a module-level `tuple[Step, ...]` of `Step(label, argv)` dataclass instances. Steps are inert data — they do not require their own injection seam — and a module-level tuple keeps `spx/15-validation.enabler/65-gate.enabler/gate.md`'s compliance assertion ("the declared step list includes `ruff check` and `spx validation markdown`") falsifiable by reading the constant rather than running the orchestrator.

A capturing runner that writes the child's output to a file rather than reading an inherited pipe makes the wait depend only on the invoked process exiting, so a descendant that keeps the stream open cannot block the read. The timeout plus process-group `SIGKILL` bound the wait even when the child itself hangs or ignores `SIGTERM`. Dependency injection keeps the command-building logic verifiable at `l1` and lets a test drive the bounded-wait path with a real controlled process rather than a substituted dependency.

Alternatives rejected:

- `monkeypatch.setattr("subprocess.Popen", ...)` in tests — directly violates `spx/15-test-infrastructure.pdr.md` `<dependency_injection>`.
- A full `Runner` Protocol that owns the entire step loop — moves the logic-under-test behind an interface; assertions about ordering, headers, and timing become tests of the test double instead of the orchestrator.
- Reading the step list from a TOML file — adds I/O and parsing surface; the gain is configurability the marketplace does not need (the step set is intentionally fixed and reviewed in PRs).
- An unbounded `subprocess.run(..., capture_output=True)` in a capturing CLI — blocks on pipe EOF when a descendant holds the write-end, the failure this decision exists to prevent.
- A capture call bounded only by `subprocess.run(timeout=...)` while retaining inherited pipes — resumes a blocking read on expiry, so the bound is not enforced.

## Trade-offs accepted

| Trade-off                                                                                                                              | Mitigation / reasoning                                                                                                                                                                    |
| -------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Two injected dependencies instead of zero for the orchestrator                                                                         | The production entry point binds both in one place; consumers of `just check` see no change. Tests gain `l1` coverage of every observable behavior.                                       |
| Step list edits require a PR rather than a config change                                                                               | The fixed step list is the point — drift in the gate's composition is what `spx/ISSUES.md` flags as the regression to prevent.                                                            |
| `ProcessSpawner` Protocol leaks `subprocess.Popen` semantics (process groups, signal forwarding) into a marketplace-internal interface | The orchestrator's contract IS the process-group semantics; abstracting them away would defeat the purpose. The Protocol names them explicitly so test doubles implement them faithfully. |
| A capturing runner writes output to a temp file instead of streaming it                                                                | The temp file is caller-owned and removed on every exit path; its cost is bounded and small relative to an unbounded hang.                                                                |
| The capturing runner's bound can cut off a legitimately slow validator                                                                 | The bound is generous and source-owned; a wrapped CLI that exceeds it is itself the defect, since it returns promptly in normal operation.                                                |

## Compliance

### Recognized by

The orchestrator module exposes a top-level `run(spawner: ProcessSpawner, sink: TextIO, steps: tuple[Step, ...]) -> int` function. The production entry point (`outcomeeng/validation/__main__.py`'s `if __name__ == "__main__":` block) constructs the default `ProcessSpawner` adapter over `subprocess.Popen` and passes `sys.stdout`. `l1` tests pass recording doubles for both. The gate orchestrator's underscore-prefixed modules (`_engine.py`, `_model.py`, `_spawner.py`, `_steps.py`, plus `__init__.py` and `__main__.py`) import `subprocess` only in the production `_spawner.py` adapter. A capturing validator CLI (`plugins.py` and peers) invokes each external process through a runner that bounds the wait, isolates stdin, captures output without blocking on a descendant-held stream, and `SIGKILL`s the process group on expiry; the wait-bound is a source-owned module constant.

### MUST

- The orchestrator's step-execution function accepts the `ProcessSpawner` and the output sink as parameters — enables `l1` verification of step ordering, header emission, timing summary content, and exit-code propagation without launching real validators ([review])
- The `ProcessSpawner` Protocol method returns a handle exposing `pid: int`, `poll() -> int | None`, `wait() -> int`, and `send_signal_to_group(sig: int) -> None` — names every observable the signal-handling path needs ([review])
- The production `ProcessSpawner` adapter passes `start_new_session=True` to `subprocess.Popen` so the returned handle's `send_signal_to_group` can target the child's process group via `os.killpg` — keeps the orchestrator's signal-forwarding promise on a real OS process tree ([review])
- The step list is exposed as a module-level `tuple[Step, ...]` constant (`STEPS`) importable by tests — enables the `spx/15-validation.enabler/65-gate.enabler/gate.md` compliance assertion about `ruff check` and `spx validation markdown` to be verified by reading the constant ([review])
- A capturing validator CLI runs each external-process invocation through a dependency-injected runner whose default bounds the wait with an explicit, overridable timeout, isolates the child's standard input, captures output without depending on a descendant closing an inherited stream, and `SIGKILL`s the child's process group on expiry; the overridable timeout lets an `l1` test drive the bounded-wait path with a real controlled child ([review])
- The capturing runner's wait-bound is a source-owned constant on the owning module, imported by tests rather than restated — keeps the bound single-sourced ([review])
- On timeout, the capturing runner returns a non-zero result identifying the timed-out command — preserves the package's exit-code contract when a child fails to exit ([review])

### NEVER

- A gate orchestrator module (`_engine.py`, `_model.py`, `_spawner.py`, `_steps.py`, `__init__.py`, `__main__.py`) imports `subprocess` outside the production `_spawner.py` adapter — coupling the step loop to the real subprocess module defeats `l1` testability ([review])
- Tests for the orchestrator use `unittest.mock.patch`, `monkeypatch.setattr`, or `MagicMock` to replace `subprocess`, `os.killpg`, `time.monotonic`, or any other module the orchestrator imports — `spx/15-test-infrastructure.pdr.md` `<dependency_injection>` prohibits framework replacement of the behavior under test ([review])
- The step list is loaded from a config file, environment variable, or plugin discovery mechanism — drift in the gate's composition is the regression `spx/ISSUES.md` records; the fixed tuple is the safeguard ([review])
- A capturing validator CLI performs an unbounded capture that waits on pipe EOF — a surviving descendant holding the stream blocks the read without bound ([review])
- A capturing CLI relies on `SIGTERM` alone to stop a child — a child that ignores the signal leaves the wait unbounded ([review])
