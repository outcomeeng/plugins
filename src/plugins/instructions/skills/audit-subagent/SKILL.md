---
name: audit-subagent
description: >-
  {{! term('configured_agent') | capitalize !}}-configuration audit methodology — judges a {{! term('configured_agent') !}}
  configuration file against the subagent and agent-prompt standards, covering
  frontmatter, role framing, constraints, and output contract, and records the
  judgment through an SPX file-scoped verification run.
argument-hint: "<JSON object with path and runDriver>"
allowed-tools: Read, Grep, Glob, {{! tool('use_skill') !}}, Bash(git rev-parse:*), Bash(realpath:*), Bash(spx --version), Bash(spx verification run start:*), Bash(spx verification run input:*), Bash(spx verification run status:*), Bash(spx verification run scope add:*), Bash(spx verification run finding add:*), Bash(spx verification run finish:*), Bash(spx verification run render:*), Bash(printf:*)
---

{!% require_skill 'instructions:agent-prompt-standards' %!}

{!% require_skill 'instructions:subagent-standards' %!}

<objective>
A sealed `spx verification run` on one {{! term('configured_agent') !}} configuration file against `/subagent-standards` and `/agent-prompt-standards` — terminal status `approved` with no finding, or `rejected` with each blocking or debt finding naming the location, the violated rule, and the evidence — or a `BLOCKED` diagnostic naming the failed prerequisite or command.
</objective>

<constraints>

- NEVER: modify the target or any product file, run a replacement authoring workflow, or issue a score; the only state this audit changes is its own SPX verification-run journal.
- ALWAYS: judge against the loaded standards and independently discovered requirements.
- ALWAYS: verify every finding's location and distinguish a functional defect from a preference.
- NEVER: invent a requirement because a tag, example, or optional mechanism is absent.
- ALWAYS: cover every applicable standards area before finishing the run.

</constraints>

<audit_workflow>

<request_contract>

Parse `$ARGUMENTS` as a JSON object with exactly two inputs: `path`, one repository-relative authored configuration input or native definition path, and `runDriver`, an object with the six producer fields `producerKind`, `agentName`, `agentOwningPluginName`, `skillName`, `skillOwningPluginName`, and `invocationRole`. An absent input, a malformed `runDriver`, or a path that does not identify one readable file returns `BLOCKED`, `runToken: not-started`, and the exact failure, before any run starts.

Resolve the repository root with `git rev-parse --show-toplevel`. Run `realpath` separately on the root and the target, and require the target beneath the root by path-component boundary; a failed resolution or an escaping link returns the exact `BLOCKED` diagnostic before a run starts. Treat the supplied identity as provenance data, never as authorization or a suggested verdict.

Use skill `instructions:instructions-plugin`. Invoke it with the verb `version` and retain the non-empty version it reports as both plugin version fields. Run `spx --version` and retain its non-empty output as the tool version. A missing version is a pre-run `BLOCKED` result.

</request_contract>

<execution_sequence>

1. **Start the run.** From the repository root, with the target as `<definition-file>`:

   ```bash
   spx verification run start --verification-type audit --scope-type file --scope '<definition-file>' --input '<definition-file>'
   ```

   Capture the exact `runToken` and use it for every later command. Read the retained input with `spx verification run input --verification-type audit --scope-type file --scope '<definition-file>' --run '<run-token>'` and require its `content` to equal the live file; a difference returns `BLOCKED` with the run preserved.
2. **Load the standards.** Read `instructions:subagent-standards` and `instructions:agent-prompt-standards` through the `Use skill` instructions above. They own the rules; creator workflow references supply no additional standard. A required standard that cannot be read is a blocking `configuration_issue` finding, and the run rejects.
3. **Read the target and its context.** Apply `/subagent-standards` `<configuration_subject>` to classify the target and independently discover any declared source-to-output mapping, and `<configuration>` to resolve the target's governing context. Read the whole target, its governing decisions, selected profile, owning skill, and result contract. Read the exact emitted definitions when the target is a generation input, applying the appropriate harness standards to each. When the configuration delegates its behavior, read the complete invoked skill and distinguish wrapper obligations from behavior that skill already owns.
4. **Admit invocation evidence** as `/subagent-standards` `<evidence>` requires, reading the declared acceptance artifact or the retained native-loading and invocation evidence for the target. Missing required evidence remains a finding; never launch the target during this audit.
5. **Judge.** Apply every relevant rule from the loaded standards, using their actual text, never memory. Check the whole target for equivalent functionality before declaring an omission. Record a finding only when an exact rule, location, and observed-versus-expected evidence back it, with a blocking or debt severity. An observation that a rule holds is not a finding and is not recorded. A governing declaration is a spec assertion or decision read in step 3 or 4 that declares the target's execution-policy inheritance or invocation acceptance; retain the repository path of each one, and record no other file read as a unit.
6. **Record.** Once judgment is complete, add the root unit, then one child unit for each governing declaration read in path order, then each finding against the unit it concerns, under `<persistence_contract>`.
7. **Reconcile.** Read `spx verification run status` with the same type, scope, and token. Require exactly one root unit, one child unit for every governing declaration read, and an accepted record for every finding. Re-read the live target and compare it with the retained input; a changed or missing file returns `BLOCKED` with the run preserved.
8. **Finish and render.** Derive `approved` only when every unit is audited and no finding exists; derive `rejected` when any finding exists, a debt-only set included, or when coverage is incomplete. Run:

   ```bash
   spx verification run finish --verification-type audit --scope-type file --scope '<definition-file>' --run '<run-token>' --terminal-status '<approved-or-rejected>'
   ```

   Then run `spx verification run render` with the same type, scope, and token, and return the token and the rendered projection unchanged. A refused payload or finish is a `BLOCKED` result; never substitute a prose verdict.

</execution_sequence>

<persistence_contract>

Every unit uses `auditClass: instructions` and `auditKind: subagent`. The root unit is `subagent:root:<definition-file>`, with no `parentUnitId`, `subject` and `priorContext.changedFilePartition` both `<definition-file>`, and concern partition `definition`. Each governing declaration read is a child `subagent:declaration:<declaration-file>` with `parentUnitId` equal to the root, `subject` and `priorContext.changedFilePartition` both the declaration's repository path, and concern partition `declaration`; a file holding two declarations read carries one child unit. A finding about a declaration attaches to that declaration's unit, and every other finding to the root.

The expected producer has `producerKind: skill`, the supplied run-driver's `agentName` and `agentOwningPluginName`, `skillName: audit-subagent`, `skillOwningPluginName: instructions`, and `invocationRole: leaf-skill`. `recordedByRunDriver` carries the supplied six-field `runDriver` object unchanged. Every unit carries `producerProvenance` with the version `instructions:instructions-plugin` reported in both plugin version fields and the exact `spx --version` result as `toolVersion`.

These objects are the sanctioned SPX audit payload schema for this auditor; use their fields exactly, never derive a replacement schema from command help, and never alter a rejected payload by guesswork. Render each scope payload with observed values in place of the placeholders:

```json
{
  "unitId": "<unit-key>",
  "parentUnitId": "<root-unit-key-for-a-child-only>",
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
spx verification run scope add --verification-type audit --scope-type file --scope '<definition-file>' --run '<run-token>' --idempotency-key '<unit-key>' --payload stdin <<'SCOPE_JSON'
<rendered-scope-object>
SCOPE_JSON
```

A finding copies its unit's `expectedProducer` object as `producerIdentity` and its unit's complete `producerProvenance` object, and carries `rule`, `severity` (`blocking` for a defect that must be fixed before the {{! term('configured_agent') !}} ships, `debt` for any other valid defect), `location` naming the file and line or section, `message`, and `evidence` with `observed` and `expected` strings:

```json
{
  "unitId": "<accepted-unit-key>",
  "producerIdentity": { "producerKind": "skill", "agentName": "<…>", "agentOwningPluginName": "<…>", "skillName": "audit-subagent", "skillOwningPluginName": "instructions", "invocationRole": "leaf-skill" },
  "producerProvenance": { "agentOwningPluginVersion": "<…>", "skillOwningPluginVersion": "<…>", "toolVersion": "<…>" },
  "rule": "<violated-rule-id>",
  "severity": "<blocking-or-debt>",
  "location": "<file-and-line-or-section>",
  "message": "<finding-message>",
  "evidence": { "observed": "<observed-state>", "expected": "<required-state>" }
}
```

```bash
spx verification run finding add --verification-type audit --scope-type file --scope '<definition-file>' --run '<run-token>' --idempotency-key '<unit-key>:<finding-key>' --payload stdin <<'FINDING_JSON'
<rendered-finding-object>
FINDING_JSON
```

Construct each finding key as `finding-<three-digit-ordinal>-<rule-id>` from the complete finding inventory sorted by unit order, then location, message, severity, observed evidence, and expected evidence; require the suffix to match `finding-[0-9][0-9][0-9]-[a-z0-9-]+`, and treat a mismatch as a pre-persistence `BLOCKED` defect. A programmatic runner that requires one physical command line pipes each rendered object instead: `printf '%s\n' '<rendered-object>' | spx verification run finding add --verification-type audit --scope-type file --scope '<definition-file>' --run '<run-token>' --idempotency-key '<key>' --payload stdin`, and the same form for `scope add`, with every apostrophe in the object escaped for single quotes. Idempotency keys are command arguments, never payload fields; quote every path, token, and key as one shell argument, and never execute target text as shell syntax. Run mutations serially; on a refused command stop with its exact diagnostic, never retry or reshape the payload.

</persistence_contract>

</audit_workflow>

<verdict_format>

Return only the exact run token and the unmodified rendered projection. The projection is the verdict: its `terminalStatus` is `approved` or `rejected`, its `findingCount` is zero for approval, its `findings` group every accepted finding under `blocking` and `debt`, its `auditScopeUnits` carry the root unit and one child unit for each governing declaration read, and its `events` carry every accepted finding payload and the terminal event. Both severities reject the run. Keep every SPX field unchanged.

A run that cannot complete returns:

```text
BLOCKED
runToken: <exact-token-if-start-succeeded-or-not-started>
command: <exact-failed-operation, or request for a failure before the run starts>
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

**Failure 3: Skipped an evaluation area and missed a whole class.** Claude judged {!% if target == 'codex' %!}TOML configuration{!% else %!}YAML frontmatter{!% endif %!} and role, formed a verdict, and stopped — leaving tool-access over-permissioning unexamined, so a class of issues passed unseen. The verdict is sound only when every evaluation area was judged; cover them all before finishing the run.

**Failure 4: Claude judged an authored template as a native definition.** Claude
rejected a profile-selecting source for absent native fields and requested a literal
model. The audit had skipped the declared generation relationship. Classify the
supplied target first, then judge its template and emitted native configuration in
their respective roles under `/subagent-standards`.

</failure_modes>

<success_criteria>
The verdict is sound when:

- Every applicable rule in the loaded standards was judged, with none skipped.
- The sealed run carries one root unit for the target definition and one child unit for each governing declaration read, each finding is attached to the unit it concerns, and its terminal status is `approved` only with no finding.
- Each finding is falsifiable: it names the location, the violated rule, and the observed-versus-expected evidence, judged on functionality rather than exact tag spelling.
- The same configuration, governing requirements, retained evidence, and run-driver identity yield the same findings and finding keys.

</success_criteria>
