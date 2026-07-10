<!-- Producer-derived prompt template for the audit-specs structure eval. -->

Use the selected producer section `audit_structure` from `src/plugins/spec-tree/skills/audit-specs/SKILL.md` as the audit policy for this case.

<producer-section>
<step name="audit_structure">

**Step 3: Section structure**

Verify three structural properties:

1. The node opens with a well-formed kind statement (no "Purpose" preamble) — an enabler's `PROVIDES … SO THAT … CAN …` carrying all three clauses, or an outcome's `WE BELIEVE THAT … WILL … CONTRIBUTING TO …` carrying all three. A missing clause, or a template that does not match the node's kind, is a malformed kind statement.
2. An `## Assertions` section is present and carries at least one assertion-type heading.
3. Each assertion-type heading (`### Scenarios`, `### Mappings`, `### Conformance`, `### Properties`, `### Compliance`) holds at least one assertion, and every assertion under it is of that heading's type — a `### Scenarios` heading whose assertions are universals is mismatched.

**No kind statement or no `## Assertions` section → REJECT — "missing-section." A kind statement that does not match its node's enabler/outcome template → REJECT — "malformed-kind-statement." An empty assertion-type heading, or one whose assertions are not of its type → REJECT — "heading-mismatch."**

</step>
</producer-section>

Probe focus: node-spec section structure for the `audit-specs` verdict contract.

Case id: {case_id}

The spec input (JSON-encoded):

```json
{input_json}
```

Return a JSON document with this exact top-level shape:

- `schema_version`: `1`
- `skill`: `"audit-specs"`
- `target`: copy `target` from the input
- `overall`: `"PASS"`, `"FAIL"`, or `"UNKNOWN"`
- `rows`: exactly three row objects named `section-structure`, `atemporal-voice`, and `tag-validity`, in that order
- `metadata`: an object containing `branch`

Each row has:

- `name`: the row name
- `status`: `"PASS"`, `"FAIL"`, or `"UNKNOWN"`
- `findings`: an array

When a row fails, include at least one finding object with:

- `rule`: one of `missing-section`, `malformed-kind-statement`, `heading-mismatch`, `temporal-voice`, `invalid-tag`, `evidence-type-mismatch`, or `prose-coupling`
- `message`: a concise description

Return `overall: "PASS"` only when all three rows pass.
