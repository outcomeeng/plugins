<!-- Generated from the complete producer at {producer_path}. -->

This eval runs in the isolated verifier context required by the producer below. The runner substitutes only the case's `input` object into `{input_json}`; grader expectations remain withheld from the producer. Apply the complete producer to the supplied test-evidence package. This assertion begins after required language-concern composition succeeds: treat `input.language_composition` as the authoritative completed Step 3f result, do not invoke or re-run any language-specific concern skill, and judge only the language-neutral evidence chain. Return only the producer's structured JSON verdict.

{producer_file}
The test-evidence package (JSON-encoded):

```json
{input_json}
```
