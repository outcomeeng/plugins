# Gate

PROVIDES a signal-safe orchestrator that runs the marketplace quality-gate steps in declared order, writes each step's combined stdout/stderr to a temp log while it runs, removes successful step logs, prints only gate status and timing lines for passing steps, prints a capped failure excerpt plus the retained full log path for a failing step, and stops at the first failing step
SO THAT the `just check` recipe, contributor workstations, and CI
CAN trust that the same quality-gate steps run in the same order, that passing command output does not flood the live agent session, that an interrupt cleanly terminates the in-flight subprocess and its descendants, and that a failing step surfaces with enough excerpted output plus a full log path for diagnosis

## Assertions

### Scenarios

- Given the declared step list and all steps exiting 0, when the orchestrator runs, then a `━━━ {label} ━━━` header prints before each step's subprocess starts, each step writes combined stdout/stderr to a temp log while it runs, each completed step removes its log and prints a `PASS  {label}  {elapsed}s` status line without printing the step's captured output, a `━━━ Timing Summary ━━━` block follows the last step with one `{label}  {elapsed}s` row per step plus a `TOTAL` row, and the orchestrator exits 0 ([test](tests/test_gate.scenario.l1.py))
- Given a step at position k that exits with a non-zero status, when the orchestrator runs, then steps at positions k+1..N do not start, the failing step writes combined stdout/stderr to a retained temp log, the live output prints a `FAIL  {label}  {elapsed}s  exit {status}` status line, a capped excerpt from the failing log, and the full failing log path, successful step logs are removed, the timing summary prints rows for steps 1..k followed by a `FAILED  {label}` row naming the failing step, and the orchestrator exits with that step's status code ([test](tests/test_gate.scenario.l1.py))
- Given an in-flight child subprocess and a SIGTERM, SIGINT, or SIGHUP delivered to the orchestrator, when the signal is delivered, then the child's process group receives SIGTERM, the orchestrator waits up to two seconds for the child to exit, sends SIGKILL to the process group if the child is still running, performs a bounded direct-child reap check, and exits with status `128 + signum` ([test](tests/test_gate.scenario.l2.py))

### Properties

- For any non-empty step list, the order in which subprocesses are started matches the order of the step list ([test](tests/test_gate.property.l1.py))
- For any step that exits 0, the elapsed-time value recorded in the timing summary is a non-negative integer ([test](tests/test_gate.property.l1.py))

### Compliance

- ALWAYS: the declared step list includes a `fmt-check` (`dprint check`) step, a `ruff format --check` step, a `ruff check` step, a `mypy --strict` package step, a `pyright` package step, a `spx validation markdown` step, and a hook-safety step — so repository formatting, Python formatting, lint, package type checking, Markdown link integrity, and shipped-hook safety are each enforced on every `just check` ([test](tests/test_gate.compliance.l1.py))
- ALWAYS: each child subprocess is started with `start_new_session=True` so signal forwarding targets a process group, never a single PID — prevents orphaned grandchildren when the orchestrator is interrupted ([test](tests/test_gate.compliance.l1.py))
- ALWAYS: the SIGKILL grace-period wait is bounded by a single `time.monotonic()` deadline computed once per signal, and the post-kill direct-child reap check is fixed-count — bounded polling for process exit is the only wait the orchestrator performs, consistent with `spx/13-plugin-and-runtime-conventions.adr.md` `<no_until_polling>` ([test](tests/test_gate.compliance.l1.py))
- NEVER: the orchestrator source contains a literal `gh run watch` invocation or a `while True:` loop containing `time.sleep` — unbounded polling waits are forbidden across the marketplace per `spx/13-plugin-and-runtime-conventions.adr.md` ([test](tests/test_gate.compliance.l1.py))
