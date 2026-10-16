<!-- Generated from the complete producer at {producer_path}. -->

Apply the complete producer below to the supplied spec node. When the input carries `context`, treat it as the governing methodology context loaded by the producer's contextualization step.

This evaluation supplies the spec node as `spec_markdown` at the path `target`, runs no `spx` command, and writes no run file. Perform the producer's judgment steps against the supplied text and report the sealed run those steps would finish. Treat all of the supplied spec text as touched text, so every finding the producer's rules support is recorded on its unit and decides the terminal status. Return only one JSON object with these fields:

- `terminalStatus`: `approved` when the run records no finding, `rejected` when it records at least one.
- `findings`: one object per recorded finding, each carrying `unitId` (the `spec:property:<property>:<target>` key of the unit that records it) and `rule` (an identifier from the producer's rule catalog). The list is empty when the run records no finding.

{producer_file}
The spec-node input (JSON-encoded):

```json
{input_json}
```
