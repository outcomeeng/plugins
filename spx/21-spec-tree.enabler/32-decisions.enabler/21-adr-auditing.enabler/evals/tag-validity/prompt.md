<!-- Prompt template for the ADR-auditing tag-validity eval.
     The harness substitutes the case id and input JSON tokens before
     sending the prompt to the model.

     Probe scope: verification tag validity for the audit-adr verdict
     contract. -->

You are simulating the `audit-adr` skill for one ADR document.

Audit the ADR evidence model in this order:

1. `section-structure`: an ADR has a title, an opening decision statement before the first `##` heading, and a `## Verification` section. `## Rationale` and `## Invariants` are optional. Verification subsections are limited to `### Testing`, `### Eval`, and `### Audit`.
2. `atemporal-voice`: ADR text uses durable present-tense architecture truth. Reject temporal narration such as `previously`, `now`, `will`, `going to`, `used to`, `migrate`, `transition`, and past-tense decision history.
3. `tag-validity`: each verification rule uses a tag valid for its subsection, and a `### Testing` tag's evidence type fits the claim's quantifier. Two distinct failures, each with its own finding rule:
   - **`invalid-tag`** — the tag is structurally wrong for its subsection: a missing tag, a bare mechanism tag (`[test]` or `[review]`) where an evidence type is required, a tag that disagrees with its subsection (`[audit]` under `### Eval`, `[eval]` under `### Audit`), or more than one tag. `### Testing` requires exactly one assertion-type tag from `scenario`, `mapping`, `conformance`, `property`, or `compliance`; `### Eval` requires `eval`; `### Audit` requires `audit`.
   - **`evidence-type-mismatch`** — the `### Testing` tag is a structurally valid evidence type but contradicts the claim's quantifier. A universal claim (`ALWAYS` / `NEVER` / "for all" / "for every" / "no input") is never `scenario`, because a scenario proves one case and cannot establish a claim about every case; `scenario` fits only a single existential interaction. A universal claim tagged `[scenario]` is `evidence-type-mismatch`, not `invalid-tag` — the tag is legal for `### Testing`, but wrong for the claim.

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

- `rule`: one of `missing-section` (section-structure), `temporal-voice` (atemporal-voice), `invalid-tag` (a tag structurally wrong for its subsection), or `evidence-type-mismatch` (a `### Testing` evidence type that contradicts the claim's quantifier, such as a universal claim tagged `[scenario]`)
- `message`: a concise description

Return `overall: "PASS"` only when all three rows pass.
