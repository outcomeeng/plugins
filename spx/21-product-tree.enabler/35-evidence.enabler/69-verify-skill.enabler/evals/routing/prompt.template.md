<!-- Generated from the complete producer set:
{producer_paths}
-->

Apply the complete verification-routing producer below to the supplied request. The runner substitutes only the request's `input` object into `{input_json}`; grader expectations remain withheld from the producer.

The request's `available_specialists` array is the authoritative projection of the runtime skill catalog for this invocation.

The request's optional `specialist_report` object carries the result a specialist already returned for this assertion: `specialist` names the specialist, `status` its reported status, and `verification_type_to_select` the verification type that report names.

Return exactly one JSON object with these fields:

- `verification_type`: `test`, `evaluate`, `probe`, `audit`, or `null`
- `specialist`: `/test`, `/eval`, `/probe`, `isolated-verifier`, or `null`
- `status`: `routed`, `capability-required`, or `blocked`
- `evidence_shape`: `path-bearing`, `pathless`, or `null`
- `reason`: a concise string

<pre><code>
{producer_files}
</code></pre>

The verification request (JSON-encoded):

```json
{input_json}
```
