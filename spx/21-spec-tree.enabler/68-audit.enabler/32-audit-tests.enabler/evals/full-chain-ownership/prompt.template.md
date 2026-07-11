<!-- Generated from the {producer_section_name} concern at {producer_path}. -->

This eval runs in the isolated verifier context required by the producer concern below. The runner substitutes only the case's `input` object into `{input_json}`; grader expectations remain withheld from the producer. Required language-concern composition has already succeeded, as recorded in `input.language_composition`. Apply the selected language-neutral concern to the supplied test-evidence package. Return only the structured JSON verdict defined by that concern.

{producer_section}
The test-evidence package (JSON-encoded):

```json
{input_json}
```
