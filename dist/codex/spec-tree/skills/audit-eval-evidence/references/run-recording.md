<objective>

The unit identities, payload schemas, and payload-file rules with which the eval-evidence audit records its run.

</objective>

<contents>

- `<persistence_contract>` — unit identities and the unit and finding payloads
- `<payload_files>` — how a payload reaches a command

</contents>

<persistence_contract>

Every unit carries `auditClass: implementation` and `auditKind: eval-evidence`. The scope `<path>` is the node spec path, and every unit's `subject` and `priorContext.changedFilePartition` are that path. Unit identities:

| Unit | `unitId`                           | `parentUnitId` | `concernPartition`                                                                                                   |
| ---- | ---------------------------------- | -------------- | -------------------------------------------------------------------------------------------------------------------- |
| Root | `eval-evidence:root:<path>`        | omitted        | `eval-evidence`                                                                                                      |
| Gate | `eval-evidence:gate:<gate>:<path>` | the root       | `<gate>`, one of `producer-coupling`, `oracle-independence`, `assertion-alignment`, `falsifiability`, `run-evidence` |

A root unit and a gate unit that was decided are `audited`, whether the gate holds or carries findings. A gate unit of a node with no `[eval]` assertion is `not-applicable`. A gate unit whose inspection could not be completed is `incomplete`. Every unit is `required`, and every unit's `expectedProducer` is this skill.

A scope unit:

```json
{
  "unitId": "<unit-key>",
  "parentUnitId": "<root-unit-key-for-a-child-only>",
  "auditClass": "implementation",
  "auditKind": "eval-evidence",
  "subject": "<path>",
  "coverageRequirement": "required",
  "coverageStatus": "<audited-or-not-applicable-or-incomplete>",
  "priorContext": {
    "changedFilePartition": "<path>",
    "concernPartition": "<eval-evidence-or-gate>"
  },
  "expectedProducer": {
    "producerKind": "skill",
    "agentName": "<runDriver.agentName>",
    "agentOwningPluginName": "<runDriver.agentOwningPluginName>",
    "skillName": "audit-eval-evidence",
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

Add a unit with `spx verification run scope add --verification-type audit --scope-type file --scope <path> --run <token> --payload <payload-file> --idempotency-key '<unitId>'`. The root unit omits the `parentUnitId` field.

Add a finding with `spx verification run finding add` and the same selectors, `--payload <payload-file>`, and `--idempotency-key '<finding-key>'`, the finding key `<unitId>:<rule>`. Its payload names an accepted unit; `producerIdentity` repeats that unit's `expectedProducer`; `producerProvenance` carries the spec-tree plugin version the request contract retained in both version fields, and no `toolVersion`; `rule` is one identifier from the rule catalog that SKILL.md names, and `severity` is the severity that row declares; name no identifier outside that catalog. The finding of an `incomplete` unit is `gate-undecidable`, and its `message` and `evidence.observed` name the cause: the artifact, the command, or the read that could not be completed.

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
  "message": "<finding-message-naming-assertion-property-and-evidentiary-gap>",
  "evidence": {
    "observed": "<observed-state>",
    "expected": "<state the rule requires>"
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
