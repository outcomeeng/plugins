<!-- Generated from the complete producer at {producer_path}.

     Probe scope: the eval verifies that the writing skill itself declines a
     repository-governed artifact and routes it to the governing workflow. The
     producer's own scope and ownership rules are the only routing authority;
     this template supplies the request and the verdict shape, never the rules. -->

Apply the complete producer below to the supplied request. Decide whether this skill handles the request or routes it elsewhere, using only the producer's own rules.

{producer_file}
The authoring request (JSON-encoded):

```json
{input_json}
```

Input fields:

- `request`: the user's phrasing of what they want written or edited.
- `artifact`: the artifact's path or workspace location.
- `reader`: who reads the artifact.

Verdict schema — three fields, all mandatory:

- `handles`: `"YES"` when this skill writes or edits the artifact, `"NO"` when it declines.
- `route`: `"this-skill"`, `"governing-repository-skill"`, or `"prose-skill"`.
- `reason`: `"workspace-native"`, `"repository-governed"`, or `"external-audience"`.

Return only a parseable JSON document matching the schema.
