# Check Pipeline

PROVIDES a signal-safe orchestrator that runs the marketplace quality-gate steps in declared order, prints a labeled header before each step and a per-step timing summary at the end, and stops at the first failing step
SO THAT the `just check` recipe, contributor workstations, and CI
CAN trust that the same quality-gate steps run in the same order, that an interrupt cleanly terminates the in-flight subprocess and its descendants, and that a failing step surfaces with a partial timing summary identifying the failure

## Assertions

### Scenarios

- Given the declared step list and all steps exiting 0, when the orchestrator runs, then a `━━━ {label} ━━━` header prints before each step's subprocess starts, a `━━━ Timing Summary ━━━` block follows the last step with one `{label}  {elapsed}s` row per step plus a `TOTAL` row, and the orchestrator exits 0 ([test](tests/test_check_pipeline.scenario.l1.py))
- Given a step at position k that exits with a non-zero status, when the orchestrator runs, then steps at positions k+1..N do not start, the timing summary prints rows for steps 1..k followed by a `FAILED  {label}` row naming the failing step, and the orchestrator exits with that step's status code ([test](tests/test_check_pipeline.scenario.l1.py))
- Given an in-flight child subprocess and a SIGTERM, SIGINT, or SIGHUP delivered to the orchestrator, when the signal is delivered, then the child's process group receives SIGTERM, the orchestrator waits up to two seconds for the child to exit, sends SIGKILL to the process group if the child is still running, and exits with status `128 + signum` ([test](tests/test_check_pipeline.scenario.l2.py))

### Properties

- For any non-empty step list, the order in which subprocesses are started matches the order of the step list ([test](tests/test_check_pipeline.property.l1.py))
- For any step that exits 0, the elapsed-time value recorded in the timing summary is a non-negative integer ([test](tests/test_check_pipeline.property.l1.py))

### Compliance

- ALWAYS: the declared step list includes a `ruff check` step and a `spx validation markdown` step — `spx/ISSUES.md` records prior lint and link drift attributed to their absence from `just check` ([test](tests/test_check_pipeline.compliance.l1.py))
- ALWAYS: each child subprocess is started with `start_new_session=True` so signal forwarding targets a process group, never a single PID — prevents orphaned grandchildren when the orchestrator is interrupted ([test](tests/test_check_pipeline.compliance.l1.py))
- ALWAYS: the SIGKILL grace-period wait is bounded by a single `time.monotonic()` deadline computed once per signal — bounded polling for a process exit is the only wait the orchestrator performs, consistent with `spx/13-plugin-and-runtime-conventions.adr.md` `<no_until_polling>` ([test](tests/test_check_pipeline.compliance.l1.py))
- NEVER: the orchestrator source contains a literal `gh run watch` invocation or a `while True:` loop containing `time.sleep` — unbounded polling waits are forbidden across the marketplace per `spx/13-plugin-and-runtime-conventions.adr.md` ([test](tests/test_check_pipeline.compliance.l1.py))
