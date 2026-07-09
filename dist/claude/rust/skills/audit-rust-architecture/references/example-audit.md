<example_verdict>

This ADR-target example is the complete JSON output for a rejected Rust architecture audit. It includes only Rust-specific architecture concerns; generic ADR section structure, atemporal voice, and tag validity are absent because the composing artifact-type auditor owns them.

```json
{
  "schema_version": 1,
  "skill": "audit-rust-architecture",
  "target": "spx/example.enabler/15-command-runner.adr.md",
  "overall": "FAIL",
  "rows": [
    {
      "name": "testability-in-verification",
      "status": "FAIL",
      "findings": [
        {
          "rule": "missing-testability",
          "file": "spx/example.enabler/15-command-runner.adr.md",
          "message": "`## Verification` does not require external command execution to flow through an injected trait or function seam; add an ALWAYS rule requiring the seam so command construction can be audited independently from process execution."
        }
      ]
    },
    {
      "name": "mocking-prohibition",
      "status": "FAIL",
      "findings": [
        {
          "rule": "generated-mock-seam",
          "file": "spx/example.enabler/15-command-runner.adr.md",
          "message": "`mockall` is named as the controlled implementation; dependency injection must inject a real trait implementation or function seam, not a generated mock framework double."
        }
      ]
    },
    { "name": "level-accuracy", "status": "PASS", "findings": [] },
    {
      "name": "anti-patterns",
      "status": "FAIL",
      "findings": [
        {
          "rule": "level-assignment-table",
          "file": "spx/example.enabler/15-command-runner.adr.md",
          "message": "A level assignment table appears in the Rust architecture decision; remove the table and keep level selection in the testing workflow while the ADR states the seam that makes the levels possible."
        }
      ]
    },
    { "name": "ancestor-consistency", "status": "PASS", "findings": [] }
  ],
  "metadata": { "branch": "work/example" }
}
```

</example_verdict>
