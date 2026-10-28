<!-- Generated from the complete producer set:
{producer_paths}
-->

Apply the complete producer below to the supplied PDR as the file-scoped audit its request contract describes: the input's `target` is the PDR path, `pdr_markdown` is the PDR's complete committed content, and `context` (when present) holds the product document and ancestor decisions the context-loading step reads. Treat the PDR as absent at the base, so every location in it is touched text and no finding is returned as `filed`. Do not inspect a repository, run a command, write a payload file, or persist an SPX verification run for this eval case, and skip the producer's request-contract, plugin-version, and run-command steps: the run identity `<path>` is the input's `target`.

Return only one JSON object that reports the sealed run the producer would record, with these members:

- `terminalStatus`: `approved` or `rejected`, derived by the producer's verdict rules.
- `units`: the root unit first, then the five child units. Each unit carries `unitId`, `parentUnitId` (omitted on the root), `auditKind`, `subject`, and `coverageStatus`.
- `findings`: every finding the producer records, each with `key`, `unitId`, `rule`, `severity`, `location`, and `evidence` holding `observed` and `expected`. The array is empty when the run records no finding.

<pre><code>
{producer_files}
</code></pre>

The PDR input (JSON-encoded):

```json
{input_json}
```
