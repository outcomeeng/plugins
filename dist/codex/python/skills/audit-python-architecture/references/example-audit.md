<example_verdict>

This ADR-target example is the complete JSON output for a rejected Python architecture audit. It includes only Python-specific architecture concerns; generic ADR section structure, atemporal voice, and tag validity are absent because the composing artifact-type auditor owns them.

```json
{
  "schema_version": 1,
  "skill": "audit-python-architecture",
  "target": "spx/example.enabler/15-trakt-list-provider.adr.md",
  "overall": "REJECTED",
  "rows": [
    {
      "name": "testability-in-verification",
      "status": "FAIL",
      "findings": [
        {
          "rule": "missing-testability",
          "file": "spx/example.enabler/15-trakt-list-provider.adr.md",
          "severity": "blocking",
          "message": "The ADR leaves list operations without an enforceable dependency-injection seam.",
          "observed": "The decision defines TraktListProvider but its Verification rules do not require list operations to accept that protocol.",
          "expected": "Verification rules require the source-owned provider seam used by list operations."
        }
      ]
    },
    {
      "name": "mocking-prohibition",
      "status": "FAIL",
      "findings": [
        {
          "rule": "mocking-language",
          "file": "spx/example.enabler/15-trakt-list-provider.adr.md",
          "severity": "blocking",
          "message": "The architecture prescribes a replacement mock as the provider seam.",
          "observed": "An ADR example names respx.mock as the intended Trakt provider boundary.",
          "expected": "The architecture defines a dependency-injected provider boundary without framework replacement mocks."
        }
      ]
    },
    {
      "name": "level-accuracy",
      "status": "FAIL",
      "findings": [
        {
          "rule": "saas-l2",
          "file": "spx/example.enabler/15-trakt-list-provider.adr.md",
          "severity": "blocking",
          "message": "The architecture assigns a local execution level to a remote SaaS boundary.",
          "observed": "The decision classifies Trakt.tv API behavior as l2.",
          "expected": "Remote SaaS behavior is l3; isolated local behavior is classified independently at l1."
        }
      ]
    },
    { "name": "anti-patterns", "status": "PASS", "findings": [] },
    { "name": "ancestor-consistency", "status": "PASS", "findings": [] },
    {
      "name": "test-double-exception-cases",
      "status": "FAIL",
      "findings": [
        {
          "rule": "missing-test-double-exception",
          "file": "spx/example.enabler/15-trakt-list-provider.adr.md",
          "severity": "blocking",
          "message": "The architecture permits a test double without an applicable exception classification.",
          "observed": "The decision allows a controlled provider double without naming a Stage 5 exception case.",
          "expected": "Every permitted test double is justified by one applicable Stage 5 exception case."
        }
      ]
    }
  ],
  "metadata": { "branch": "work/example" }
}
```

</example_verdict>
