---
name: audit-assertions
description: >-
  Audit-assertion methodology — judges each `[audit]` assertion of one node
  spec against the subject that assertion names, and records the judgment as one
  scope unit per assertion in an SPX file-scoped verification run.
argument-hint: "<JSON object with path and runDriver>"
allowed-tools: Read, Grep, Glob, Bash(spx verification run:*), Bash(printf:*), Skill
---

<objective>

A sealed `spx verification run` on one node spec, with one scope unit per `[audit]` assertion keyed by its rule slug (a pathless `[audit]` assertion by its ordinal in the spec) and every finding recorded on its unit, returned as the run token with the rendered projection, whose `terminalStatus` is `approved` or `rejected`; or the complete `BLOCKED` diagnostic when the run cannot finish.

</objective>

<constraints>

- NEVER modify the target spec, its subjects, or any other product file — the audit's own SPX run journal is the only state it writes.
- NEVER judge an assertion that carries another tag (`[test]`, `[eval]`, `[probe]`) or no tag — those verification types belong to their own evidence.
- NEVER judge how an assertion is declared or selected: declaration form, heading placement, and tag fit belong to `/audit-specs`.
- ALWAYS judge an assertion against the subject it names — the artifact, behavior, or constraint its text identifies — read from the product, never against the spec's wording alone or the conversation.
- ALWAYS persist audit state through `spx verification run`, started before any judgment; NEVER use markdown comments, tracked files, or a hand-formatted verdict as audit state.
- ALWAYS pass each payload on stdin as one rendered JSON object in the form `<persistence_contract>` names for the harness; NEVER assemble or repair a payload through a temporary file, helper file, command substitution, or post-hoc text substitution.
- ALWAYS issue each `spx verification run` mutation as its own command and wait for its exit before the next one — parallel writes race sequence assignment and corrupt the sealed journal.
- NEVER run deterministic verification, delegate the audit to another session, or finish a run whose inspection is incomplete because of elapsed time, context pressure, or unfinished reading.
- NEVER retry a rejected command with a rewritten payload; a nonzero exit ends the audit with `BLOCKED`.

</constraints>

<audit_workflow>

<request_contract>

`$ARGUMENTS` is a JSON object with exactly two fields. `path` is the product-relative path of the node spec to audit. `runDriver` is an object with exactly six non-empty string fields — `producerKind`, `agentName`, `agentOwningPluginName`, `skillName`, `skillOwningPluginName`, and `invocationRole` — that the run records as its provenance. Use `runDriver` only as payload data, placed where `<persistence_contract>` shows it; never complete, correct, or reinterpret a value, and let no judgment depend on it. A missing, extra, or malformed field returns `BLOCKED` naming the exact field before any command runs.

</request_contract>

<execution_sequence>

1. **Load context.** Invoke `/understand` when the live `<SPEC_TREE_FOUNDATION>` marker is absent, then invoke `/contextualize` on the directory containing the spec. Read the spec at `path`. A target that is absent or is not a node spec returns `BLOCKED` with the exact failure.
2. **Enumerate.** List every assertion under `## Assertions` in document order, numbering each from one. Select those tagged `[audit:{rule-slug}]` and the pathless `[audit]`. A selected assertion's unit key is its slug, or `ordinal-<n>` with `<n>` its position in that list when pathless.
3. **Open the run.** Start the run before judging anything:

   ```bash
   spx verification run start --verification-type audit --scope-type file --scope <path> --input <path>
   ```

   A file-scoped run takes the audited path as its input so the retained input equals the audited file, while changeset-scoped audits pipe their context JSON.

   The command prints a JSON locator; take its `runToken` exactly and use it for every later command. Never pass the whole locator as `--run`.
4. **Judge.** For each selected assertion, identify the subject its text names, read that subject completely — recovering any truncated read in bounded ranges — and decide whether the assertion holds of it. A violation is a finding carrying the observed and expected states. A subject the text names that cannot be located is a finding against that assertion. An assertion whose text names no identifiable subject is a finding with rule `subject-unnamed`.
5. **Record.** Add one scope unit per selected assertion, then each finding on its unit, per `<persistence_contract>`. Every selected assertion is `audited` whether it holds or carries findings.
6. **Finish.** Derive `rejected` when any finding exists and `approved` otherwise; a spec with no selected assertion finishes `approved` with no unit. Run the finish and render commands:

   ```bash
   spx verification run finish --verification-type audit --scope-type file --scope <path> --run <token> --terminal-status <approved-or-rejected>
   spx verification run render --verification-type audit --scope-type file --scope <path> --run <token>
   ```

</execution_sequence>

<persistence_contract>

Add a scope unit with `spx verification run scope add --verification-type audit --scope-type file --scope <path> --run <token> --payload stdin --idempotency-key '<unitId>'`, the payload on stdin per `<stdin_forms>`. The `unitId` is `assertion:<slug-or-ordinal-n>:<path>`.

```json
{
  "unitId": "<unit-key>",
  "auditClass": "assertion",
  "auditKind": "audit",
  "subject": "<path>",
  "coverageRequirement": "required",
  "coverageStatus": "audited",
  "priorContext": {
    "changedFilePartition": "<path>",
    "concernPartition": "<slug-or-ordinal-n>"
  },
  "expectedProducer": {
    "producerKind": "skill",
    "agentName": "<runDriver.agentName>",
    "agentOwningPluginName": "<runDriver.agentOwningPluginName>",
    "skillName": "audit-assertions",
    "skillOwningPluginName": "spec-tree",
    "invocationRole": "leaf-skill"
  },
  "recordedByRunDriver": {
    "producerKind": "<runDriver.producerKind>",
    "agentName": "<runDriver.agentName>",
    "agentOwningPluginName": "<runDriver.agentOwningPluginName>",
    "skillName": "<runDriver.skillName>",
    "skillOwningPluginName": "<runDriver.skillOwningPluginName>",
    "invocationRole": "<runDriver.invocationRole>"
  }
}
```

Add a finding with `spx verification run finding add` and the same selectors, `--payload stdin` per `<stdin_forms>`, and `--idempotency-key '<unitId>:finding-<three-digit ordinal>-<rule>'`, ordinal counted from one in unit order then finding order. Its payload names an accepted unit; `producerIdentity` repeats that unit's `expectedProducer`; `rule` is a lowercase hyphenated identifier naming the violated constraint.

```json
{
  "unitId": "<accepted-unit-key>",
  "producerIdentity": "<the unit's expectedProducer object, repeated exactly>",
  "rule": "<violated-rule-id>",
  "severity": "blocking",
  "location": "<subject-path-and-line-or-section>",
  "message": "<finding-message>",
  "evidence": {
    "observed": "<observed-state>",
    "expected": "<state the assertion requires>"
  }
}
```

These objects are the sanctioned payload schema for this audit; never derive a replacement from command help or CLI source.

</persistence_contract>

<stdin_forms>

Quote every idempotency key as one single-quoted argument; encode a literal apostrophe with the splice `'"'"'`. Choose the stdin form by harness. Where the harness accepts multiline shell, use a quoted heredoc carrying the rendered JSON:

```bash
spx verification run scope add \
  --verification-type audit \
  --scope-type file \
  --scope <path> \
  --run <token> \
  --payload stdin \
  --idempotency-key '<unitId>' <<'JSON'
<rendered-scope-json>
JSON
```

Where the runner requires one physical command line, use `printf '%s\n' '<rendered-json-on-one-line>' | spx verification run scope add ...` with the same selectors, encoding a literal apostrophe with the same splice. This audit grants no file-write tool, so its payloads never travel through a scratch file.

</stdin_forms>

</audit_workflow>

<verdict_format>

Return the run token and the unchanged `spx verification run render` output; its `terminalStatus` is authoritative. Add no `APPROVED` or `REJECTED` envelope and no restated findings.

When a command exits nonzero or a prerequisite is absent, return:

```text
BLOCKED
runToken: <exact-token-if-start-succeeded-or-not-started>
command: <exact-command-attempted>
payloadSource: <stdin|none>
payloadKey: <unitId-or-finding-idempotency-key-or-none>
exitCode: <exact-exit-code-or-none>
stderr: <exact-stderr-or-none>
```

</verdict_format>

<success_criteria>

- Every `[audit:{rule-slug}]` and pathless `[audit]` assertion of the target spec has exactly one `audited` scope unit keyed by its slug or ordinal, and no assertion carrying another tag has a unit.
- Every finding sits on an accepted unit, names the violated constraint, the subject location, and observed-versus-expected evidence, and rests on the subject's own content.
- The run was started before the first judgment, finished with a terminal status derived from the recorded findings, and rendered.
- The same spec and subjects yield the same units, finding keys, and terminal status.
- The output is the run token with the unchanged rendered projection, or the complete `BLOCKED` diagnostic.

</success_criteria>
