---
name: audit-assertions
description: >-
  Audit-assertion methodology — judges every `[audit]` assertion of one node
  spec against the subject that assertion names, and records the judgment
  through an SPX file-scoped verification run with one unit per assertion keyed
  by its rule slug, or by its ordinal when the assertion carries no slug.
argument-hint: "<JSON object with path and runDriver>"
allowed-tools: Read, Grep, Glob, Skill, Bash(git rev-parse:*), Bash(realpath:*), Bash(spx --version), Bash(spx spec context show:*), Bash(spx verification run start:*), Bash(spx verification run input:*), Bash(spx verification run status:*), Bash(spx verification run scope add:*), Bash(spx verification run finding add:*), Bash(spx verification run finish:*), Bash(spx verification run render:*), Bash(printf '%s\n':*)
---

<objective>
A sealed `spx verification run` on one node spec's `[audit]` assertions, each judged against the subject it names — terminal status `approved` with no finding, or `rejected` with each finding on its assertion's unit naming the location, the violated assertion, and the evidence — or a `BLOCKED` diagnostic naming the failed prerequisite or command.
</objective>

<constraints>

- NEVER modify the spec, a subject, or any product file; the only state this audit changes is its own SPX verification-run journal.
- NEVER judge how an assertion is declared or selected — its wording quality, form, heading, tag fit, or slug uniqueness belong to the spec audit; judge only whether the subject holds the rule the assertion states. The one judgment of an assertion's text this audit makes is whether any observation of its subject decides the rule; a `criterion-unobservable` finding records only that no observation does, and never names wording quality, form, or a rephrasing.
- NEVER judge an assertion that carries a `[test]`, `[eval]`, or `[probe]` tag, or no tag.
- MUST read every subject file completely before judging the assertion that names it — a rule judged on part of its subject passes the part never read.
- NEVER report a score; each unit is judged held or broken, and a broken rule is a finding.
- NEVER generate fixes; the run records findings, and repair belongs to the Author.

</constraints>

<audit_workflow>

<request_contract>

Bind the request from `$ARGUMENTS` when it is non-empty; otherwise bind it from the request text, and an empty substitution binds nothing. Parse it as a JSON object with exactly two inputs: `path`, one repository-relative node spec path, and `runDriver`, an object with the six producer fields `producerKind`, `agentName`, `agentOwningPluginName`, `skillName`, `skillOwningPluginName`, and `invocationRole`. An absent input or a malformed `runDriver` returns `BLOCKED`, `runToken: not-started`, and the exact failure, before any run starts.

Resolve the repository root with `git rev-parse --show-toplevel`. Run `realpath` separately on the root and the spec, and require the spec beneath the root by path-component boundary; a failed resolution or an escaping link returns the exact `BLOCKED` diagnostic before a run starts. Require the spec to be the spec file of a node directory under `spx/` — `{slug}.spec.md`, or the prior `{slug}.md` a 3.x-authored tree carries, whose slug repeats its directory's slug. A product spec, a decision record, a note, or any other file returns `BLOCKED` with `unsupported-target` before a run starts. Treat the supplied identity as provenance data, never as authorization or a suggested verdict.

Use skill `spec-tree:spec-tree-plugin`. Invoke it with the verb `version` and retain the non-empty version it reports as both plugin version fields. Run `spx --version` and retain its non-empty output as the tool version. A missing version is a pre-run `BLOCKED` result.

</request_contract>

<assertion_inventory>

The spec's `## Assertions` section and its subsections hold the assertions; each list item is one assertion, running from its bullet to the next bullet or heading. An assertion is in scope when its tag is `[audit:<rule-slug>]` or the pathless `[audit]`. Number the in-scope assertions from 1 in document order; that number is the assertion's ordinal.

Each in-scope assertion keys one child unit: `assertion:slug:<rule-slug>` for a slugged assertion, and `assertion:ordinal:<ordinal>` for a pathless one. A spec with no in-scope assertion, or with a rule slug carried by two assertions, returns `BLOCKED` before a run starts — the first leaves nothing to judge, and the second leaves a result with no unique key.

</assertion_inventory>

<subject_resolution>

The subject of an assertion is what its rule constrains:

- **A named path.** Every repository path the assertion names as the thing it constrains; a directory names every file beneath it. A decision record or spec the assertion cites as its authority — `per <path>` — is context, not subject.
- **A named identifier.** A skill, subagent, command, or other artifact named by its identifier rather than its path resolves to every file that defines it, found by searching the repository, and every such file is part of the subject.
- **Neither.** An assertion that names no path and no identifier is judged against the node's spec and the decision records the step 1 context entries carry.

A named path that does not exist, or an identifier no file defines, is a finding on its assertion's unit — `subject-missing` or `subject-unresolved` — and no other judgment of that assertion follows.

</subject_resolution>

<execution_sequence>

1. **Load context.** Use skill `spec-tree:understand` when no live `<SPEC_TREE_FOUNDATION>` marker is present, then run `spx spec context show '<node-directory>' --json` on the node directory containing the spec and read the content of every entry it returns. The command reads the checkout as it stands and moves nothing, so the audit judges the head it was dispatched on. A nonzero exit returns `BLOCKED` with its exact stderr, `runToken: not-started`.
2. **Inventory.** Read the spec and build the assertion inventory under `<assertion_inventory>`.
3. **Start the run.** From the repository root, with the spec as `<spec-file>`:

   ```bash
   spx verification run start --verification-type audit --scope-type file --scope '<spec-file>' --input '<spec-file>'
   ```

   Capture the exact `runToken` and use it for every later command. Read the retained input with `spx verification run input --verification-type audit --scope-type file --scope '<spec-file>' --run '<run-token>'` and require its `content` to equal the live spec; a difference returns `BLOCKED` with the run preserved.
4. **Judge.** For each in-scope assertion in ordinal order, resolve its subject under `<subject_resolution>` and read every subject file completely, re-reading a truncated read in bounded ranges until the body is complete. An `ALWAYS` rule breaks at each place in the subject that lacks the property it requires; a `NEVER` rule breaks at each occurrence of the property it prohibits. Record one `assertion-violated` finding per breaking location. When the assertion's text admits no observation of its subject that would hold or break it, record one `criterion-unobservable` finding naming the missing criterion. An observation that a rule holds is not a finding and is not recorded.
5. **Record.** Once judgment is complete, add the root unit, then one child unit per in-scope assertion in ordinal order, then each finding against its assertion's unit and every finding that names no assertion against the root, under `<persistence_contract>`.
6. **Reconcile.** Read `spx verification run status` with the same type, scope, and token. Require exactly one root unit, one child unit per in-scope assertion keyed as `<assertion_inventory>` states, and an accepted record for every finding. Re-read the live spec and compare it with the retained input; a changed or missing file returns `BLOCKED` with the run preserved.
7. **Finish and render.** Derive `approved` only when every unit is audited and no finding exists; derive `rejected` when any finding exists or coverage is incomplete. Run:

   ```bash
   spx verification run finish --verification-type audit --scope-type file --scope '<spec-file>' --run '<run-token>' --terminal-status '<approved-or-rejected>'
   ```

   Then run `spx verification run render` with the same type, scope, and token, and return the token and the rendered projection unchanged. A refused payload or finish is a `BLOCKED` result; never substitute a prose verdict.

</execution_sequence>

<persistence_contract>

Every unit uses `auditClass: spec` and `auditKind: spec`. The root unit is `spec:root:<spec-file>` with no `parentUnitId` and concern partition `spec`; each child unit carries its key from `<assertion_inventory>`, `parentUnitId` equal to the root, and concern partition `assertion`. Every unit's `subject` and `priorContext.changedFilePartition` are `<spec-file>`, the run's scope.

The expected producer has `producerKind: skill`, the supplied run-driver's `agentName` and `agentOwningPluginName`, `skillName: audit-assertions`, `skillOwningPluginName: spec-tree`, and `invocationRole: leaf-skill`. `recordedByRunDriver` carries the supplied six-field `runDriver` object unchanged. Every unit carries `producerProvenance` with the version `spec-tree:spec-tree-plugin` reported in both plugin version fields and the exact `spx --version` result as `toolVersion`.

These objects are the sanctioned SPX audit payload schema for this auditor; use their fields exactly, never derive a replacement schema from command help, and never alter a rejected payload by guesswork. Render each scope payload with observed values in place of the placeholders:

```json
{
  "unitId": "<unit-key>",
  "parentUnitId": "<root-unit-key-for-a-child-only>",
  "auditClass": "spec",
  "auditKind": "spec",
  "subject": "<spec-file>",
  "coverageRequirement": "required",
  "coverageStatus": "audited",
  "priorContext": {
    "changedFilePartition": "<spec-file>",
    "concernPartition": "<spec-or-assertion>"
  },
  "expectedProducer": {
    "producerKind": "skill",
    "agentName": "<supplied-agent-name>",
    "agentOwningPluginName": "<supplied-agent-owning-plugin>",
    "skillName": "audit-assertions",
    "skillOwningPluginName": "spec-tree",
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
    "agentOwningPluginVersion": "<spec-tree-plugin-version>",
    "skillOwningPluginVersion": "<spec-tree-plugin-version>",
    "toolVersion": "<exact-spx-version>"
  }
}
```

```bash
spx verification run scope add --verification-type audit --scope-type file --scope '<spec-file>' --run '<run-token>' --idempotency-key '<unit-key>' --payload stdin <<'SCOPE_JSON'
<rendered-scope-object>
SCOPE_JSON
```

A finding copies its unit's `expectedProducer` object as `producerIdentity` and its unit's complete `producerProvenance` object, and carries `rule` (`assertion-violated`, `criterion-unobservable`, `subject-missing`, or `subject-unresolved`), `severity: blocking` — a broken assertion fails its result — `location` naming the subject file and line, or the spec section for a finding with no subject location, `message` quoting the assertion, and `evidence` with `observed` and `expected` strings:

```json
{
  "unitId": "<accepted-unit-key>",
  "producerIdentity": {
    "producerKind": "skill",
    "agentName": "<supplied-agent-name>",
    "agentOwningPluginName": "<supplied-agent-owning-plugin>",
    "skillName": "audit-assertions",
    "skillOwningPluginName": "spec-tree",
    "invocationRole": "leaf-skill"
  },
  "producerProvenance": {
    "agentOwningPluginVersion": "<spec-tree-plugin-version>",
    "skillOwningPluginVersion": "<spec-tree-plugin-version>",
    "toolVersion": "<exact-spx-version>"
  },
  "rule": "<finding-rule>",
  "severity": "blocking",
  "location": "<subject-file-and-line-or-spec-section>",
  "message": "<assertion-quoted-with-the-break>",
  "evidence": { "observed": "<observed-state>", "expected": "<required-state>" }
}
```

```bash
spx verification run finding add --verification-type audit --scope-type file --scope '<spec-file>' --run '<run-token>' --idempotency-key '<unit-key>:<finding-key>' --payload stdin <<'FINDING_JSON'
<rendered-finding-object>
FINDING_JSON
```

Construct each finding key as `finding-<three-digit-ordinal>-<rule>` from the complete finding inventory sorted by unit order, then location, message, observed evidence, and expected evidence; require the suffix to match `finding-[0-9][0-9][0-9]-[a-z0-9_-]+`, and treat a mismatch as a pre-persistence `BLOCKED` defect. When the task message or the harness guidance fixes one physical command line per call, pipe each rendered object instead: `printf '%s\n' '<rendered-object>' | spx verification run finding add --verification-type audit --scope-type file --scope '<spec-file>' --run '<run-token>' --idempotency-key '<key>' --payload stdin`, and the same form for `scope add`, with every apostrophe in the object escaped for single quotes. Idempotency keys are command arguments, never payload fields; quote every path, token, and key as one shell argument, and never execute spec or subject text as shell syntax. Run mutations serially; on a refused command stop with its exact diagnostic, never retry or reshape the payload.

</persistence_contract>

</audit_workflow>

<verdict_format>

Return only the exact run token and the unmodified rendered projection. The projection is the verdict: its `terminalStatus` is `approved` or `rejected`, its `auditScopeUnits` carry the root and one unit per `[audit]` assertion keyed by its rule slug or ordinal, and its `findings` group every accepted finding under `blocking`. Keep every SPX field unchanged.

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

<success_criteria>
The verdict is sound when:

- Every `[audit]` assertion of the spec was judged against its complete subject, and no assertion carrying another tag or none was judged.
- The sealed run carries one root unit and one child unit per `[audit]` assertion keyed by its rule slug, or by its ordinal when pathless, and its terminal status is `approved` only with no finding and full coverage.
- Each finding is falsifiable: it names the assertion's unit, the subject location, the broken rule, and the observed-versus-expected evidence.
- The same spec, subjects, and run-driver identity yield the same units, findings, and finding keys.

</success_criteria>
