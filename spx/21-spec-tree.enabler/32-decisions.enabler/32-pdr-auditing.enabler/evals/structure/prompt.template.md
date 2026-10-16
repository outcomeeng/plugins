<!-- Generated from the complete producer set:
{producer_paths}
-->

Apply the complete producer below to the supplied PDR. When the input carries `context`, treat it as the product spec, the decision records, and the cited decisions that the producer's context-loading step reads for the PDR.

This evaluation supplies the PDR as `pdr_markdown` at the path `target`, runs no `spx` command, loads no further context, and writes no run file. Treat the producer's request contract, plugin version, and template reads as satisfied. Perform the producer's judgment steps against the supplied text and report the sealed run those steps would finish. Treat all of the supplied PDR text as touched text, so every finding the producer's rules support is recorded on its unit. Return only one JSON object with these fields:

- `terminalStatus`: `rejected` when the run records at least one finding whose catalog severity is `blocking`, `approved` otherwise.
- `findings`: one object per recorded finding, each carrying `unitId` (the key of the unit that records it: `pdr:property:<property>:<target>`, or `pdr:root:<target>` for a finding on the root unit) and `rule` (an identifier from the producer's rule catalog). The list is empty when the run records no finding.

<pre><code>
{producer_files}
</code></pre>

The PDR input (JSON-encoded):

```json
{input_json}
```
