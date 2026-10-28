<!-- Generated from the complete producer at {producer_path}. -->

Apply the complete producer below to the supplied spec node, whose `spec_markdown` stands in for the node spec file at `target`. When the input carries `context`, treat it as the governing methodology context loaded by the producer's context step. Do not read a file, run a command, write a payload file, or persist an SPX verification run for this eval case, and skip the producer's request-contract, plugin-version, run-command, and touched-text diff steps: `target` is the audited `<path>`, and the supplied spec is absent at the base, so it is touched in full and every finding it yields is recorded on its unit and rejects.

Return only one JSON object that reports the sealed run the producer would record, with these members:

- `terminalStatus`: `approved` or `rejected`, derived by the producer's verdict rules.
- `units`: every unit the producer records, the root unit first and then the `section-structure`, `atemporal-voice`, and `tag-fitness` child units in that order. Each unit carries `unitId`, `auditKind`, `subject`, `coverageStatus`, and `priorContext` as the producer's persistence contract shows them, and `parentUnitId` on each child: omit `parentUnitId` on the root, and omit `auditClass`, `coverageRequirement`, `expectedProducer`, and `recordedByRunDriver`.
- `findings`: every finding the producer records, each with `key`, `unitId`, `rule`, `severity`, `location`, and `evidence` holding `observed` and `expected`. The array is empty when the run records no finding.

---

{producer_file}
The spec-node input (JSON-encoded):

```json
{input_json}
```
