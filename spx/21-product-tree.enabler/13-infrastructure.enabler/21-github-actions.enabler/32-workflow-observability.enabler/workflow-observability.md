---
id: 01a0ebba-5f5e-76b3-b374-5b002c6b5572
malleability: spec
---

# Workflow Observability

PROVIDES Python-driven inspection of repository identity, host authentication state, workflow files, workflow runs, jobs, logs, check rollups, and artifacts — packaged as three helper modules (`gh_access.py`, `workflow_inspect.py`, `mutation_gate.py`) under the github-actions skill's `scripts/` directory
SO THAT workflow review, runtime operations, workflow evolution, and any skill response that summarizes observed GitHub state
CAN read structured data with bounded subprocess lifetime rather than parsing free-form `gh` output

## Assertions

### Scenarios

- Given a working directory with a GitHub remote, when `gh_access.py` runs with no arguments, then it returns JSON on stdout containing `owner_repo`, `current_account`, `has_access`, `available_accounts`, and `is_tty` fields ([test](tests/test_workflow_observability.scenario.l3.py))
- Given a workflow run id, when `workflow_inspect.py run <id>` runs, then it returns JSON containing the run's `databaseId`, `status`, `conclusion`, `workflowName`, `headBranch`, `headSha`, `createdAt`, and a `jobs` array with per-job `databaseId`, `name`, `status`, `conclusion` ([test](tests/test_workflow_observability.scenario.l3.py))
- Given a state-changing `gh` subcommand argument, when `mutation_gate.py check <command>` runs without `--user-instructed`, then it exits non-zero and writes a JSON error to stderr naming the missing consent flag and the gated subcommand ([test](tests/test_workflow_observability.scenario.l1.py))
- Given a state-changing `gh` subcommand argument and the `--user-instructed` flag, when `mutation_gate.py check <command> --user-instructed` runs, then it exits zero and appends one line to `${CLAUDE_PROJECT_DIR}/.spx/mutation-audit.log` containing the timestamp, current account, and gated command ([test](tests/test_workflow_observability.scenario.l1.py))
- Given recorded `gh run list` output, when `workflow_inspect.py runs --branch <branch> --limit <n>` runs, then it exits zero, returns the recorded list in `runs` with `error` null, and issues one `gh run list` call carrying the branch and the limit ([test](tests/test_workflow_inspect.scenario.l1.py))
- Given recorded `gh run view` output, when `workflow_inspect.py run <id>` and `workflow_inspect.py jobs <id>` run, then `run` returns the run fields with per-job `databaseId`, `name`, `status`, `conclusion`, and `jobs` returns per-job fields that add `startedAt` and `completedAt` ([test](tests/test_workflow_inspect.scenario.l1.py))
- Given recorded log text, when `workflow_inspect.py log <id>` runs, then it returns the text verbatim in `log` with `byte_count`, `truncated` false, and `failed_only`; with `--failed` it requests `gh run view --log-failed`; with `--max-bytes` below the encoded size it returns the last `--max-bytes` bytes with `truncated` true, and at exactly the encoded size it returns the whole log ([test](tests/test_workflow_inspect.scenario.l1.py))
- Given recorded `gh pr view` and `gh api` output, when `workflow_inspect.py checks <pr>` and `workflow_inspect.py artifacts <id>` run, then `checks` returns `number`, `headRefName`, and `statusCheckRollup`, and `artifacts` returns the recorded `id`, `name`, `size_in_bytes`, and `expired` entries from a call that never requests the archive download URL ([test](tests/test_workflow_inspect.scenario.l1.py))
- Given recorded `gh workflow list` output, when `workflow_inspect.py workflow-files` runs, then it returns the recorded definitions in `workflows` ([test](tests/test_workflow_inspect.scenario.l1.py))
- Given `gh` exits 124, exits nonzero with no output, or prints text that is not JSON, when any `workflow_inspect.py` subcommand runs, then `error` reads `<subcommand> <argument>: <cause>. Next: <action>.` with the timeout, no-output, or decoder cause and its own next action, and the script exits 1 ([test](tests/test_workflow_inspect.scenario.l1.py))
- Given a real child process, when the script's `_run` seam runs it, then it returns the exit code, stdout verbatim, and stripped stderr, and reports a child that outlasts the timeout as exit 124 naming the command ([test](tests/test_workflow_inspect.scenario.l1.py))
- Given `workflow_inspect.py --help` or `workflow_inspect.py log --help`, when it runs, then it lists the seven subcommands and the `--failed` and `--max-bytes` options without calling `gh` ([test](tests/test_workflow_inspect.scenario.l1.py))

### Mappings

- Each of `runs`, `run`, `jobs`, `checks`, `artifacts`, and `workflow-files` maps `gh` JSON of the wrong shape to an `error` that names the subcommand, its argument, and the missing object, ends with a next action, and exits 1 ([test](tests/test_workflow_inspect.mapping.l1.py))

### Properties

- Each helper module returns valid JSON on stdout when it exits zero; diagnostic output goes to stderr — consumers parse stdout safely ([test](tests/test_workflow_observability.property.l1.py))
- Each helper module uses Python stdlib only (`subprocess`, `json`, `pathlib`, `argparse`, `sys`, `os`) — no third-party HTTP libraries, no streaming subprocesses ([test](tests/test_workflow_observability.property.l1.py))
- Each helper module's stdout JSON includes a `schema_version` field — schema-breaking changes bump the version ([test](tests/test_workflow_observability.property.l1.py))
- Every run id or pull request number that is not a positive integer is rejected by `run`, `jobs`, `log`, `artifacts`, and `checks` with `<subcommand> <value>: <label> must be a positive integer, got '<value>'. Next: pass the number from <source>.`, exit 1, and no `gh` call ([test](tests/test_workflow_inspect.property.l1.py))
- Every `--limit` or `--max-bytes` below 1 is rejected with `<subcommand> --<option> <value>: <option> must be at least 1. Next: pass --<option> with a positive integer.`, exit 1, and no `gh` call ([test](tests/test_workflow_inspect.property.l1.py))
- Every nonzero `gh` exit code other than 124 is reported as `<subcommand> <argument>: gh <gh subcommand> exited <code>: <stderr>. Next: run python3 gh_access.py to check gh authentication and repository access, then retry.` ([test](tests/test_workflow_inspect.property.l1.py))
- For every log text and every `--max-bytes` of at least 1, `log` reports the encoded `byte_count`, sets `truncated` exactly when `byte_count` exceeds `--max-bytes`, and returns the last `--max-bytes` bytes of the log when truncated and the whole log otherwise ([test](tests/test_workflow_inspect.property.l1.py))

### Compliance

- ALWAYS: helper modules invoke `gh` and `git` via `subprocess.run(..., capture_output=True, text=True)` — streaming subprocesses are forbidden ([test](tests/test_workflow_observability.compliance.l1.py))
- NEVER: helper modules invoke or reference `gh run watch` or any other streaming `gh` subcommand — the marketplace's runtime-safety rule applies ([test](tests/test_workflow_observability.compliance.l1.py))
- NEVER: helper modules implement polling waits — `while ... : time.sleep(...)` constructs are absent ([test](tests/test_workflow_observability.compliance.l1.py))
