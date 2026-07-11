<!-- Generated from {producer_path}, section {producer_section_name}. -->

Apply the complete producer workflow below to the supplied ADR input. Treat the caller's scope classification as language-neutral; the supplied ADR content is the context for this curated eval case.

{producer_section}

The ADR input (JSON-encoded):

```json
{input_json}
```

Return only this `audit-adr` JSON shape, replacing placeholders and adding findings where a row fails:

```json
{
  "schema_version": 1,
  "skill": "audit-adr",
  "target": "<copy input target>",
  "overall": "APPROVED | REJECTED",
  "rows": [
    {"name": "section-structure", "status": "PASS | FAIL | NOT_APPLICABLE", "findings": []},
    {"name": "atemporal-voice", "status": "PASS | FAIL | NOT_APPLICABLE", "findings": []},
    {"name": "tag-validity", "status": "PASS | FAIL | NOT_APPLICABLE", "findings": []}
  ],
  "metadata": {"branch": "<branch>"}
}
```

Every finding has `rule`, `severity` (`blocking`), `location`, `message`, `observed`, and `expected`. The `rule` is exactly one of `missing-section`, `temporal-voice`, `invalid-tag`, `evidence-type-mismatch`, `template-missing`, `language-routing-unavailable`, or `language-skill-unavailable`.
