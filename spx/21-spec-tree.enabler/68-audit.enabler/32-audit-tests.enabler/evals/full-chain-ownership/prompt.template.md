<!-- Generated from the complete producer at {producer_path}. -->

The runner substitutes only the case's `input` object into `{input_json}`; grader expectations remain withheld from the producer. Apply the complete producer below to the supplied test-evidence package. The package's `language_composition` field carries the completed result of the language-specific audit the producer composes, so treat it as that composed result and validate it as the producer's language-result step requires.

This evaluation supplies the audited node as `target`, its one `[test]` assertion as `assertion`, the linked test and every artifact of its evidence chain in `artifacts`, runs no `spx` command, and writes no run file. Perform the producer's judgment steps against the supplied package and report the sealed run those steps would finish. Treat all of the supplied text as touched text, so every finding the producer's rules support is recorded on its unit and decides the terminal status. Return only one JSON object with these fields:

- `terminalStatus`: `approved` when the run records no finding, `rejected` when it records at least one.
- `findings`: one object per recorded finding, each carrying `unitId` (the key of the unit that records it, formed by the producer's unit identities with the package's `target` as the spec and the supplied assertion as ordinal 1) and `rule` (an identifier from the producer's rule catalog). The list is empty when the run records no finding.

{producer_file}
The test-evidence package (JSON-encoded):

```json
{input_json}
```
