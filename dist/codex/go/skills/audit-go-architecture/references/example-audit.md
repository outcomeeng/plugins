<example_verdict>

This ADR-target example is the complete JSON output for a rejected Go architecture audit. It includes only Go-specific architecture concerns; generic ADR section structure, atemporal voice, and tag validity are absent because the composing artifact-type auditor owns them.

```json
{
  "schema_version": 1,
  "skill": "audit-go-architecture",
  "target": "spx/example.enabler/15-command-runner.adr.md",
  "overall": "REJECTED",
  "rows": [
    {
      "name": "testability-in-verification",
      "status": "FAIL",
      "findings": [
        {
          "rule": "missing-testability",
          "file": "spx/example.enabler/15-command-runner.adr.md",
          "severity": "blocking",
          "message": "The ADR leaves external command execution without an enforceable injection seam.",
          "observed": "Verification rules do not require command execution to flow through an injected interface or function.",
          "expected": "Verification rules require the source-owned command-execution seam."
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
          "severity": "blocking",
          "message": "The architecture defines a generated mock as the injected command runner.",
          "observed": "The decision names a mockery-generated double as the controlled implementation of the runner boundary.",
          "expected": "The architecture defines a real interface implementation or function seam without a generated mock."
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
          "severity": "blocking",
          "message": "The architecture decision owns execution-level selection instead of the testing workflow.",
          "observed": "The ADR contains a table assigning execution levels to evidence paths.",
          "expected": "The ADR defines architecture seams while the testing workflow selects execution levels."
        }
      ]
    },
    { "name": "ancestor-consistency", "status": "PASS", "findings": [] }
  ],
  "metadata": { "branch": "work/example" }
}
```

</example_verdict>
