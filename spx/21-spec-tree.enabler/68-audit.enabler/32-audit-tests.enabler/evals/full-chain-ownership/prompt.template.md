<!-- Generated from the complete producer at {producer_path}. -->

This eval runs in the isolated verifier context required by the producer below. The runner substitutes only the case's `input` object into `{input_json}`; grader expectations remain withheld from the producer. Apply the complete producer to the supplied test-evidence package. This assertion begins after required language-concern composition succeeds: the caller has classified the package as TypeScript, and the package carries the passing TypeScript concern result. Judge the language-neutral evidence chain only. Return only the producer's structured JSON verdict.

{producer_file}
The test-evidence package (JSON-encoded):

```json
{input_json}
```
