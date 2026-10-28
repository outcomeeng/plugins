<!-- Generated from the complete producer at {producer_path}. -->

Apply the complete producer's semantic classification workflow to the supplied evidence packet as an already-collected changeset subject. Do not inspect a repository, run a command, write a payload file, or persist an SPX verification run for this eval case, and skip the producer's request-contract, plugin-version, scope-resolution, and run-command steps: the packet's `scope` supplies the two full commit identities, and the run identity `<scope>` is `<base>..<head>` from them.

Return only one JSON object that reports the sealed run the producer would record, with these members:

- `terminalStatus`: `approved` or `rejected`, derived by the producer's verdict rules.
- `scope`: `{"base": "<full-commit-id>", "head": "<full-commit-id>"}`, the packet's identities verbatim.
- `units`: every unit the producer records, the root unit first and then each cluster unit in dependency order, then each unresolved unit. Each unit carries the members the producer's recording contract shows, except `unitId`, `parentUnitId`, `auditKind`, `subject`, `coverageStatus`, and `priorContext`: omit `parentUnitId` on the root, and omit `auditClass`, `coverageRequirement`, `expectedProducer`, and `recordedByRunDriver`.
- `findings`: every finding the producer records, each with `key`, `unitId`, `rule`, `severity`, `location`, and `evidence` holding `observed` and `expected`. The array is empty when the run records no finding.

Where the recording contract names a list without naming its separator, sort the entries lexicographically and join them with `,`.

---

{producer_file}
The changeset evidence packet (JSON-encoded):

```json
{input_json}
```
