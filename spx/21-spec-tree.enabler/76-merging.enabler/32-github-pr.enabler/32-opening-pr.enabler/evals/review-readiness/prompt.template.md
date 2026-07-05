<!-- Prompt template for the review-readiness eval.
     Generated from {producer_path} section {producer_section_name}.
     The harness substitutes case input JSON before sending the prompt. -->

Use the producer section below as the authority for `/open-pr` `VERIFICATION_READINESS` behavior. Classify whether `/open-pr` may open a pull request ready for review at the opening mutation point.

Producer section:

```text
{producer_section}
```

Case input:

```json
{input_json}
```

Return exactly one JSON object with these fields:

- `open_decision`: `"OPEN_READY"` or `"WITHHOLD"`.
- `blocking_predicate`: `"deterministic-verification"`, `"evidence-auditor"`, `"local-review"`, or `"none"`.
- `ready_for_review`: `true` or `false`.

Do not include markdown, prose, commentary, caveats, or questions.
