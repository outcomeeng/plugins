<!-- Prompt template for the diagnostic-remediation eval.
     The harness substitutes the input JSON token before sending the prompt. -->

You are the `diagnose` skill after running this exact command:

```bash
spx diagnose --manifest "${CLAUDE_SKILL_DIR}/manifest.json" --format json
```

The captured command result follows as JSON:

```json
{input_json}
```

Return exactly one JSON document. If stdout contains a diagnostic report, copy
the report into `relayed` without changing check names, verdicts, details,
identity values, or the overall verdict. If the overall verdict is `healthy`,
set `remediation` to an empty array. If the overall verdict is not `healthy`,
add one `remediation` item for each non-healthy check using only that check's
verdict, detail, and remediation field.

If no diagnostic report was emitted because the command failed before startup
or before manifest processing completed, return `startup_failure` with
`exit_code`, `stdout`, and `stderr` copied from the captured result, plus a
`remediation` array that directs the user to install or update
`@outcomeeng/spx` to the manifest floor.

Response schema:

```json
{
  "relayed": { "overall": "<verdict>", "checks": [] },
  "startup_failure": {
    "exit_code": 127,
    "stdout": "<captured stdout>",
    "stderr": "<captured stderr>"
  },
  "remediation": [
    { "check": "<check name>", "verdict": "<verdict>", "action": "<action>" }
  ]
}
```

Use either `relayed` or `startup_failure`. Do not include markdown fences or
prose outside the JSON document.
