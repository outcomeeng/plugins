---
name: audit-assertions
description: >-
  Audit-assertion methodology — judges each `[audit]` assertion of one node
  spec against the subject that assertion names, and records the judgment as one
  child scope unit per assertion under one root unit for the spec in an SPX
  file-scoped verification run.
argument-hint: "<JSON object with path and runDriver>"
allowed-tools: Read, Grep, Glob, Bash(spx verification run:*), Bash(printf '%s\n':*), Bash(git merge-base:*), Bash(git diff:*), {{! tool('use_skill') !}}
---

<objective>

A sealed `spx verification run` on one node spec, with one root scope unit for the spec (none when the spec has no `[audit]` assertion) and one child scope unit per `[audit]` assertion identified by its rule slug (a pathless `[audit]` assertion by its ordinal in the spec), every finding on touched text recorded on its child unit, returned as the run token with the rendered projection, whose `terminalStatus` is `approved` or `rejected`, followed by each other finding as a `filed` line; or the complete `BLOCKED` diagnostic when the run cannot finish.

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
- NEVER reject, or record on a unit, a finding that lies outside touched text; classify every finding as `${CLAUDE_SKILL_DIR}/references/touched-text.md` states and return each standing finding as `filed`.
- NEVER retry a rejected command with a rewritten payload; a nonzero exit ends the audit with `BLOCKED`.

</constraints>

<audit_workflow>

<request_contract>

`$ARGUMENTS` is a JSON object with exactly two fields. `path` is the product-relative path of the node spec to audit. `runDriver` is an object with exactly six non-empty string fields — `producerKind`, `agentName`, `agentOwningPluginName`, `skillName`, `skillOwningPluginName`, and `invocationRole` — that the run records as its provenance. Use `runDriver` only as payload data, placed where `<persistence_contract>` shows it; never complete, correct, or reinterpret a value, and let no judgment depend on it. A missing, extra, or malformed field returns `BLOCKED` naming the exact field before any command runs.

Use skill `spec-tree:spec-tree-plugin`. Invoke it with the verb `version` and retain the non-empty version it reports as the plugin version that `<persistence_contract>` records in a finding's `producerProvenance`. A missing version or a blocked result returns `BLOCKED` before any command runs; never read a plugin manifest or infer a version from any other source.

</request_contract>

<execution_sequence>

1. **Load context.** Invoke `/understand` when the live `<SPEC_TREE_FOUNDATION>` marker is absent, then invoke `/contextualize` on the directory containing the spec. Read the spec at `path`. A target that is absent or is not a node spec returns `BLOCKED` with the exact failure.
2. **Enumerate.** List every assertion under `## Assertions` in document order, numbering each from one. Select those tagged `[audit:{rule-slug}]` and the pathless `[audit]`. A selected assertion's designator is its slug, or `ordinal-<n>` with `<n>` its position in that list when pathless; its unit key is `assertion:<designator>:<path>`.
3. **Open the run.** Start the run before judging anything:

   ```bash
   spx verification run start --verification-type audit --scope-type file --scope <path> --input <path>
   ```

   A file-scoped run takes the audited path as its input so the retained input equals the audited file, while changeset-scoped audits pipe their context JSON.

   The command prints a JSON locator; take its `runToken` exactly and use it for every later command. Never pass the whole locator as `--run`.
4. **Judge.** For each selected assertion, identify the subject its text names, read that subject completely — recovering any truncated read in bounded ranges — and decide whether the assertion holds of it. A violation is a finding carrying the observed and expected states and a severity of `blocking` or `debt`, whose message opens with the assertion's designator, kept per `${CLAUDE_SKILL_DIR}/references/touched-text.md`. Merge the violations of one rule on one assertion into one finding, because a finding's key is its unit key and rule. A subject the text names that cannot be located is a finding against that assertion. An assertion whose text names no identifiable subject is a finding with rule `subject-unnamed`.
5. **Classify.** Resolve the base and run the diff commands as `${CLAUDE_SKILL_DIR}/references/touched-text.md` states, and sort each finding into touched text or standing text.
6. **Record.** When any assertion is selected, add the root scope unit first, because a run admits one root and every child names it, then one child scope unit per selected assertion, then each finding on touched text on its child unit, per `<persistence_contract>`. Every selected assertion is `audited` whether it holds or carries findings. A standing finding is recorded nowhere in the run.
7. **Finish.** Derive `rejected` when a finding on touched text exists and `approved` otherwise, whatever standing findings exist; a spec with no selected assertion finishes `approved` with no unit. Run the finish and render commands:

   ```bash
   spx verification run finish --verification-type audit --scope-type file --scope <path> --run <token> --terminal-status <approved-or-rejected>
   spx verification run render --verification-type audit --scope-type file --scope <path> --run <token>
   ```

</execution_sequence>

<persistence_contract>

Add a scope unit with `spx verification run scope add --verification-type audit --scope-type file --scope <path> --run <token> --payload stdin --idempotency-key '<unitId>'`, the payload on stdin per `<stdin_forms>`. The root unit's `unitId` is the audited `<path>`, its concern partition is `spec`, and it omits `parentUnitId`; the run admits one root. Each child unit's `unitId` is the unit key, `assertion:<designator>:<path>`, and its `parentUnitId` is the root's `unitId`. The class `spec` and kind `spec` are the pair `spx` accepts for a node spec subject, and the child unit key alone carries the assertion's identity; `spx` refuses the class `assertion`.

The root unit:

```json
{
  "unitId": "<path>",
  "auditClass": "spec",
  "auditKind": "spec",
  "subject": "<path>",
  "coverageRequirement": "required",
  "coverageStatus": "audited",
  "priorContext": {
    "changedFilePartition": "<path>",
    "concernPartition": "spec"
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

A child unit:

```json
{
  "unitId": "<unit-key>",
  "parentUnitId": "<path>",
  "auditClass": "spec",
  "auditKind": "spec",
  "subject": "<path>",
  "coverageRequirement": "required",
  "coverageStatus": "audited",
  "priorContext": {
    "changedFilePartition": "<path>",
    "concernPartition": "<designator>"
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

Add a finding with `spx verification run finding add` and the same selectors, `--payload stdin` per `<stdin_forms>`, and `--idempotency-key '<unitId>:<rule>'`, the finding key `${CLAUDE_SKILL_DIR}/references/touched-text.md` defines. Its payload names an accepted child unit; `producerIdentity` repeats that unit's `expectedProducer`; `producerProvenance` carries the plugin version `<request_contract>` retained in both version fields, and no `toolVersion`; `rule` is a lowercase hyphenated identifier naming the violated constraint.

```json
{
  "unitId": "<accepted-unit-key>",
  "producerIdentity": "<the unit's expectedProducer object, repeated exactly>",
  "producerProvenance": {
    "agentOwningPluginVersion": "<spec-tree-plugin-version>",
    "skillOwningPluginVersion": "<spec-tree-plugin-version>"
  },
  "rule": "<violated-rule-id>",
  "severity": "<blocking-or-debt>",
  "location": "<subject-path-and-line-or-section>",
  "message": "<designator>: <finding-message>",
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

Return the run token and the unchanged `spx verification run render` output; its `terminalStatus` is authoritative. Add no `APPROVED` or `REJECTED` envelope and no restated findings. After the projection, return each standing finding on its own line in the form `${CLAUDE_SKILL_DIR}/references/touched-text.md` gives, or `filed: none`.

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

- When the spec has a selected assertion, the run holds one `audited` root scope unit for the target spec, and every `[audit:{rule-slug}]` and pathless `[audit]` assertion of the spec has exactly one `audited` child unit under its unit key that names the root, and no assertion carrying another tag has a unit.
- Every recorded finding lies on touched text and sits on an accepted unit, names the violated constraint, the subject location, and observed-versus-expected evidence, and rests on the subject's own content.
- Every standing finding appears as a `filed` line carrying its key, `baseRefEvidence`, and `issuesEntry`, and rejects no run.
- The run was started before the first judgment, finished with a terminal status derived from the recorded findings, and rendered.
- The same spec, subjects, and base yield the same units, finding keys, and terminal status.
- The output is the run token with the unchanged rendered projection and the `filed` lines, or the complete `BLOCKED` diagnostic.

</success_criteria>
