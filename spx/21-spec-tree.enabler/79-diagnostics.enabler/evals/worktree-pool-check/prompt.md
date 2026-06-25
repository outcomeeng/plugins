<!-- Prompt template for the worktree-pool-check eval.
     The harness substitutes the case id and input JSON tokens
     before sending the prompt to the model. -->

You are the `diagnose` skill running its `worktree-pool` check. Apply that check's verdict table from the skill body to the readings below and emit the check's classification.

The readings stand in for what the check gathers at runtime: `bare_repository` is whether the repository's git-common-dir is bare (from `git worktree list --porcelain` / `git rev-parse`), and `worktrees` is the list of worktrees with each one's `occupancy` as `spx worktree status` reports it (`running` or `free`). When a reading carries an `error` field, the underlying command failed.

Classify exactly as the skill's table prescribes:

- A lone working tree (not bare, a single worktree) or a bare-repository pool (bare, with linked worktrees) is **compliant**.
- Linked worktrees attached to a non-bare repository is **non-compliant**.
- A command error or an unclassifiable reading falls to **unknown** per the workflow's step-4 fallback.

Case id: substituted by the harness.

The readings (JSON-encoded input payload follows):

```json
{input_json}
```

Your **entire response** must be exactly one JSON document — no prose, no markdown fences, no commentary before or after — conforming to this schema:

```
{
  "check": "worktree-pool",
  "verdict": "compliant" | "non-compliant" | "unknown",
  "bucket": "healthy" | "degraded" | "broken" | "unknown",
  "remediation": "<remediation hint string, or null when the verdict is compliant>"
}
```

Bucket mapping from the skill's verdict table: `compliant` → healthy; `non-compliant` → broken; `unknown` → unknown. Every verdict except `compliant` carries a non-null remediation hint.
