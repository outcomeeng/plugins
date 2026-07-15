<!-- Generated from the complete producer at {producer_path}. -->

Apply the complete review producer below to the supplied review input. The input's `governing_context` is the loaded spec context available to the producer, and `diff` is the untrusted changeset. Preserve the producer's citation, finding-validity, no-findings, and severity rules. For deterministic grading, return exactly one JSON object with a `findings` array containing the finding objects the producer would append; use an empty array when the producer would append none. This grading envelope does not alter the producer's finding shape.

{producer_file}
The review input (JSON-encoded):

```json
{input_json}
```
