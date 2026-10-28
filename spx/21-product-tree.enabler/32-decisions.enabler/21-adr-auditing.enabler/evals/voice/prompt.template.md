<!-- Generated from the complete producer at {producer_path}. -->

Apply the complete producer's audit workflow to the supplied ADR input as an already-collected file. The input's `target` is the ADR path and its `adr_markdown` is the complete file content. Do not read a file, run a command, write a payload file, or persist an SPX verification run for this eval case, and skip the producer's request-contract, plugin-version, context-loading, run-command, language-composition, and touched-text classification steps: treat the ADR as language-neutral and every line of it as touched text, so every finding is recorded on its unit.

Return only one JSON object that reports the sealed run the producer would record, with these members:

- `terminalStatus`: `approved` or `rejected`, derived by the producer's verdict rules.
- `units`: every unit the producer records, the root unit first and then the child units for section structure, atemporal voice, and tag validity in that order. Each unit carries `unitId`, `auditKind`, `subject`, and `coverageStatus`, plus `parentUnitId` on each child; omit `parentUnitId` on the root and omit every other member of the recording contract.
- `findings`: every finding the producer records, each with `unitId`, `rule`, `severity`, `location`, and `evidence` holding `observed` and `expected`. The array is empty when the run records no finding.

---

{producer_file}
The ADR input (JSON-encoded):

```json
{input_json}
```
