<objective>

The scope-unit, accounting-record, and finding payload shapes that `spx verification run scope add` and `finding add` accept for an implementation audit.

</objective>

<contents>

- `scope_payload`
- `accounting_payload`
- `finding_payload`

</contents>

<scope_payload>

Every scope payload uses the published SPX field names below. Emit one scope
unit per subject path and concern partition; `subject` and
`priorContext.changedFilePartition` are strings, never path arrays. Emit only
the fields shown. The `producerProvenance` object is optional for a scope unit
and is omitted for `coverage-gap`; when present, both plugin-version fields are
required.

```json
{
  "unitId": "<stable-scope-key>",
  "auditClass": "implementation",
  "auditKind": "<code|tests|architecture|coverage-gap>",
  "subject": "<the exact resolved path>",
  "coverageRequirement": "<required|optional>",
  "coverageStatus": "<audited|not-applicable|missing-skill|unsupported>",
  "priorContext": {
    "changedFilePartition": "<the exact resolved path>",
    "languagePartition": "<selected-kind-when-known>",
    "concernPartition": "<code|tests|architecture|coverage-gap>"
  },
  "expectedProducer": {
    "producerKind": "skill",
    "agentName": "<run-driver-agent-name>",
    "agentOwningPluginName": "<run-driver-agent-owning-plugin-name>",
    "skillName": "<selected-audit-skill>",
    "skillOwningPluginName": "<selected-audit-skill-plugin>",
    "invocationRole": "leaf-skill"
  },
  "recordedByRunDriver": "<the six producer fields of the run-driver identity>",
  "producerProvenance": {
    "agentOwningPluginVersion": "<spec-tree-plugin-version>",
    "skillOwningPluginVersion": "<selected-audit-skill-plugin-version>",
    "toolVersion": "<spx-version-when-known>"
  }
}
```

`languagePartition` is the only optional prior-context field. Omit it when the
kind is unknown; never replace `priorContext` with top-level partition
fields. Use `coverage-gap` with `producerProvenance` omitted, because no leaf
skill executed, for a missing producer, an unsupported subject, and the
accounting record the `<coverage_model>` of SKILL.md requires for an unclaimed resolved path.

</scope_payload>

<accounting_payload>

The `coverageStatus` values in `<scope_payload>` are the required-unit set. An optional unit
may additionally carry `skipped`; no unit carries `incomplete`. The accounting
record for a resolved path no concern claimed is this complete payload — every
field shown is required, and `producerProvenance` is omitted:

```json
{
  "unitId": "implementation:unknown:coverage-gap:<the exact resolved path>",
  "auditClass": "implementation",
  "auditKind": "coverage-gap",
  "subject": "<the exact resolved path>",
  "coverageRequirement": "optional",
  "coverageStatus": "skipped",
  "priorContext": { "changedFilePartition": "<the exact resolved path>", "concernPartition": "coverage-gap" },
  "expectedProducer": "<the six producer fields of the run-driver identity>",
  "recordedByRunDriver": "<the six producer fields of the run-driver identity>"
}
```

When the selection names an artifact-type audit skill for the path, its
accounting record names it: `unitId` carries the selection's kind in place of
`unknown`, and `expectedProducer` is the producer shape of a concern unit with
that `skillName`, that `skillOwningPluginName`, and `invocationRole`
`leaf-skill`; each selected artifact-type skill gets its own record.

</accounting_payload>

<finding_payload>

Every finding payload uses the exact published SPX field names below. Its
`unitId` references a scope unit already accepted by the run, its
`producerIdentity` matches that unit's `expectedProducer`, and observed versus
expected text lives under `evidence`.

```json
{
  "unitId": "<accepted-scope-unit-id>",
  "producerIdentity": "<the unit's expectedProducer object, repeated exactly>",
  "producerProvenance": "<the unit's producerProvenance object, repeated exactly>",
  "rule": "<violated-rule-or-principle>",
  "severity": "<blocking|debt>",
  "location": "<path-and-line-or-subject-location>",
  "message": "<finding-message>",
  "evidence": {
    "observed": "<observed-state>",
    "expected": "<required-state>"
  }
}
```

</finding_payload>
