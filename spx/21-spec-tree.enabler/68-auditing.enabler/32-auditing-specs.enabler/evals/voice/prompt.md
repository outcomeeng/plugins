<!-- Prompt template for the audit-specs structure eval.
     The harness substitutes the case id and input JSON tokens before
     sending the prompt to the model.

     Probe scope: section structure for the audit-specs verdict contract. -->

You are simulating the `audit-specs` skill auditing one spec node — an enabler or outcome `{slug}.md`.

Decide from this prompt and the input below alone. Use no tools, read no files, and invoke no skills — answer in a single turn, returning only the JSON verdict.

Audit the node in this order:

1. `section-structure`: the node opens with a well-formed kind statement before the first `##` heading — an enabler's `PROVIDES … SO THAT … CAN …` carrying all three clauses, or an outcome's `WE BELIEVE THAT … WILL … CONTRIBUTING TO …` carrying all three. It carries an `## Assertions` section with at least one assertion-type heading (`### Scenarios`, `### Mappings`, `### Conformance`, `### Properties`, `### Compliance`), each holding at least one assertion of that heading's type. A missing kind statement or missing `## Assertions` is `missing-section`; a kind statement missing a clause or using the wrong template for its node kind is `malformed-kind-statement`; an empty assertion-type heading, or one whose assertions are not of its type (a `### Scenarios` heading holding a universal `ALWAYS`/`NEVER` claim), is `heading-mismatch`.
2. `atemporal-voice`: the node states durable present-tense product truth. Reject temporal narration — `previously`, `now`, `will`, `used to`, `migrate`, `transition`, past-tense history. Finding `temporal-voice`.
3. `tag-fitness`: every assertion carries exactly one verification-type tag — `([test](path))` and `([eval](path))` carry a path; `([audit])` and its legacy spelling `([review])` are bare. A missing tag, a duplicate tag, or a `[test]`/`[eval]` tag with no path is `invalid-tag` (a bare `[audit]`/`[review]` is valid). A `[test]` assertion's assertion type must fit the claim's quantifier — a universal (`ALWAYS`/`NEVER`/"for all") is never `scenario`, else `evidence-type-mismatch`. A `[test]` tag on a claim whose subject is the content of an authored prose or documentation artifact (a skill body, a spec body, a prompt) belongs in `[eval]` or `[audit]`, flagged `prose-coupling`.

Case id: {case_id}

The spec node input (JSON-encoded):

```json
{input_json}
```

Return a JSON document with this exact top-level shape:

- `schema_version`: `1`
- `skill`: `"audit-specs"`
- `target`: copy `target` from the input
- `overall`: `"PASS"`, `"FAIL"`, or `"UNKNOWN"`
- `rows`: exactly three row objects named `section-structure`, `atemporal-voice`, and `tag-fitness`, in that order
- `metadata`: an object containing `branch`

Each row has `name`, `status` (`"PASS"` / `"FAIL"` / `"UNKNOWN"`), and `findings` (an array). A failing row's finding object carries `rule` (one of `missing-section`, `malformed-kind-statement`, `heading-mismatch`, `temporal-voice`, `invalid-tag`, `evidence-type-mismatch`, `prose-coupling`) and `message`.

Return `overall: "PASS"` only when all three rows pass.
