<objective>

The recording contract of the changeset-coherence audit: the units and payload objects that `spx verification run` accepts, and the payload-file procedure for every recording command.

</objective>

<contents>
- `persistence_contract`
- `payload_files`

</contents>

<persistence_contract>

Add a scope unit with `spx verification run scope add --verification-type audit --scope-type changeset --scope <scope> --run <token> --payload <payload-file> --idempotency-key '<unitId>'`, the payload file written per `<payload_files>`. The class `changeset` is the class `spx` accepts for this audit; its root takes kind `coherence` and every child takes kind `review-unit`. A child names the root as its parent and nests no further. `spx` keeps only the members this contract shows, so every recorded fact sits in one of them.

| Level | `unitId`                               | `parentUnitId`      | Created for                                                                                                                          |
| ----- | -------------------------------------- | ------------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| Root  | `<scope>`                              | omitted             | The committed changeset, `<base>..<head>` from the two full commit identities; the run admits one root                               |
| Child | `coherence:cluster-<n>`                | the root's `unitId` | Each semantic cluster that survives collapse, `<n>` its position in dependency order                                                 |
| Child | `coherence:unresolved:<path-or-scope>` | the root's `unitId` | Each changed artifact whose behavioral claim or generated-source producer cannot be established, and `scope` for missing calibration |

The root unit:

```json
{
  "unitId": "<scope>",
  "auditClass": "changeset",
  "auditKind": "coherence",
  "subject": "<scope>",
  "coverageRequirement": "required",
  "coverageStatus": "audited",
  "priorContext": {
    "changedFilePartition": "<scope>",
    "concernPartition": "coherence"
  },
  "expectedProducer": {
    "producerKind": "skill",
    "agentName": "<runDriver.agentName>",
    "agentOwningPluginName": "<runDriver.agentOwningPluginName>",
    "skillName": "audit-changeset-coherence",
    "skillOwningPluginName": "product-tree",
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

A cluster child carries the same fields with `auditKind` `review-unit`, its `unitId`, `parentUnitId`, and `coverageStatus` `audited`, or `incomplete` when a finding records missing evidence for the cluster. Its `priorContext.concernPartition` is `cluster-<n>`, and its `priorContext.changedFilePartition` lists the cluster's authored artifacts sorted lexicographically and separated by `;`, followed by `| generated:` and the cluster's generated fanout in the same form when the cluster has any. Its `subject` is one line of the cluster's remaining facts in this order, each as `<name>: <value>` separated by `;`: `outcome` the behavioral outcome, `verification` its verification story, `rollback` its rollback story, `dependencies` the cluster identifiers it depends on or `none`, and `independentlyMergeable` `true`. A story with several entries joins them with `/`; an empty story is written `none`:

```json
{
  "unitId": "coherence:cluster-<n>",
  "parentUnitId": "<scope>",
  "auditClass": "changeset",
  "auditKind": "review-unit",
  "subject": "outcome: <outcome>; verification: <story>; rollback: <story>; dependencies: <cluster-ids-or-none>; independentlyMergeable: true",
  "coverageRequirement": "required",
  "coverageStatus": "audited | incomplete",
  "priorContext": {
    "changedFilePartition": "<authored-paths> | generated: <generated-paths>",
    "concernPartition": "cluster-<n>"
  },
  "expectedProducer": "<the root unit's expectedProducer object, repeated exactly>",
  "recordedByRunDriver": "<the root unit's recordedByRunDriver object, repeated exactly>"
}
```

An unresolved child carries `coverageStatus` `incomplete`, `subject` `<scope>`, `priorContext.changedFilePartition` the artifact path or `<scope>`, and `priorContext.concernPartition` `unresolved`.

Add a finding with `spx verification run finding add` and the same selectors, `--payload <payload-file>` per `<payload_files>`, and `--idempotency-key '<unitId>:<rule>'`, the finding key. Its payload names an accepted unit; `producerIdentity` repeats that unit's `expectedProducer`; `producerProvenance` carries the plugin version `SKILL.md` `<request_contract>` retained in both version fields, and no `toolVersion`; `rule` is an identifier from `${SKILL_DIR}/references/rule-catalog.md`; `location` is the changed path or `scope`. `evidence.observed` and `evidence.expected` are strings; `spx` rejects any other shape and drops any other member of `evidence`.

A `split-required` finding sits on the root unit with `location` `scope`. Its `evidence.observed` carries the recommended sequence, one line per review unit in dependency order, separated by a newline, each line `review-unit-<k>: clusters <cluster-ids>; outcome: <review-unit outcome>; artifacts: <authored and generated paths>; depends_on: <earlier review-unit ids or none>`, and its `evidence.expected` states one cluster, or inseparable clusters with one verification and one rollback story. The sequence covers every cluster exactly once and references only earlier review units in `depends_on`; review units number in the same order as their clusters. A missing-evidence finding sits on the `incomplete` unit that needs the evidence, with the unavailable evidence in `observed` and the required evidence in `expected`; a review-load signal the finding bears on is copied into `observed` without reinterpretation.

```json
{
  "unitId": "<accepted-unit-key>",
  "producerIdentity": "<the unit's expectedProducer object, repeated exactly>",
  "producerProvenance": {
    "agentOwningPluginVersion": "<product-tree-plugin-version>",
    "skillOwningPluginVersion": "<product-tree-plugin-version>"
  },
  "rule": "<catalog-rule-id>",
  "severity": "blocking",
  "location": "<path-or-scope>",
  "message": "<finding>",
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

- ALWAYS copy the scratch directory the harness names for the session into each payload path character for character, and write the start input, each scope payload, and each finding payload with the file-write tool to its own file there, under a name unique to this run and payload, such as `<selector-slug>-start.json` for the start input, which exists before a run token does, and `<run-token>-scope-<n>.json` and `<run-token>-finding-<n>.json`. Where the harness names no scratch directory, use the one the hosting environment designates, such as `$RUNNER_TEMP` on a hosted runner.
- ALWAYS write only payload files with the file-write tool.
- ALWAYS stop before the command that reads a payload file when the file-write result reports a path that the scratch directory does not contain by whole path components, returning the `SKILL.md` `<verdict_format>` diagnostic naming the reported path.
- ALWAYS pass `--payload` and `--input` the path exactly as the file-write tool's result reports it, copied from that result, never retyped from memory.
- ALWAYS pass the file as the value of `--payload`, its path written out literally:

  ```bash
  spx verification run scope add --verification-type audit --scope-type changeset --scope <scope> --run <token> --payload <scope-file> --idempotency-key '<unitId>'
  ```

- ALWAYS add each scope unit and each finding with its own literal command and its own payload file, one at a time, and stop the audit at the first command that exits nonzero, other than the one rerun on an absent-payload diagnostic that the next bullet allows, returning the `SKILL.md` `<verdict_format>` diagnostic.
- A permission refusal is no absent payload file and takes no rerun.
- ALWAYS, when a command exits nonzero with a diagnostic that names its payload file as absent, run that command once more with the path copied from the file-write result; on a second failure, stop with the `SKILL.md` `<verdict_format>` diagnostic naming the run token.
- NEVER remove a payload file; the harness clears its scratch directory.

</payload_files>
