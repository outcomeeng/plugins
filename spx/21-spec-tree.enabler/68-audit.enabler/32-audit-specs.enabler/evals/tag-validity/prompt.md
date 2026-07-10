<!-- Producer-derived prompt template for the audit-specs tag-validity eval. -->

Use the selected producer section `audit_tag_fitness` from `src/plugins/spec-tree/skills/audit-specs/SKILL.md` as the audit policy for this case.

<producer-section>
<step name="audit_tag_fitness">

**Step 5: Per-assertion tag fitness**

For each assertion under `## Assertions`:

1. The assertion carries exactly one verification-type tag — `([test](path))` and `([eval](path))` carry a path; `([audit])` is bare by design, and `([review])` is its compatibility form, also bare. A missing tag, a tag carried more than once, or a `[test]` or `[eval]` mechanism tag with no path is invalid; a bare `([audit])` or `([review])` is valid.
2. Under `[test]`, the assertion type fits the claim's quantifier — apply the quantifier rule from `<essential_principles>` (a universal is never `scenario`). Reject a type the `/test` router would not produce; do not relitigate a choice the router leaves open between equally valid types.
3. The tag is reachable for the claim's subject. A `[test]` tag is reachable for a parseable runtime or configuration contract when deterministic evidence parses the artifact and checks a structural contract such as field presence, schema conformance, registered command shape, generated output shape, or configured section names. When the claim's subject is the semantic content of authored prose or documentation rather than an executable or parseable contract, `[test]` is unreachable — its only evidence reads the authored text and asserts on it (directly or through a fixture or harness that exposes or reads the artifact), proving the prose was authored rather than that code behaves. The tag belongs in `[eval]` (a graded judgment over the producer's structured verdict) or `[audit]` (a semantic constraint).

**A missing tag, a duplicate tag, or a bare mechanism tag → REJECT — "invalid-tag." A `[test]` assertion type that contradicts the claim's quantifier → REJECT — "evidence-type-mismatch." `[test]` on a claim whose subject is semantic authored prose content rather than executable or parseable structure → REJECT — "prose-coupling."**

</step>
</producer-section>

Probe focus: assertion tag validity and assertion-type fitness for the `audit-specs` verdict contract.

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
