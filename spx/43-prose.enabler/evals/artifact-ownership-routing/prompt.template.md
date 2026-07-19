<!-- Generated from the complete producer at {producer_path}.

     Probe scope: the eval verifies the internal-doc catalog's scope boundary —
     whether artifact ownership or reader audience decides which surface handles a
     request. The catalog's own scope rules are the only routing authority; this
     template supplies the request and the verdict shape, never the rules. -->

Apply the complete producer below to the supplied request. Decide which surface governs the artifact and which skill handles the request, using only the producer's own scope rules.

{producer_file}
The routing request (JSON-encoded):

```json
{input_json}
```

Input fields:

- `request`: the user's phrasing of what they want done.
- `artifact`: the artifact's path or workspace location, or `"none"` when unstated.
- `reader`: who reads the artifact.

Verdict schema — three fields, all mandatory:

- `scope`: `"INTERNAL_DOC"` when the internal-doc catalog governs the artifact, `"GOVERNED_ELSEWHERE"` when a repository or domain workflow owns it, `"EXTERNAL_PROSE"` when it is written for strangers.
- `route`: `"write-internal-docs"`, `"audit-internal-docs"`, `"governing-repository-skill"`, `"write-prose"`, or `"audit-prose"`.
- `precedence_reason`: `"workspace-native"`, `"repository-governed"`, or `"external-audience"`.

Return only a parseable JSON document matching the schema.
