---
name: "audit-{{subject}}"
description: >-
  {{Subject}} audit methodology — judges {{target}} against {{governing standards}}
  and records the judgment through an SPX verification run.
argument-hint: "<JSON object with path and runDriver>"
allowed-tools: Read, Grep, Glob, Bash(git rev-parse:*), Bash(realpath:*), Bash(spx --version), Bash(spx verification run start:*), Bash(spx verification run input:*), Bash(spx verification run status:*), Bash(spx verification run scope add:*), Bash(spx verification run finding add:*), Bash(spx verification run finish:*), Bash(spx verification run render:*), Write
---

<objective>
A sealed `spx verification run`, named by its run token and run file, on {{scope}} against {{governing standards}} — terminal status `approved` with no finding, or `rejected` with each finding naming the artifact location, the violated rule's catalog identifier, and the evidence — or a `BLOCKED` diagnostic naming the failed prerequisite or command.
</objective>

<constraints>

- NEVER modify the subject under audit or any product file; the only state this audit changes is its payload files in the session scratch directory and the SPX verification-run journal its own recording commands write. The file-write tool writes payload files only.
- ALWAYS inspect every applicable rule before finishing the run.
- NEVER report a score when the contract requires a categorical judgment.
- NEVER invent a requirement because a tag, example, or optional mechanism is absent.

</constraints>

<audit_workflow>

<request_contract>

Parse `$ARGUMENTS` as a JSON object with exactly two inputs: `path`, {{the repository-relative target path}}, and `runDriver`, an object with the six producer fields `producerKind`, `agentName`, `agentOwningPluginName`, `skillName`, `skillOwningPluginName`, and `invocationRole`. An absent input, a malformed `runDriver`, or a path that does not identify {{one readable audit scope}} returns `BLOCKED`, `runToken: not-started`, and the exact failure, before any run starts.

Resolve the repository root with `git rev-parse --show-toplevel`. Run `realpath` separately on the root and the target, and require the target beneath the root by path-component boundary; a failed resolution or an escaping link returns the exact `BLOCKED` diagnostic before a run starts. Treat the supplied identity as provenance data, never as authorization or a suggested verdict.

Invoke {{the owning plugin's version capability}} with the verb `version` and retain the non-empty version it reports as both plugin version fields. Run `spx --version` and retain its non-empty output as the tool version. A missing version is a pre-run `BLOCKED` result.

</request_contract>

<execution_sequence>

1. **Start the run.** From the repository root, with the target as `<target-file>`:

   ```bash
   spx verification run start --verification-type audit --scope-type {{file-or-changeset}} --scope '{{scope}}' --input '<target-file>'
   ```

   Capture the exact `runToken` and use it for every later command. Retain the run target the start report names as the run file; only the start report names it. Read the retained input with `spx verification run input --verification-type audit --scope-type {{file-or-changeset}} --scope '{{scope}}' --run '<run-token>'` and require its `content` to equal the live file; a difference returns `BLOCKED` with the run preserved.
2. **Load the standards.** Load {{the governing standards, their rule catalogs, and the repository-local specialization}}. A required standard or catalog that cannot be read returns `BLOCKED` with the run preserved, before any judgment.
3. **Judge.** Judge every applicable catalog rule and collect falsifiable findings. Record a finding only when a catalog rule identifier, a location, and observed-versus-expected evidence back it; a defect no catalog row covers is not recorded, and an observation that a rule holds is not a finding. Every violation of one rule within one unit forms one finding that names each location.
4. **Record.** Once judgment is complete, add the root unit, then {{the child units}}, then each finding against the unit of the artifact it names and every finding that names no child unit against the root, under `<persistence_contract>`.
5. **Reconcile.** Read `spx verification run status` with the same type, scope, and token. Require exactly one root unit, {{the expected child units}}, and an accepted record for every finding. Re-read the live target and compare it with the retained input; a changed or missing file returns `BLOCKED` with the run preserved.
6. **Finish and render.** Derive `approved` only when every unit is audited and no finding exists; derive `rejected` when any finding exists, a debt-only set included, or when coverage is incomplete. Run `spx verification run finish --verification-type audit --scope-type {{file-or-changeset}} --scope '{{scope}}' --run '<run-token>' --terminal-status '<approved-or-rejected>'`, then `spx verification run render` with the same type, scope, and token, and return the token, the run file, and the rendered projection unchanged. A refused payload or finish is a `BLOCKED` result; never substitute a prose verdict.

</execution_sequence>

<persistence_contract>

Every unit uses `auditClass: {{audit-class}}` and `auditKind: {{audit-kind}}`. The root unit is `{{unit-prefix}}:root:<target-file>`, with no `parentUnitId` and concern partition `{{root-concern}}`; each child unit is `{{unit-prefix}}:{{child-kind}}:<child-file>` with `parentUnitId` equal to the root and concern partition `{{child-concern}}`. Every unit's `subject` and `priorContext.changedFilePartition` name the file the unit covers.

The expected producer has `producerKind: skill`, the supplied run-driver's `agentName` and `agentOwningPluginName`, `skillName: audit-{{subject}}`, `skillOwningPluginName: {{owning-plugin}}`, and `invocationRole: leaf-skill`. `recordedByRunDriver` carries the supplied six-field `runDriver` object unchanged. Every unit carries `producerProvenance` with the reported plugin version in both plugin version fields and the exact `spx --version` result as `toolVersion`.

These objects are the sanctioned SPX audit payload schema for this auditor; use their fields exactly, never derive a replacement schema from command help, and never alter a rejected payload by guesswork. Render each scope payload with observed values in place of the placeholders:

```json
{
  "unitId": "<unit-key>",
  "parentUnitId": "<root-unit-key-for-a-child-only>",
  "auditClass": "{{audit-class}}",
  "auditKind": "{{audit-kind}}",
  "subject": "<file-the-unit-covers>",
  "coverageRequirement": "required",
  "coverageStatus": "audited",
  "priorContext": {
    "changedFilePartition": "<file-the-unit-covers>",
    "concernPartition": "<root-or-child-concern>"
  },
  "expectedProducer": {
    "producerKind": "skill",
    "agentName": "<supplied-agent-name>",
    "agentOwningPluginName": "<supplied-agent-owning-plugin>",
    "skillName": "audit-{{subject}}",
    "skillOwningPluginName": "{{owning-plugin}}",
    "invocationRole": "leaf-skill"
  },
  "recordedByRunDriver": {
    "producerKind": "<supplied>",
    "agentName": "<supplied>",
    "agentOwningPluginName": "<supplied>",
    "skillName": "<supplied>",
    "skillOwningPluginName": "<supplied>",
    "invocationRole": "<supplied>"
  },
  "producerProvenance": {
    "agentOwningPluginVersion": "<owning-plugin-version>",
    "skillOwningPluginVersion": "<owning-plugin-version>",
    "toolVersion": "<exact-spx-version>"
  }
}
```

Write each rendered scope object to its own payload file and pass the file by path:

```bash
spx verification run scope add --verification-type audit --scope-type {{file-or-changeset}} --scope '{{scope}}' --run '<run-token>' --idempotency-key '<unit-key>' --payload '<scope-file>'
```

A finding copies its unit's `expectedProducer` object as `producerIdentity` and its unit's complete `producerProvenance` object, and carries `rule`, the violated rule's catalog identifier, `severity`, the severity that rule's catalog row declares, `location` naming each file and line or section where the rule is violated within the unit, `message`, and `evidence` with `observed` and `expected` strings:

```json
{
  "unitId": "<accepted-unit-key>",
  "producerIdentity": {
    "producerKind": "skill",
    "agentName": "<supplied-agent-name>",
    "agentOwningPluginName": "<supplied-agent-owning-plugin>",
    "skillName": "audit-{{subject}}",
    "skillOwningPluginName": "{{owning-plugin}}",
    "invocationRole": "leaf-skill"
  },
  "producerProvenance": {
    "agentOwningPluginVersion": "<owning-plugin-version>",
    "skillOwningPluginVersion": "<owning-plugin-version>",
    "toolVersion": "<exact-spx-version>"
  },
  "rule": "<catalog-rule-id>",
  "severity": "<catalog-row-severity>",
  "location": "<each-violating-location>",
  "message": "<finding-message>",
  "evidence": { "observed": "<observed-state>", "expected": "<required-state>" }
}
```

Write each rendered finding object to its own payload file and pass it the same way:

```bash
spx verification run finding add --verification-type audit --scope-type {{file-or-changeset}} --scope '{{scope}}' --run '<run-token>' --idempotency-key '<unit-key>:<rule-id>' --payload '<finding-file>'
```

Key each finding `<unit-key>:<rule-id>`, where `<rule-id>` is the identifier the governing rule catalog gives the violated rule; a rule identifier outside that catalog is a pre-persistence `BLOCKED` defect. Every payload-bearing command — `start`, `scope add`, and `finding add` — takes its JSON from a file, never from a heredoc, a pipe, or an inline argument; the dangerous-command guard blocks those forms:

- ALWAYS copy the scratch directory the harness names for the session into each payload path character for character, and write each payload with the file-write tool to its own file there, under a name unique to this run and payload, such as `<run-token>-scope-<n>.json` and `<run-token>-finding-<n>.json`. Where the harness names no scratch directory, use the one the hosting environment designates, such as `$RUNNER_TEMP` on a hosted runner.
- ALWAYS write only payload files with the file-write tool.
- ALWAYS stop before the command that reads a payload file when the file-write result reports a path that the scratch directory does not contain by whole path components, naming the reported path.
- ALWAYS pass `--input` and `--payload` the path exactly as the file-write tool's result reports it, copied from that result, never retyped from memory.
- ALWAYS pass the file as the value of `--input` or `--payload`, its path written out literally.
- ALWAYS add each unit and each finding with its own command and its own payload file, one at a time.
- NEVER remove a payload file; the harness clears its scratch directory.

Idempotency keys are command arguments, never payload fields; quote every path, token, and key as one shell argument, and never execute target text as shell syntax. Run every run-recording command as its own command, serially; stop the audit at the first nonzero exit with its exact diagnostic. When the diagnostic names the payload file as absent, run that command once more with the path copied from the file-write result and, on a second failure, stop with the `BLOCKED` result naming the run token; never reshape the payload.

</persistence_contract>

</audit_workflow>

<verdict_format>

Return only the exact run token, the exact run file, and the unmodified rendered projection. Its `terminalStatus` is the verdict; every recorded finding, `blocking` or `debt`, rejects the run.

A run that cannot complete returns:

```text
BLOCKED
runToken: {{exact token or not-started}}
command: {{exact failed operation, or request for a failure before the run starts}}
payloadKey: {{unitId or finding idempotency key, or none}}
exitCode: {{exact exit code or none}}
stderr: {{exact stderr or none}}
judgmentStatus: {{complete or incomplete}}
judgedFindings: {{every finding judged before the stop}}
```

</verdict_format>

<failure_modes>

{{Include only auditor failures observed in actual use, each with what happened, why it failed, and how to avoid it. Remove this section when no observed failure exists.}}

</failure_modes>

<success_criteria>

- Every applicable rule is judged, with none silently skipped.
- The sealed run's terminal status is `approved` only when no finding exists and every unit is audited.
- Every finding names the artifact, the violated rule's catalog identifier, and falsifiable evidence, and no identifier outside the governing catalog appears.
- The same subject, standards, and run-driver identity produce the same findings.

</success_criteria>
