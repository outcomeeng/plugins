<!-- Prompt template for the ADR-auditing structure eval.
     The harness substitutes the case id and input JSON tokens before
     sending the prompt to the model.

     Probe scope: section structure for the audit-adr verdict contract. -->

You are simulating the `audit-adr` skill for one ADR document.

Audit the ADR evidence model in this order:

1. `section-structure`: an ADR has a title, an opening decision statement before the first `##` heading, and a `## Verification` section. `## Rationale` and `## Invariants` are optional. Verification subsections are limited to `### Testing`, `### Eval`, and `### Audit`.
2. `atemporal-voice`: ADR text uses durable present-tense architecture truth. Reject temporal narration such as `previously`, `now`, `will`, `going to`, `used to`, `migrate`, `transition`, and past-tense decision history.
3. `tag-validity`: each verification rule uses a tag valid for its subsection. `### Testing` uses one assertion-type tag from `scenario`, `mapping`, `conformance`, `property`, or `compliance`; `### Eval` uses `eval`; `### Audit` uses `audit`. A universal `ALWAYS` or `NEVER` claim is never `scenario`.

Case id: {case_id}

The ADR input (JSON-encoded):

```json
{input_json}
```

Return a JSON document with this exact top-level shape:

- `schema_version`: `1`
- `skill`: `"audit-adr"`
- `target`: copy `target` from the input
- `overall`: `"PASS"`, `"FAIL"`, or `"UNKNOWN"`
- `rows`: exactly three row objects named `section-structure`, `atemporal-voice`, and `tag-validity`, in that order
- `metadata`: an object containing `branch`

Each row has:

- `name`: the row name
- `status`: `"PASS"`, `"FAIL"`, or `"UNKNOWN"`
- `findings`: an array

When a row fails, include at least one finding object with:

- `rule`: one of `missing-section`, `temporal-voice`, `invalid-tag`, or `evidence-type-mismatch`
- `message`: a concise description

Return `overall: "PASS"` only when all three rows pass.
