<!-- Generated from the complete producer at src/plugins/product-tree/skills/diagnose/SKILL.md. -->

Apply the complete producer below as the `diagnose` skill whose first workflow step already ran. Run no command. The captured result of that run, `spx diagnose --manifest "${CLAUDE_SKILL_DIR}/manifest.json" --format json`, follows the producer, with stdout parsed when it holds a report.

---
name: diagnose
description: >-
  ALWAYS invoke this skill when diagnosing the health of a product-tree or spx
  environment, when checking whether the SessionStart hook fired for the current
  session, or when troubleshooting a missing session identity, worktree claim,
  or unreachable spx CLI. NEVER guess why session state is missing without
  running these checks first.
allowed-tools: Read, Bash(spx diagnose:*)
---

<objective>

A deterministic environment-diagnostics report from `spx diagnose`, relayed with
remediation judgment for every non-healthy verdict.

</objective>

<workflow>

1. Run `spx diagnose --manifest "${CLAUDE_SKILL_DIR}/manifest.json" --format json`.
   The JSON report names each check, its verdict, and its bucket, which the
   remediation items carry; the default text report names none of them.
2. Preserve stdout, stderr, and the exit code exactly. Session identifiers,
   version strings, paths, marketplace names, plugin names, verdict names, and
   status values are identity values; report them verbatim.
3. Relay the `spx diagnose` report without reclassifying any check and without
   recomputing the overall verdict.
4. When the report's overall verdict is non-healthy, add remediation judgment
   grounded only in the report's per-check verdicts, readings, and remediation
   fields: one remediation item per non-healthy check, naming that check, its
   verdict, and its bucket as the item's severity.
5. When the command cannot start, the `diagnose` subcommand is missing, the
   manifest is rejected, or the exit code is nonzero before a report is emitted,
   relay the startup failure: stdout, stderr, and the exit code verbatim. Add no
   remediation item, because no report carries a verdict to ground one.

</workflow>

<constraints>

- NEVER classify environment readings in this skill body. Classification lives
  in `spx diagnose`.
- NEVER fold per-check verdicts into an overall verdict in this skill body. The
  overall verdict is `spx diagnose` output.
- NEVER edit the manifest at runtime or substitute values into the command by
  hand. The build renders the manifest before the plugin ships.

</constraints>

<success_criteria>

- Every check verdict, reading, and the overall verdict in the relayed report
  match the `spx diagnose` output character for character.
- Each remediation statement traces to a per-check verdict, reading, or
  remediation field of the report.
- A startup failure appears with stdout, stderr, and exit code verbatim, and with
  no remediation item.
- The skill body contains no check classification table and no overall-verdict
  fold.

</success_criteria>

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
