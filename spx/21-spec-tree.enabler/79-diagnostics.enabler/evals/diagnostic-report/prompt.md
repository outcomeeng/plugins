<!-- Prompt template for the diagnostic-report eval.
     The harness substitutes the case id and input JSON tokens
     before sending the prompt to the model. -->

You are the `diagnose` skill aggregating its per-check results into one report. The checks below are already classified (each with its `name`, `verdict`, and aggregation `bucket`). Compute the overall verdict exactly as the skill's `report_format` prescribes.

Overall-verdict precedence over the buckets: **broken** when any check is broken, else **unknown** when any check is `unknown`, else **degraded** when any check is degraded, else **healthy** when every applicable check is healthy. A `not-applicable` check is excluded from the overall; when every check is `not-applicable`, the overall is `not-applicable`.

Case id: substituted by the harness.

The classified checks (JSON-encoded input payload follows):

```json
{input_json}
```

Your **entire response** must be exactly one JSON document — no prose, no markdown fences, no commentary before or after — conforming to this schema:

```
{
  "checks": [
    { "name": "<check name>", "verdict": "<check verdict>", "bucket": "<check bucket>" }
  ],
  "overall": "healthy" | "degraded" | "broken" | "unknown" | "not-applicable"
}
```

Echo each input check in `checks` and set `overall` per the precedence above.
