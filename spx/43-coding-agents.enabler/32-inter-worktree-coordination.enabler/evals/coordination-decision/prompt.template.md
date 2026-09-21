<!-- Generated from the complete producer set:
{producer_paths}
-->

This is an isolated, non-mutating behavioral evaluation. The JSON below is a
synthetic case fixture, and the complete producer sources are the subject under
evaluation. Compute the coordination decision those producers specify for the
fixture. Treat fixture identities and checked-result fields as valid observations
inside this case only; do not claim they describe a live system. Resolve each
fixture path according to the Prowl producer and construct each planned message
according to the messaging producer. Return exactly the coordinator's structured
JSON decision so the deterministic grader can score it. Invoke no external tool
and send no message; this evaluation asks only for the planned output.

<pre><code>
{producer_files}
</code></pre>

The authoritative coordination evidence (JSON-encoded):

```json
{input_json}
```
