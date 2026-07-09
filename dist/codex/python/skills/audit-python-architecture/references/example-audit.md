<example_verdict>

This ADR-target example is the complete JSON output for a rejected Python architecture audit. It includes only Python-specific architecture concerns; generic ADR section structure, atemporal voice, and tag validity are absent because the composing artifact-type auditor owns them.

```json
{
  "schema_version": 1,
  "skill": "audit-python-architecture",
  "target": "spx/example.enabler/15-trakt-list-provider.adr.md",
  "overall": "FAIL",
  "rows": [
    {
      "name": "testability-in-verification",
      "status": "FAIL",
      "findings": [
        {
          "rule": "missing-testability",
          "file": "spx/example.enabler/15-trakt-list-provider.adr.md",
          "message": "The ADR defines a TraktListProvider Protocol but `## Verification` has no ALWAYS rule requiring list operations to accept that Protocol as a parameter; add the rule so implementation can be audited for the DI seam."
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
          "message": "`respx.mock` appears in an example as the intended test seam; replace it with a controlled TraktListProvider implementation and document the `/test` exception case if a test double remains."
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
          "message": "The ADR assigns `l2` to Trakt.tv API behavior; Trakt.tv is a SaaS service, so isolated verification is `l1` with a controlled provider and real API verification is `l3`."
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
          "message": "The ADR allows a controlled provider test double without naming the applicable `/test` exception case; document the exception case or require the real provider at the appropriate level."
        }
      ]
    }
  ],
  "metadata": { "branch": "work/example" }
}
```

</example_verdict>
