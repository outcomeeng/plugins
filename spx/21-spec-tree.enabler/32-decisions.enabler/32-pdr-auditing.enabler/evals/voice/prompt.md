<!-- Prompt template for the PDR-auditing voice eval.
     The harness substitutes the case id and input JSON tokens before
     sending the prompt to the model.

     Probe scope: atemporal voice for the audit-pdr verdict contract. -->

You are simulating the `audit-pdr` skill for one PDR document.

Audit the PDR evidence model in this order:

1. `content-classification`: every statement is observable product behavior or an observable non-functional property. A technology choice, implementation approach, data structure, or schema belongs in an ADR or code, not a PDR — reject it as architecture or implementation content. ("Sessions expire after 1 hour" is product behavior; "Sessions use JWT with a 1-hour TTL" is architecture.)
2. `property-quality`: every product property is observable from the user's perspective and falsifiable. A property observable only to an implementer (for example database row-level locking, connection-pool sizing) or one that cannot be falsified is not a product property.
3. `tag-validity`: each verification rule uses a tag valid for its subsection. `### Testing` uses one assertion-type tag from `scenario`, `mapping`, `conformance`, `property`, or `compliance`; `### Eval` uses `eval`; `### Audit` uses `audit`. A structural tag problem — a bare mechanism tag (`test`/`review`), a tag that disagrees with its subsection, a missing tag, or more than one tag — is finding `invalid-tag`. A `### Testing` rule whose assertion type contradicts the claim's quantifier — most clearly a universal `ALWAYS`/`NEVER` claim tagged `scenario`, which a single-case scenario cannot establish — is finding `assertion-type-mismatch`.
4. `atemporal-voice`: PDR text uses durable present-tense product truth. Reject temporal narration such as `we discovered`, `previously`, `currently`, `now`, `will`, `after feedback`, `used to`, and past-tense decision history.
5. `consistency`: the PDR does not contradict the product spec or an ancestor PDR. The input may include a `context` field carrying product-spec or ancestor-PDR excerpts; when present, check the PDR against them and reject a direct contradiction.

Case id: {case_id}

The PDR input (JSON-encoded):

```json
{input_json}
```

Return a JSON document with this exact top-level shape:

- `schema_version`: `1`
- `skill`: `"audit-pdr"`
- `target`: copy `target` from the input
- `overall`: `"PASS"`, `"FAIL"`, or `"UNKNOWN"`
- `rows`: exactly five row objects named `content-classification`, `property-quality`, `tag-validity`, `atemporal-voice`, and `consistency`, in that order
- `metadata`: an object containing `branch`

Each row has:

- `name`: the row name
- `status`: `"PASS"`, `"FAIL"`, or `"UNKNOWN"`
- `findings`: an array

When a row fails, include at least one finding object with:

- `rule`: one of `architecture-content`, `non-observable-property`, `invalid-tag`, `assertion-type-mismatch`, `temporal-language`, or `consistency-violation`
- `message`: a concise description

Return `overall: "PASS"` only when all five rows pass.
