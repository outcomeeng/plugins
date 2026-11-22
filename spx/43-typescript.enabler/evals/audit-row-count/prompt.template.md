<!-- Generated from the complete producer at {producer_path}. -->

Apply the complete producer below at the point where it reports completion. `/verify` routed the spec that follows the producer; read that spec as the routed source artifact and apply the producer's `<audit_requirement_handoff>` to it. Write no code and run no command.

{producer_file}
The routed spec (JSON-encoded, with its path in `target` and its text in `spec_markdown`):

```json
{input_json}
```

Return exactly one JSON document with no markdown fences or prose outside it. Put the number of rows the producer treats as audit-routed in `audit_row_count`, and one entry per such row in `audit_requirements`, each with `source_artifact`, `exact_subject` and `status`; `audit_requirements` is an empty array when the count is zero.

```json
{
  "audit_row_count": 0,
  "audit_requirements": [
    { "source_artifact": "<full spx/... path>", "exact_subject": "<exact row text>", "status": "preserved" }
  ]
}
```
