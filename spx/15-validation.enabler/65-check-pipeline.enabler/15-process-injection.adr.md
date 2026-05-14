# Process Injection for the Check Pipeline

## Purpose

This decision governs how the check-pipeline orchestrator creates and supervises subprocesses, so that the orchestrator's behavior — step ordering, header printing, timing summary, exit-code propagation, signal forwarding — is verifiable at `l1` without invoking the real validators it wraps.

## Context

**Business impact:** The orchestrator runs every step in the marketplace's quality gate. A regression in its sequencing, signal handling, or exit-code propagation silently weakens the gate. Verification has to be cheap enough to run on every change, which means `l1` tests against the orchestrator's logic — not `l2` integration tests against `ruff`, `pytest`, and `dprint`.

**Technical constraints:**

- The orchestrator delegates each step to a subprocess and must survive `SIGTERM`, `SIGINT`, and `SIGHUP` cleanly, forwarding to the child's process group.
- Real validator steps invoke `uv run python -m ...`, `dprint`, and `spx validation markdown`. Each adds seconds of wall-clock time, requires the marketplace's `uv` environment, and produces output that a unit test cannot meaningfully assert on.
- `spx/15-test-infrastructure.pdr.md` mandates harnesses for subprocess access, prohibits framework mocks for the behavior under test, and requires source-owned protocol values.
- `spx/13-plugin-and-runtime-conventions.adr.md` forbids unbounded polling and long-lived subprocesses, leaving signal-driven termination as the only acceptable interruption path.

## Decision

The check-pipeline orchestrator accepts a `ProcessSpawner` Protocol parameter for subprocess creation and a `TextIO`-like sink for output, both passed through dependency injection; the production entry point binds them to `subprocess.Popen` (with `start_new_session=True`) and `sys.stdout`, and `l1` tests bind them to in-process doubles that record invocations and emit deterministic exit codes.

## Rationale

A `ProcessSpawner` Protocol whose single method returns an object implementing `pid`, `poll`, `wait`, and a process-group-aware `terminate`/`kill` contract gives the orchestrator one observable seam. Production binds it to a thin adapter over `subprocess.Popen`; tests bind it to a recording double that returns scripted exit codes. The orchestrator never imports `subprocess` directly, so the signal-handling path, step-iteration path, and timing-summary path all run under test without launching real validators.

An output sink as a second injected dependency lets tests capture the header lines (`━━━ {label} ━━━`) and timing summary (`━━━ Timing Summary ━━━` followed by rows) as strings rather than scraping stdout. Production binds it to `sys.stdout`; tests bind it to `io.StringIO`. The sink boundary keeps the orchestrator's prose stable while letting tests assert on what gets emitted.

The step list stays as a module-level `tuple[Step, ...]` of `Step(label, argv)` dataclass instances. Steps are inert data — they do not require their own injection seam — and a module-level tuple keeps `spx/15-validation.enabler/65-check-pipeline.enabler/check-pipeline.md`'s compliance assertion ("the declared step list includes `ruff check` and `spx validation markdown`") falsifiable by reading the constant rather than running the orchestrator.

Alternatives rejected:

- `monkeypatch.setattr("subprocess.Popen", ...)` in tests — directly violates `spx/15-test-infrastructure.pdr.md` `<dependency_injection>`.
- A full `Runner` Protocol that owns the entire step loop — moves the logic-under-test behind an interface; assertions about ordering, headers, and timing become tests of the test double instead of the orchestrator.
- Reading the step list from a TOML file — adds I/O and parsing surface; the gain is configurability the marketplace does not need (the step set is intentionally fixed and reviewed in PRs).

## Trade-offs accepted

| Trade-off                                                                                                                              | Mitigation / reasoning                                                                                                                                                                    |
| -------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Two injected dependencies instead of zero                                                                                              | The production entry point binds both in one place; consumers of `just check` see no change. Tests gain `l1` coverage of every observable behavior.                                       |
| Step list edits require a PR rather than a config change                                                                               | The fixed step list is the point — drift in the gate's composition is what `spx/ISSUES.md` flags as the regression to prevent.                                                            |
| `ProcessSpawner` Protocol leaks `subprocess.Popen` semantics (process groups, signal forwarding) into a marketplace-internal interface | The orchestrator's contract IS the process-group semantics; abstracting them away would defeat the purpose. The Protocol names them explicitly so test doubles implement them faithfully. |

## Compliance

### Recognized by

The orchestrator module exposes a top-level `run(spawner: ProcessSpawner, sink: TextIO, steps: tuple[Step, ...]) -> int` function. The production entry point (`outcomeeng/scripts/check.py`'s `if __name__ == "__main__":` block) constructs the default `ProcessSpawner` adapter over `subprocess.Popen` and passes `sys.stdout`. `l1` tests pass recording doubles for both. No module under `outcomeeng/scripts/check_pipeline/` imports `subprocess` outside the production adapter.

### MUST

- The orchestrator's step-execution function accepts the `ProcessSpawner` and the output sink as parameters — enables `l1` verification of step ordering, header emission, timing summary content, and exit-code propagation without launching real validators ([review])
- The `ProcessSpawner` Protocol method returns a handle exposing `pid: int`, `poll() -> int | None`, `wait() -> int`, and `send_signal_to_group(sig: int) -> None` — names every observable the signal-handling path needs ([review])
- The production `ProcessSpawner` adapter passes `start_new_session=True` to `subprocess.Popen` so the returned handle's `send_signal_to_group` can target the child's process group via `os.killpg` — keeps the orchestrator's signal-forwarding promise on a real OS process tree ([review])
- The step list is exposed as a module-level `tuple[Step, ...]` constant (`STEPS`) importable by tests — enables the `spx/15-validation.enabler/65-check-pipeline.enabler/check-pipeline.md` compliance assertion about `ruff check` and `spx validation markdown` to be verified by reading the constant ([review])

### NEVER

- The orchestrator module imports `subprocess` outside the production `ProcessSpawner` adapter — coupling the step loop to the real subprocess module defeats `l1` testability ([review])
- Tests for the orchestrator use `unittest.mock.patch`, `monkeypatch.setattr`, or `MagicMock` to replace `subprocess`, `os.killpg`, `time.monotonic`, or any other module the orchestrator imports — `spx/15-test-infrastructure.pdr.md` `<dependency_injection>` prohibits framework replacement of the behavior under test ([review])
- The step list is loaded from a config file, environment variable, or plugin discovery mechanism — drift in the gate's composition is the regression `spx/ISSUES.md` records; the fixed tuple is the safeguard ([review])
