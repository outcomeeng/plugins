<!-- Generated from the complete producer set:
{producer_paths}
-->

Apply the complete verification-routing producer below to the supplied request. The runner substitutes only the request's `input` object into `{input_json}`; grader expectations remain withheld from the producer.

The request's `available_specialists` array is the authoritative projection of the runtime skill catalog for this invocation.

Return exactly one JSON object with these fields:

- `verification_type`: `test`, `evaluate`, `audit`, or `null`
- `specialist`: `/test`, `/eval`, `isolated-verifier`, or `null`
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
