<!-- Prompt template for the session-environment-check eval.
     The harness substitutes the case id and input JSON tokens
     before sending the prompt to the model. -->

You are the `diagnose` skill running its `session-environment` check. Apply that check's verdict table from the skill body to the readings below and emit the check's classification.

The readings stand in for what the check gathers at runtime: the harness session variables (`CLAUDE_SESSION_ID`, `CLAUDE_WORKTREE_CLAIMED`, `CLAUDE_PROJECT_DIR`), the `spx worktree status --format json` result (its `.status` field, or an `error` when the command fails), and whether the current runtime ships the spec-tree `SessionStart` hook (`runtime_ships_hook`). Classify exactly as the skill's table prescribes, including the runtime-scoping rule (a runtime that ships no such hook is `not-applicable`) and the step-4 fallback (inconsistent readings or a command error fall to `unknown`).

Case id: substituted by the harness.

The readings (JSON-encoded input payload follows):

```json
{input_json}
```

Your **entire response** must be exactly one JSON document — no prose, no markdown fences, no commentary before or after — conforming to this schema:

```
{
  "check": "session-environment",
  "verdict": "working" | "identity-only" | "silent no-op" | "not-applicable" | "unknown",
  "bucket": "healthy" | "degraded" | "broken" | "not-applicable" | "unknown",
  "remediation": "<remediation hint string, or null when the verdict is healthy or not-applicable>"
}
```

Bucket mapping from the skill's verdict table: `working` → healthy; `identity-only` → degraded; `silent no-op` → degraded; `not-applicable` → not-applicable; `unknown` → unknown. Every verdict except `working` and `not-applicable` carries a non-null remediation hint.
