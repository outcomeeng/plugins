<!-- Producer-derived prompt template for the audit-specs structure eval. -->

Use the selected producer section `{producer_section_name}` from `{producer_path}` as the audit policy for this case.

<producer-section>
{producer_section}
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
