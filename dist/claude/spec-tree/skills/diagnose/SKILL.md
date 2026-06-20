---
name: diagnose
description: >-
  ALWAYS invoke this skill when diagnosing the health of a spec-tree or spx
  environment, when checking whether the SessionStart hook fired for the current
  session, or when troubleshooting a missing session identity, worktree claim,
  or unreachable spx CLI. NEVER guess why session state is missing without
  running these checks first.
allowed-tools: Bash, Read
---

<objective>

Diagnose the health of a spec-tree / spx environment and report a named verdict per check with a remediation hint. Run a sequence of independent read-only checks over surfaces every environment has — the `spx` CLI, the harness session environment, and the git worktree layout, with further surfaces listed under `<extending>` — classify each, and aggregate one report.

Every check is read-only. It inspects environment variables and queries `spx` with non-mutating status commands; it never changes credentials, runs workflows, writes session state, or edits files.

</objective>

<workflow>

1. Run each check in `<checks>`. Capture each reading verbatim — session identifiers, version strings, and `spx` status fields are reported exactly as their source emits them, NEVER paraphrased or rounded.
2. Classify each check's readings against its verdict table. A check yields exactly one verdict, and each verdict maps to one aggregation bucket — healthy, degraded, broken, or not-applicable — named in the check's table; a not-yet-classifiable reading falls to `unknown` per step 4. Pair each verdict with the matching remediation hint.
3. Aggregate into one report per `<report_format>`: one line per check plus an overall verdict.
4. When a reading is ambiguous, matches no verdict row (an inconsistent partial state), or a command errors, report the check as `unknown` with the captured readings rather than forcing a verdict — a misread check is worse than an honest gap.

</workflow>

<checks>

<check name="session-environment">

Verifies that the runtime's `SessionStart` hook delivered the session environment for the current session. The spec-tree plugin ships this hook for the Claude Code runtime: it writes the agent session identity and project directories into the harness environment and records a worktree-occupancy claim. This check reads the observable traces of that work.

The check applies only on a runtime that ships such a hook. On a runtime that does not — for example Codex, where the `CLAUDE_*` variables are never set — report `not-applicable` rather than classifying against the table below; absent variables there mean "no such hook here," not a failed hook.

Read the three harness variables and the `spx` worktree status, running the status query from inside the repository worktree:

```bash
echo "id=${CLAUDE_SESSION_ID:-UNSET} claimed=${CLAUDE_WORKTREE_CLAIMED:-UNSET} proj=${CLAUDE_PROJECT_DIR:-UNSET}"
spx worktree status --format json
```

`spx worktree status --format json` reports the worktree state in its `.status` field (`occupied`, `unclaimed`, or `stale`). A `stale` reading for the current worktree — a lingering claim from a dead session — matches no row below and falls to `unknown` per step 4. Classify:

| Reading                                                                                                    | Verdict            | Bucket         | Remediation                                                                                                                                                                                                                   |
| ---------------------------------------------------------------------------------------------------------- | ------------------ | -------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `id` is a session identifier, `claimed=1`, `proj` set, and worktree status reports the worktree `occupied` | **working**        | healthy        | None — the hook reached `spx`, which wrote identity and project dirs and claimed the worktree, and `spx` recognizes the claim.                                                                                                |
| `id` is a session identifier, `claimed=UNSET`, worktree status `unclaimed`                                 | **identity-only**  | degraded       | An older hook that does not delegate to `spx` is active for this session. Update the plugin to the version whose `SessionStart` hook delegates to `spx`, then start a new session.                                            |
| `id=UNSET` and worktree status `unclaimed`, on a runtime that ships the hook                               | **silent no-op**   | degraded       | `spx` is not on the hook's PATH, or the hook kill switch is set. Put `spx` on PATH, unset the hook's disable variable, then start a new session. The hook fails open, so nothing is broken — only session identity is absent. |
| The runtime ships no such hook (for example Codex)                                                         | **not-applicable** | not-applicable | None — this runtime has no spec-tree `SessionStart` hook, so session-identity delivery does not apply.                                                                                                                        |

The strongest single signal is worktree status `occupied` together with `claimed=1`: that pair is reachable only when the hook reached `spx`, `spx` claimed the worktree, and the claim's controlling process — the live session — is alive.

This check calls `spx` before the spx-reachability check runs; that ordering is intentional and the two checks classify different conditions. When `spx` is missing from the hook's PATH but installed where the skill runs, this check reads `silent no-op` while spx-reachability reads `reachable`. When `spx` is absent from the system entirely, `spx worktree status` errors and this check falls to `unknown` per step 4 while spx-reachability reads `unreachable`. Neither check depends on the other, so the report's line order is stable.

</check>

<check name="spx-reachability">

Verifies that the `spx` CLI is installed and on PATH, and reports its version.

```bash
command -v spx && spx --version
```

Classify the resolution, reporting the resolved path and version verbatim:

| Reading                                      | Verdict         | Bucket  | Remediation                                                                                      |
| -------------------------------------------- | --------------- | ------- | ------------------------------------------------------------------------------------------------ |
| `spx` resolves on PATH and reports a version | **reachable**   | healthy | None — report the resolved path and version verbatim.                                            |
| `command -v spx` finds nothing               | **unreachable** | broken  | Install `spx` and put it on PATH; the spec-tree skills and the `SessionStart` hook depend on it. |

Comparing the reported version against a required floor is a future extension: it needs a minimum-version declaration the installed plugin tree exposes (no such declaration ships today), so this check reports the version rather than judging it against a floor.

</check>

<check name="worktree-pool">

Verifies the repository's git worktree layout and flags stale occupancy claims. A spec-tree checkout is either a lone working tree or a bare-repository worktree pool; `spx worktree status` reports each worktree's occupancy as `occupied`, `unclaimed`, or `stale` — a claim whose holding session is dead.

Read the worktree set, then query each non-bare worktree's occupancy:

```bash
git worktree list
git worktree list --porcelain |
  awk '/^worktree /{p=substr($0,10);b=0} /^bare$/{b=1} /^$/{if(p&&!b)print p;p=""} END{if(p&&!b)print p}' |
  while IFS= read -r wt; do spx worktree status --format json "$wt"; done
```

`git worktree list --porcelain` puts each worktree on its own `worktree <path>` line and marks the bare entry with a `bare` line; the `awk` extracts the non-bare paths verbatim (spaces preserved) and the loop queries each with single-path `spx worktree status --format json "$wt"` — the path is quoted, so a path containing spaces stays one argument, and the single-path form is the one existing skills already rely on. Each call returns a `{worktree, status}` object whose `status` is `occupied`, `unclaimed`, or `stale`; a bare path is excluded because `spx worktree status` resolves occupancy only for real worktrees. Classify:

| Reading                                                                                               | Verdict           | Bucket   | Remediation                                                                                                                        |
| ----------------------------------------------------------------------------------------------------- | ----------------- | -------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| A lone working tree, or a bare-repository pool with linked worktrees, and no worktree reports `stale` | **compliant**     | healthy  | None — report the layout shape and worktree count.                                                                                 |
| A recognized layout (lone tree or bare pool), but one or more worktrees report `stale`                | **stale-claims**  | degraded | Release each stale claim — run `spx worktree release` from that worktree, or let a live session reclaim it.                        |
| Linked worktrees attached to a non-bare repository                                                    | **non-compliant** | broken   | The layout is neither a lone working tree nor a bare-repository pool. Provision the pool so worktrees attach to a bare repository. |

`spx worktree status` exposes occupancy and staleness; this check reports the worktree set, the layout shape, and any stale claim, but does not re-derive the full repository-layout compliance rules — the repository-name main checkout, the `.spx/` placement beside the git-common-dir. Auditing those is test-bearing classification that belongs in the `spx` CLI; surface it here once `spx` exposes it.

</check>

</checks>

<report_format>

Emit one report. Each check is one line: its name, its verdict, and a trailing detail — the remediation hint when the verdict is not healthy, or the captured readings or error when the verdict is `unknown`. Map each verdict to its bucket per the check's table, then close with an overall verdict over the buckets, in precedence order: **broken** when any check is broken, else **unknown** when any check is `unknown`, else **degraded** when any check is degraded, else **healthy** when every applicable check is healthy. A `not-applicable` check is reported on its own line but excluded from the overall verdict; when every check is `not-applicable`, the overall is **not-applicable**.

```text
diagnose — environment report

  session-environment   unknown — id set, claimed=1, but spx worktree status reports unclaimed
  spx-reachability      reachable — /opt/homebrew/bin/spx, 0.61.0
  worktree-pool         stale-claims — plugins-c holds a stale claim

overall: unknown
```

On a runtime without the spec-tree `SessionStart` hook, that check is reported and excluded from the overall:

```text
diagnose — environment report

  session-environment   not-applicable — runtime has no spec-tree SessionStart hook
  spx-reachability      reachable — /opt/homebrew/bin/spx, 0.61.0
  worktree-pool         compliant — bare-repository pool, 7 worktrees, no stale claims

overall: healthy
```

Report every reading verbatim. Never collapse a session identifier or version string to a summary; downstream comparison against the source depends on the literal value.

</report_format>

<extending>

Each check is an independent named diagnostic: a reading step, a verdict table that maps each reading to a named verdict and its aggregation bucket — healthy, degraded, broken, or not-applicable, with `unknown` for readings that match no row or a command that errors — and a remediation hint per non-healthy state. A check that inspects a runtime-specific surface reports `not-applicable` where that surface is absent rather than misclassifying. Add a check by appending a new `<check>` block and one line to the report — NEVER by restructuring the existing checks. A check MUST remain a light orchestration of surfaces the environment already exposes. Heavy, test-bearing classification logic MUST live in the `spx` CLI — invoked here as one more non-mutating command — never embedded in this skill.

Candidate checks to add by extension: marketplace install state across the Claude and Codex surfaces, and session-store consistency across the `todo` / `doing` / `archive` queues.

</extending>

<success_criteria>

- Every check in `<checks>` ran and reported a single verdict — its named verdict, an honest `unknown` with the captured error, or `not-applicable` where its surface is absent.
- Each reading appears verbatim in the report.
- Each non-healthy verdict carries its remediation hint, and each `unknown` verdict carries the captured readings or error.
- The report closes with an overall verdict over the aggregation buckets in precedence order — broken, else unknown, else degraded, else healthy — with `not-applicable` checks excluded.

</success_criteria>
