<objective>

The unit identities, payload schemas, and payload-file rules with which the test-evidence audit records its run.

</objective>

<contents>

- `<persistence_contract>` — unit identities and the unit and finding payloads
- `<payload_files>` — how a payload reaches a command

</contents>

<persistence_contract>

Every unit carries `auditClass: implementation` and `auditKind: tests`. The scope `<scope>` is the node spec path or `<base>..<head>`, and `<spec>` is the spec path an assertion belongs to. Unit identities:

| Unit       | `unitId`                                            | `parentUnitId` | `subject`     | `concernPartition` |
| ---------- | --------------------------------------------------- | -------------- | ------------- | ------------------ |
| Root       | `tests:root:<scope>`                                | omitted        | `<scope>`     | `tests`            |
| Assertion  | `tests:assertion:<ordinal>:<spec>`                  | the root       | `<spec>`      | `assertion`        |
| Test file  | `tests:file:<ordinal>:<spec>:<concern>:<test-path>` | its assertion  | `<test-path>` | the concern        |
| Retirement | `tests:retired:<test-path>`                         | the root       | `<test-path>` | `retired`          |

The concern of a test-file unit is `evidence` for this audit's language-neutral properties and `language-<lang>` for a composed language concern. Each unit's `priorContext.changedFilePartition` is its `subject`; a test-file unit adds `priorContext.languagePartition` with its language, and the `evidence` concern omits it. A test-file unit and an assertion unit are `audited`; a retirement unit is `not-applicable`. Every unit's `expectedProducer` is this skill.

A scope unit:

```json
{
  "unitId": "<unit-key>",
  "parentUnitId": "<parent-unit-key-for-a-child-only>",
  "auditClass": "implementation",
  "auditKind": "tests",
  "subject": "<subject>",
  "coverageRequirement": "required",
  "coverageStatus": "<audited-or-not-applicable>",
  "priorContext": {
    "changedFilePartition": "<subject>",
    "concernPartition": "<concern-partition>"
  },
  "expectedProducer": {
    "producerKind": "skill",
    "agentName": "<runDriver.agentName>",
    "agentOwningPluginName": "<runDriver.agentOwningPluginName>",
    "skillName": "audit-tests",
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

Add a unit with `spx verification run scope add --verification-type audit --scope-type <file-or-changeset> --scope <scope> --run <token> --payload <payload-file> --idempotency-key '<unitId>'`. The root unit omits the `parentUnitId` field.

Add a finding with `spx verification run finding add` and the same selectors, `--payload <payload-file>`, and `--idempotency-key '<finding-key>'`, the finding key `${CLAUDE_SKILL_DIR}/references/touched-text.md` defines as `<unitId>:<rule>`. Its payload names an accepted unit; `producerIdentity` repeats that unit's `expectedProducer`; `producerProvenance` carries the spec-tree plugin version the request contract retained in both version fields, and no `toolVersion`; `rule` is one identifier from `<rule_catalog>` in `${CLAUDE_SKILL_DIR}/references/test-evidence-rules.md`, and `severity` is the severity that row declares; name no identifier outside that catalog. `evidence.expected` names the remediation owner the catalog row declares.

```json
{
  "unitId": "<accepted-unit-key>",
  "producerIdentity": "<the unit's expectedProducer object, repeated exactly>",
  "producerProvenance": {
    "agentOwningPluginVersion": "<spec-tree-plugin-version>",
    "skillOwningPluginVersion": "<spec-tree-plugin-version>"
  },
  "rule": "<finding-identifier>",
  "severity": "<catalog-row-severity>",
  "location": "<artifact-path-and-assertion-or-declaration-text>",
  "message": "<finding-message-naming-assertion-rule-and-evidentiary-gap>",
  "evidence": {
    "observed": "<observed-state>",
    "expected": "<state the rule requires, and its remediation owner>"
  }
}
```

These objects are the sanctioned payload schema for this audit; never derive a replacement from command help or CLI source.

</persistence_contract>

<payload_files>

Quote every idempotency key as one single-quoted argument; encode a literal apostrophe with the splice `'"'"'`.

- ALWAYS write each scope and finding payload with the file-write tool to its own file in the scratch directory the harness names for the session, under a name unique to this run and payload, such as `<run-token>-scope-<n>.json` and `<run-token>-finding-<n>.json`. Where the harness names no scratch directory, use the one the hosting environment designates, such as `$RUNNER_TEMP` on a hosted runner.
- ALWAYS write only payload files with the file-write tool.
- ALWAYS pass `--payload` the path exactly as the file-write tool's result reports it, copied from that result, never retyped.
- ALWAYS add each unit and each finding with its own literal command and its own payload file, one at a time, and stop the audit at the first command that exits nonzero, returning the `BLOCKED` diagnostic.
- NEVER remove a payload file; the harness clears its scratch directory.

</payload_files>
