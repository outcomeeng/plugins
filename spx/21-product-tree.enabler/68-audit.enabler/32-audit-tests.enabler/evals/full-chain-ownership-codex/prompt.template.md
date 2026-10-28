<!-- Generated from the complete producer at {producer_path}. -->

The runner substitutes only the case's `input` object into `{input_json}`; grader expectations remain withheld from the producer. Apply the complete producer below to the supplied test-evidence package as a `path` target, one of the two targets its request contract accepts: the package's `target` names the node whose tests are audited, and its `artifacts` hold the committed contents of every file the audit reads, standing in for the checkout. The package's `language_composition` field is the completed result of the language audit that the producer composes. The run supplies no run-driver identity and no `spx` commands, so judge the package as the producer's audit steps direct. Treat the package's `target` as both the audited path and the spec the units name, and its `assertion` as the one `[test]` assertion, ordinal 1. Skip the producer's request-contract, plugin-version, scope-resolution, and run-command steps, and treat every finding as lying on touched text. Return only one JSON object that reports the sealed run the producer would record, with these members:

- `terminalStatus`: `approved` or `rejected`, derived by the producer's verdict rules.
- `units`: every unit the producer records, the root unit first, each carrying `unitId`, `coverageStatus`, and, except on the root, `parentUnitId`.
- `findings`: every finding the producer records, each with `unitId`, `rule`, `severity`, `location`, `message`, `remediationTarget` (the target the message names), and `evidence` holding `observed` and `expected`. The array is empty when the run records no finding.

{producer_file}
The test-evidence package (JSON-encoded):

```json
{input_json}
```
