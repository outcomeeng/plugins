# Gate

PROVIDES a signal-safe recipe orchestrator with two primitive deterministic verification recipes, `validation` and `test`, plus a `check` wrapper that composes them
SO THAT the `just validation`, `just test`, and `just check` recipes, contributor workstations, CI, and coding agents
CAN run conformance and correctness verification with bounded live output, retained failure diagnostics, structured summaries, and verification vocabulary aligned to `spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md`

## Assertions

### Scenarios

- Given the `validation` primitive recipe and all preflight and recipe steps exiting 0, when the orchestrator runs, then preflight runs inside the orchestrator before validation steps, each step writes combined stdout/stderr to a temp log while it runs, each completed step removes its log and prints a `PASS  {label}  {elapsed}s` status line without printing captured child output, the run summary records `recipe: validation`, `verification_type: validation`, `purpose: conformance`, phase, commands, statuses, durations, and exit codes without discarded log paths, and the orchestrator exits 0 ([test](tests/test_gate.scenario.l1.py))
- Given the `test` primitive recipe and all preflight and recipe steps exiting 0, when the orchestrator runs, then preflight runs inside the orchestrator before the pytest-backed `[test]` step, the run summary records `recipe: test`, `verification_type: testing`, `purpose: correctness`, phase, commands, statuses, durations, and exit codes without discarded log paths, and the orchestrator exits 0 ([test](tests/test_gate.scenario.l1.py))
- Given a primitive recipe step at position k that exits with a non-zero status, when the orchestrator runs, then steps at positions k+1..N do not start, the failing step writes combined stdout/stderr to a retained temp log, the live output prints a `FAIL  {label}  {elapsed}s  exit {status}` status line, a capped excerpt from the failing log, the retained full log path, and the structured summary path, successful step logs are removed, the timing summary prints rows for steps 1..k followed by a `FAILED  {label}` row naming the failing step, the summary records the failed phase, command, exit code, excerpt, and full log path, and the orchestrator exits with that step's status code ([test](tests/test_gate.scenario.l1.py))
- Given a primitive recipe step fails before returning a child handle, when the orchestrator runs, then the failing step writes the spawn failure to a retained temp log, the live output prints the failed step status, the summary records the failed phase, exit code, excerpt, and full log path, and the orchestrator exits non-zero ([test](tests/test_gate.scenario.l1.py))
- Given the `check` wrapper and the `validation` primitive recipe failing, when the orchestrator runs, then `test` does not start, the wrapper summary reports `recipe: check`, no `verification_type`, aggregate failed status from the validation primitive summary, and no third verification type ([test](tests/test_gate.scenario.l1.py))
- Given the `check` wrapper and the `validation` primitive recipe passing, when the orchestrator runs, then `test` starts after validation, and the wrapper summary aggregates the validation and test primitive summaries in that order ([test](tests/test_gate.scenario.l1.py))
- Given the `check` wrapper receives SIGTERM, SIGINT, or SIGHUP before a child handle is available, when the wrapper handles the signal, then it exits with status `128 + signum` and writes a failed check summary without step records ([test](tests/test_gate.scenario.l1.py))
- Given SIGTERM, SIGINT, or SIGHUP arrives during production child spawn after the child process exists, when the spawn call returns, then the orchestrator forwards the signal to the child process group, applies the bounded SIGKILL escalation if the child ignores SIGTERM, records the failed step, and exits with status `128 + signum` ([test](tests/test_gate.scenario.l2.py))
- Given an in-flight child subprocess and a SIGTERM, SIGINT, or SIGHUP delivered to the orchestrator, when the signal is delivered, then the child's process group receives SIGTERM, the orchestrator waits up to two seconds for the child to exit, sends SIGKILL to the process group if the child is still running, performs a bounded direct-child reap check, and exits with status `128 + signum` ([test](tests/test_gate.scenario.l2.py))

### Conformance

- Every structured run summary conforms to the gate summary schema: top-level recipe, phase, status, exit code, summary path, primitive recipe summaries, and step records with recipe, phase, label, command argv, status, duration, exit code, optional retained log path, and optional excerpt ([test](tests/test_gate.conformance.l1.py))

### Properties

- For any non-empty step list, the order in which subprocesses are started matches the order of the step list ([test](tests/test_gate.property.l1.py))
- For any step that exits 0, the elapsed-time value recorded in the timing summary is a non-negative integer ([test](tests/test_gate.property.l1.py))

### Compliance

- ALWAYS: the declared step list includes a `fmt-check` (`dprint check`) step, a `ruff format --check` step, a `ruff check` step, a `mypy --strict` package step, a `pyright` package step, a `spx validation markdown` step, and a hook-safety step — so repository formatting, Python formatting, lint, package type checking, Markdown link integrity, and shipped-hook safety are each enforced on every `just check` ([test](tests/test_gate.compliance.l1.py))
- ALWAYS: the `validation` primitive recipe reports `verification_type: validation` and `purpose: conformance`, and the `test` primitive recipe reports `verification_type: testing` and `purpose: correctness`, matching `spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md` and the `/understanding` verification taxonomy ([test](tests/test_gate.compliance.l1.py))
- NEVER: the `check` wrapper introduces a third verification type — it reports aggregate primitive results only ([test](tests/test_gate.compliance.l1.py))
- ALWAYS: the `validation` primitive recipe includes a `fmt-check` (`dprint check`) step, a `ruff format --check` step, a `ruff check` step, a `mypy --strict` package step, a `pyright` package step, and a `spx validation markdown` step, and excludes the pytest-backed `[test]` evidence step ([test](tests/test_gate.compliance.l1.py))
- ALWAYS: the `test` primitive recipe executes pytest-backed `[test]` evidence through the configured runner and excludes deterministic validation steps ([test](tests/test_gate.compliance.l1.py))
- ALWAYS: passing child stdout/stderr is captured to temp logs and never streamed line-by-line to the live session; passing live output grows with recipe step count, not child output volume ([test](tests/test_gate.compliance.l1.py))
- ALWAYS: each child subprocess is started with `start_new_session=True` so signal forwarding targets a process group, never a single PID — prevents orphaned grandchildren when the orchestrator is interrupted ([test](tests/test_gate.compliance.l1.py))
- ALWAYS: each production child subprocess unblocks SIGTERM, SIGINT, and SIGHUP before exec so the orchestrator's protected spawn window does not make validators inherit a blocked forwarded-signal mask ([test](tests/test_gate.compliance.l1.py))
- ALWAYS: the SIGKILL grace-period wait is bounded by a single `time.monotonic()` deadline computed once per signal, and the post-kill direct-child reap check is fixed-count — bounded polling for process exit is the only wait the orchestrator performs, consistent with `spx/13-plugin-and-runtime-conventions.adr.md` `<no_until_polling>` ([test](tests/test_gate.compliance.l1.py))
- NEVER: the orchestrator source contains a literal `gh run watch` invocation or a `while True:` loop containing `time.sleep` — unbounded polling waits are forbidden across the marketplace per `spx/13-plugin-and-runtime-conventions.adr.md` ([test](tests/test_gate.compliance.l1.py))
