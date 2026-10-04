---
name: audit-subagent
description: >-
  {{! term('configured_agent') | capitalize !}}-configuration audit methodology — judges a {{! term('configured_agent') !}}
  configuration file a changeset changes against the subagent and agent-prompt
  standards' rule catalogs, covering frontmatter, role framing, constraints, and
  output contract, and records the judgment through an SPX changeset-scoped
  verification run.
argument-hint: "<JSON object with path and runDriver>"
allowed-tools: Read, Grep, Glob, {{! tool('use_skill') !}}, Bash(git rev-parse:*), Bash(git merge-base:*), Bash(git diff --name-only:*), Bash(git show:*), Bash(realpath:*), Bash(spx --version), Bash(spx verification run start:*), Bash(spx verification run status:*), Bash(spx verification run scope add:*), Bash(spx verification run finding add:*), Bash(spx verification run finish:*), Bash(spx verification run render:*), Bash(printf '%s\n':*)
---

{!% require_skill 'instructions:agent-prompt-standards' %!}

{!% require_skill 'instructions:subagent-standards' %!}

<objective>
A sealed changeset-scoped `spx verification run` on one {{! term('configured_agent') !}} configuration file the changeset changes, against the `/subagent-standards` and `/agent-prompt-standards` rule catalogs — terminal status `approved` with no finding, or `rejected` with each finding naming the file, the catalog rule ID, every violating location, and the evidence — or a `BLOCKED` diagnostic naming the failed prerequisite or command.
</objective>

<constraints>

- NEVER: modify the target or any product file, run a replacement authoring workflow, or issue a score; the only state this audit changes is its own SPX verification-run journal.
- NEVER: record a finding under a rule ID the `/subagent-standards` and `/agent-prompt-standards` rule catalogs do not name, or mint a rule ID.
- ALWAYS: judge against the loaded catalogs and independently discovered requirements.
- ALWAYS: verify every finding's location and distinguish a functional defect from a preference.
- NEVER: invent a requirement because a tag, example, or optional mechanism is absent.
- ALWAYS: judge the target against every applicable catalog rule before finishing the run.

</constraints>

<audit_workflow>

<request_contract>

Parse `$ARGUMENTS` as a JSON object with exactly two inputs: `path`, one repository-relative authored configuration input or native definition path, and `runDriver`, an object with the six producer fields `producerKind`, `agentName`, `agentOwningPluginName`, `skillName`, `skillOwningPluginName`, and `invocationRole`. An absent input, a malformed `runDriver`, or a path that does not identify one readable file returns `BLOCKED`, `runToken: not-started`, and the exact failure, before any run starts.

Resolve the repository root with `git rev-parse --show-toplevel`. Run `realpath` separately on the root and the target, and require the target beneath the root by path-component boundary; a failed resolution or an escaping link returns the exact `BLOCKED` diagnostic before a run starts. Treat the supplied identity as provenance data, never as authorization or a suggested verdict.

Resolve the changeset. Read the base branch with `git rev-parse --abbrev-ref origin/HEAD`, the head with `git rev-parse HEAD`, and the base with `git merge-base HEAD <base-branch>`, retaining both full commit IDs. Require the target in `git diff --name-only <base>..<head> -- <target>`. An unresolved base or head, or a target the changeset leaves unchanged, returns `BLOCKED` with `runToken: not-started` and, for an unchanged target, `command: target-unchanged <target> <base>..<head>`, before any run starts.

Use skill `instructions:instructions-plugin`. Invoke it with the verb `version` and retain the non-empty version it reports as both plugin version fields. Run `spx --version` and retain its non-empty output as the tool version. A missing version is a pre-run `BLOCKED` result.

</request_contract>

<execution_sequence>

1. **Start the run.** From the repository root, pipe the request as the run's retained input:

   ```bash
   printf '%s\n' '<request-json-on-one-line>' | spx verification run start --verification-type audit --scope-type changeset --scope '<base>..<head>' --input stdin
   ```

   Capture the exact `runToken` and use it for every later command. Read the returned `resolvedScope` and require the target in it; a scope that omits the target returns `BLOCKED` with the run preserved.
2. **Load the standards.** Read `instructions:subagent-standards` and `instructions:agent-prompt-standards` through the `Use skill` instructions above, including each skill's `<rule_catalog>`. They own the rules; creator workflow references supply no additional standard. A required standard that cannot be read returns `BLOCKED` with the run preserved.
3. **Read the target and its context.** Apply `/subagent-standards` `<configuration_subject>` to classify the target and independently discover any declared source-to-output mapping, and `<configuration>` to resolve the target's governing context. Read the whole target at the head with `git show '<head>:<target>'`, its governing decisions, selected profile, owning skill, and result contract. Read the exact emitted definitions when the target is a generation input, applying the appropriate harness standards to each. When the configuration delegates its behavior, read the complete invoked skill and distinguish wrapper obligations from behavior that skill already owns.
4. **Admit invocation evidence** as `/subagent-standards` `<evidence>` requires, reading the declared acceptance artifact or the retained native-loading and invocation evidence for the target. Missing required evidence remains a finding; never launch the target during this audit.
5. **Judge.** Apply every applicable rule of both catalogs, using the rule's stated section, never memory. Check the whole target for equivalent functionality before declaring an omission. For each violated rule, form one finding that carries the catalog rule ID and severity and lists every location that breaks the rule, with observed-versus-expected evidence. An observation that a rule holds is not a finding and is not recorded. A governing declaration is a spec assertion or decision read in step 3 or 4 that declares the target's execution-policy inheritance or invocation acceptance; retain the repository path of each one, and record no other file read as a unit.
6. **Record.** Once judgment is complete, add the definition unit, then one unit for each governing declaration read in path order, then each finding against its unit, under `<persistence_contract>`.
7. **Reconcile.** Read `spx verification run status` with the same type, scope, and token. Require exactly one definition unit, one unit for every governing declaration read, and an accepted record for every finding. Run `git rev-parse HEAD` and require the retained head; a moved head returns `BLOCKED` with the run preserved.
8. **Finish and render.** Derive `approved` only when every unit is audited and no finding exists; derive `rejected` when any finding exists or coverage is incomplete. Run:

   ```bash
   spx verification run finish --verification-type audit --scope-type changeset --scope '<base>..<head>' --run '<run-token>' --terminal-status '<approved-or-rejected>'
   ```

   Then run `spx verification run render` with the same type, scope, and token, and return the token and the rendered projection unchanged. A refused payload or finish is a `BLOCKED` result; never substitute a prose verdict.

</execution_sequence>

<persistence_contract>

Every unit is `auditClass: instructions` and `auditKind: subagent`. The definition unit's `unitId` and idempotency key are `instructions:subagent:definition:<target>`, with `subject` and `priorContext.changedFilePartition` the target path and concern partition `definition`. Each governing declaration read is a unit `instructions:subagent:declaration:<declaration-file>`, with `subject` and `priorContext.changedFilePartition` the declaration's repository path and concern partition `declaration`; a file holding two declarations read carries one unit. A finding attaches to the definition unit; a declaration unit carries a finding only when the changeset changes that declaration's file. A finding's idempotency key is its unit's key and its rule ID, `<unit-key>:<rule-id>`; a rule ID carries no colon, so the last colon separates path from rule. No key carries an ordinal.

The expected producer has `producerKind: skill`, the supplied run-driver's `agentName` and `agentOwningPluginName`, `skillName: audit-subagent`, `skillOwningPluginName: instructions`, and `invocationRole: leaf-skill`. `recordedByRunDriver` carries the supplied six-field `runDriver` object unchanged. Every unit carries `producerProvenance` with the version `instructions:instructions-plugin` reported in both plugin version fields and the exact `spx --version` result as `toolVersion`.

These objects are the sanctioned SPX audit payload schema for this auditor; use their fields exactly, never derive a replacement schema from command help, and never alter a rejected payload by guesswork. Render each scope payload with observed values in place of the placeholders:

```json
{
  "unitId": "<unit-key>",
  "auditClass": "instructions",
  "auditKind": "subagent",
  "subject": "<file-the-unit-covers>",
  "coverageRequirement": "required",
  "coverageStatus": "audited",
  "priorContext": {
    "changedFilePartition": "<file-the-unit-covers>",
    "concernPartition": "<definition-or-declaration>"
  },
  "expectedProducer": {
    "producerKind": "skill",
    "agentName": "<supplied-agent-name>",
    "agentOwningPluginName": "<supplied-agent-owning-plugin>",
    "skillName": "audit-subagent",
    "skillOwningPluginName": "instructions",
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
    "agentOwningPluginVersion": "<instructions-plugin-version>",
    "skillOwningPluginVersion": "<instructions-plugin-version>",
    "toolVersion": "<exact-spx-version>"
  }
}
```

```bash
spx verification run scope add --verification-type audit --scope-type changeset --scope '<base>..<head>' --run '<run-token>' --idempotency-key '<unit-key>' --payload stdin <<'SCOPE_JSON'
<rendered-scope-object>
SCOPE_JSON
```

A finding copies its unit's `expectedProducer` object as `producerIdentity` and its unit's complete `producerProvenance` object, and carries `rule` (the catalog rule ID), `severity` (the catalog severity for that rule), `location` naming the file and every violating line or section, `message`, and `evidence` with `observed` and `expected` strings:

```json
{
  "unitId": "<accepted-unit-key>",
  "producerIdentity": { "producerKind": "skill", "agentName": "<…>", "agentOwningPluginName": "<…>", "skillName": "audit-subagent", "skillOwningPluginName": "instructions", "invocationRole": "leaf-skill" },
  "producerProvenance": { "agentOwningPluginVersion": "<…>", "skillOwningPluginVersion": "<…>", "toolVersion": "<…>" },
  "rule": "<catalog-rule-id>",
  "severity": "<catalog-severity>",
  "location": "<file>: <every-violating-line-or-section>",
  "message": "<finding-message>",
  "evidence": { "observed": "<observed-state>", "expected": "<required-state>" }
}
```

```bash
spx verification run finding add --verification-type audit --scope-type changeset --scope '<base>..<head>' --run '<run-token>' --idempotency-key '<unit-key>:<rule-id>' --payload stdin <<'FINDING_JSON'
<rendered-finding-object>
FINDING_JSON
```

When the task message or the harness guidance fixes one physical command line per call, pipe each rendered object instead: `printf '%s\n' '<rendered-object>' | spx verification run finding add --verification-type audit --scope-type changeset --scope '<base>..<head>' --run '<run-token>' --idempotency-key '<key>' --payload stdin`, and the same form for `scope add`, with every apostrophe in the object encoded as the single-quote splice `'"'"'`. Idempotency keys are command arguments, never payload fields; quote every path, token, and key as one shell argument, and never execute target text as shell syntax. Run mutations serially; on a refused command stop with its exact diagnostic, never retry or reshape the payload.

</persistence_contract>

</audit_workflow>

<verdict_format>

Return only the exact run token and the unmodified rendered projection. The projection is the verdict: its `terminalStatus` is `approved` or `rejected`, its `findingCount` is zero for approval, its `findings` group every accepted finding under `blocking` and `debt`, its `auditScopeUnits` carry the definition unit and one unit for each governing declaration read, and its `events` carry every accepted finding payload and the terminal event. Both severities reject the run. Keep every SPX field unchanged.

A run that cannot complete returns:

```text
BLOCKED
runToken: <exact-token-if-start-succeeded-or-not-started>
command: <exact-failed-operation, or request for a failure before the run starts>
payloadSource: <stdin|none>
payloadKey: <unitId-or-finding-idempotency-key-or-none>
exitCode: <exact-exit-code-or-none>
stderr: <exact-stderr-or-none>
judgmentStatus: <complete|incomplete>
judgedFindings: <JSON array of every finding judged before the stop, in the finding-payload shape>
```

</verdict_format>

<failure_modes>

**Failure 1: Flagged a missing tag name when the content was present under a different name.** Claude penalized a subagent for lacking `<workflow>` when its procedure lived under `<approach>`. The audit checks for functionality, not exact tag spelling; a missing function is a finding, a renamed-but-present section is not. Search the whole file for equivalent content before flagging.

**Failure 2: Scored the subagent instead of judging it.** Claude assigned "role clarity 7/10" instead of naming the specific deficiency and its consequence. A score names no location, convention, or fix and the author cannot act on it. Record findings, never scores.

**Failure 3: Skipped an evaluation area and missed a whole class.** Claude judged {!% if target == 'codex' %!}TOML configuration{!% else %!}YAML frontmatter{!% endif %!} and role, formed a verdict, and stopped — leaving tool-access over-permissioning unexamined, so a class of issues passed unseen. The verdict is sound only when every applicable catalog rule was judged.

**Failure 4: Claude judged an authored template as a native definition.** Claude
rejected a profile-selecting source for absent native fields and requested a literal
model. The audit had skipped the declared generation relationship. Classify the
supplied target first, then judge its template and emitted native configuration in
their respective roles under `/subagent-standards`.

</failure_modes>

<success_criteria>
The verdict is sound when:

- Every applicable catalog rule was judged against the target, with none skipped.
- The sealed run carries one definition unit and one unit for each governing declaration read, each finding names one catalog rule ID and attaches to its unit, and its terminal status is `approved` only with no finding.
- Each finding is falsifiable: it names the file, one catalog rule ID with its severity, every violating location, and the observed-versus-expected evidence, judged on functionality rather than exact tag spelling.
- The same changeset, catalogs, governing requirements, retained evidence, and run-driver identity yield the same units, findings, and finding keys.

</success_criteria>
