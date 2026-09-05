<examples>

The skill's entire output is the JSON concern verdict. These examples show `PASS`, `FAIL`, and `NOT_APPLICABLE`; the audit runs no deterministic verification.

<example name="pass">

```json
{
  "schema_version": 1,
  "skill": "audit-go-code",
  "target": "internal/config/",
  "overall": "APPROVED",
  "rows": [
    { "name": "function-comprehension", "status": "PASS", "findings": [] },
    { "name": "design-coherence", "status": "PASS", "findings": [] },
    { "name": "import-structure", "status": "PASS", "findings": [] },
    {
      "name": "concurrency-soundness",
      "status": "NOT_APPLICABLE",
      "explanation": "scope contains no goroutine, channel, sync primitive, or context-accepting function",
      "findings": []
    },
    {
      "name": "unsafe-soundness",
      "status": "NOT_APPLICABLE",
      "explanation": "scope contains no unsafe conversion or cgo site",
      "findings": []
    },
    { "name": "adr-pdr-compliance", "status": "PASS", "findings": [] }
  ],
  "metadata": { "branch": "<branch>" }
}
```

</example>

<example name="fail">

```json
{
  "schema_version": 1,
  "skill": "audit-go-code",
  "target": "internal/orders/",
  "overall": "REJECTED",
  "rows": [
    {
      "name": "concurrency-soundness",
      "status": "FAIL",
      "findings": [
        {
          "file": "internal/orders/processor.go",
          "line": 42,
          "rule": "goroutine-no-owner",
          "severity": "blocking",
          "message": "The notification goroutine is launched with no owner and no exit condition, so cancellation never reaches it and every request leaks one goroutine.",
          "observed": "Process launches `go notify(order)` with no context, errgroup, or wait group",
          "expected": "the goroutine is owned by an errgroup bound to the request context and exits on cancellation"
        }
      ]
    }
  ],
  "metadata": { "branch": "<branch>" }
}
```

</example>

</examples>
