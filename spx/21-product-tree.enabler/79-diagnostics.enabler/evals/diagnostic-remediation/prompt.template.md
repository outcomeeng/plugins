<!-- Generated from the complete producer at {producer_path}. -->

Apply the complete producer below as the `diagnose` skill whose first workflow step already ran. Run no command. The captured result of that run, `spx diagnose --manifest "${CLAUDE_SKILL_DIR}/manifest.json" --format json`, follows the producer, with stdout parsed when it holds a report.

{producer_file}

The captured `spx diagnose` result (JSON-encoded):

```json
{input_json}
```

Return exactly one JSON document with no markdown fences or prose outside it. Put the relayed report in `relayed` when stdout holds one, or the startup failure's `exit_code`, `stdout`, and `stderr` in `startup_failure` when no report was emitted, never both. Put each remediation item the producer adds in `remediation`, each with `check`, `verdict`, `severity`, and `action`; `remediation` is an empty array when the producer adds none.

```json
{
  "relayed": { "overall": "<verdict>", "checks": [] },
  "startup_failure": { "exit_code": 0, "stdout": "", "stderr": "" },
  "remediation": [
    { "check": "<check name>", "verdict": "<verdict>", "severity": "<bucket>", "action": "<action>" }
  ]
}
```
