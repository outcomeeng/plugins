<example_verdict>

This ADR-target example is the complete JSON output for a rejected TypeScript architecture audit. It includes only TypeScript-specific architecture concerns; generic ADR section structure, atemporal voice, and tag validity are absent because the composing artifact-type auditor owns them.

```json
{
  "schema_version": 1,
  "skill": "audit-typescript-architecture",
  "target": "spx/example.enabler/15-build-runner.adr.md",
  "overall": "FAIL",
  "rows": [
    {
      "name": "testability-in-verification",
      "status": "FAIL",
      "findings": [
        {
          "rule": "missing-testability",
          "file": "spx/example.enabler/15-build-runner.adr.md",
          "message": "`## Verification` does not require build orchestration to accept a dependency-injected runner parameter; add an ALWAYS rule requiring the runner seam so command construction can be audited independently from process execution."
        }
      ]
    },
    {
      "name": "mocking-prohibition",
      "status": "FAIL",
      "findings": [
        {
          "rule": "mocking-language",
          "file": "spx/example.enabler/15-build-runner.adr.md",
          "message": "`vi.fn()` is named as the controlled implementation and the ADR also calls it a fake runner without naming a `/test` exception case; dependency injection must inject a real function or object, and any test double language must name the applicable exception case."
        }
      ]
    },
    {
      "name": "level-accuracy",
      "status": "FAIL",
      "findings": [
        {
          "rule": "saas-l2",
          "file": "spx/example.enabler/15-build-runner.adr.md",
          "message": "The decision assigns `l2` to a SaaS-hosted deployment API; SaaS behavior has no local level, so isolated command construction is `l1` and real API verification is `l3`."
        }
      ]
    },
    { "name": "anti-patterns", "status": "PASS", "findings": [] },
    { "name": "ancestor-consistency", "status": "PASS", "findings": [] }
  ],
  "metadata": { "branch": "work/example" }
}
```

</example_verdict>
