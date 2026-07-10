<example_verdict>

This ADR-target example is the complete JSON output for a rejected TypeScript architecture audit. It includes only TypeScript-specific architecture concerns; generic ADR section structure, atemporal voice, and tag validity are absent because the composing artifact-type auditor owns them.

```json
{
  "schema_version": 1,
  "skill": "audit-typescript-architecture",
  "target": "spx/example.enabler/15-build-runner.adr.md",
  "overall": "REJECTED",
  "rows": [
    {
      "name": "testability-in-verification",
      "status": "FAIL",
      "findings": [
        {
          "rule": "missing-testability",
          "file": "spx/example.enabler/15-build-runner.adr.md",
          "severity": "blocking",
          "message": "The ADR leaves build orchestration without an enforceable runner seam.",
          "observed": "Verification rules do not require build orchestration to accept the source-owned runner parameter.",
          "expected": "Verification rules require the dependency-injected runner used by build orchestration."
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
          "severity": "blocking",
          "message": "The architecture defines a framework mock as the injected build runner.",
          "observed": "The decision names vi.fn() as a fake runner and provides no Stage 5 exception classification.",
          "expected": "The architecture defines a real function or object seam and classifies every permitted test double."
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
          "severity": "blocking",
          "message": "The architecture assigns a local execution level to a remote SaaS boundary.",
          "observed": "The decision classifies a SaaS-hosted deployment API as l2.",
          "expected": "Remote SaaS behavior is l3; isolated local behavior is classified independently at l1."
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
