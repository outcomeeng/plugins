<objective>

The unit identities, payload schemas, and payload-file rules with which the changeset-coherence audit records its run.

</objective>

<contents>

- `<persistence_contract>` — unit identities and the unit and finding payloads
- `<payload_files>` — how a payload reaches a command

</contents>

<persistence_contract>

The run is changeset-scoped on `<base>..<head>`, written with the full base and head commit identities exactly as the resolver reported them. Every unit carries `auditClass: changeset`. Unit identities:

| Unit        | `unitId`                                         | `auditKind`   | `parentUnitId` | `subject`         | `concernPartition` |
| ----------- | ------------------------------------------------ | ------------- | -------------- | ----------------- | ------------------ |
| Root        | `coherence:root:<base>..<head>`                  | `coherence`   | omitted        | `<base>..<head>`  | `coherence`        |
| Review unit | `coherence:review-unit:<ordinal>:<base>..<head>` | `review-unit` | the root       | `review-unit-<n>` | `review-unit`      |

The root is the first unit of the run and is `required`. Each review unit is `required`; `<ordinal>` and `<n>` are the review unit's position in the dependency order. Every unit's `priorContext.changedFilePartition` is `<base>..<head>`. A unit whose inspection was completed is `audited`; a unit whose evidence cannot be established is `incomplete`. Every unit's `expectedProducer` is this skill.

A changeset that forms one inseparable cluster records one review unit. A changeset with two or more independently mergeable clusters records one review unit per cluster, in the order of the review-unit sequence.

A scope unit:

```json
{
  "unitId": "<unit-key>",
  "parentUnitId": "<root-unit-key-for-a-review-unit-only>",
  "auditClass": "changeset",
  "auditKind": "<coherence-or-review-unit>",
  "subject": "<subject>",
  "coverageRequirement": "required",
  "coverageStatus": "<audited-or-incomplete>",
  "priorContext": {
    "changedFilePartition": "<base>..<head>",
    "concernPartition": "<coherence-or-review-unit>"
  },
  "expectedProducer": {
    "producerKind": "skill",
    "agentName": "<runDriver.agentName>",
    "agentOwningPluginName": "<runDriver.agentOwningPluginName>",
    "skillName": "audit-changeset-coherence",
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

Add a unit with `spx verification run scope add --verification-type audit --scope-type changeset --scope <base>..<head> --run <token> --payload <payload-file> --idempotency-key '<unitId>'`. The root unit omits the `parentUnitId` field.

Add a finding with `spx verification run finding add` and the same selectors, `--payload <payload-file>`, and `--idempotency-key '<finding-key>'`, the finding key `<unitId>:<rule>`. One unit and rule yield one finding, which names every location it covers. Its payload names an accepted unit; `producerIdentity` repeats that unit's `expectedProducer`; `producerProvenance` carries the spec-tree plugin version the request contract retained in both version fields, and no `toolVersion`; `rule` is one identifier from the rule catalog in `${CLAUDE_SKILL_DIR}/references/coherence-model.md`, and `severity` is the severity that row declares; name no identifier outside that catalog.

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
  "location": "<changed-path-or-cluster-and-scope>",
  "message": "<finding-message-naming-the-rule-and-the-evidentiary-gap>",
  "evidence": {
    "observed": "<observed-state>",
    "expected": "<state the rule requires>"
  }
}
```

A `split-required` finding sits on the root. Its `evidence.observed` lists every cluster on its own line as `cluster-<n> | outcome: <outcome> | authored: <paths> | generated: <paths> | verification: <story> | rollback: <story> | depends_on: <cluster-ids-or-none> | load: <review-load-signals-or-none>`. Its `evidence.expected` carries the review-unit sequence, one line per review unit in dependency order as `review-unit-<n> | clusters: <cluster-ids> | depends_on: <review-unit-ids-or-none>`, covering every cluster exactly once.

A `missing-*` finding sits on the `incomplete` unit. Its `message` and `evidence.observed` name the cause: the artifact, the relationship, or the read that could not be established. The `incomplete` unit is the review unit whose cluster needs the evidence, or the root when no cluster can be formed.

These objects are the sanctioned payload schema for this audit; never derive a replacement from command help or CLI source.

</persistence_contract>

<payload_files>

Quote every idempotency key as one single-quoted argument; encode a literal apostrophe with the splice `'"'"'`.

- ALWAYS write the start input and each scope and finding payload with the file-write tool to its own file in the scratch directory the harness names for the session, under a name unique to this run and payload, such as `<run-token>-scope-<n>.json` and `<run-token>-finding-<n>.json`. Where the harness names no scratch directory, use the one the hosting environment designates, such as `$RUNNER_TEMP` on a hosted runner.
- ALWAYS write only payload files with the file-write tool.
- ALWAYS pass `--payload` and `--input` the path exactly as the file-write tool's result reports it, copied from that result, never retyped.
- ALWAYS add each unit and each finding with its own literal command and its own payload file, one at a time, and stop the audit at the first command that exits nonzero, returning the `BLOCKED` diagnostic.
- NEVER remove a payload file; the harness clears its scratch directory.

</payload_files>
