# Workflow Observability

PROVIDES Python-driven inspection of repository identity, host authentication state, workflow files, workflow runs, jobs, logs, check rollups, and artifacts — packaged as three helper modules (`gh_access.py`, `workflow_inspect.py`, `mutation_gate.py`) under the github-actions skill's `scripts/` directory
SO THAT workflow review, runtime operations, workflow evolution, and any skill response that summarizes observed GitHub state
CAN read structured data with bounded subprocess lifetime rather than parsing free-form `gh` output

## Assertions

### Scenarios

- Given a working directory with a GitHub remote, when `gh_access.py` runs with no arguments, then it returns JSON on stdout containing `owner_repo`, `current_account`, `has_access`, `available_accounts`, and `is_tty` fields ([test](tests/test_workflow_observability.scenario.l1.py))
- Given a workflow run id, when `workflow_inspect.py run <id>` runs, then it returns JSON containing the run's `databaseId`, `status`, `conclusion`, `workflowName`, `headBranch`, `headSha`, `createdAt`, and a `jobs` array with per-job `databaseId`, `name`, `status`, `conclusion` ([test](tests/test_workflow_observability.scenario.l1.py))
- Given a state-changing `gh` subcommand argument, when `mutation_gate.py check <command>` runs without `--user-instructed`, then it exits non-zero and writes a JSON error to stderr naming the missing consent flag and the gated subcommand ([test](tests/test_workflow_observability.scenario.l1.py))
- Given a state-changing `gh` subcommand argument and the `--user-instructed` flag, when `mutation_gate.py check <command> --user-instructed` runs, then it exits zero and appends one line to `${CLAUDE_PROJECT_DIR}/.spx/mutation-audit.log` containing the timestamp, current account, and gated command ([test](tests/test_workflow_observability.scenario.l1.py))

### Properties

- Each helper module returns valid JSON on stdout when it exits zero; diagnostic output goes to stderr — consumers parse stdout safely ([test](tests/test_workflow_observability.property.l1.py))
- Each helper module uses Python stdlib only (`subprocess`, `json`, `pathlib`, `argparse`, `sys`, `os`) — no third-party HTTP libraries, no streaming subprocesses ([test](tests/test_workflow_observability.property.l1.py))
- Each helper module's stdout JSON includes a `schema_version` field — schema-breaking changes bump the version ([test](tests/test_workflow_observability.property.l1.py))

### Compliance

- ALWAYS: helper modules invoke `gh` and `git` via `subprocess.run(..., capture_output=True, text=True)` — streaming subprocesses are forbidden ([test](tests/test_workflow_observability.compliance.l1.py))
- NEVER: helper modules invoke or reference `gh run watch` or any other streaming `gh` subcommand — the marketplace's runtime-safety rule applies ([test](tests/test_workflow_observability.compliance.l1.py))
- NEVER: helper modules implement polling waits — `while ... : time.sleep(...)` constructs are absent ([test](tests/test_workflow_observability.compliance.l1.py))
