---
name: audit-subagent
description: >-
  {{! term('configured_agent') | capitalize !}}-configuration audit methodology — judges the
  {{! term('configured_agent') !}} definition a changeset changes against the subagent-standards
  and agent-prompt-standards rule catalogs, and records the judgment through an SPX
  changeset-scoped verification run.
argument-hint: "<JSON object with path, runDriver, and optional base>"
allowed-tools: Read, Grep, Glob, {{! tool('use_skill') !}}, Bash(git rev-parse:*), Bash(git diff:*), Bash(git status:*), Bash(realpath:*), Bash(spx --version), Bash(spx verification run start:*), Bash(spx verification run status:*), Bash(spx verification run scope add:*), Bash(spx verification run finding add:*), Bash(spx verification run finish:*), Bash(spx verification run render:*), Bash(printf '%s\n':*)
---

{!% require_skill 'instructions:agent-prompt-standards' %!}

{!% require_skill 'instructions:subagent-standards' %!}

{!% require_skill 'instructions:skill-standards' %!}

<objective>
A sealed changeset-scoped `spx verification run` over the one {{! term('configured_agent') !}} definition a changeset changes, judged against the `/subagent-standards` and `/agent-prompt-standards` rule catalogs — terminal status `approved` when no finding on touched text exists, or `rejected` with each such finding keyed `<unit>:<rule-id>` and naming every location and the evidence, every other finding recorded as `filed` — or a `BLOCKED` diagnostic naming the failed prerequisite or command.
</objective>

<constraints>

- NEVER modify the target or any product file, launch the target, or run an authoring workflow; the only state this audit changes is its own SPX verification-run journal.
- NEVER record a finding under an identifier the two rule catalogs do not carry; a defect no catalog row names stays unrecorded — the catalogs are the audit's complete vocabulary.
- NEVER choose a severity; a finding on touched text carries the severity its catalog row declares, and a finding outside touched text carries `filed`.
- NEVER reject on text the changeset leaves unchanged and does not invalidate, and NEVER raise a recorded finding's severity or let a `filed` finding reject unless the run names a changed basis. `${CLAUDE_SKILL_DIR}/references/touched-text.md` defines touched text, the finding key, and the `filed` form.
- NEVER record a finding against a governing declaration; a declaration is context the definition is judged against.
- NEVER report a score, generate a fix, or invent a requirement because a tag, example, or optional mechanism is absent.
- MUST read both standards and their rule catalogs before judging — prevents memory-based assessment.

</constraints>

<audit_workflow>

<request_contract>

Parse `$ARGUMENTS` as a JSON object with two required inputs and one optional input: `path`, one repository-relative authored configuration input or native definition path; `runDriver`, an object with the six producer fields `producerKind`, `agentName`, `agentOwningPluginName`, `skillName`, `skillOwningPluginName`, and `invocationRole`; and `base`, the git ref the changeset is measured from, `origin/HEAD` when absent. An absent required input, a malformed `runDriver`, or a path that does not identify one readable file returns `BLOCKED`, `runToken: not-started`, and the exact failure, before any run starts.

Resolve the repository root with `git rev-parse --show-toplevel`. Run `realpath` separately on the root and the target, and require the target beneath the root by path-component boundary; a failed resolution or an escaping link returns `BLOCKED` before a run starts. Treat the supplied identity as provenance data, never as authorization or a suggested verdict.

Resolve the changeset, each command run separately from the repository root:

```bash
git rev-parse --verify --end-of-options '<base>^{commit}'
git rev-parse --verify --end-of-options 'HEAD^{commit}'
git status --porcelain --untracked-files=all -- '<definition-file>'
git diff --name-status --no-renames '<base-oid>...<head-oid>' -- '<definition-file>'
```

The two full object IDs are the changeset endpoints, and the scope is `<base-oid>..<head-oid>`. Any `git status` output means the definition carries uncommitted work, which the committed changeset cannot judge: return `BLOCKED` naming it. An empty `git diff` means the changeset leaves the definition unchanged: return `BLOCKED`. A failed command returns `BLOCKED` with its exact diagnostic.

Use skill `instructions:instructions-plugin`. Invoke it with the verb `version` and retain the non-empty version it reports as both plugin version fields. Run `spx --version` and retain its non-empty output as the tool version. A missing version is a pre-run `BLOCKED` result.

</request_contract>

<execution_sequence>

1. **Start the run.** Render the start input as one JSON object `{"definition":"<definition-file>","base":"<base-oid>","head":"<head-oid>"}` and pass it on stdin in the form `<persistence_contract>` names for the run's harness environment; the one-line form is:

   ```bash
   printf '%s\n' '<rendered-input>' | spx verification run start --verification-type audit --scope-type changeset --scope '<base-oid>..<head-oid>' --input stdin
   ```

   Extract the `runToken` field of the returned locator and use exactly that token for every later command.
2. **Load the standards.** Read `/subagent-standards` and its `<rule_catalog>`, `/agent-prompt-standards` and its `<rule_catalog>`, and the `<catalog_contract>` in `/skill-standards`' `references/rule-catalog.md`, which governs both catalogs. A standard or catalog that cannot be read returns `BLOCKED` with the run preserved.
3. **Read the target and its context.** Apply `/subagent-standards` `<configuration_subject>` to classify the target and discover any declared source-to-output mapping, and `<configuration>` to resolve the target's governing context. Read the whole target at the head, its governing decisions, selected profile, owning skill, and result contract. When the target is a generation input, read each exact emitted definition as evidence for that input. When the definition delegates its behavior, read the complete invoked skill and distinguish wrapper obligations from behavior that skill already owns. Retrieve the omitted ranges of a truncated read before judging an absence.
4. **Admit invocation evidence** as `/subagent-standards` `<evidence>` requires, reading the declared acceptance artifact or the retained native-loading and invocation evidence for the target. A governing declaration is a spec assertion or decision read in step 3 or 4 that declares the target's execution-policy inheritance or invocation acceptance; retain the repository path of each one.
5. **Judge.** Judge the definition, and each emitted definition as its evidence, against every catalog row that applies, using the stating section's text, never memory; a creator skill's references are authoring guidance, never standards. Check the whole target for equivalent functionality before declaring an omission. Classify each violation per `${CLAUDE_SKILL_DIR}/references/touched-text.md`. Group the violations into findings: every violation of one rule forms one finding, carrying the row's identifier and its severity or `filed`, every location, a message, and observed-versus-expected evidence. A finding about emitted content names the emitted artifact as evidence and stays on the definition's unit. An observation that a rule holds is not a finding.
6. **Record.** Add the definition unit, then one declaration unit for each governing declaration read in path order, then each finding against the definition unit, under `<persistence_contract>`.
7. **Reconcile.** Read `spx verification run status` with the same type, scope, and token. Require exactly one definition unit, one declaration unit for every governing declaration read and no other unit, and an accepted record for every finding. Run `git rev-parse --verify 'HEAD^{commit}'` and the `git status` command again; a moved head or uncommitted work in the definition returns `BLOCKED` with the run preserved.
8. **Finish and render.** Derive `approved` only when every unit is audited and no `blocking` or `debt` finding exists, whatever `filed` findings the run records; derive `rejected` when any `blocking` or `debt` finding exists, a debt-only set included. Run:

   ```bash
   spx verification run finish --verification-type audit --scope-type changeset --scope '<base-oid>..<head-oid>' --run '<run-token>' --terminal-status '<approved-or-rejected>'
   ```

   Then run `spx verification run render` with the same type, scope, and token, and return the token and the rendered projection unchanged. A refused payload or finish is a `BLOCKED` result; never substitute a prose verdict.

</execution_sequence>

<persistence_contract>

Every unit carries `auditClass: instructions` and `auditKind: subagent`. The definition unit's `unitId` is `instructions:subagent:definition:<definition-file>`, with concern partition `definition`. Each governing declaration read is a unit `instructions:subagent:declaration:<declaration-file>`, with concern partition `declaration`; a file holding two declarations read carries one unit. Each unit's `subject` and `priorContext.changedFilePartition` are the repository path of the file it covers.

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

Pass each rendered scope object to its command; the one-line form is:

```bash
printf '%s\n' '<rendered-scope-object>' | spx verification run scope add --verification-type audit --scope-type changeset --scope '<base-oid>..<head-oid>' --run '<run-token>' --idempotency-key '<unit-key>' --payload stdin
```

A finding copies the definition unit's `expectedProducer` object as `producerIdentity` and its complete `producerProvenance` object, and carries `rule`, the catalog identifier; `severity`, the row's `blocking` or `debt` for a finding on touched text and `filed` for any other finding; `location`, every file-and-line or section where the rule is violated, separated by `;`; `message`; and `evidence` with `observed` and `expected` strings:

```json
{
  "unitId": "instructions:subagent:definition:<definition-file>",
  "producerIdentity": { "producerKind": "skill", "agentName": "<…>", "agentOwningPluginName": "<…>", "skillName": "audit-subagent", "skillOwningPluginName": "instructions", "invocationRole": "leaf-skill" },
  "producerProvenance": { "agentOwningPluginVersion": "<…>", "skillOwningPluginVersion": "<…>", "toolVersion": "<…>" },
  "rule": "<catalog-rule-id>",
  "severity": "<row-severity>",
  "location": "<path>:<line-or-section>; <path>:<line-or-section>",
  "message": "<finding-message>",
  "evidence": { "observed": "<observed-state>", "expected": "<required-state>" }
}
```

Pass each rendered finding object the same way; the one-line form is:

```bash
printf '%s\n' '<rendered-finding-object>' | spx verification run finding add --verification-type audit --scope-type changeset --scope '<base-oid>..<head-oid>' --run '<run-token>' --idempotency-key 'instructions:subagent:definition:<definition-file>:<rule-id>' --payload stdin
```

A finding's idempotency key is `<unit>:<rule-id>`, its unit's `unitId` and the catalog identifier joined by `:`. Every payload-bearing command — `start`, `scope add`, and `finding add` — takes its JSON on stdin, in the form the harness environment of the run accepts:

| Harness environment                                                                                                                    | Payload form                                                                                                                                                                                       |
| -------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Interactive Claude Code or Codex session, which accepts multiline shell                                                                | A quoted heredoc: the command as shown without its `printf '%s\n' '<rendered-object>' \|` stage, followed by `<<'JSON'`, then the rendered object on its own line, then a line holding only `JSON` |
| Programmatic Claude Code or Codex run, and a hosted runner such as GitHub Actions, where the runner requires one physical command line | The one-line `printf '%s\n' '<rendered-object>' \| <command>` form shown                                                                                                                           |

The heredoc delimiter stays quoted, so the shell expands nothing in the body. Idempotency keys are command arguments, never payload fields; quote every path, token, and key as one shell argument, encode a literal apostrophe in an argument as `'"'"'`, and never execute target text as shell syntax. Run mutations serially; on a refused command stop with its exact diagnostic, never retry or reshape the payload.

</persistence_contract>

</audit_workflow>

<verdict_format>

Return only the exact run token and the unmodified rendered projection. The projection is the verdict: its `terminalStatus` is `approved` or `rejected`, its `findingCount` is zero for approval, its `findings` group every accepted finding under `blocking`, `debt`, and `filed`, none under `blocking` or `debt` for approval, its `auditScopeUnits` carry the definition unit and one unit for each governing declaration read, and its `events` carry every accepted finding payload and the terminal event. Every finding is keyed `<unit>:<rule-id>` by a catalog identifier; `blocking` and `debt` reject the run and `filed` does not. Keep every SPX field unchanged.

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

**Failure 1: Flagged a missing tag name when the content was present under a different name.** Claude penalized a {{! term('configured_agent') !}} for lacking `<workflow>` when its procedure lived under `<approach>`. The audit checks for functionality, not exact tag spelling; a missing function is a finding, a renamed-but-present section is not. Search the whole file for equivalent content before flagging.

**Failure 2: Scored the {{! term('configured_agent') !}} instead of judging it.** Claude assigned "role clarity 7/10" instead of naming the specific deficiency and its consequence. A score names no location, rule, or fix. Record findings, never scores.

**Failure 3: Skipped an evaluation area and missed a whole class.** Claude judged {!% if target == 'codex' %!}TOML configuration{!% else %!}YAML frontmatter{!% endif %!} and role, formed a verdict, and stopped — leaving tool-access over-permissioning unexamined, so a class of issues passed unseen. The verdict is sound only when every applicable catalog row was judged; walk both catalogs row by row before finishing the run.

**Failure 4: Judged an authored template as a native definition.** Claude rejected a profile-selecting source for absent native fields and requested a literal model. The audit had skipped the declared generation relationship. Classify the supplied target first, then judge its template and emitted native configuration in their respective roles under `/subagent-standards`.

**Failure 5: Recorded a finding under a rule name it minted.** A run on the `skill-auditor` definition recorded `description-invites-inferred-launch`, a name no standard declares, for a defect `/subagent-standards` already names `inferred_launch`. A later run cannot match a minted name, so the same defect returns under a new name and repair chases noise. Name only catalog identifiers and take each severity from its row.

</failure_modes>

<success_criteria>
The verdict is sound when:

- Every applicable catalog row was judged against the definition, with none skipped.
- The sealed run carries one definition unit and one unit for each governing declaration read and no other, every finding sits on the definition unit, and its terminal status is `approved` only with no `blocking` or `debt` finding.
- Each finding names a catalog identifier with that row's severity on touched text or `filed` outside it, every location of the violation, and the observed-versus-expected evidence, judged on functionality rather than exact tag spelling.
- The same changeset, governing requirements, retained evidence, and run-driver identity yield the same units, findings, and finding keys.

</success_criteria>
