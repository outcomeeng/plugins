# Runtime Operations

PROVIDES failure triage and explicitly-requested run-control operations using observed runs, jobs, logs, check rollups, and the mutation gate from `32-workflow-safety`
SO THAT workflow-evolution surfaces
CAN diagnose failed runs and act on them when the user explicitly requests action

## Assertions

### Compliance

- ALWAYS: a status response names repository, branch, run id, workflow name, status, conclusion, and commit SHA before narrative ([audit])
- ALWAYS: failure triage runs `gh run view <run-id> --log-failed` before any full-log retrieval and surfaces the failing job, failing step, and at least one error excerpt ([audit])
- ALWAYS: when the active `gh` account lacks repository access, a TTY-attached session with authenticated accounts for the repository host lists those host-scoped accounts and prompts for an account switch via `gh auth switch --hostname <host> -u <account>`; when no account is available or the session is non-TTY, it reports the active account and manual remediation commands without prompting ([audit])
- ALWAYS: run selection is evidence-based — every workflow summary names the user-provided identifier (run id, PR, branch, commit) or the default rule (active branch + HEAD) used to select the run ([audit])
- ALWAYS: a failure diagnosis relates the remote failure to the workflow-design surface — trigger, job, dependency, runner, cache, artifact, environment, permission, secret, validation command, or repository script — so the failure is framed architecturally rather than only mechanically ([audit])
- ALWAYS: a failure diagnosis names the local Spec Tree or repository command that verifies the same concern when the repository provides one — local-runnable equivalents make the failure reproducible without GitHub ([audit])
- ALWAYS: in-progress PR-check follow-up guidance uses exactly `gh pr checks <pr-number> --watch --fail-fast --interval 30` as one foreground command, with the bounded return condition named by the invoking workflow ([audit])
