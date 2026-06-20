---
name: diagnose
description: >-
  ALWAYS invoke this skill when diagnosing the health of a spec-tree or spx
  environment, when checking whether the SessionStart hook fired for the current
  session, or when troubleshooting a missing session identity, worktree claim,
  or unreachable spx CLI. NEVER guess why session state is missing without
  running these checks first.
---

<objective>

Diagnose the health of a spec-tree / spx environment and report a named verdict per check with a remediation hint. This is the self-serve form of an interrogation a user would otherwise recall and type by hand: it runs a sequence of independent read-only checks over surfaces every environment has — the `spx` CLI, the harness session environment, and the install state — classifies each, and aggregates one report.

Every check is read-only. It inspects environment variables and queries `spx` with non-mutating status commands; it never changes credentials, runs workflows, writes session state, or edits files.

</objective>

<workflow>

1. Run each check in `<checks>`. Capture each reading verbatim — session identifiers, version strings, and `spx` status fields are reported exactly as their source emits them, NEVER paraphrased or rounded.
2. Classify each check's readings against its verdict table. A check yields exactly one verdict: a healthy state, a degraded state, or a broken state, each paired with the matching remediation hint.
3. Aggregate into one report per `<report_format>`: one line per check plus an overall verdict.
4. When a reading is ambiguous or a command errors, report the check as `unknown` with the captured error rather than forcing a verdict — a misread check is worse than an honest gap.

</workflow>

<checks>

<check name="session-environment">

Verifies that the `SessionStart` hook delivered the session environment for the current session. The hook writes the agent session identity and project directories into the harness environment and records a worktree-occupancy claim; this check reads the observable traces of that work.

Read the three harness variables and the `spx` worktree status, running the status query from inside the repository worktree:

```bash
echo "id=${CLAUDE_SESSION_ID:-UNSET} claimed=${CLAUDE_WORKTREE_CLAIMED:-UNSET} proj=${CLAUDE_PROJECT_DIR:-UNSET}"
spx worktree status --format json
```

Classify:

| Reading                                                                                                    | Verdict           | Remediation                                                                                                                                                                                                                   |
| ---------------------------------------------------------------------------------------------------------- | ----------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `id` is a session identifier, `claimed=1`, `proj` set, and worktree status reports the worktree `occupied` | **working**       | None — the hook reached `spx`, which wrote identity and project dirs and claimed the worktree, and `spx` recognizes the claim.                                                                                                |
| `id` is a session identifier, `claimed=UNSET`, worktree status `unclaimed`                                 | **identity-only** | An older hook that does not delegate to `spx` is active for this session. Update the plugin to the version whose `SessionStart` hook delegates to `spx`, then start a new session.                                            |
| `id=UNSET` and worktree status `unclaimed`                                                                 | **silent no-op**  | `spx` is not on the hook's PATH, or the hook kill switch is set. Put `spx` on PATH, unset the hook's disable variable, then start a new session. The hook fails open, so nothing is broken — only session identity is absent. |

The strongest single signal is worktree status `occupied` together with `claimed=1`: that pair is reachable only when the hook reached `spx`, `spx` claimed the worktree, and the claim's controlling process — the live session — is alive.

</check>

<check name="spx-reachability">

Verifies that the `spx` CLI is installed, on PATH, and new enough for the installed plugins.

```bash
command -v spx && spx --version
```

Classify the resolution and the reported version against the minimum version the installed plugins declare:

| Reading                                                                    | Verdict                   | Remediation                                                                                                    |
| -------------------------------------------------------------------------- | ------------------------- | -------------------------------------------------------------------------------------------------------------- |
| `spx` resolves on PATH and its version is at or above the declared minimum | **reachable-and-current** | None.                                                                                                          |
| `spx` resolves on PATH but its version is below the declared minimum       | **reachable-below-floor** | Upgrade `spx` to at least the declared minimum; the installed plugins assume capabilities the older CLI lacks. |
| `command -v spx` finds nothing                                             | **unreachable**           | Install `spx` and put it on PATH; the spec-tree skills and the `SessionStart` hook depend on it.               |

When the declared minimum cannot be determined in the current environment, report the resolved path and version verbatim and note the floor as undetermined rather than asserting a below-floor verdict.

</check>

</checks>

<report_format>

Emit one report. Each check is one line: its name, its verdict, and — when not healthy — the remediation hint. Close with an overall verdict: **healthy** when every check is in its healthy state, **degraded** when at least one check is in a degraded-but-non-fatal state and none is broken, **broken** when any check is in a broken state.

```text
diagnose — environment report

  session-environment   working
  spx-reachability      reachable-below-floor — upgrade spx to at least the declared minimum

overall: degraded
```

Report every reading verbatim. Never collapse a session identifier or version string to a summary; downstream comparison against the source depends on the literal value.

</report_format>

<extending>

Each check is an independent named diagnostic: a reading step, a verdict table mapping readings to a healthy / degraded / broken state, and a remediation hint per non-healthy state. Add a check by appending a new `<check>` block and one line to the report — NEVER by restructuring the existing checks. A check MUST remain a light orchestration of surfaces the environment already exposes. Heavy, test-bearing classification logic MUST live in the `spx` CLI — invoked here as one more non-mutating command — never embedded in this skill.

Candidate checks to add by extension: marketplace install state across the Claude and Codex surfaces, worktree-pool layout and stale-claim health, and session-store consistency across the `todo` / `doing` / `archive` queues.

</extending>

<success_criteria>

- Every check in `<checks>` ran and reported a single verdict or an honest `unknown` with the captured error.
- Each reading appears verbatim in the report.
- Each non-healthy verdict carries its remediation hint.
- The report closes with an overall verdict derived from the per-check verdicts.

</success_criteria>
