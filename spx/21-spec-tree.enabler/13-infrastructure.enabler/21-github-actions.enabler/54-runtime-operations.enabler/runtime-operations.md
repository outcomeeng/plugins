# Runtime Operations

PROVIDES failure triage and explicitly-requested run-control operations using observed runs, jobs, logs, check rollups, and the mutation gate from `32-workflow-safety`
SO THAT workflow-evolution surfaces
CAN diagnose failed runs and act on them when the user explicitly requests action

## Assertions

### Scenarios

- Given a GitHub repository with workflow runs on the active branch, when the skill handles a status request, then the response names repository, branch, run id, workflow name, status, conclusion, and commit SHA before narrative ([test](tests/test_runtime_operations.scenario.l1.py))
- Given a workflow run with conclusion `failure`, when the skill triages it, then `gh run view <run-id> --log-failed` runs before any full-log retrieval and the response surfaces failing job, failing step, and at least one error excerpt ([test](tests/test_runtime_operations.scenario.l1.py))
- Given the active `gh` account lacks repository access, when the skill detects the failure on a TTY-attached session with authenticated accounts for the repository host, then it lists those host-scoped accounts and prompts for an account switch via `gh auth switch --hostname <host> -u <account>`; when no account is available or the session is non-TTY, it reports the active account and manual remediation commands without prompting ([test](tests/test_runtime_operations.scenario.l1.py))

### Properties

- Run selection is evidence-based: every workflow summary names the user-provided identifier (run id, PR, branch, commit) or the default rule (active branch + HEAD) used to select the run ([test](tests/test_runtime_operations.property.l1.py))

### Compliance

- ALWAYS: a failure diagnosis relates the remote failure to the workflow-design surface — trigger, job, dependency, runner, cache, artifact, environment, permission, secret, validation command, or repository script — so the failure is framed architecturally rather than only mechanically ([audit])
- ALWAYS: a failure diagnosis names the local Spec Tree or repository command that verifies the same concern when the repository provides one — local-runnable equivalents make the failure reproducible without GitHub ([audit])
- ALWAYS: in-progress PR-check follow-up guidance uses exactly `gh pr checks <pr-number> --watch --fail-fast --interval 30` as one foreground command, with the bounded return condition named by the invoking workflow ([audit])
