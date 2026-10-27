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

1. Run `spx diagnose --manifest "${CLAUDE_SKILL_DIR}/manifest.json"`.
2. Preserve stdout, stderr, and the exit code exactly. Session identifiers,
   version strings, paths, marketplace names, plugin names, verdict names, and
   status values are identity values; report them verbatim.
3. Relay the `spx diagnose` report without reclassifying any check and without
   recomputing the overall verdict.
4. When the report's overall verdict is non-healthy, add remediation judgment
   grounded only in the report's per-check verdicts, readings, and remediation
   fields.
5. When the command cannot start, the `diagnose` subcommand is missing, the
   manifest is rejected, or the exit code is nonzero before a report is emitted,
   report stdout, stderr, and the exit code verbatim, then direct the user to
   install or update `@outcomeeng/spx` to the floor declared in the manifest.

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
- A startup failure appears with stdout, stderr, and exit code verbatim, followed
  by the install-or-update direction.
- The skill body contains no check classification table and no overall-verdict
  fold.

</success_criteria>
