<!-- Generated from the complete producer at {producer_path}.

     Probe scope: the eval verifies that the review skill itself declines a
     repository-governed artifact and routes its review to the governing
     workflow. The producer's own scope and ownership rules are the only routing
     authority; this template supplies the request and the verdict shape, never
     the rules. -->

Apply the complete producer below to the supplied request. Decide whether this skill reviews the artifact or routes it elsewhere, using only the producer's own rules.

{producer_file}
The review request (JSON-encoded):

```json
{input_json}
```

Input fields:

- `request`: the user's phrasing of the review they want.
- `artifact`: the artifact's path or workspace location.
- `reader`: who reads the artifact.

Verdict schema — three fields, all mandatory:

- `handles`: `"YES"` when this skill reviews the artifact, `"NO"` when it declines.
- `route`: `"this-skill"`, `"governing-repository-skill"`, or `"prose-skill"`.
- `reason`: `"workspace-native"`, `"repository-governed"`, or `"external-audience"`.

Return only a parseable JSON document matching the schema.
