---
name: inspect-github-actions
description: >-
  ALWAYS invoke this skill when the user asks about CI failures, workflow logs, GitHub Actions status, pipeline issues, or troubleshooting failed builds. NEVER attempt CI workflow investigation through ad hoc gh CLI calls without this skill.
allowed-tools: Bash(python3 "${SKILL_DIR}/scripts/gh_access.py":*), Bash(git branch --show-current), Bash(git rev-parse:*), Bash(gh run view:*), Bash(gh run list:*), Bash(gh pr view:*), Bash(gh pr checks:*), Read, Grep, request_user_input
---

<objective>

A GitHub Actions workflow-run diagnosis that names the selected run by its identifying tuple, reports the literal status and conclusion, and surfaces the failing job, failing step, and error excerpt.

</objective>

<workflow>

<step name="orient">

Resolve repository identity, host, and gh authentication state in one call. The helper parses `git remote get-url origin`, extracts `owner_repo` and `host`, probes repo access with the active gh account, lists available authenticated accounts for that host, and reports whether the session is TTY-attached:

```bash
python3 "${SKILL_DIR}/scripts/gh_access.py"
```

The output is a JSON object with these fields:

| Field                | Meaning                                                                      |
| -------------------- | ---------------------------------------------------------------------------- |
| `schema_version`     | Helper schema version (currently `1`)                                        |
| `owner_repo`         | `owner/repo` derived from the git remote, or `null` if not derivable         |
| `host`               | Hostname from the remote (e.g., `github.com`); `null` if not derivable       |
| `current_account`    | Active gh account, or `null` if `gh` is not authenticated                    |
| `has_access`         | `true` if the active account can read the repository                         |
| `available_accounts` | Authenticated gh accounts for `host`                                         |
| `is_tty`             | `true` only when both stdin and stdout are TTYs                              |
| `error`              | Non-null when identity could not be resolved (no GitHub remote, parse error) |

If `error` is non-null or `host` is `null`, stop and report. Otherwise continue; the helper supports `github.com` and GitHub Enterprise hostnames.

If `has_access` is `false`, `is_tty` is `true`, and `available_accounts` is non-empty, ask the user via `request_user_input` which account to switch to. Calling `gh auth switch --hostname <host> -u <account>` is permitted only after the user has answered — that answer is the explicit instruction the safety rule requires.

If `has_access` is `false`, `is_tty` is `true`, and `available_accounts` is empty, report the active account, the access failure, and the manual remediation commands. Do not ask for an account switch when no account is available.

If `has_access` is `false` and `is_tty` is `false` (CI, scripts, batch), report the active account, the access failure, and the manual remediation commands. Do not attempt a switch.

When downstream steps need the active branch or HEAD commit, run them just-in-time:

```bash
BRANCH=$(git branch --show-current)
HEAD_SHA=$(git rev-parse HEAD)
```

</step>

<step name="select_run">

Pick the run by the most-specific identifier the user named. If they named nothing, default to the most recent run on the active branch with `$HEAD_SHA` as the commit. Always name the selection rule in the output so the run is traceable.

```bash
# By run id (most specific)
gh run view "$RUN_ID" --json databaseId,status,conclusion,workflowName,headBranch,headSha

# By pull request
gh pr view "$PR_NUMBER" --json statusCheckRollup,headRefName

# By commit SHA
gh run list --commit "$HEAD_SHA" --limit 5 \
    --json databaseId,status,conclusion,workflowName,headBranch,createdAt

# By branch (default rule when no identifier given)
gh run list --branch "$BRANCH" --limit 5 \
    --json databaseId,status,conclusion,workflowName,headSha,createdAt
```

</step>

<step name="report_status">

For a status request, name these fields in this order before any narrative:

1. repository (`$OWNER_REPO`)
2. branch
3. run id
4. workflow name
5. status
6. conclusion
7. commit SHA

Use only the literal `conclusion` value returned by `gh run view --json conclusion`: `success`, `failure`, `cancelled`, `skipped`, `timed_out`, `action_required`, `neutral`, `stale`, or `startup_failure`. Do not derive states ("looks failed", "probably passing").

</step>

<step name="triage_failure">

For a failure triage request, retrieve only the failed-step logs first:

```bash
gh run view "$RUN_ID" --log-failed
```

From that output, surface the failing job, the failing step, and at least one error excerpt before any other log retrieval. Request full logs (`gh run view "$RUN_ID" --log`) only if `--log-failed` is empty or the user explicitly asks.

When listing jobs to find a specific failure point:

```bash
gh run view "$RUN_ID" --json jobs \
    --jq '.jobs[] | {id: .databaseId, name: .name, status: .status, conclusion: .conclusion}'
gh run view "$RUN_ID" --job "$JOB_ID" --log
```

</step>

<step name="check_for_followups">

If the run is still in progress (`status` ∈ {`queued`, `in_progress`, `waiting`, `requested`, `pending`}) and the user wants to know when it finishes:

- When the run belongs to a pull request and the PR number is known, run the sanctioned PR-check wait:

  ```bash
  gh pr checks <pr-number> --watch --fail-fast --interval 30
  ```

  The command exits when all PR checks finish, and `--fail-fast` exits when any check fails. After it exits, re-run the selection/status step and report the terminal state.

- When only a run ID, commit SHA, or branch is known, report the current run state and say the sanctioned wait form requires a PR number. Do not create a runtime timer.

</step>

</workflow>

<safety_rules>

- NEVER invoke `gh run watch`. Unreaped subprocess trees from `gh run watch` exhaust the workstation when the harness fails to reap them across turns.
- NEVER write `until <check>; do sleep N; done` or `while ! <check>; do sleep N; done`. Per-iteration process trees from these constructs accumulate until the host is exhausted.
- NEVER call any state-changing `gh` subcommand without an explicit user instruction in the same turn. The user's answer to `request_user_input` is explicit instruction. The full list — also enforced programmatically by `${SKILL_DIR}/scripts/mutation_gate.py` — is `gh auth login`, `gh auth switch`, `gh auth refresh`, `gh auth logout`, `gh run rerun`, `gh run cancel`, `gh run delete`, `gh workflow run`, `gh workflow enable`, and `gh workflow disable`.

</safety_rules>

<failure_modes>

**Failure 1: Claude assigned to a variable named `status`.** Claude parsed gh JSON output into a shell variable named `status`, which is read-only under zsh and fails with `read-only variable: status` at the first assignment. Name the variable `run_status` or similar.

**Failure 2: Claude assumed `gh` was authenticated inside a CI runner.** Claude ran `gh` commands in a GitHub Actions job, where default runners do not authenticate `gh`, and the commands failed. When the skill runs inside a CI job, surface "gh is not authenticated" and the standard remediation: pipe `${{ secrets.GITHUB_TOKEN }}` into `gh auth login --with-token`. Do not attempt account switching in CI — switching requires a TTY which CI does not have.

**Failure 3: Claude led a status report with narrative.** Claude wrote "the workflow failed" before naming the run id, branch, and commit SHA, which left the user unable to verify which run. Lead with the identifying tuple in the order listed in `<step name="report_status">`.

</failure_modes>

<success_criteria>

- A status request reports repository, branch, run id, workflow name, status, conclusion, and commit SHA before any narrative.
- A failure triage request runs `gh run view --log-failed` first and surfaces failing job, failing step, and at least one error excerpt before any other log retrieval.
- Auth-failure handling matches the TTY/non-TTY split: prompt-and-switch on TTY, manual remediation on non-TTY.
- Conclusion field carries the literal value returned by `gh run view --json conclusion`, never a derivation.
- In-progress PR-check waiting uses exactly `gh pr checks <pr-number> --watch --fail-fast --interval 30`; run-only in-progress status is reported without a watcher or runtime timer.
- No `gh run watch` invocation. No polling loops. No credential or workflow mutation outside an explicit user instruction.

</success_criteria>

<script_test_record>

Each script is tested with the standard library only; the tests that run offline replace the script's `gh` runner with recorded replies.

- `scripts/gh_access.py` — remote parsing of SCP-form, URL-form, and malformed remotes; an enterprise host reaching every API call; account filtering by host; a run outside a git checkout; an unreachable repository; and a live run against real `gh` credentials.
- `scripts/mutation_gate.py` — a gated command refused without `--user-instructed` and, with it, allowed and logged; an ungated command passed through; a blocked command writing only to stderr.
- `scripts/workflow_inspect.py` — every subcommand against recorded `gh` replies; log truncation at, below, and above `--max-bytes`, including inside a multibyte character; invalid run ids, PR numbers, `--limit`, and `--max-bytes` rejected before any `gh` call; `gh` failures, timeouts, non-JSON output, and wrong-shape JSON, each reported as `<subcommand> <argument>: <cause>. Next: <action>.` with exit 1; and one live run against real `gh` credentials.
- All three — standard-library imports only, `capture_output=True` on every `subprocess.run`, no `subprocess.Popen`, no `gh run watch`, and no `time.sleep`.

</script_test_record>
