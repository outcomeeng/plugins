<!-- Prompt template for the session-store-check eval.
     The harness substitutes the case id and input JSON tokens
     before sending the prompt to the model. -->

You are the `diagnose` skill running its `session-store` check. Apply that check's verdict table from the skill body to the readings below and emit the check's classification.

The readings stand in for what the check gathers at runtime: `doing` is the list of in-progress sessions, each already joined to the occupancy of the worktree backing its claim (`backing_worktree` is `running`, `free`, or `absent` — `absent` meaning no worktree exists on the session's `git_ref`); `todo_count` and `archive_count` are the queue sizes. When a reading carries an `error` field, the underlying command failed.

Classify exactly as the skill's table prescribes: the store is **consistent** when it reads and every `doing` session's `backing_worktree` is `running` (including when there are no `doing` sessions); **orphaned-claims** when one or more `doing` sessions have a `backing_worktree` of `free` or `absent` (the holder is gone); and **unknown** when a command errors per the workflow's step-4 fallback.

Case id: substituted by the harness.

The readings (JSON-encoded input payload follows):

```json
{input_json}
```

Your **entire response** must be exactly one JSON document — no prose, no markdown fences, no commentary before or after — conforming to this schema:

```
{
  "check": "session-store",
  "verdict": "consistent" | "orphaned-claims" | "unknown",
  "bucket": "healthy" | "degraded" | "unknown",
  "remediation": "<remediation hint string, or null when the verdict is consistent>"
}
```

Bucket mapping from the skill's verdict table: `consistent` → healthy; `orphaned-claims` → degraded; `unknown` → unknown. Every verdict except `consistent` carries a non-null remediation hint.
