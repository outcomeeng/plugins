<objective>

The recording contract of the test-evidence audit: the units and payload objects that `spx verification run` accepts, and the payload-file procedure for every recording command.

</objective>

<contents>
- `persistence_contract`
- `payload_files`

</contents>

<persistence_contract>

Add a scope unit with `spx verification run scope add --verification-type audit --scope-type <scope-type> --scope <scope> --run <token> --payload <payload-file> --idempotency-key '<unitId>'`, the payload file written per `<payload_files>`. The class `spec` and kind `tests` are the pair `spx` accepts for this audit. The units form three levels for a `path` target. A `changeset` target adds one node level: its root unit is `<base>..<head>`, and each audited spec has a node child below it whose assertion children and `not-applicable` child hang from it.

| Level      | `unitId`                                    | `parentUnitId`        | Created for                                                                                                                                                                                                          |
| ---------- | ------------------------------------------- | --------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Root       | `<path>` or `<base>..<head>`                | omitted               | The audited spec file, or the committed changeset; the run admits one root                                                                                                                                           |
| Node       | `tests:node:<spec>`                         | the root's `unitId`   | Each audited spec of a `changeset` target; a `path` target has none                                                                                                                                                  |
| Child      | `tests:assertion-<n>:<spec>`                | the root, or the node | Each `[test]` assertion of `<spec>`, `<n>` its ordinal from Step 4; the parent is the node child for a `changeset` target                                                                                            |
| Grandchild | `tests:assertion-<n>:<concern>:<test-path>` | the assertion's child | Each linked test file, once with `<concern>` `evidence` for the language-neutral concerns, and once per language partition of that file with `<concern>` the language name (`python`, `typescript`, `go`, or `rust`) |
| Child      | `tests:not-applicable:<subject>`            | the root, or the node | Each retired path a language audit reports `NOT_APPLICABLE`, and the spec with no `[test]` assertion, whose `<subject>` is `<spec>`; the parent is the node child for a `changeset` target                           |

An evidence-chain artifact that several assertions reach is recorded once, on the unit of the first assertion whose linked test reaches it, with the artifact in the finding's `location`. The language-neutral findings sit on the `evidence` grandchild, and composed language findings sit on the language grandchild.

The root unit:

```json
{
  "unitId": "<path-or-base..head>",
  "auditClass": "spec",
  "auditKind": "tests",
  "subject": "<path-or-base..head>",
  "coverageRequirement": "required",
  "coverageStatus": "audited",
  "priorContext": {
    "changedFilePartition": "<path-or-base..head>",
    "concernPartition": "tests"
  },
  "expectedProducer": {
    "producerKind": "skill",
    "agentName": "<runDriver.agentName>",
    "agentOwningPluginName": "<runDriver.agentOwningPluginName>",
    "skillName": "audit-tests",
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

A child or grandchild unit carries the same fields with its `unitId`, its `parentUnitId`, `coverageStatus` `audited`, `incomplete`, or, for a `not-applicable` child, `not-applicable`, and `priorContext.concernPartition` the part of its `unitId` after `tests:` and before the final `:<spec>` (`assertion-<n>`, `assertion-<n>:<concern>`, or `not-applicable`); a node child's `concernPartition` is `node`. A child's or grandchild's `subject` is `<spec>`. A grandchild's `changedFilePartition` is its `<test-path>`, and every other unit's is `<spec>`:

```json
{
  "unitId": "<unit-key>",
  "parentUnitId": "<parent-unit-key>",
  "auditClass": "spec",
  "auditKind": "tests",
  "subject": "<spec>",
  "coverageRequirement": "required",
  "coverageStatus": "audited | incomplete | not-applicable",
  "priorContext": {
    "changedFilePartition": "<spec-or-test-path>",
    "concernPartition": "<concern-partition>"
  },
  "expectedProducer": "<the root unit's expectedProducer object, repeated exactly>",
  "recordedByRunDriver": "<the root unit's recordedByRunDriver object, repeated exactly>"
}
```

Add a finding with `spx verification run finding add` and the same selectors, `--payload <payload-file>` per `<payload_files>`, and `--idempotency-key '<unitId>:<rule>'`, the finding key of the touched-text classification. Its payload names an accepted grandchild unit; `producerIdentity` repeats that unit's `expectedProducer`; `producerProvenance` carries the plugin version `SKILL.md` `<request_contract>` retained in both version fields, and no `toolVersion`; `rule` is an identifier from this audit's rule catalog or the catalog of the composed language skill; `location` lists every assertion, declaration, call, or artifact where that rule is violated, named by its text and never by a line number, separated by `;`. The message names the failed property, the evidentiary gap, and the remediation target, one of `source-contract`, `harness`, `generator`, `fixture`, `eval-case`, `test-file`, `source-file`, `test-infrastructure`, `independent-oracle`, `skill-installation`, or `language-partition`. A finding that records the cause of an `incomplete` unit names the unavailable inspection in `observed`.

```json
{
  "unitId": "<accepted-unit-key>",
  "producerIdentity": "<the unit's expectedProducer object, repeated exactly>",
  "producerProvenance": {
    "agentOwningPluginVersion": "<product-tree-plugin-version>",
    "skillOwningPluginVersion": "<product-tree-plugin-version>"
  },
  "rule": "<catalog-rule-id>",
  "severity": "<blocking-or-debt>",
  "location": "<assertion-text>: <declaration-call-or-artifact>[; <further-location>...]",
  "message": "<property>: <evidentiary-gap>; remediation target: <target>",
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

- ALWAYS copy the scratch directory the harness names for the session into each payload path character for character, and write the changeset start input, each scope payload, and each finding payload with the file-write tool to its own file there, under a name unique to this run and payload, such as `<selector-slug>-start.json` for the start input, which exists before a run token does, and `<run-token>-scope-<n>.json` and `<run-token>-finding-<n>.json`. Where the harness names no scratch directory, use the one the hosting environment designates, such as `$RUNNER_TEMP` on a hosted runner.
- ALWAYS write only payload files with the file-write tool.
- ALWAYS stop before the command that reads a payload file when the file-write result reports a path that the scratch directory does not contain by whole path components, returning the `SKILL.md` `<verdict_format>` diagnostic naming the reported path.
- ALWAYS pass `--payload` the path exactly as the file-write tool's result reports it, copied from that result, never retyped from memory.
- ALWAYS pass the file as the value of `--payload`, its path written out literally:

  ```bash
  spx verification run scope add --verification-type audit --scope-type <scope-type> --scope <scope> --run <token> --payload <scope-file> --idempotency-key '<unitId>'
  ```

- ALWAYS add each scope unit and each finding with its own literal command and its own payload file, one at a time, and stop the audit at the first command that exits nonzero, other than the one rerun on an absent-payload diagnostic that the next bullet allows, returning the `SKILL.md` `<verdict_format>` diagnostic.
- A permission refusal is no absent payload file and takes no rerun.
- ALWAYS, when a command exits nonzero with a diagnostic that names its payload file as absent, run that command once more with the path copied from the file-write result; on a second failure, stop with the `SKILL.md` `<verdict_format>` diagnostic naming the run token.
- NEVER remove a payload file; the harness clears its scratch directory.

</payload_files>
