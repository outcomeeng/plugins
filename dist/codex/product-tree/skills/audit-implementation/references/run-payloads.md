Contents:

- Scope payload: fields, accounting record for an unclaimed path, artifact-type accounting
- Finding payload: fields and evidence shape
- Idempotency keys: form, colon-free rule segment, kind segment, quoting
- Payload files: write, path-copy, serial-command, and rerun rules

<objective>

The payload shapes, key forms, and payload-file rules of the implementation audit's `spx verification run` commands, read before the first scope or finding payload is written.

</objective>

<payload_contract>

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
    "agentOwningPluginVersion": "<product-tree-plugin-version>",
    "skillOwningPluginVersion": "<selected-audit-skill-plugin-version>",
    "toolVersion": "<spx-version-when-known>"
  }
}
```

The `coverageStatus` values above are the required-unit set. An optional unit
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

`languagePartition` is the only optional prior-context field. Omit it when the
kind is unknown; never replace `priorContext` with top-level partition
fields. Use `coverage-gap` with `producerProvenance` omitted, because no leaf
skill executed, for a missing producer, an unsupported subject, and the
accounting record `<coverage_model>` requires for an unclaimed resolved path.

Every finding payload uses the exact published SPX field names below. Its
`unitId` references a scope unit already accepted by the run, its
`producerIdentity` matches that unit's `expectedProducer`, and observed versus
expected text lives under `evidence`.

```json
{
  "unitId": "<accepted-scope-unit-id>",
  "producerIdentity": "<the unit's expectedProducer object, repeated exactly>",
  "producerProvenance": "<the unit's producerProvenance object, repeated exactly>",
  "rule": "<rule-identifier-from-a-catalog>",
  "severity": "<blocking|debt>",
  "location": "<path-and-line-or-subject-location>",
  "message": "<finding-message>",
  "evidence": {
    "observed": "<observed-state>",
    "expected": "<required-state>"
  }
}
```

The idempotency key is a command argument, never a payload field. A scope
unit's key is the value its payload carries in `unitId`: audit class, kind
partition, concern partition, and subject path joined with `:` —
`implementation:<kind>:<concern>:<subject-path>`. A finding's key extends its
unit's key with the violated rule — `<stable-scope-key>:<rule>`.

Keep the rule segment colon-free. SPX never parses the key back into segments,
so a `:` inside a subject path is not a separator; a colon-free rule makes the
last `:` the boundary between subject path and rule, and a colon inside the rule
collides two distinct findings on one key.

The key always carries a kind segment, even though
`priorContext.languagePartition` may be omitted. Render an unknown kind as
the literal `unknown`; the key substitutes no default for a segment left out.

Pass every key as one single-quoted argument, `--idempotency-key
'<stable-scope-key>'` — a subject path can carry `|`, `&`, `;`, `(`, `)`, `<`,
`>`, `*`, `?`, or whitespace, and unquoted it splits the command so the shell
runs a fragment as a program. Encode a literal apostrophe with the single-quote
splice `'"'"'`.

Never emit the retired aliases `id`, `subjectPaths`, `expectedProducerIdentity`,
`executionProducerIdentity`, `stableProducerIdentity`, top-level `observed`,
or top-level `expected`; SPX rejects or discards those shapes at the
verification-type boundary.

Write each rendered scope object to its own payload file and pass the file by
path:

```bash
spx -C '{repository-root}' verification run scope add --verification-type audit --scope-type changeset --scope '<base>..<head>' --run '<token>' --idempotency-key '<stable-scope-key>' --payload '<scope-file>'
```

Write each rendered finding object to its own payload file and pass it the same
way:

```bash
spx -C '{repository-root}' verification run finding add --verification-type audit --scope-type changeset --scope '<base>..<head>' --run '<token>' --idempotency-key '<stable-scope-key>:<rule>' --payload '<finding-file>'
```

- ALWAYS copy the scratch directory the harness names for the session into each payload path character for character, and write each scope and finding payload with the file-write tool to its own file there, under a name unique to this run and payload, such as `<run-token>-scope-<n>.json` and `<run-token>-finding-<n>.json`. Where the harness names no scratch directory, use the one the hosting environment designates, such as `$RUNNER_TEMP` on a hosted runner.
- ALWAYS stop before the command that reads a payload file or the audit-input file when the file-write result reports a path that the scratch directory does not contain by whole path components, returning the `<verdict_format>` blocked diagnostic naming the reported path.
- ALWAYS pass `--payload` the path exactly as the file-write tool's result reports it, copied from that result, never retyped from memory; pass `--audit-input` the audit-input path exactly as its file-write result reports it and `--scratch-dir` the scratch directory that contains it; pass `--input` the start-input path named in the resolver's `--output` argument, written out literally.
- ALWAYS write only payload files with the file-write tool, and pass each file as the value of `--payload`, its path written out literally.
- ALWAYS add each scope unit and each finding with its own literal command and its own payload file, one at a time, and stop the audit at the first command that exits nonzero, other than the one rerun on an absent-payload diagnostic that the next bullet allows, returning the `<verdict_format>` blocked diagnostic.
- ALWAYS, when a scope-add or finding-add command exits nonzero with a diagnostic that names its payload file as absent, run that command once more with the `--payload` path copied from the file-write result; on a second failure, stop with the `<verdict_format>` blocked diagnostic naming the run token. A `run start` whose diagnostic names its `--input` file as absent runs no second time, because the resolver wrote that file and no file-write result names it: stop with the `<verdict_format>` blocked diagnostic.
- NEVER send a payload through a heredoc, a pipe, or an inline argument, and never build one with an interpreter or `printf` stage — the dangerous-command guard blocks those forms.
- NEVER remove a payload file; the harness clears its scratch directory.

</payload_contract>
