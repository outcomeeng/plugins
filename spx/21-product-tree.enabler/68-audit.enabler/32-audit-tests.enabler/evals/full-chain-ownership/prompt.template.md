<!-- Generated from the complete producer at {producer_path}. -->

The runner substitutes only the case's `input` object into `{input_json}`; grader expectations remain withheld from the producer. Apply the complete producer below to the supplied test-evidence package as a `path` target, one of the two targets its request contract accepts: the package's `target` names the node whose tests are audited, and its `artifacts` hold the committed contents of every file the audit reads, standing in for the checkout. The package's `language_composition` field is the completed result of the language audit that the producer composes. The run supplies no run-driver identity and no `spx` commands, so judge the package as the producer's audit steps direct, and return only the verdict the run would record as one JSON object: `overall`, the gate `rows` with their `findings`, and `metadata` carrying the evidence chain.

{producer_file}
The test-evidence package (JSON-encoded):

```json
{input_json}
```
