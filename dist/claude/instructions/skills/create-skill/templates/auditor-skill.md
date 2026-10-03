---
name: "audit-{{subject}}"
description: >-
  {{Subject}} audit methodology — judges {{target}} against {{governing standards}}
  and records the judgment through an SPX verification run.
argument-hint: "<JSON object with path and runDriver>"
allowed-tools: Read, Grep, Glob, Skill, Bash(git rev-parse:*), Bash(spx --version), Bash(spx verification run start:*), Bash(spx verification run input:*), Bash(spx verification run status:*), Bash(spx verification run scope add:*), Bash(spx verification run finding add:*), Bash(spx verification run finish:*), Bash(spx verification run render:*)
---

<objective>
A sealed `spx verification run` on {{scope}} against {{governing standards}} — terminal status `approved` with no finding, or `rejected` with each finding naming the artifact location, the violated rule, and the evidence — or a `BLOCKED` diagnostic naming the failed prerequisite or command.
</objective>

<constraints>

- NEVER modify the subject under audit or any product file; the only state this audit changes is its own SPX verification-run journal.
- ALWAYS inspect every applicable rule before finishing the run.
- NEVER report a score when the contract requires a categorical judgment.

</constraints>

<audit_workflow>

1. Parse {{the target path and the run-driver identity}} and resolve {{the complete audit scope}}; a missing or unreadable target returns `BLOCKED` with `runToken: not-started` before any run starts.
2. Start one run with `spx verification run start --verification-type audit --scope-type {{file-or-changeset}} --scope '{{scope}}'` and use its exact `runToken` for every later command.
3. Load {{the governing standards and repository-local specialization}}.
4. Judge every applicable rule and collect falsifiable findings.
5. Add {{the scope units}} with `spx verification run scope add`, under audit class `{{audit-class}}` and audit kind `{{audit-kind}}`, then each finding against the unit of the artifact it names with `spx verification run finding add`.
6. Read `spx verification run status`, require every unit and finding accepted, and finish with `spx verification run finish --terminal-status approved` only when no finding exists, otherwise `rejected`.
7. Render the run with `spx verification run render` and return the token and projection unchanged. A refused payload or finish returns `BLOCKED`.

</audit_workflow>

<verdict_format>

Return only the exact run token and the unmodified rendered projection. Its `terminalStatus` is the verdict; every recorded finding, `blocking` or `debt`, rejects the run.

A run that cannot complete returns:

```text
BLOCKED
runToken: {{exact token or not-started}}
command: {{exact failed operation, or request for a failure before the run starts}}
exitCode: {{exact exit code or none}}
stderr: {{exact stderr or none}}
judgedFindings: {{every finding judged before the stop}}
```

</verdict_format>

<failure_modes>

{{Include only auditor failures observed in actual use, each with what happened, why it failed, and how to avoid it. Remove this section when no observed failure exists.}}

</failure_modes>

<success_criteria>

- Every applicable rule is judged, with none silently skipped.
- The sealed run's terminal status is `approved` only when no finding exists and every unit is audited.
- Every finding names the artifact, violated rule, and falsifiable evidence.
- The same subject, standards, and run-driver identity produce the same findings.

</success_criteria>
